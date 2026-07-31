#!/data/data/com.termux/files/usr/bin/bash
# The Void OS — Termux Installer
# Run: bash install.sh

set -e

PKG_DIR="$HOME/.void_os"
BIN_DIR="$HOME/.local/bin"
VOID_BIN="$BIN_DIR/void"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   T H E   V O I D   O S   —   I N S T  ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# Check dependencies
echo "  [1/4] Checking dependencies..."
if ! command -v python3 &>/dev/null; then
    echo "  Installing python..."
    pkg update -y && pkg install -y python
fi

# Create directories
echo "  [2/4] Setting up directories..."
mkdir -p "$PKG_DIR"
mkdir -p "$BIN_DIR"

# Copy game files
echo "  [3/4] Installing game files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/void_os.py" "$PKG_DIR/"
cp "$SCRIPT_DIR/server.py" "$PKG_DIR/"
cp -r "$SCRIPT_DIR/man" "$PKG_DIR/"

# Create launcher
echo "  [4/4] Creating launcher..."
cat > "$VOID_BIN" << 'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
# The Void OS launcher
exec python3 "$HOME/.void_os/void_os.py" "$@"
LAUNCHER
chmod +x "$VOID_BIN"

# Create web launcher
cat > "$BIN_DIR/void-web" << 'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
# The Void OS web launcher
echo ""
echo "  Open http://$(hostname -I | awk '{print $1}'):8080"
echo "  in your browser"
echo ""
exec python3 "$HOME/.void_os/server.py" "$@"
LAUNCHER
chmod +x "$BIN_DIR/void-web"

# Ensure bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo '' >> "$HOME/.bashrc"
    echo '# The Void OS' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    export PATH="$BIN_DIR:$PATH"
fi

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   I N S T A L L E D   S U C C E S S    ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║                                          ║"
echo "  ║   CLI mode:   void                      ║"
echo "  ║   Web mode:   void-web                  ║"
echo "  ║   Manual:     man void                  ║"
echo "  ║                                          ║"
echo "  ║   Restart terminal or run:              ║"
echo "  ║     source ~/.bashrc                    ║"
echo "  ║                                          ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
