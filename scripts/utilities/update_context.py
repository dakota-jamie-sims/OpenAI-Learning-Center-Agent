#!/usr/bin/env python3
"""
Context Update Script - Run periodically to keep CLAUDE.md current
Captures current project state for future Claude sessions
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return None

def get_latest_files(directory, pattern="*.csv", limit=5):
    """Get the most recent files matching pattern"""
    path = Path(directory)
    files = sorted(path.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return [str(f) for f in files[:limit]]

def analyze_enrichment_status():
    """Analyze current enrichment status"""
    status = {
        "stage1_complete": False,
        "stage2_started": False,
        "stage2_complete": False,
        "last_processed": None,
        "total_companies": 0,
        "enrichment_stats": {}
    }
    
    # Check Stage 1
    stage1_file = "data/output/enriched_5000_companies_complete.csv"
    if os.path.exists(stage1_file):
        status["stage1_complete"] = True
        try:
            df = pd.read_csv(stage1_file)
            status["total_companies"] = int(len(df))
            status["enrichment_stats"]["websites_found"] = int(df['Website'].notna().sum())
            status["enrichment_stats"]["high_confidence"] = int((df['Confidence Score'] >= 80).sum())
        except:
            pass
    
    # Check Stage 2
    comprehensive_files = get_latest_files("data/output", "comprehensive*.csv")
    if comprehensive_files:
        status["stage2_started"] = True
        status["last_processed"] = comprehensive_files[0]
        
        # Check if full run complete
        if any("5000" in f or "complete" in f for f in comprehensive_files):
            status["stage2_complete"] = True
    
    return status

def update_context_file():
    """Update CLAUDE.md with current project state"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Gather current state
    git_branch = run_command("git branch --show-current")
    git_status = run_command("git status --porcelain | wc -l")
    recent_commits = run_command("git log --oneline -5")
    latest_outputs = get_latest_files("data/output")
    latest_logs = get_latest_files("logs", "*.log")
    env_status = "Configured" if os.path.exists(".env") else "Not configured"
    
    # Analyze enrichment
    enrichment_status = analyze_enrichment_status()
    
    # Create context update section
    context_update = f"""
## AUTO-GENERATED CONTEXT UPDATE
Last updated: {timestamp}

### Current Project State
- **Git Branch**: {git_branch}
- **Uncommitted Changes**: {git_status} files
- **Environment**: {env_status}
- **Stage 1 (Website Enrichment)**: {'✓ Complete' if enrichment_status['stage1_complete'] else '✗ Not complete'}
- **Stage 2 (Comprehensive Extraction)**: {'✓ Complete' if enrichment_status['stage2_complete'] else '✓ In Progress' if enrichment_status['stage2_started'] else '✗ Not started'}

### Enrichment Statistics
- **Total Companies**: {enrichment_status['total_companies']}
- **Websites Found**: {enrichment_status['enrichment_stats'].get('websites_found', 'N/A')}
- **High Confidence**: {enrichment_status['enrichment_stats'].get('high_confidence', 'N/A')}

### Recent Files
**Latest Outputs**:
{chr(10).join(f"- {f}" for f in latest_outputs)}

**Latest Logs**:
{chr(10).join(f"- {f}" for f in latest_logs)}

### Recent Git Activity
```
{recent_commits}
```

### Next Recommended Actions
"""
    
    # Add recommendations based on state
    if not enrichment_status['stage1_complete']:
        context_update += "1. Complete Stage 1 website enrichment\n"
    elif not enrichment_status['stage2_started']:
        context_update += "1. Start Stage 2 comprehensive extraction (test with 50 companies first)\n"
    elif enrichment_status['stage2_started'] and not enrichment_status['stage2_complete']:
        context_update += "1. Continue Stage 2 extraction (check quality reports first)\n"
    else:
        context_update += "1. Review final results and quality reports\n"
    
    # Read current CLAUDE.md
    with open("CLAUDE.md", "r") as f:
        content = f.read()
    
    # Find and replace the auto-generated section
    start_marker = "## AUTO-GENERATED CONTEXT UPDATE"
    end_marker = "## Rate Limiting"  # Or another section that follows
    
    if start_marker in content:
        # Replace existing auto-generated section
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker, start_idx)
        if end_idx > start_idx:
            content = content[:start_idx] + context_update + "\n" + content[end_idx:]
        else:
            # No end marker found, append at end
            content = content[:start_idx] + context_update
    else:
        # Insert before Rate Limiting section
        if end_marker in content:
            idx = content.find(end_marker)
            content = content[:idx] + context_update + "\n" + content[idx:]
        else:
            # Append at end
            content += "\n" + context_update
    
    # Write updated content
    with open("CLAUDE.md", "w") as f:
        f.write(content)
    
    print(f"✓ Context updated at {timestamp}")
    print(f"  - Branch: {git_branch}")
    print(f"  - Stage 1: {'Complete' if enrichment_status['stage1_complete'] else 'Incomplete'}")
    print(f"  - Stage 2: {'Complete' if enrichment_status['stage2_complete'] else 'In Progress' if enrichment_status['stage2_started'] else 'Not started'}")
    
    # Also create a quick status file
    status_file = {
        "last_update": timestamp,
        "git_branch": git_branch,
        "enrichment_status": enrichment_status,
        "latest_files": {
            "outputs": latest_outputs,
            "logs": latest_logs
        }
    }
    
    with open("data/cache/context_status.json", "w") as f:
        json.dump(status_file, f, indent=2)
    
    print(f"✓ Status file saved to data/cache/context_status.json")

if __name__ == "__main__":
    update_context_file()