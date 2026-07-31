#!/bin/bash
# The Void OS — Launcher
# Usage:
#   ./play.sh          CLI mode (terminal)
#   ./play.sh --web    Web mode (browser)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" = "--web" ] || [ "$1" = "-w" ]; then
    echo ""
    echo "  T H E   V O I D   O S   —   W E B   M O D E"
    echo "  ============================================"
    echo ""
    echo "  Starting server..."
    echo "  Open http://localhost:8080 in your browser"
    echo ""
    python3 "$SCRIPT_DIR/server.py"
else
    echo ""
    echo "  T H E   V O I D   O S   —   C L I   M O D E"
    echo "  ============================================"
    echo ""
    python3 "$SCRIPT_DIR/void_os.py"
fi
