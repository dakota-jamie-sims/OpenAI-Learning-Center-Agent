#!/bin/bash
# Quick context update wrapper
# Usage: ./update_context.sh [operation] "description" [options]

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."

# Check if at least 2 arguments provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 [stage1|stage2|fix|test|custom] \"description\" [options]"
    echo ""
    echo "Options:"
    echo "  --input FILE          Input file used"
    echo "  --output FILE         Output file created"
    echo "  --metrics '{JSON}'    Metrics as JSON string"
    echo "  --complete 'task'     Mark task as completed"
    echo "  --add-task 'task'     Add new task to backlog"
    echo "  --auto-commit         Auto-commit changes"
    echo ""
    echo "Examples:"
    echo "  $0 stage1 'Processed 1000 companies' --output data/output/batch1.csv --metrics '{\"success_rate\": \"91.3%\"}'"
    echo "  $0 fix 'Fixed ownership types' --complete 'Fix ownership classification' --auto-commit"
    exit 1
fi

# Run the Python script with all arguments
cd "$PROJECT_ROOT"
# Try to use venv python if available, otherwise use python3
if [ -f "venv/bin/python" ]; then
    venv/bin/python scripts/utilities/auto_update_context.py --operation "$1" --description "$2" "${@:3}"
else
    python3 scripts/utilities/auto_update_context.py --operation "$1" --description "$2" "${@:3}"
fi