#!/usr/bin/env python3
"""
The Void OS — Web Terminal Server
Full terminal emulator in the browser with the game engine.
"""

import os
import sys
import json
import asyncio
import io
import contextlib
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    except Exception:
        print("ERROR: Could not install websockets.")
        print("Run manually: python3 -m pip install websockets")
        sys.exit(1)
    import websockets

# Import the game engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from void_os import VoidOS, C

# ── Capture stdout per session ──────────────────────────────────────────────
class OutputCapture:
    def __init__(self):
        self.buffer = io.StringIO()
        self._original = sys.stdout

    def write(self, text):
        self.buffer.write(text)
        self._original.write(text)

    def flush(self):
        self.buffer.flush()

    def get_and_clear(self):
        val = self.buffer.getvalue()
        self.buffer.truncate(0)
        self.buffer.seek(0)
        return val


# ── Per-session game instance ───────────────────────────────────────────────
class GameSession:
    def __init__(self):
        self.game = VoidOS()
        self.capture = OutputCapture()

    def process_command(self, cmd):
        """Process a command and return output."""
        old_stdout = sys.stdout
        sys.stdout = self.capture
        self.capture.buffer.truncate(0)
        self.capture.buffer.seek(0)

        output = ""
        try:
            cmd = cmd.strip()
            if not cmd:
                return ""

            # Route to game logic
            state = self.game.state
            lvl = state.data["current_level"]
            name = state.data.get("hacker_name", "void")

            # Menu commands
            if cmd in ("help", "menu", "?"):
                output = self._menu_text()
            elif cmd == "play":
                output = self._play_level()
            elif cmd == "tracks":
                output = self._tracks_text()
            elif cmd == "status":
                output = self._status_text()
            elif cmd in ("inventario", "flags"):
                output = self._inventory_text()
            elif cmd == "salir":
                state.save()
                output = "saved. goodbye."
            else:
                # Try as shell command in current level
                output = self._run_shell_cmd(cmd)

        except Exception as e:
            output = f"error: {e}"
        finally:
            sys.stdout = old_stdout

        # Get captured output (from print statements in game)
        captured = self.capture.get_and_clear()
        return captured + output

    def _menu_text(self):
        return (
            "\r\n"
            "  [play]         — Campaign levels\r\n"
            "  [walkthrough]  — Guided tutorial\r\n"
            "  [riddles]      — Hacker history puzzles\r\n"
            "  [hackername]   — Generate serial alias\r\n"
            "  [tracks]       — View all tracks\r\n"
            "  [status]       — Progress & points\r\n"
            "  [inventario]   — Captured flags\r\n"
            "  [salir]        — Exit\r\n"
        )

    def _tracks_text(self):
        from void_os import TRACKS, FLAGS
        lines = ["\r\n  TRACKS & LEVELS\r\n"]
        for tid, track in TRACKS.items():
            lines.append(f"  TRACK {tid}: {track['name']}")
            for lid, lv in track["levels"].items():
                done = lid in self.game.state.data["completed"]
                unlocked = self.game.state.is_unlocked(lid)
                if done:
                    s = "[DONE]"
                elif unlocked:
                    s = "[UNLOCKED]"
                else:
                    s = "[LOCKED]"
                pts = lv["diff"].count("★") * 100
                lines.append(f"    {lid}  {lv['name']:<30} {lv['diff']}  {s}  +{pts}pts")
            lines.append("")
        return "\r\n".join(lines)

    def _status_text(self):
        d = self.game.state.data
        done = len(d["completed"])
        total = len(FLAGS)
        bar_len = int((done / total) * 30) if total else 0
        bar = "█" * bar_len + "░" * (30 - bar_len)
        name = d.get("hacker_name", "none")
        return (
            f"\r\n  STATUS\r\n"
            f"  points:   {d['points']}\r\n"
            f"  levels:   {done}/{total}\r\n"
            f"  flags:    {len(d['flags'])}/{total}\r\n"
            f"  current:  {d['current_level']}\r\n"
            f"  name:     {name}\r\n"
            f"  [{bar}] {done}/{total}\r\n"
        )

    def _inventory_text(self):
        flags = self.game.state.data["flags"]
        if not flags:
            return "\r\n  no flags yet.\r\n"
        lines = ["\r\n  CAPTURED FLAGS\r\n"]
        for f in flags:
            lines.append(f"  {f}")
        lines.append("")
        return "\r\n".join(lines)

    def _play_level(self):
        from void_os import create_level, TRACKS, FLAGS
        lid = self.game.state.data["current_level"]

        if lid in self.game.state.data["completed"]:
            return f"\r\n  Level {lid} already completed.\r\n"
        if not self.game.state.is_unlocked(lid):
            return f"\r\n  Level {lid} is locked.\r\n"

        ps = self.game.state.get_puzzle_state(lid)
        level = create_level(lid, self.game.state, ps)
        if not level:
            return f"\r\n  Level {lid} not found.\r\n"

        # Store active level
        self._active_level = level
        track = TRACKS[lid.split(".")[0]]
        return (
            f"\r\n  TRACK {lid.split('.')[0]}: {track['name']}\r\n"
            f"  {track['levels'][lid]['name']}\r\n\r\n"
            f"  {level.get_lore()[:200]}...\r\n\r\n"
            f"  {level.get_enigma()}\r\n"
            f"  Type 'help' for commands, 'exit' to leave level.\r\n"
        )

    def _run_shell_cmd(self, cmd):
        if hasattr(self, '_active_level') and self._active_level:
            level = self._active_level

            if cmd == "exit":
                self._active_level = None
                return "\r\n  Returned to menu.\r\n"
            if cmd == "study":
                return f"\r\n{level.get_study()}\r\n"
            if cmd in ("hint", "mirar"):
                return f"\r\n  > {level.get_hint()}\r\n"

            result = level.shell.execute(cmd)
            if result and "__FLAG__" in result:
                submitted = result.replace("__FLAG__", "").strip()
                if submitted == level.flag:
                    level.solved = True
                    level._victory()
                    self.game.state.complete_level(level.level_id)
                    self.game.state.save_puzzle_state(level.level_id, level.puzzle_state)
                    self._active_level = None
                    return f"\r\n  FLAG CAPTURED! Returning to menu.\r\n"
                else:
                    return f"\r\n  invalid flag.\r\n"
            return f"\r\n{result}\r\n" if result else ""
        return f"\r\n  Unknown command. Type 'help' for menu.\r\n"


# ── WebSocket handler ───────────────────────────────────────────────────────
sessions = {}

async def handle_client(websocket, path):
    client_id = id(websocket)
    session = GameSession()
    sessions[client_id] = session

    try:
        # Send welcome
        welcome = (
            "\033[36m\033[1m"
            "\r\n"
            "  ╔══════════════════════════════════════════════════════════╗\r\n"
            "  ║                                                          ║\r\n"
            "  ║   T H E   V O I D   O S   //   v0.2.0-web              ║\r\n"
            "  ║                                                          ║\r\n"
            "  ║   Full terminal in your browser                         ║\r\n"
            "  ║   Type 'help' to start                                  ║\r\n"
            "  ║                                                          ║\r\n"
            "  ╚══════════════════════════════════════════════════════════╝\r\n"
            "\033[0m"
        )
        await websocket.send(welcome)

        # Get initial prompt
        state = session.game.state
        lvl = state.data["current_level"]
        name = state.data.get("hacker_name", "void")
        prompt = f"\033[32m[{lvl}] {name}@void:~$ \033[0m"
        await websocket.send(prompt)

        async for message in websocket:
            if message.startswith("__KEY__:"):
                # Handle special keys
                key = message.split("__KEY__:")[1]
                if key == "enter":
                    continue  # handled by normal flow
                continue

            cmd = message.strip()
            if not cmd:
                await websocket.send("\r\n")
                continue

            output = session.process_command(cmd)
            if output:
                await websocket.send(output)

            # Send new prompt
            state = session.game.state
            lvl = state.data["current_level"]
            name = state.data.get("hacker_name", "void")
            prompt = f"\033[32m[{lvl}] {name}@void:~$ \033[0m"
            await websocket.send(prompt)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        session.game.state.save()
        del sessions[client_id]


# ── HTML Page ───────────────────────────────────────────────────────────────
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Void OS</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #0a0a0a;
    color: #00ff41;
    font-family: 'Fira Code', 'JetBrains Mono', 'Cascadia Code', monospace;
    height: 100vh;
    overflow: hidden;
  }
  #header {
    background: #0d0d0d;
    border-bottom: 1px solid #1a1a1a;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 40px;
  }
  #header .title {
    color: #00ff41;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
  }
  #header .status {
    color: #666;
    font-size: 11px;
  }
  #header .status .online { color: #00ff41; }
  #tabs {
    background: #0d0d0d;
    border-bottom: 1px solid #1a1a1a;
    display: flex;
    padding: 0 8px;
    height: 32px;
    align-items: flex-end;
  }
  .tab {
    padding: 6px 16px;
    font-size: 11px;
    color: #666;
    background: #111;
    border: 1px solid #1a1a1a;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    cursor: pointer;
    margin-right: 2px;
    font-family: inherit;
  }
  .tab.active {
    color: #00ff41;
    background: #0a0a0a;
    border-color: #00ff41;
  }
  .tab:hover { color: #00ff41; }
  #terminal-container {
    height: calc(100vh - 72px);
    padding: 4px;
  }
  #terminal {
    height: 100%;
    width: 100%;
  }
  .xterm { padding: 8px; }
  .xterm-viewport::-webkit-scrollbar { width: 6px; }
  .xterm-viewport::-webkit-scrollbar-track { background: #0a0a0a; }
  .xterm-viewport::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
  .xterm-viewport::-webkit-scrollbar-thumb:hover { background: #555; }
</style>
</head>
<body>
  <div id="header">
    <span class="title">THE VOID OS</span>
    <span class="status">
      <span class="online">●</span> connected
      &nbsp;|&nbsp; TAB: autocomplete &nbsp;|&nbsp; man: manual &nbsp;|&nbsp; hint: pista
    </span>
  </div>
  <div id="tabs">
    <button class="tab active" onclick="focusTerminal()">terminal</button>
    <button class="tab" onclick="showHelp()">help</button>
  </div>
  <div id="terminal-container">
    <div id="terminal"></div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/xterm-addon-web-links@0.9.0/lib/xterm-addon-web-links.js"></script>
  <script>
    const term = new Terminal({
      theme: {
        background: '#0a0a0a',
        foreground: '#00ff41',
        cursor: '#00ff41',
        cursorAccent: '#0a0a0a',
        selectionBackground: '#00ff4133',
        black: '#0a0a0a',
        red: '#ff0040',
        green: '#00ff41',
        yellow: '#fffc00',
        blue: '#0066ff',
        magenta: '#cc00ff',
        cyan: '#00ffff',
        white: '#cccccc',
        brightBlack: '#555555',
        brightRed: '#ff5555',
        brightGreen: '#55ff55',
        brightYellow: '#ffff55',
        brightBlue: '#5555ff',
        brightMagenta: '#ff55ff',
        brightCyan: '#55ffff',
        brightWhite: '#ffffff',
      },
      fontFamily: "'Fira Code', 'JetBrains Mono', 'Cascadia Code', monospace",
      fontSize: 14,
      lineHeight: 1.2,
      cursorBlink: true,
      cursorStyle: 'block',
      allowTransparency: true,
      scrollback: 10000,
    });

    const fitAddon = new FitAddon.FitAddon();
    const webLinksAddon = new WebLinksAddon.WebLinksAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);

    term.open(document.getElementById('terminal'));
    fitAddon.fit();

    window.addEventListener('resize', () => fitAddon.fit());

    // WebSocket connection
    const ws = new WebSocket(
      (location.protocol === 'https:' ? 'wss:' : 'ws:') +
      '//' + location.host + '/ws'
    );

    let inputBuffer = '';
    let currentPrompt = '';

    ws.onmessage = (event) => {
      const data = event.data;
      if (data.startsWith('\033[')) {
        // This is a prompt - write it styled
        term.write(data);
        currentPrompt = data;
      } else {
        term.write(data);
      }
    };

    ws.onclose = () => {
      term.write('\r\n\033[31m[disconnected]\033[0m\r\n');
    };

    ws.onerror = (err) => {
      term.write('\r\n\033[31m[connection error]\033[0m\r\n');
    };

    // Handle keyboard input
    term.onKey(({ key, domEvent }) => {
      const ev = domEvent;
      const printable = !ev.altKey && !ev.ctrlKey && !ev.metaKey;

      if (ev.key === 'Enter') {
        if (inputBuffer.trim()) {
          ws.send(inputBuffer);
        } else {
          ws.send('');
        }
        inputBuffer = '';
        term.write('\r\n');
      } else if (ev.key === 'Backspace') {
        if (inputBuffer.length > 0) {
          inputBuffer = inputBuffer.slice(0, -1);
          term.write('\b \b');
        }
      } else if (ev.ctrlKey && ev.key === 'c') {
        term.write('^C\r\n');
        inputBuffer = '';
        ws.send('');
      } else if (ev.ctrlKey && ev.key === 'l') {
        term.clear();
        term.write(currentPrompt);
      } else if (ev.key === 'Tab') {
        ev.preventDefault();
        // Send tab for completion
        ws.send('__TAB__:' + inputBuffer);
      } else if (printable) {
        inputBuffer += key;
        term.write(key);
      }
    });

    // Handle paste
    term.onData((data) => {
      // Multi-character paste
      if (data.length > 1 && !data.startsWith('\x1b')) {
        inputBuffer += data;
        term.write(data);
      }
    });

    function focusTerminal() {
      term.focus();
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelector('.tab').classList.add('active');
    }

    function showHelp() {
      ws.send('help');
      term.focus();
    }

    // Auto-focus
    term.focus();
  </script>
</body>
</html>"""


# ── HTTP Server ──────────────────────────────────────────────────────────────
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

class VoidHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            # Serve static files from the void_os directory
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logs


def run_http(port):
    server = HTTPServer(('0.0.0.0', port), VoidHandler)
    server.serve_forever()


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    http_port = 8080
    ws_port = 8081

    print(f"\033[36m")
    print(f"  ╔══════════════════════════════════════════════════════════╗")
    print(f"  ║   T H E   V O I D   O S   //   v0.2.0-web             ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║                                                          ║")
    print(f"  ║   Terminal:  http://localhost:{http_port}                  ║")
    print(f"  ║   WebSocket: ws://localhost:{ws_port}                     ║")
    print(f"  ║                                                          ║")
    print(f"  ║   Open in browser for full terminal experience          ║")
    print(f"  ║   Press Ctrl+C to stop                                  ║")
    print(f"  ║                                                          ║")
    print(f"  ╚══════════════════════════════════════════════════════════╝")
    print(f"\033[0m")

    # Start HTTP server in thread
    http_thread = threading.Thread(target=run_http, args=(http_port,), daemon=True)
    http_thread.start()

    # Start WebSocket server
    async with websockets.serve(handle_client, "0.0.0.0", ws_port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\033[32mThe Void OS closed.\033[0m")
