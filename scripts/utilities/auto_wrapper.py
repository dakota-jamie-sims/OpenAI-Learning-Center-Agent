#!/usr/bin/env python3
"""
Automatic wrapper for enrichment scripts
Monitors script execution and automatically updates context
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
import argparse

class AutoWrapper:
    """Wraps any script execution with automatic context updates"""
    
    def __init__(self):
        self.start_time = time.time()
        self.script_dir = Path(__file__).parent
        self.update_script = self.script_dir / "update_context.sh"
        
    def run_script(self, script_path, script_args):
        """Run a script and automatically update context based on results"""
        
        # Determine script type from path
        script_type = self._detect_script_type(script_path)
        
        # Capture pre-execution state
        pre_state = self._capture_state()
        
        print(f"🚀 Running {script_path} with auto-context updates...")
        
        try:
            # Run the actual script
            # Try to use venv python if available
            python_exe = sys.executable
            venv_python = Path(self.script_dir).parent.parent / "venv/bin/python"
            if venv_python.exists():
                python_exe = str(venv_python)
                
            result = subprocess.run(
                [python_exe, script_path] + script_args,
                capture_output=True,
                text=True
            )
            
            # Check if script succeeded
            if result.returncode == 0:
                # Capture post-execution state
                post_state = self._capture_state()
                
                # Extract metrics from output or state changes
                metrics = self._extract_metrics(
                    script_type, 
                    pre_state, 
                    post_state, 
                    result.stdout,
                    script_args
                )
                
                # Auto-update context
                self._update_context(script_type, script_args, metrics, success=True)
                
                print("✅ Script completed successfully and context updated!")
            else:
                # Log error
                self._update_context(
                    script_type, 
                    script_args, 
                    {"error": result.stderr[-500:]}, 
                    success=False
                )
                print(f"❌ Script failed with error: {result.returncode}")
                
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
                
            return result.returncode
            
        except Exception as e:
            self._update_context(
                script_type,
                script_args,
                {"error": str(e)},
                success=False
            )
            print(f"❌ Failed to run script: {e}")
            return 1
            
    def _detect_script_type(self, script_path):
        """Detect the type of script being run"""
        path_str = str(script_path).lower()
        
        if 'website_enrichment' in path_str or 'stage1' in path_str:
            return 'stage1'
        elif 'comprehensive_extraction' in path_str or 'stage2' in path_str:
            return 'stage2'
        elif 'fix' in path_str:
            return 'fix'
        elif 'test' in path_str:
            return 'test'
        else:
            return 'custom'
            
    def _capture_state(self):
        """Capture current state (file counts, sizes, etc.)"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'output_files': {}
        }
        
        # Capture output directory state
        output_dir = Path('data/output')
        if output_dir.exists():
            for file in output_dir.glob('*.csv'):
                state['output_files'][str(file)] = {
                    'size': file.stat().st_size,
                    'mtime': file.stat().st_mtime
                }
                
        return state
        
    def _extract_metrics(self, script_type, pre_state, post_state, stdout, args):
        """Extract metrics from execution"""
        metrics = {
            'duration': f"{time.time() - self.start_time:.1f} seconds"
        }
        
        # Find new or modified output files
        new_files = []
        for file, info in post_state['output_files'].items():
            if (file not in pre_state['output_files'] or 
                info['mtime'] > pre_state['output_files'][file]['mtime']):
                new_files.append(file)
                
        if new_files:
            metrics['output_files'] = new_files
            
        # Try to extract metrics from stdout
        if 'success rate' in stdout.lower():
            # Look for percentage patterns
            import re
            rates = re.findall(r'(\d+\.?\d*)%', stdout)
            if rates:
                metrics['success_rate'] = f"{rates[0]}%"
                
        # Count companies processed (look for CSV line counts)
        for file in new_files:
            try:
                with open(file, 'r') as f:
                    line_count = sum(1 for line in f) - 1  # Subtract header
                    metrics['companies_processed'] = line_count
                    break
            except:
                pass
                
        return metrics
        
    def _update_context(self, script_type, args, metrics, success=True):
        """Update context using the automation system"""
        
        # Find output file from args
        output_file = None
        for i, arg in enumerate(args):
            if arg in ['--output', '-o'] and i + 1 < len(args):
                output_file = args[i + 1]
                break
                
        # Build update command
        description = f"{'Completed' if success else 'Failed'} {script_type} execution"
        
        cmd = [
            str(self.update_script),
            script_type,
            description
        ]
        
        if output_file:
            cmd.extend(['--output', output_file])
            
        if metrics:
            cmd.extend(['--metrics', json.dumps(metrics)])
            
        cmd.append('--auto-commit')
        
        try:
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"⚠️ Context update failed: {e}")

def main():
    """Wrapper entry point"""
    if len(sys.argv) < 2:
        print("Usage: auto_wrapper.py <script_path> [script_args...]")
        print("\nExample:")
        print("  python auto_wrapper.py scripts/website_enrichment/enrich_competitors_enhanced_optimized.py --input data.csv --output out.csv")
        sys.exit(1)
        
    script_path = sys.argv[1]
    script_args = sys.argv[2:]
    
    wrapper = AutoWrapper()
    return wrapper.run_script(script_path, script_args)

if __name__ == "__main__":
    sys.exit(main())