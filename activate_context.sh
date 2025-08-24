#!/bin/bash
# Activate automatic context system

# Load virtual environment if it exists
# Note: venv was moved to archive during cleanup
# Uncomment and update path if you recreate a virtual environment
# if [ -f "venv/bin/activate" ]; then
#     source venv/bin/activate
# fi

# Load context aliases
source .context_aliases

echo "🚀 Automatic context system activated!"
echo ""
echo "Available commands:"
echo "  auto <script> [args]      - Run any script with auto-context"
echo "  auto_generate [args]      - Run article generation with auto-context"
echo "  monitor_context           - Start background monitor"
echo "  update_context            - Manual context update"
echo "  status_update             - Quick status update"
echo "  view_context              - View recent context"
echo ""
echo "Example: auto_generate --topic 'private equity' --output articles/"