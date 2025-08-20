#!/usr/bin/env python3
"""
Automated Context Update System for Unstructured Data Pipeline
Automatically updates context files based on recent operations
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
import subprocess
import argparse

class ContextUpdater:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root or os.getcwd())
        self.context_dir = self.project_root / "context"
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S ET")
        
    def update_journal(self, entry_type, description, details=None):
        """Add entry to JOURNAL.md"""
        journal_path = self.context_dir / "JOURNAL.md"
        
        # Read existing content
        content = journal_path.read_text()
        
        # Find today's section or create it
        today = datetime.now().strftime("%Y-%m-%d")
        today_header = f"## {today}"
        
        if today_header not in content:
            # Add today's section
            new_section = f"\n{today_header} ({datetime.now().strftime('%A')})\n\n"
            # Insert after the first header
            lines = content.split('\n')
            insert_idx = 2  # After title and blank line
            lines.insert(insert_idx, new_section)
            content = '\n'.join(lines)
        
        # Add new entry
        entry = f"\n### {entry_type} ({self.timestamp})\n"
        entry += f"- **Action**: {description}\n"
        if details:
            for key, value in details.items():
                entry += f"- **{key}**: {value}\n"
        
        # Insert entry after today's header
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == today_header:
                # Find next section or end
                insert_idx = i + 2  # After header and blank line
                while insert_idx < len(lines) and not lines[insert_idx].startswith('##'):
                    insert_idx += 1
                lines.insert(insert_idx, entry)
                break
        
        # Write back
        journal_path.write_text('\n'.join(lines))
        print(f"✅ Updated JOURNAL.md with {entry_type}")
        
    def update_todo(self, completed_tasks=None, new_tasks=None):
        """Update TODO.md with completed and new tasks"""
        todo_path = self.context_dir / "TODO.md"
        content = todo_path.read_text()
        
        # Mark completed tasks
        if completed_tasks:
            for task in completed_tasks:
                # Simple pattern matching
                content = re.sub(
                    rf"- \[ \] {re.escape(task)}",
                    f"- [x] {task}",
                    content
                )
        
        # Add new tasks to backlog
        if new_tasks:
            backlog_idx = content.find("### 📋 Backlog")
            if backlog_idx != -1:
                # Find next section
                next_section = content.find("\n##", backlog_idx)
                if next_section == -1:
                    next_section = content.find("\n---", backlog_idx)
                
                # Insert new tasks
                insert_point = content.find("\n\n", backlog_idx) + 2
                new_tasks_text = "\n".join([f"- [ ] {task}" for task in new_tasks])
                content = content[:insert_point] + new_tasks_text + "\n" + content[insert_point:]
        
        # Update timestamp
        content = re.sub(
            r"\*Last updated: .*\*",
            f"*Last updated: {self.timestamp}*",
            content
        )
        
        todo_path.write_text(content)
        print(f"✅ Updated TODO.md")
        
    def create_status_file(self, operation_type, results):
        """Create a status file for an operation"""
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"status_{operation_type}_{date_str}.txt"
        status_path = self.context_dir / filename
        
        content = f"{operation_type.upper()} STATUS\n"
        content += "=" * (len(operation_type) + 7) + "\n"
        content += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        content += f"Time: {datetime.now().strftime('%H:%M ET')}\n\n"
        
        for key, value in results.items():
            if isinstance(value, dict):
                content += f"\n{key.upper()}:\n"
                for k, v in value.items():
                    content += f"- {k}: {v}\n"
            else:
                content += f"{key}: {value}\n"
        
        status_path.write_text(content)
        print(f"✅ Created {filename}")
        return filename
        
    def update_claude_md(self, section, content):
        """Update specific section in CLAUDE.md"""
        claude_path = self.project_root / "CLAUDE.md"
        claude_content = claude_path.read_text()
        
        # Update Current State section
        if section == "Current State":
            pattern = r"(### Current State \(Updated: .*?\))(.*?)(###)"
            new_content = f"### Current State (Updated: {self.timestamp})\n{content}\n"
            claude_content = re.sub(pattern, rf"\g<1>\n{content}\n\g<3>", 
                                   claude_content, flags=re.DOTALL)
        
        claude_path.write_text(claude_content)
        print(f"✅ Updated CLAUDE.md - {section}")
        
    def parse_script_output(self, output_file):
        """Parse output from enrichment scripts"""
        results = {}
        
        if Path(output_file).exists():
            # Count lines (companies processed)
            with open(output_file, 'r') as f:
                line_count = sum(1 for line in f) - 1  # Subtract header
            results['companies_processed'] = line_count
            
            # Try to extract metrics from CSV
            # This would need to be customized based on output format
            
        return results
        
    def auto_commit(self, message):
        """Automatically commit context updates"""
        try:
            subprocess.run(["git", "add", "-A"], cwd=self.project_root)
            subprocess.run(["git", "commit", "-m", message], cwd=self.project_root)
            print(f"✅ Committed: {message}")
        except Exception as e:
            print(f"⚠️ Git commit failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto-update context files")
    parser.add_argument("--operation", required=True, 
                       choices=["stage1", "stage2", "fix", "test", "custom"],
                       help="Type of operation completed")
    parser.add_argument("--description", required=True,
                       help="Brief description of what was done")
    parser.add_argument("--input-file", help="Input file used")
    parser.add_argument("--output-file", help="Output file created")
    parser.add_argument("--metrics", type=json.loads, 
                       help='JSON string of metrics, e.g. \'{"success_rate": "91.3%"}\'')
    parser.add_argument("--completed-tasks", nargs="+", 
                       help="Tasks to mark as completed in TODO.md")
    parser.add_argument("--new-tasks", nargs="+",
                       help="New tasks to add to TODO.md")
    parser.add_argument("--auto-commit", action="store_true",
                       help="Automatically commit changes")
    
    args = parser.parse_args()
    
    updater = ContextUpdater()
    
    # Prepare details for journal
    details = {}
    if args.input_file:
        details["Input"] = args.input_file
    if args.output_file:
        details["Output"] = args.output_file
    if args.metrics:
        details.update(args.metrics)
    
    # Update journal
    updater.update_journal(
        entry_type=args.operation.title(),
        description=args.description,
        details=details
    )
    
    # Update TODO if tasks provided
    if args.completed_tasks or args.new_tasks:
        updater.update_todo(
            completed_tasks=args.completed_tasks,
            new_tasks=args.new_tasks
        )
    
    # Create status file if output provided
    if args.output_file and args.metrics:
        results = {
            "Script": args.description,
            "Input": args.input_file or "N/A",
            "Output": args.output_file,
            **args.metrics
        }
        updater.create_status_file(args.operation, results)
    
    # Auto-commit if requested
    if args.auto_commit:
        commit_msg = f"Auto-update context: {args.operation} - {args.description}"
        updater.auto_commit(commit_msg)

if __name__ == "__main__":
    main()