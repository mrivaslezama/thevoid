#!/usr/bin/env python3
"""
The Void OS — Web Terminal Server
Full terminal emulator in the browser with the game engine.
Single-port: serves HTML and WebSocket on the same port.
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from void_os import VoidOS, C


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


class GameSession:
    def __init__(self):
        self.game = VoidOS()
        self.capture = OutputCapture()

    def process_command(self, cmd):
        old_stdout = sys.stdout
        sys.stdout = self.capture
        self.capture.buffer.truncate(0)
        self.capture.buffer.seek(0)

        output = ""
        try:
            cmd = cmd.strip()
            if not cmd:
                return ""

            state = self.game.state
            lvl = state.data["current_level"]
            name = state.data.get("hacker_name", "void")

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
                output = self._run_shell_cmd(cmd)

        except Exception as e:
            output = f"error: {e}"
        finally:
            sys.stdout = old_stdout

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

        self._active_level = level
        track = TRACKS[lid.split(".")[0]]
        lore = level.get_lore()
        enigma = level.get_enigma()
        return (
            f"\r\n  TRACK {lid.split('.')[0]}: {track['name']}\r\n"
            f"  {track['levels'][lid]['name']}\r\n\r\n"
            f"  {lore[:200]}\r\n\r\n"
            f"  {enigma}\r\n"
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

async def handle_client(websocket):
    client_id = id(websocket)
    session = GameSession()
    sessions[client_id] = session

    try:
        state = session.game.state
        lvl = state.data["current_level"]
        name = state.data.get("hacker_name", "void")

        welcome = (
            "\033[36m\033[1m"
            "\r\n"
            "  ╔══════════════════════════════════════════════════════════╗\r\n"
            "  ║                                                          ║\r\n"
            "  ║   T H E   V O I D   O S   //   v0.3.0                  ║\r\n"
            "  ║                                                          ║\r\n"
            "  ║   Full terminal in your browser                         ║\r\n"
            "  ║   Type 'help' to start                                  ║\r\n"
            "  ║                                                          ║\r\n"
            "  ╚══════════════════════════════════════════════════════════╝\r\n"
            "\033[0m"
        )
        await websocket.send(welcome)

        prompt = f"\033[32m[{lvl}] {name}@void:~$ \033[0m"
        await websocket.send(prompt)

        async for message in websocket:
            cmd = message.strip()
            if not cmd:
                await websocket.send("\r\n")
                continue

            output = session.process_command(cmd)
            if output:
                await websocket.send(output)

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
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Void OS</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0c0c0c;color:#b0b0b0;font-family:'IBM Plex Mono','Fira Code','Courier New',monospace;height:100vh;overflow:hidden;display:flex;flex-direction:column}
  #bar{background:#0a0a0a;border-bottom:1px solid #1c1c1c;padding:6px 14px;display:flex;align-items:center;justify-content:space-between;height:36px;flex-shrink:0}
  #bar .t{color:#3399ff;font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase}
  #bar .s{color:#444;font-size:10px;font-family:'IBM Plex Mono',monospace}
  #bar .s .on{color:#3399ff}
  #term{flex:1;padding:2px;overflow:hidden}
  #term .xterm{height:100%}
  .xterm-viewport::-webkit-scrollbar{width:4px}
  .xterm-viewport::-webkit-scrollbar-track{background:#0c0c0c}
  .xterm-viewport::-webkit-scrollbar-thumb{background:#222;border-radius:2px}
  .xterm-viewport::-webkit-scrollbar-thumb:hover{background:#333}
  #scanline{position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.03) 2px,rgba(0,0,0,0.03) 4px);z-index:9999}
  #fade{position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;background:radial-gradient(ellipse at center,transparent 60%,rgba(0,0,0,0.4) 100%);z-index:9998}
</style>
</head>
<body>
<div id="bar">
  <span class="t">void@term</span>
  <span class="s"><span class="on">&#9679;</span> connected &nbsp;|&nbsp; tab: complete &nbsp;|&nbsp; help: menu</span>
</div>
<div id="term"></div>
<div id="scanline"></div>
<div id="fade"></div>

<script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
<script>
const term = new Terminal({
  theme:{
    background:'#0c0c0c',
    foreground:'#b0b0b0',
    cursor:'#3399ff',
    cursorAccent:'#0c0c0c',
    selectionBackground:'#3399ff33',
    black:'#0c0c0c',red:'#cc3333',green:'#33cc33',yellow:'#cc9933',
    blue:'#3399ff',magenta:'#9933cc',cyan:'#33cccc',white:'#b0b0b0',
    brightBlack:'#555',brightRed:'#ff5555',brightGreen:'#55ff55',
    brightYellow:'#ffff55',brightBlue:'#5599ff',brightMagenta:'#cc55ff',
    brightCyan:'#55ffff',brightWhite:'#ffffff'
  },
  fontFamily:"'IBM Plex Mono','Fira Code','Courier New',monospace",
  fontSize:13,lineHeight:1.3,
  cursorBlink:true,cursorStyle:'block',
  allowTransparency:true,scrollback:5000
});

const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('term'));
fitAddon.fit();
window.addEventListener('resize',()=>fitAddon.fit());

const ws = new WebSocket(
  (location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/ws'
);

let inputBuf='';
let promptStr='';

ws.onmessage=(e)=>{
  const d=e.data;
  if(d.startsWith('\033[')){
    promptStr=d;
    term.write('\r\x1b[K'+d);
  }else{
    term.write(d);
  }
};
ws.onclose=()=>term.write('\r\n\033[31m[disconnected]\033[0m\r\n');
ws.onerror=()=>term.write('\r\n\033[31m[connection error]\033[0m\r\n');

term.onKey(({key,domEvent:e})=>{
  if(e.key==='Enter'){
    ws.send(inputBuf);
    inputBuf='';
    term.write('\r\n');
  }else if(e.key==='Backspace'){
    if(inputBuf.length>0){inputBuf=inputBuf.slice(0,-1);term.write('\b \b');}
  }else if(e.ctrlKey&&e.key==='c'){
    term.write('^C\r\n');inputBuf='';ws.send('');
  }else if(e.ctrlKey&&e.key==='l'){
    term.clear();term.write(promptStr);
  }else if(e.key==='Tab'){
    e.preventDefault();
    const cmds=['ls','cat','find','grep','cd','pwd','echo','chmod','mkdir','touch',
      'file','stat','wc','strings','head','tail','decode','encode','caesar',
      'bruteforce','hash','env','export','man','hint','submit','help','exit',
      'play','tracks','status','inventario','hackername','salir'];
    const m=cmds.filter(c=>c.startsWith(inputBuf));
    if(m.length===1){inputBuf=m[0];term.write('\r\x1b[K'+promptStr+inputBuf);}
    else if(m.length>1)term.write('\r\n'+m.join('  ')+'\r\n'+promptStr+inputBuf);
  }else if(!e.ctrlKey&&!e.altKey&&!e.metaKey&&e.key.length===1){
    inputBuf+=e.key;term.write(key);
  }
});
term.onData(d=>{if(d.length>1&&!d.startsWith('\x1b')){inputBuf+=d;term.write(d);}});
term.focus();
</script>
</body>
</html>"""


# ── Main ────────────────────────────────────────────────────────────────────
async def process_request(path, headers):
    if path == "/" or path == "/index.html":
        return (200, [("Content-Type", "text/html")], HTML_PAGE.encode())
    return None


async def main():
    port = 8080

    print(f"\033[36m")
    print(f"  ╔══════════════════════════════════════════════════════════╗")
    print(f"  ║   T H E   V O I D   O S   //   v0.3.0                 ║")
    print(f"  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║                                                          ║")
    print(f"  ║   http://localhost:{port}                                ║")
    print(f"  ║                                                          ║")
    print(f"  ║   Press Ctrl+C to stop                                  ║")
    print(f"  ║                                                          ║")
    print(f"  ╚══════════════════════════════════════════════════════════╝")
    print(f"\033[0m")

    async with websockets.serve(
        handle_client, "0.0.0.0", port,
        process_request=process_request
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\033[32mThe Void OS closed.\033[0m")
