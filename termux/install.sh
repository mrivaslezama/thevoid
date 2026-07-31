#!/data/data/com.termux/files/usr/bin/bash
# The Void OS — Termux Installer
# Run: bash install.sh
# Or pipe: wget -qO- https://raw.githubusercontent.com/.../install.sh | bash

set -e

REPO="mrivaslezama/thevoid"
BRANCH="main"
PKG_DIR="$HOME/.void_os"
BIN_DIR="$HOME/.local/bin"
VOID_BIN="$BIN_DIR/void"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   T H E   V O I D   O S   —   I N S T  ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ── Helper: download file from GitHub ────────────────────────────────────────
download() {
    local path="$1"
    local dest="$2"
    local url="https://raw.githubusercontent.com/${REPO}/${BRANCH}/${path}"

    # Try wget first (works when curl is broken on Termux)
    if command -v wget &>/dev/null; then
        wget -q -O "$dest" "$url" 2>/dev/null && return 0
    fi

    # Fallback to curl
    if command -v curl &>/dev/null; then
        curl -sL -o "$dest" "$url" 2>/dev/null && return 0
    fi

    echo "  ERROR: Could not download $path"
    echo "  Install wget: pkg install wget"
    return 1
}

# ── Check dependencies ──────────────────────────────────────────────────────
echo "  [1/5] Checking dependencies..."

if ! command -v python3 &>/dev/null; then
    echo "  Installing python..."
    pkg update -y && pkg install -y python
fi

if ! command -v wget &>/dev/null && ! command -v curl &>/dev/null; then
    echo "  Installing wget..."
    pkg update -y && pkg install -y wget
fi

# ── Create .bashrc if missing ───────────────────────────────────────────────
echo "  [2/5] Setting up shell..."
if [ ! -f "$HOME/.bashrc" ]; then
    touch "$HOME/.bashrc"
fi

# Ensure readline is configured for better terminal experience
if ! grep -q "# The Void OS" "$HOME/.bashrc" 2>/dev/null; then
    echo '' >> "$HOME/.bashrc"
    echo '# The Void OS' >> "$HOME/.bashrc"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# ── Create directories ─────────────────────────────────────────────────────
echo "  [3/5] Setting up directories..."
mkdir -p "$PKG_DIR"
mkdir -p "$PKG_DIR/man"
mkdir -p "$BIN_DIR"

# ── Download game files ─────────────────────────────────────────────────────
echo "  [4/5] Downloading game files..."
download "void_os.py" "$PKG_DIR/void_os.py"
download "server.py" "$PKG_DIR/server.py"
download "play.sh" "$PKG_DIR/play.sh"
download "index.html" "$PKG_DIR/index.html"
download "man/walkthrough.md" "$PKG_DIR/man/walkthrough.md"
chmod +x "$PKG_DIR/play.sh"

# ── Install Python dependencies ─────────────────────────────────────────────
echo "  [5/5] Installing Python packages..."
python3 -m ensurepip --upgrade 2>/dev/null || true
python3 -m pip install --upgrade pip 2>/dev/null || true
python3 -m pip install websockets 2>/dev/null || true

# ── Create launcher ─────────────────────────────────────────────────────────
cat > "$VOID_BIN" << 'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
# The Void OS launcher
exec python3 "$HOME/.void_os/void_os.py" "$@"
LAUNCHER
chmod +x "$VOID_BIN"

# ── Create web launcher ─────────────────────────────────────────────────────
cat > "$BIN_DIR/void-web" << 'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
# The Void OS web launcher
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$IP" ] && IP="localhost"
echo ""
echo "  Open http://${IP}:8080"
echo "  in your browser"
echo ""
exec python3 "$HOME/.void_os/server.py" "$@"
LAUNCHER
chmod +x "$BIN_DIR/void-web"

# ── Ensure PATH includes bin ────────────────────────────────────────────────
export PATH="$BIN_DIR:$PATH"

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
