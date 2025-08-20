#!/usr/bin/env python3
"""
Context Monitor - Watches for changes and automatically updates context
Runs in background and monitors file system events
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import re

class ContextMonitor(FileSystemEventHandler):
    """Monitor file system for changes and auto-update context"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.update_script = self.project_root / "scripts/utilities/update_context.sh"
        self.last_update = {}
        self.debounce_seconds = 5  # Wait 5 seconds before updating
        
        # Patterns to monitor
        self.output_patterns = {
            'stage1': re.compile(r'enriched.*\.csv$|stage1.*\.csv$', re.I),
            'stage2': re.compile(r'comprehensive.*\.csv$|final.*\.csv$|stage2.*\.csv$', re.I),
            'fix': re.compile(r'fixed.*\.csv$|corrected.*\.csv$', re.I)
        }
        
        self.log_patterns = {
            'completed': re.compile(r'Process completed|Successfully processed|Finished', re.I),
            'error': re.compile(r'ERROR|FAILED|Exception', re.I),
            'stats': re.compile(r'Success rate: ([\d.]+)%|Processed: (\d+)', re.I)
        }
        
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
            
        path = Path(event.src_path)
        
        # Check if it's an output file
        if path.suffix == '.csv' and 'output' in str(path):
            self._handle_output_file(path)
            
    def on_modified(self, event):
        """Handle file modifications"""
        if event.is_directory:
            return
            
        path = Path(event.src_path)
        
        # Monitor log files for completion
        if path.suffix == '.log' and 'logs' in str(path):
            self._handle_log_update(path)
            
    def _handle_output_file(self, filepath):
        """Process new output files"""
        filename = filepath.name
        
        # Debounce - don't update too frequently
        if filename in self.last_update:
            if time.time() - self.last_update[filename] < self.debounce_seconds:
                return
                
        self.last_update[filename] = time.time()
        
        # Determine operation type
        operation = 'custom'
        for op_type, pattern in self.output_patterns.items():
            if pattern.search(filename):
                operation = op_type
                break
                
        # Extract metrics
        metrics = self._analyze_output_file(filepath)
        
        # Update context
        print(f"📊 New output detected: {filename}")
        self._update_context(
            operation,
            f"Auto-detected new output: {filename}",
            str(filepath),
            metrics
        )
        
    def _handle_log_update(self, filepath):
        """Monitor logs for completion signals"""
        try:
            # Read last 50 lines of log
            with open(filepath, 'r') as f:
                lines = f.readlines()[-50:]
                
            content = ''.join(lines)
            
            # Check for completion
            if self.log_patterns['completed'].search(content):
                # Extract stats
                stats = {}
                
                # Look for success rate
                rate_match = self.log_patterns['stats'].search(content)
                if rate_match:
                    if rate_match.group(1):
                        stats['success_rate'] = f"{rate_match.group(1)}%"
                    if rate_match.group(2):
                        stats['processed'] = rate_match.group(2)
                        
                # Find associated output file (mentioned in log)
                output_files = re.findall(r'(data/output/[^\s]+\.csv)', content)
                if output_files:
                    output_file = output_files[-1]  # Most recent mention
                    
                    print(f"✅ Process completed: {filepath.name}")
                    self._update_context(
                        'custom',
                        f"Process completed (from log: {filepath.name})",
                        output_file,
                        stats
                    )
                    
        except Exception as e:
            print(f"Error reading log: {e}")
            
    def _analyze_output_file(self, filepath):
        """Extract metrics from output file"""
        metrics = {}
        
        try:
            # Count rows
            with open(filepath, 'r') as f:
                row_count = sum(1 for line in f) - 1  # Subtract header
                metrics['rows'] = row_count
                
            # File size
            size_mb = filepath.stat().st_size / (1024 * 1024)
            metrics['size'] = f"{size_mb:.1f} MB"
            
            # Creation time
            metrics['created'] = datetime.fromtimestamp(
                filepath.stat().st_mtime
            ).strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            print(f"Error analyzing file: {e}")
            
        return metrics
        
    def _update_context(self, operation, description, output_file, metrics):
        """Call the context update script"""
        cmd = [
            str(self.update_script),
            operation,
            description,
            '--output', output_file,
            '--metrics', json.dumps(metrics),
            '--auto-commit'
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ Context updated for {operation}")
        except Exception as e:
            print(f"⚠️ Context update failed: {e}")
            
    def start_monitoring(self):
        """Start the file system monitor"""
        observer = Observer()
        
        # Monitor key directories
        watch_dirs = [
            self.project_root / "data/output",
            self.project_root / "logs"
        ]
        
        for watch_dir in watch_dirs:
            if watch_dir.exists():
                observer.schedule(self, str(watch_dir), recursive=False)
                print(f"👀 Monitoring: {watch_dir}")
                
        observer.start()
        print("🚀 Context monitor started. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n🛑 Context monitor stopped.")
            
        observer.join()

def main():
    """Run the context monitor"""
    monitor = ContextMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()