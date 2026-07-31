#!/usr/bin/env python3
"""
T H E   V O I D   O S   //   v0.2.0-beta
======================================================================
Ultra-minimalist, poetic, dark interactive terminal game for training
elite hackers through real Linux command simulation.

Inspirations: The Dark Room, Ruby Koans, pwn.college, PicoCTF,
              Hacker 101, OverTheWire, Phrack Magazine lore.
"""

import os
import sys
import json
import random
import hashlib
import base64
import codecs
import shlex
import time
from datetime import datetime
from abc import ABC, abstractmethod
from collections import OrderedDict

# ── Readline (TAB completion) ───────────────────────────────────────────────
_READLINE = False
try:
    import readline
    _READLINE = True
except ImportError:
    try:
        import pyreadline3 as readline
        _READLINE = True
    except ImportError:
        readline = None

# ── ANSI Palette (ultra-minimalist) ─────────────────────────────────────────
class C:
    RST  = "\033[0m"
    DIM  = "\033[2m"
    RED  = "\033[31m"
    GRN  = "\033[32m"
    YEL  = "\033[33m"
    BLU  = "\033[34m"
    MAG  = "\033[35m"
    CYN  = "\033[36m"
    WHT  = "\033[37m"
    BOLD = "\033[1m"
    ITAL = "\033[3m"
    UND  = "\033[4m"

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE  = os.path.join(BASE_DIR, ".void_state.json")
DIARY_FILE = os.path.join(BASE_DIR, ".void_diary.md")

# ── Hacker Lore Strings ─────────────────────────────────────────────────────
LORE = {
    "manifesto": (
        "\"We explore... we probe... we test... we hack. We are\n"
        "  theengers of theelectronic frontier. We exist without\n"
        "  skin color, without nationality, without religious bias.\"\n"
        "                          — The Conscience of a Hacker, 1986"
    ),
    "thompson": (
        "\"Rumors have it that Ken Thompson compiled the first C\n"
        "  compiler on a piece of paper, then hand-tuned the binary\n"
        "  by reading hex dumps of the output. The trust model of\n"
        "  Unix began with one man and one compiler.\"\n"
        "                          — The Unix Haters Handbook"
    ),
    "morris": (
        "\"On November 2, 1988, the Morris Worm crawled through\n"
        "  ARPANET at 300 machines per hour. Its creator, Robert\n"
        "  Tappan Morris, became the first person convicted under\n"
        "  the Computer Fraud and Abuse Act. The worm was never\n"
        "  meant to destroy — it was curiosity, and curiosity killed\n"
        "  the network.\"\n"
        "                          — The New Yorker, 1988"
    ),
    "phrack": (
        "\"Phrack was born in 1985. It was the gospel of the\n"
        "  underground. Each issue was a battlefield of ideas,\n"
        "  exploits, and the raw truth that telcos didn't want\n"
        "  you to read. Phreak, hack, learn, repeat.\"\n"
        "                          — Phrack Magazine, Vol. 1"
    ),
    "suid_myth": (
        "\"In the beginning, there was root. And root looked upon\n"
        "  the system and saw that it was good. But then came the\n"
        "  SUID bit — a key left in the door by the gods of Unix.\n"
        "  And the mortals learned to walk where only gods could go.\"\n"
        "                          — The Book of Permissions"
    ),
    "buffer_overflow": (
        "\"Stack smashing is the art of pouring more data into a\n"
        "  vessel than it was designed to hold. The stack doesn't\n"
        "  know the difference between data and return addresses.\n"
        "  Aleph One wrote the gospel: 'Smashing The Stack For Fun\n"
        "  And Profit.' The stack has never been safe since.\"\n"
        "                          — Phrack #49, 1996"
    ),
    "cypherpunk": (
        "\"Cypherpunks write code. We know that someone has to\n"
        "  write software to defend privacy. We will do it.\"\n"
        "                          — Eric Hughes, 1993"
    ),
    "cron_warning": (
        "\"The crontab is a sleeping god. It awakens every minute,\n"
        "  executes the will of root, and sleeps again. But if you\n"
        "  can write to its script... you become the god.\"\n"
        "                          — The Unix Underground"
    ),
}

# ── Flags ────────────────────────────────────────────────────────────────────
FLAGS = {
    "1.1": "void{3ch0_1n_th3_d4rk}",
    "1.2": "void{n0t_4ll_wh0_w4nd3r_4r3_3mpty}",
    "1.3": "void{th3_n33dl3_1n_th3_h4yst4ck}",
    "2.1": "void{h1j4ck3d_p4th5_2_gl0ry}",
    "2.2": "void{3nv1r0nm3nt_1z_d3st1ny}",
    "3.1": "void{5u1d_k3y5_2_th3_k1ngd0m}",
    "3.2": "void{cr0n_th3_sl33p1ng_g0d}",
    "4.1": "void{th3_st4ck_r3m3mb3r5_4ll}",
}

# ── Tracks & Levels ──────────────────────────────────────────────────────────
TRACKS = {
    "1": {
        "name": "SENSING THE VOID",
        "subtitle": "Flujos, Archivos y Arqueología Hacker",
        "lore": LORE["manifesto"],
        "levels": {
            "1.1": {"name": "El Despertar del Eco", "diff": "★☆☆", "mode": "walkthrough"},
            "1.2": {"name": "Los Archivos Fantasma", "diff": "★★☆", "mode": "riddle"},
            "1.3": {"name": "El Archivo de los Sabios", "diff": "★★★", "mode": "trial"},
        },
    },
    "2": {
        "name": "ALTERING REALITY",
        "subtitle": "Variables, Rutas y Entornos",
        "lore": LORE["thompson"],
        "levels": {
            "2.1": {"name": "El Sendero Perdido", "diff": "★★☆", "mode": "trial"},
            "2.2": {"name": "Las Máscaras del Entorno", "diff": "★★☆", "mode": "riddle"},
        },
    },
    "3": {
        "name": "PRIVILEGE ESCALATION",
        "subtitle": "El Mito de Prometeo / Acceso Root",
        "lore": LORE["suid_myth"],
        "levels": {
            "3.1": {"name": "El Espejo del Rey", "diff": "★★★", "mode": "learning"},
            "3.2": {"name": "La Cronología del Caos", "diff": "★★★", "mode": "trial"},
        },
    },
    "4": {
        "name": "MEMORY REVERSING",
        "subtitle": "El Inframundo del Silicio",
        "lore": LORE["buffer_overflow"],
        "levels": {
            "4.1": {"name": "El Desborde del Alma", "diff": "★★★★", "mode": "trial"},
        },
    },
}

# ── Virtual Filesystem ───────────────────────────────────────────────────────
class VirtualFile:
    __slots__ = ("name", "is_dir", "content", "perms", "owner", "children", "size")

    def __init__(self, name, is_dir=False, content="", perms="-rw-r--r--", owner="root"):
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.perms = perms
        self.owner = owner
        self.children = OrderedDict() if is_dir else None
        self.size = len(content)

    def add_child(self, child):
        if self.is_dir:
            self.children[child.name] = child

    def _list(self, show_hidden=False):
        if not self.is_dir:
            return []
        return [c for n, c in self.children.items() if show_hidden or not n.startswith(".")]


class VirtualFS:
    def __init__(self):
        self.root = VirtualFile("/", is_dir=True, perms="drwxr-xr-x")
        self.cwd = self.root
        self.cwd_path = "/"

    def _normalize(self, path):
        if path.startswith("~"):
            path = "/home/hacker" + path[1:]
        if path.startswith("/"):
            parts = [p for p in path.split("/") if p]
            stack = []
        else:
            parts = [p for p in path.split("/") if p]
            stack = [p for p in self.cwd_path.split("/") if p]
        for p in parts:
            if p == ".":
                continue
            if p == "..":
                if stack:
                    stack.pop()
            else:
                stack.append(p)
        return stack

    def _resolve(self, path):
        if not path:
            return self.cwd
        parts = self._normalize(path)
        node = self.root
        for p in parts:
            if not node.is_dir or p not in node.children:
                return None
            node = node.children[p]
        return node

    def _full_path(self, parts):
        return "/" + "/".join(parts) if parts else "/"

    def ls(self, path=None, show_hidden=False):
        node = self._resolve(path) if path else self.cwd
        if node and node.is_dir:
            return [(f.name, f.is_dir, f.perms, f.owner, f.size) for f in node._list(show_hidden)]
        return None

    def cat(self, path):
        node = self._resolve(path)
        if node and not node.is_dir:
            return node.content
        return None

    def mkdir(self, path, name):
        parent = self._resolve(path)
        if parent and parent.is_dir:
            parent.add_child(VirtualFile(name, is_dir=True, perms="drwxr-xr-x"))
            return True
        return False

    def touch(self, path, name, content="", perms="-rw-r--r--", owner="root", is_dir=False):
        parent = self._resolve(path)
        if parent and parent.is_dir:
            f = VirtualFile(name, is_dir=is_dir, content=content, perms=perms, owner=owner)
            parent.add_child(f)
            return True
        return False

    def find(self, name_pattern=None, perm_pattern=None, not_empty=False, min_size=None):
        results = []
        self._find_r(self.root, name_pattern, perm_pattern, not_empty, min_size, results)
        return results

    def _find_r(self, node, np, pp, ne, ms, out):
        if not node.is_dir:
            match = True
            if np and np not in node.name:
                match = False
            if pp and pp not in node.perms:
                match = False
            if ne and not node.content:
                match = False
            if ms is not None and node.size < ms:
                match = False
            if match:
                out.append(node)
            return
        for c in node.children.values():
            self._find_r(c, np, pp, ne, ms, out)

    def grep(self, pattern):
        results = []
        self._grep_r(self.root, pattern, results, "")
        return results

    def _grep_r(self, node, pat, out, prefix):
        if not node.is_dir:
            if pat.lower() in node.content.lower():
                out.append((prefix + node.name, node.content[:80]))
            return
        for c in node.children.values():
            self._grep_r(c, pat, out, prefix + node.name + "/")

    def chdir(self, path):
        if not path or path == "/":
            self.cwd = self.root
            self.cwd_path = "/"
            return True, "/"
        parts = self._normalize(path)
        node = self.root
        for p in parts:
            if not node.is_dir or p not in node.children:
                return False, path
            node = node.children[p]
        if not node.is_dir:
            return False, path
        self.cwd = node
        self.cwd_path = self._full_path(parts)
        return True, self.cwd_path

    def _list_all(self):
        """Return every file/dir name (absolute paths) for TAB completion."""
        out = []
        self._list_r(self.root, "/", out)
        return out

    def _list_r(self, node, prefix, out):
        full = prefix + node.name
        if not node.is_dir:
            out.append(full)
            return
        full += "/"
        out.append(full.rstrip("/"))
        for c in node.children.values():
            self._list_r(c, full, out)


# ── Virtual Shell ────────────────────────────────────────────────────────────
class VirtualShell:
    COMMANDS = [
        "ls", "cat", "find", "grep", "head", "tail", "cd", "pwd",
        "echo", "whoami", "id", "uname", "chmod", "mkdir", "touch",
        "file", "stat", "wc", "sort", "uniq", "strings", "tr", "xxd",
        "decode", "encode", "caesar", "bruteforce", "hash", "base64",
        "curl", "ping", "export", "env",
        "man", "hint", "submit", "help", "exit",
    ]

    def __init__(self, fs, env=None, on_command=None, level_ref=None):
        self.fs = fs
        self.env = env or {}
        self.history = []
        self._on_command = on_command
        self.level_ref = level_ref

    def execute(self, raw):
        raw = raw.strip()
        if not raw:
            return ""
        self.history.append(raw)

        # Handle pipes (but not inside quotes)
        if "|" in raw:
            return self._pipe(raw)

        # Handle semicolons
        if ";" in raw:
            results = []
            for part in raw.split(";"):
                r = self.execute(part.strip())
                if r:
                    results.append(r)
            return "\n".join(results)

        # Handle &&
        if "&&" in raw:
            left, right = raw.split("&&", 1)
            r = self.execute(left.strip())
            if r and "error" not in r.lower() and "not found" not in r.lower():
                return r + "\n" + self.execute(right.strip())
            return r

        # Handle output redirection: > and >>
        append = False
        redirect_target = None
        cmd_part = raw

        # Check for >> first (append), then > (overwrite)
        for op, is_append in [(">>", True), (">", False)]:
            if op in raw:
                parts = raw.split(op, 1)
                cmd_part = parts[0].strip()
                redirect_target = parts[1].strip()
                append = is_append
                break

        try:
            tokens = shlex.split(cmd_part)
        except ValueError:
            tokens = cmd_part.split()
        if not tokens:
            return ""

        cmd = tokens[0]
        args = tokens[1:]

        # Handle variable assignment: VAR=value
        if "=" in cmd and not cmd.startswith("-"):
            var, val = cmd.split("=", 1)
            if val.startswith("~"):
                val = "/home/hacker" + val[1:]
            self.env[var] = val
            return ""

        result = self._dispatch(cmd, args)

        # Handle redirection of output
        if redirect_target is not None and result is not None:
            # Expand tilde in redirect target
            if redirect_target.startswith("~"):
                redirect_target = "/home/hacker" + redirect_target[1:]
            node = self.fs._resolve(redirect_target)
            if node and not node.is_dir:
                if append:
                    node.content += result
                else:
                    node.content = result
                node.size = len(node.content)
            else:
                parent_path = "/".join(redirect_target.split("/")[:-1]) or "/"
                fname = redirect_target.split("/")[-1]
                # Create intermediate dirs if needed
                self._ensure_parent(redirect_target)
                self.fs.touch(parent_path, fname, result)

        # Hook: levels can return FLAG{...} or modify result
        if self._on_command:
            extra = self._on_command(cmd, args, result)
            if extra:
                # If hook returns a flag, return it exclusively
                if "__FLAG__" in extra:
                    return extra
                # Otherwise append to result
                result = (result + "\n" + extra).strip() if result else extra

        return result

    def _pipe(self, raw):
        parts = raw.split("|")
        data = ""
        for p in parts:
            cmd = p.strip()
            if not cmd:
                continue
            # Inject previous output as first argument
            if data:
                tokens = cmd.split(None, 1)
                if tokens:
                    cmd = tokens[0] + " " + data.strip()
            data = self.execute(cmd)
        return data

    def _dispatch(self, cmd, args):
        table = {
            "ls": self._ls, "cat": self._cat, "find": self._find,
            "grep": self._grep, "head": self._head, "tail": self._tail,
            "cd": self._cd, "pwd": self._pwd, "echo": self._echo,
            "whoami": self._whoami, "id": self._id, "uname": self._uname,
            "chmod": self._chmod, "mkdir": self._mkdir, "touch": self._touch,
            "file": self._file, "stat": self._stat, "wc": self._wc,
            "sort": self._sort, "uniq": self._uniq, "strings": self._strings,
            "tr": self._tr, "xxd": self._xxd,
            "decode": self._decode, "encode": self._encode,
            "caesar": self._caesar, "bruteforce": self._bruteforce,
            "hash": self._hash, "base64": self._base64_cmd,
            "curl": self._curl, "ping": self._ping,
            "export": self._export, "env": self._env,
            "man": self._man, "hint": self._hint_cmd,
            "submit": self._submit, "help": self._help,
        }
        fn = table.get(cmd)
        if fn:
            try:
                return fn(args)
            except Exception as e:
                return f"{C.RED}error: {e}{C.RST}"
        # Try running as executable path (e.g. /challenge/run)
        if cmd.startswith("/"):
            node = self.fs._resolve(cmd)
            if node and not node.is_dir:
                return self._run_script(node.content, args)
            return f"{C.RED}{cmd}: command not found{C.RST}"
        return f"{C.RED}{cmd}: command not found{C.RST}"

    def _run_script(self, script, args):
        lines = script.strip().split("\n")
        output = []
        if_stack = []
        skip_else = False
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("if ["):
                try:
                    _, rest = line.split("if [", 1)
                    rest = rest.rstrip("]; then").strip()
                    var, op, val = rest.split(None, 2)
                    var = var.strip('"$')
                    val = val.strip('"')
                    cond = self.env.get(var, "") == val
                    if_stack.append(cond)
                    skip_else = not cond
                    continue
                except Exception:
                    if_stack.append(False)
                    skip_else = True
                    continue
            if line == "else":
                if if_stack:
                    skip_else = if_stack[-1]
                continue
            if line == "fi":
                if if_stack:
                    if_stack.pop()
                continue
            if skip_else and if_stack:
                continue
            if line.startswith("echo "):
                text = line[5:].strip().strip("'\"")
                for var in list(self.env.keys()):
                    text = text.replace(f"${var}", self.env[var])
                output.append(text)
                continue
            if line.startswith("read "):
                var = line.split()[-1]
                self.env[var] = ""
                continue
            if "=" in line and not line.startswith("export"):
                k, v = line.split("=", 1)
                self.env[k.strip()] = v.strip().strip('"')
                continue
            # Unknown command — try to find it in PATH or fs
            sub_cmd = line.split()[0] if line.split() else ""
            if sub_cmd:
                # Check if it's a file in the virtual FS
                for p in ["/challenge/" + sub_cmd, sub_cmd]:
                    node = self.fs._resolve(p)
                    if node and not node.is_dir and node.content:
                        sub_result = self._run_script(node.content, line.split()[1:])
                        if sub_result:
                            output.append(sub_result)
                        break
        return "\n".join(output)

    # ── Linux Commands ───────────────────────────────────────────────────────
    def _ls(self, args):
        show_hidden, path, long = False, None, False
        for a in args:
            if a.startswith("-"):
                if "a" in a:
                    show_hidden = True
                if "l" in a:
                    long = True
            else:
                path = a
        items = self.fs.ls(path, show_hidden)
        if items is None:
            return f"ls: cannot access '{path}': No such file or directory"
        if not items:
            return ""
        if long:
            lines = []
            for name, is_dir, perms, owner, size in items:
                prefix = "d" if is_dir else "-"
                if is_dir:
                    lines.append(f"{C.DIM}{prefix}{perms[1:]}  {owner:8}  {name}/{C.RST}")
                elif "s" in perms:
                    lines.append(f"{C.RED}{prefix}{perms[1:]}  {owner:8}  {name}{C.RST}")
                elif name.startswith("."):
                    lines.append(f"{C.DIM}{prefix}{perms[1:]}  {owner:8}  {name}{C.RST}")
                else:
                    lines.append(f"{prefix}{perms[1:]}  {owner:8}  {size:>6}  {name}")
            return "\n".join(lines)
        else:
            return "  ".join(
                f"{C.DIM}{n}/{C.RST}" if d else n
                for n, d, _, _, _ in items
            )

    def _cat(self, args):
        if not args:
            return "cat: missing file operand"
        c = self.fs.cat(args[0])
        return c if c is not None else f"cat: {args[0]}: No such file or directory"

    def _find(self, args):
        start, np, pp, ne, ms = "/", None, None, False, None
        i = 0
        while i < len(args):
            if args[i] == "-name" and i + 1 < len(args):
                np = args[i + 1]; i += 2
            elif args[i] == "-perm" and i + 1 < len(args):
                pp = args[i + 1]; i += 2
            elif args[i] == "-not" and i + 1 < len(args) and args[i+1] == "-empty":
                ne = True; i += 2
            elif args[i] == "-size" and i + 1 < len(args):
                s = args[i + 1]
                if s.endswith("c"):
                    ms = int(s[:-1])
                elif s.endswith("+"):
                    ms = int(s[:-1])
                i += 2
            elif args[i] == "-type" and i + 1 < len(args):
                i += 2  # skip type f/d
            else:
                start = args[i]; i += 1
        results = self.fs.find(np, pp, ne, ms)
        return "\n".join(r.name for r in results[:30]) if results else ""

    def _grep(self, args):
        if not args:
            return "grep: missing pattern"
        path = args[1] if len(args) > 1 else None
        results = self.fs.grep(args[0])
        if not results:
            return ""
        lines = []
        for fname, content in results[:10]:
            lines.append(f"{fname}: {content}")
        return "\n".join(lines)

    def _head(self, args):
        n, path = 10, None
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                n = int(args[i + 1]); i += 2
            else:
                path = args[i]; i += 1
        if not path:
            return "head: missing file"
        c = self.fs.cat(path)
        if c is None:
            return f"head: {path}: No such file"
        return "\n".join(c.split("\n")[:n])

    def _tail(self, args):
        n, path = 10, None
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                n = int(args[i + 1]); i += 2
            else:
                path = args[i]; i += 1
        if not path:
            return "tail: missing file"
        c = self.fs.cat(path)
        if c is None:
            return f"tail: {path}: No such file"
        return "\n".join(c.split("\n")[-n:])

    def _cd(self, args):
        target = args[0] if args else "/"
        ok, resolved = self.fs.chdir(target)
        return "" if ok else f"cd: {target}: No such directory"

    def _pwd(self, _a):
        return self.fs.cwd_path

    def _echo(self, args):
        text = " ".join(args)
        # Handle $VARIABLE
        for var in list(self.env.keys()):
            text = text.replace(f"${var}", self.env[var])
        text = text.replace("$PATH", self.env.get("PATH", "/usr/bin:/bin"))
        return text.strip('"').strip("'")

    def _whoami(self, _a):
        return self.env.get("user", "hacker")

    def _id(self, _a):
        uid = self.env.get("uid", "1000")
        user = self.env.get("user", "hacker")
        return f"uid={uid}({user}) gid=1000(hacker) groups=1000(hacker)"

    def _uname(self, args):
        if "-a" in args:
            return "Linux void 5.15.0-void #1 SMP x86_64 GNU/Linux"
        return "Linux"

    def _chmod(self, args):
        if len(args) < 2:
            return "chmod: missing operand"
        node = self.fs._resolve(args[1])
        if node:
            node.perms = args[0] if len(args[0]) >= 9 else node.perms
            return ""
        return f"chmod: cannot access '{args[1]}': No such file or directory"

    def _mkdir(self, args):
        if not args:
            return "mkdir: missing operand"
        path = args[0]
        if path.startswith("~"):
            path = "/home/hacker" + path[1:]
        if path.startswith("/"):
            # Create intermediate dirs, then the final dir
            parts = [p for p in path.split("/") if p]
            cur = self.fs.root
            for part in parts:
                if part not in cur.children:
                    cur.add_child(VirtualFile(part, is_dir=True, perms="drwxr-xr-x"))
                cur = cur.children[part]
            return ""
        self.fs.touch(self.fs.cwd_path, path, is_dir=True)
        return ""

    def _touch(self, args):
        if not args:
            return "touch: missing operand"
        path = args[0]
        if path.startswith("~"):
            path = "/home/hacker" + path[1:]
        if path.startswith("/"):
            parent = "/".join(path.split("/")[:-1]) or "/"
            fname = path.split("/")[-1]
            # Create intermediate dirs if needed
            self._ensure_parent(path)
            self.fs.touch(parent, fname)
            return ""
        self.fs.touch(self.fs.cwd_path, path)
        return ""

    def _ensure_parent(self, path):
        if path.startswith("~"):
            path = "/home/hacker" + path[1:]
        parts = [p for p in path.split("/") if p][:-1]
        cur = self.fs.root
        for part in parts:
            if part not in cur.children:
                cur.add_child(VirtualFile(part, is_dir=True, perms="drwxr-xr-x"))
            cur = cur.children[part]

    def _file(self, args):
        if not args:
            return "file: missing operand"
        node = self.fs._resolve(args[0])
        if not node:
            return f"file: '{args[0]}': No such file or directory"
        if node.is_dir:
            return f"{args[0]}: directory"
        if node.content.startswith("#!/"):
            shebang = node.content.split("\n")[0]
            return f"{args[0]}: {shebang[2:].strip()} script, ASCII text executable"
        try:
            node.content.encode("ascii")
            return f"{args[0]}: ASCII text"
        except UnicodeEncodeError:
            return f"{args[0]}: data"

    def _stat(self, args):
        if not args:
            return "stat: missing operand"
        node = self.fs._resolve(args[0])
        if not node:
            return f"stat: cannot stat '{args[0]}': No such file or directory"
        return (
            f"  File: {args[0]}\n"
            f"  Size: {node.size:<10} Blocks: 8          IO Block: 4096   regular file\n"
            f"Access: ({node.perms})  Uid: (    0/    root)   Gid: (    0/    root)"
        )

    def _wc(self, args):
        if not args:
            return "wc: missing file operand"
        c = self.fs.cat(args[0])
        if c is None:
            return f"wc: {args[0]}: No such file"
        lines = len(c.split("\n"))
        words = len(c.split())
        chars = len(c)
        return f"  {lines}  {words}  {chars} {args[0]}"

    def _sort(self, args):
        if not args:
            return ""
        c = self.fs.cat(args[0]) if args[0] else ""
        if c is None:
            return ""
        lines = c.split("\n")
        lines.sort()
        return "\n".join(lines)

    def _uniq(self, args):
        if not args:
            return ""
        c = args[0]  # Could be piped input
        lines = c.split("\n") if isinstance(c, str) else []
        result = []
        for line in lines:
            if not result or result[-1] != line:
                result.append(line)
        return "\n".join(result)

    def _strings(self, args):
        if not args:
            return "strings: missing file operand"
        c = self.fs.cat(args[0])
        if c is None:
            return f"strings: {args[0]}: No such file"
        printable = []
        current = []
        for ch in c:
            if ch.isprintable() or ch in ("\n", "\t"):
                current.append(ch)
            else:
                if len(current) >= 4:
                    printable.append("".join(current))
                current = []
        if len(current) >= 4:
            printable.append("".join(current))
        return "\n".join(printable[:30])

    def _tr(self, args):
        """tr - translate/delete characters. Usage: tr <input> <from> <to>"""
        if len(args) < 2:
            return "usage: tr <text> <from> <to>\n       tr -d <chars>  (delete)"
        if args[0] == "-d" and len(args) >= 2:
            # Delete characters
            text = args[1] if len(args) > 2 else ""
            chars = args[1]
            return text.translate(str.maketrans("", "", chars))
        if len(args) >= 3:
            text, fr, to = args[0], args[1], args[2]
            table = str.maketrans(fr, to)
            return text.translate(table)
        return "usage: tr <text> <from> <to>"

    def _xxd(self, args):
        """xxd - hex dump. Usage: xxd <file>"""
        if not args:
            return "xxd: missing file"
        c = self.fs.cat(args[0])
        if c is None:
            return f"xxd: {args[0]}: No such file"
        lines = []
        for i in range(0, len(c), 16):
            chunk = c[i:i+16]
            hex_part = " ".join(f"{ord(ch):02x}" for ch in chunk)
            ascii_part = "".join(ch if ch.isprintable() else "." for ch in chunk)
            lines.append(f"{i:08x}: {hex_part:<48}  {ascii_part}")
        return "\n".join(lines)

    def _base64_cmd(self, args):
        """base64 - encode/decode. Usage: base64 <file> or base64 -d <text>"""
        if not args:
            return "usage: base64 <file>\n       base64 -d <text>"
        if args[0] == "-d":
            text = " ".join(args[1:]) if len(args) > 1 else ""
            text = text.replace("\n", "").replace(" ", "")
            try:
                return base64.b64decode(text).decode()
            except Exception as e:
                return f"base64 decode error: {e}"
        c = self.fs.cat(args[0])
        if c is None:
            # Treat as text
            try:
                return base64.b64encode(args[0].encode()).decode()
            except Exception as e:
                return f"base64 error: {e}"
        return base64.b64encode(c.encode()).decode()

    # ── Crypto Commands ──────────────────────────────────────────────────────
    def _decode(self, args):
        if len(args) < 1:
            return "usage: decode <text> <base64|hex|rot13>\n       decode <type>  (reads from previous pipe)"
        # Handle: decode <text> <type> OR decode <type> (with piped input)
        if len(args) >= 2 and args[-1].lower() in ("base64", "hex", "rot13"):
            text = " ".join(args[:-1])
            dtype = args[-1].lower()
        elif len(args) == 1 and args[0].lower() in ("base64", "hex", "rot13"):
            # Only type given — text should be in piped input (already in args via pipe)
            return f"decode: provide text to decode. Usage: echo TEXT | decode {args[0]}"
        else:
            return "usage: decode <text> <base64|hex|rot13>"
        # Clean text: remove newlines, spaces for base64
        text = text.strip()
        if dtype == "base64":
            text = text.replace("\n", "").replace(" ", "")
        try:
            if dtype == "base64":
                import base64 as b64
                return b64.b64decode(text).decode()
            if dtype == "hex":
                return bytes.fromhex(text.replace(" ", "")).decode()
            if dtype == "rot13":
                return codecs.decode(text, "rot_13")
        except Exception as e:
            return f"decode error: {e}"

    def _encode(self, args):
        if len(args) < 2:
            return "usage: encode <text> <base64|hex|rot13>"
        text, dtype = args[0], args[1].lower()
        try:
            if dtype == "base64":
                return base64.b64encode(text.encode()).decode()
            if dtype == "hex":
                return text.encode().hex()
            if dtype == "rot13":
                return codecs.encode(text, "rot_13")
            return f"encode: unknown type '{dtype}'"
        except Exception as e:
            return f"encode error: {e}"

    def _caesar(self, args):
        if len(args) < 2:
            return "usage: caesar <text> <shift> [decrypt]"
        text = args[0]
        try:
            shift = int(args[1])
        except ValueError:
            return "shift must be a number"
        dec = "decrypt" in args
        out = []
        for ch in text:
            if ch.isalpha():
                base = ord("a") if ch.islower() else ord("A")
                d = -shift if dec else shift
                out.append(chr((ord(ch) - base + d) % 26 + base))
            else:
                out.append(ch)
        return "".join(out)

    def _bruteforce(self, args):
        if not args:
            return "usage: bruteforce <caesar_text>"
        text = args[0]
        lines = []
        for s in range(26):
            d = []
            for ch in text:
                if ch.isalpha():
                    base = ord("a") if ch.islower() else ord("A")
                    d.append(chr((ord(ch) - base - s) % 26 + base))
                else:
                    d.append(ch)
            marker = f"  {C.GRN}<- likely{C.RST}" if s == 13 else ""
            lines.append(f"[{s:2d}] {''.join(d)}{marker}")
        return "\n".join(lines)

    def _hash(self, args):
        if not args:
            return "usage: hash <text> [md5|sha1|sha256]"
        text, algo = args[0], (args[1].lower() if len(args) > 1 else "md5")
        try:
            if algo == "md5":
                return hashlib.md5(text.encode()).hexdigest()
            if algo == "sha1":
                return hashlib.sha1(text.encode()).hexdigest()
            if algo == "sha256":
                return hashlib.sha256(text.encode()).hexdigest()
            return f"hash: unknown algorithm '{algo}'"
        except Exception as e:
            return f"hash error: {e}"

    # ── Web Commands ─────────────────────────────────────────────────────────
    def _curl(self, args):
        headers, cookies, url = {}, {}, None
        i = 0
        while i < len(args):
            if args[i] == "-H" and i + 1 < len(args):
                k, v = args[i + 1].split(":", 1)
                headers[k.strip()] = v.strip(); i += 2
            elif args[i] == "-b" and i + 1 < len(args):
                cookies["Cookie"] = args[i + 1]; i += 2
            elif args[i] == "-X" and i + 1 < len(args):
                i += 2
            else:
                url = args[i]; i += 1
        lines = ["HTTP/1.1 200 OK", "Server: Apache/2.4.41"]
        for k, v in headers.items():
            lines.append(f"{k}: {v}")
        for k, v in cookies.items():
            lines.append(f"{k}: {v}")
        lines += ["", "Welcome to the simulated server!"]
        return "\n".join(lines)

    def _ping(self, args):
        host = args[0] if args else "127.0.0.1"
        return "\n".join([
            f"PING {host}: 56 data bytes",
            f"64 bytes from {host}: icmp_seq=0 ttl=64 time=0.042 ms",
            f"--- {host} ping statistics ---",
            "1 packets transmitted, 1 received, 0% packet loss",
        ])

    def _export(self, args):
        if not args:
            return "\n".join(f"declare -x {k}=\"{v}\"" for k, v in sorted(self.env.items()))
        var = args[0]
        if "=" in var:
            k, v = var.split("=", 1)
            self.env[k] = v
        return ""

    def _env(self, _a):
        return "\n".join(f"{k}={v}" for k, v in sorted(self.env.items()))

    def _submit(self, args):
        if not args:
            return "usage: submit FLAG{...}"
        return f"__FLAG__{' '.join(args)}"

    def _help(self, _a):
        return (
            "commands:\n"
            "  ls [-la] [path]          list directory\n"
            "  cat <file>               read file\n"
            "  find [-name x] [-perm x] search files\n"
            "  grep <pattern>           search contents\n"
            "  head/tail [-n N] <file>  read file lines\n"
            "  cd <path>                change directory\n"
            "  pwd                      print working dir\n"
            "  file <file>              identify file type\n"
            "  stat <file>              file metadata\n"
            "  wc <file>                word/line count\n"
            "  strings <file>           extract printable strings\n"
            "  chmod <perm> <file>      change permissions\n"
            "  mkdir/touch <name>       create dir/file\n"
            "  echo <text>              print text\n"
            "  whoami / id              user info\n"
            "  decode <text> <type>     decode (base64/hex/rot13)\n"
            "  encode <text> <type>     encode (base64/hex/rot13)\n"
            "  caesar <text> <shift>    caesar cipher\n"
            "  bruteforce <text>        brute force caesar\n"
            "  hash <text> [algo]       hash (md5/sha1/sha256)\n"
            "  curl <url> [-H k:v]     http request\n"
            "  ping <host>              ping host\n"
            "  export [VAR=val]         set/show environment\n"
            "  env                      show environment\n"
            "  submit FLAG{...}         submit flag\n"
            "  help                     this help\n"
            "  exit                     leave shell"
        )

    # ── Man Pages ────────────────────────────────────────────────────────────
    MAN_PAGES = {
        "ls": (
            "LS(1)                    User Commands                    LS(1)\n\n"
            "NAME\n"
            "       ls - list directory contents\n\n"
            "SYNOPSIS\n"
            "       ls [OPTION]... [FILE]...\n\n"
            "DESCRIPTION\n"
            "       List information about the FILEs.\n\n"
            "       -a     do not ignore entries starting with .\n"
            "       -l     use a long listing format\n\n"
            "EXAMPLES\n"
            "       ls              list files in current directory\n"
            "       ls -la          list all files including hidden, long format\n"
            "       ls /path        list files in /path\n"
        ),
        "cat": (
            "CAT(1)                   User Commands                   CAT(1)\n\n"
            "NAME\n"
            "       cat - concatenate files and print on the standard output\n\n"
            "SYNOPSIS\n"
            "       cat [FILE]...\n\n"
            "DESCRIPTION\n"
            "       Concatenate FILE(s) to standard output.\n\n"
            "EXAMPLES\n"
            "       cat file.txt            display file contents\n"
            "       cat file1 file2        concatenate two files\n"
        ),
        "find": (
            "FIND(1)                  User Commands                  FIND(1)\n\n"
            "NAME\n"
            "       find - search for files in a directory hierarchy\n\n"
            "SYNOPSIS\n"
            "       find [path] [expression]\n\n"
            "DESCRIPTION\n"
            "       Find files in a directory hierarchy.\n\n"
            "       -name pattern   match filename pattern\n"
            "       -perm mode      match permission bits\n"
            "       -size +Nc       files greater than N bytes\n"
            "       -not -empty     non-empty files\n\n"
            "EXAMPLES\n"
            "       find / -name '*.conf'           find all .conf files\n"
            "       find / -perm -4000              find SUID files\n"
            "       find . -size +0c                find non-empty files\n"
        ),
        "grep": (
            "GREP(1)                  User Commands                  GREP(1)\n\n"
            "NAME\n"
            "       grep - print lines that match patterns\n\n"
            "SYNOPSIS\n"
            "       grep [OPTION]... PATTERN [FILE]...\n\n"
            "DESCRIPTION\n"
            "       Grep searches for PATTERNs in each FILE.\n\n"
            "EXAMPLES\n"
            "       grep 'error' log.txt       search for 'error' in log\n"
            "       grep -r 'secret' /etc      recursive search\n"
        ),
        "echo": (
            "ECHO(1)                  User Commands                  ECHO(1)\n\n"
            "NAME\n"
            "       echo - display a line of text\n\n"
            "SYNOPSIS\n"
            "       echo [STRING]...\n\n"
            "DESCRIPTION\n"
            "       Echo the STRING(s) to standard output.\n\n"
            "       > file      redirect output to file (overwrite)\n"
            "       >> file     redirect output to file (append)\n\n"
            "EXAMPLES\n"
            "       echo hello                  print 'hello'\n"
            "       echo data > file.txt        write 'data' to file\n"
            "       echo more >> file.txt       append 'more' to file\n"
        ),
        "chmod": (
            "CHMOD(1)                 User Commands                 CHMOD(1)\n\n"
            "NAME\n"
            "       chmod - change file permissions\n\n"
            "SYNOPSIS\n"
            "       chmod MODE FILE...\n\n"
            "DESCRIPTION\n"
            "       Change the permissions of each FILE to MODE.\n\n"
            "       Special modes:\n"
            "       4755    SUID (run as owner)\n"
            "       2755    SGID (run as group)\n"
            "       1755    sticky bit\n\n"
            "EXAMPLES\n"
            "       chmod 755 file        rwxr-xr-x\n"
            "       chmod +x script.sh    make executable\n"
            "       chmod 4755 prog       set SUID bit\n"
        ),
        "decode": (
            "DECODE(1)                User Commands                DECODE(1)\n\n"
            "NAME\n"
            "       decode - decode encoded text\n\n"
            "SYNOPSIS\n"
            "       decode TEXT TYPE\n\n"
            "DESCRIPTION\n"
            "       Decode TEXT using the specified encoding TYPE.\n\n"
            "       TYPE can be:\n"
            "       base64   Base64 encoding (charset: A-Za-z0-9+/=)\n"
            "       hex      hexadecimal (charset: 0-9a-f)\n"
            "       rot13    ROT13 substitution cipher\n\n"
            "EXAMPLES\n"
            "       decode SGVsbG8= base64       → Hello\n"
            "       decode 48656c6c6f hex        → Hello\n"
            "       decode Uryyb rot13           → Hello\n"
        ),
        "caesar": (
            "CAESAR(1)                User Commands                CAESAR(1)\n\n"
            "NAME\n"
            "       caesar - Caesar cipher encryption/decryption\n\n"
            "SYNOPSIS\n"
            "       caesar TEXT SHIFT [decrypt]\n\n"
            "DESCRIPTION\n"
            "       Shift each letter by SHIFT positions in the alphabet.\n"
            "       Add 'decrypt' to reverse the shift.\n\n"
            "EXAMPLES\n"
            "       caesar hello 3              → khoor\n"
            "       caesar khoor 3 decrypt      → hello\n"
        ),
        "submit": (
            "SUBMIT(1)                User Commands                SUBMIT(1)\n\n"
            "NAME\n"
            "       submit - submit a captured flag\n\n"
            "SYNOPSIS\n"
            "       submit FLAG{...}\n\n"
            "DESCRIPTION\n"
            "       Submit a flag to validate it. Flags have the format\n"
            "       FLAG{descriptive_text}.\n\n"
            "EXAMPLES\n"
            "       submit FLAG{echo_in_the_darkness}\n"
        ),
        "env": (
            "ENV(1)                   User Commands                   ENV(1)\n\n"
            "NAME\n"
            "       env - show/set environment variables\n\n"
            "SYNOPSIS\n"
            "       env [NAME=VALUE]\n\n"
            "DESCRIPTION\n"
            "       Without arguments, show all environment variables.\n"
            "       With NAME=VALUE, set a variable.\n\n"
            "EXAMPLES\n"
            "       env                        show all variables\n"
            "       export SECRET=abc123       set a variable\n"
            "       echo $SECRET               show variable value\n"
        ),
    }

    def _man(self, args):
        if not args:
            return "What manual page do you want?\nUsage: man <command>"
        cmd = args[0].lower()
        page = self.MAN_PAGES.get(cmd)
        if page:
            return page
        return f"No manual entry for {cmd}."

    def _hint_cmd(self, args):
        if self.level_ref:
            h = self.level_ref.get_hint()
            return f"{C.YEL}> {h}{C.RST}"
        return f"{C.DIM}No hint available outside of a level.{C.RST}"


# ── TAB Completer ────────────────────────────────────────────────────────────
class VoidCompleter:
    """TAB-completes commands and virtual filesystem paths."""

    def __init__(self, shell):
        self.shell = shell
        self._matches = []

    def complete(self, text, state):
        if state == 0:
            tokens = readline.get_begidx() == 0
            if tokens:
                self._matches = [c for c in VirtualShell.COMMANDS if c.startswith(text)]
            else:
                args = readline.get_line_buffer().split()
                if len(args) >= 2:
                    prefix = args[-1]
                    all_paths = self.shell.fs._list_all()
                    cwd_children = []
                    node = self.shell.fs.cwd
                    if node and node.is_dir:
                        for c in node.children.values():
                            cwd_children.append(c.name)
                    candidates = all_paths + cwd_children
                    if "/" in prefix:
                        dir_part = prefix.rsplit("/", 1)[0] + "/"
                        name_part = prefix.rsplit("/", 1)[1]
                        candidates = [
                            p for p in candidates
                            if p.startswith(dir_part) and p.split("/")[-1].startswith(name_part)
                        ]
                    else:
                        candidates = [c for c in candidates if c.split("/")[-1].startswith(prefix)]
                    self._matches = sorted(set(candidates))
                else:
                    self._matches = []
        try:
            return self._matches[state]
        except IndexError:
            return None


def setup_readline(shell):
    """Configure readline with TAB completion and history."""
    if not _READLINE:
        return
    comp = VoidCompleter(shell)
    readline.set_completer(comp.complete)
    readline.set_completer_delims(" \t\n")
    readline.parse_and_bind("tab: complete")
    hist = os.path.join(os.path.expanduser("~"), ".void_history")
    try:
        readline.read_history_file(hist)
    except FileNotFoundError:
        pass
    import atexit
    atexit.register(readline.write_history_file, hist)





# ── Game State ───────────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.data = self._defaults()
        self.load()

    def _defaults(self):
        return {
            "current_level": "1.1",
            "completed": [],
            "flags": [],
            "points": 0,
            "hacker_name": None,
            "puzzle_states": {},
            "started": datetime.now().isoformat(),
            "saved": datetime.now().isoformat(),
        }

    def save(self):
        self.data["saved"] = datetime.now().isoformat()
        with open(SAVE_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f:
                    loaded = json.load(f)
                self.data.update(loaded)
                self.data.setdefault("puzzle_states", {})
                return True
            except (IOError, json.JSONDecodeError):
                pass
        return False

    def save_puzzle_state(self, level_id, puzzle_state):
        self.data["puzzle_states"][level_id] = puzzle_state

    def get_puzzle_state(self, level_id):
        return dict(self.data.get("puzzle_states", {}).get(level_id, {}))

    def complete_level(self, level_id):
        if level_id not in self.data["completed"]:
            self.data["completed"].append(level_id)
            self.data["flags"].append(FLAGS[level_id])
            track = level_id.split(".")[0]
            self.data["points"] += TRACKS[track]["levels"][level_id]["diff"].count("★") * 100
            self._advance()
            self.save()

    def _advance(self):
        order = list(FLAGS.keys())
        idx = order.index(self.data["current_level"]) if self.data["current_level"] in order else -1
        if idx < len(order) - 1:
            self.data["current_level"] = order[idx + 1]

    def is_unlocked(self, level_id):
        order = list(FLAGS.keys())
        if level_id not in order:
            return False
        idx = order.index(level_id)
        if idx == 0:
            return True
        return order[idx - 1] in self.data["completed"]


# ── Abstract Level ───────────────────────────────────────────────────────────
class AbstractLevel(ABC):
    def __init__(self, level_id, game_state, saved_puzzle_state=None):
        self.level_id = level_id
        self.state = game_state
        self.fs = VirtualFS()
        self.env = {}
        self.flag = FLAGS[level_id]
        self.solved = False
        self.puzzle_state = saved_puzzle_state or {}
        self.shell = VirtualShell(self.fs, self.env, on_command=self._shell_hook, level_ref=self)
        self._setup_environment()

    @abstractmethod
    def _setup_environment(self): ...

    @abstractmethod
    def get_prompt(self): ...

    @abstractmethod
    def get_enigma(self): ...

    @abstractmethod
    def get_lore(self): ...

    @abstractmethod
    def get_hint(self): ...

    @abstractmethod
    def get_study(self): ...

    @abstractmethod
    def _shell_hook(self, cmd, args, result): ...

    def is_solved(self):
        return self.solved

    def get_prompt_plain(self):
        """Plain text prompt for readline compatibility (no ANSI codes)."""
        return "hacker@void:~$ "

    def run_shell(self):
        setup_readline(self.shell)
        print(f"\n{C.DIM}{self.get_lore()}{C.RST}")
        print(f"\n{C.BOLD}{self.get_enigma()}{C.RST}")
        print(f"{C.DIM}type 'help' for commands, 'exit' to leave{C.RST}\n")

        while not self.solved:
            try:
                # Plain prompt for readline compatibility (no ANSI codes)
                prompt = self.get_prompt_plain()
                raw = input(prompt).strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return False
            if not raw:
                continue
            if raw.lower() == "exit":
                return False
            if raw.lower() == "study":
                print(f"\n{C.DIM}{self.get_study()}{C.RST}\n")
                continue
            if raw.lower() in ("hint", "mirar"):
                h = self.get_hint()
                print(f"\n  {C.YEL}>{h}{C.RST}\n")
                continue

            result = self.shell.execute(raw)
            if result and "__FLAG__" in result:
                submitted = result.replace("__FLAG__", "").strip()
                if submitted == self.flag:
                    self.solved = True
                    self._victory()
                else:
                    print(f"{C.RED}invalid flag.{C.RST}")
            elif result:
                print(result)
        return True

    def _victory(self):
        print(f"\n{C.GRN}{'='*60}")
        print(f"  F L A G   C A P T U R E D")
        print(f"{'='*60}{C.RST}")
        print(f"\n  {C.BOLD}{self.flag}{C.RST}\n")
        pts = TRACKS[self.level_id.split(".")[0]]["levels"][self.level_id]["diff"].count("★") * 100
        print(f"  {C.CYN}RESUMEN DE PODER:{C.RST}")
        print(f"  +{pts} points")
        print(f"  Skill dominado: {self.get_study().split(chr(10))[0]}")
        print()

    def _post_exploitation(self):
        pass


# ── Level Implementations ────────────────────────────────────────────────────
class Level11(AbstractLevel):
    """Track 1.1: El Despertar del Eco - Redirección básica"""

    def _setup_environment(self):
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "core", "", perms="-rw-rw----")
        self.fs.touch("/challenge", "readme.txt",
            "The system is dormant. Inject the word DESPIERTA into /challenge/core\n"
            "using output redirection. The 'echo' command speaks to the void;\n"
            "the '>' operator captures its words.")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
        self.env["user"] = "hacker"

    def get_prompt(self):
        return f"{C.GRN}hacker@void:~$ {C.RST}"

    def get_enigma(self):
        return "El archivo /challenge/core está sediento. Su existencia está vacía."

    def get_lore(self):
        return LORE["manifesto"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "Un comando como echo PALABRA lanza texto al viento. Si usas >, puedes atrapar ese viento en un archivo.",
            "Escribe: echo DESPIERTA > /challenge/core",
            "El operador > redirige stdout a un archivo. > crea, >> adjunta.",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 1.1: Redirección Básica ---\n\n"
            "  echo TEXTO          imprime texto en pantalla\n"
            "  echo TEXTO > file   redirige salida a archivo (sobreescribe)\n"
            "  echo TEXTO >> file  agrega salida al final del archivo\n\n"
            "  stdout (1) = salida normal\n"
            "  stderr (2) = errores\n"
            "  stdin  (0) = entrada\n\n"
            "  Ejemplo:\n"
            "    echo hello > /tmp/test.txt\n"
            "    cat /tmp/test.txt   →  hello"
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "cat" and args and args[0] == "/challenge/core":
            c = self.fs.cat("/challenge/core")
            if c and "DESPIERTA" in c:
                self.puzzle_state["injected"] = True
                return f"__FLAG__{self.flag}"
        return None


class Level12(AbstractLevel):
    """Track 1.2: Los Archivos Fantasma - Archivos ocultos"""

    def _setup_environment(self):
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "vault", is_dir=True)
        # Create 99 empty files
        for i in range(99):
            self.fs.touch("/challenge/vault", f"file_{i:03d}.dat", "")
        # One file with content (the flag)
        self.fs.touch("/challenge/vault", "whisper.dat",
            "the worm speaks in whispers, not shouts. look for weight where others have none.",
            perms="-rw-r--r--")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
        self.env["user"] = "hacker"

    def get_prompt(self):
        return f"{C.GRN}hacker@void:~$ {C.RST}"

    def get_enigma(self):
        return (
            "\"Lo que es invisible a los ojos deja su peso en el disco.\"\n"
            "  Hay 100 archivos en /challenge/vault/. Solo uno no está vacío."
        )

    def get_lore(self):
        return LORE["morris"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "El Gusano de Morris llenaba los discos con basura invisible. Usa find o grep para detectar peso.",
            "Prueba: find /challenge/vault/ -size +0c",
            "O: ls -la /challenge/vault/ | grep -v '^d' | grep -v ' 0 '",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 1.2: Archivos Ocultos y Metadatos ---\n\n"
            "  ls -la              lista todo incluyendo ocultos\n"
            "  find / -name x      busca por nombre\n"
            "  find / -size +0c    busca archivos con contenido\n"
            "  file <file>         identifica tipo de archivo\n"
            "  stat <file>         muestra metadata completa\n\n"
            "  Los archivos que empiezan con '.' son ocultos.\n"
            "  find -size +0c detecta archivos que no están vacíos."
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "cat" and args:
            c = self.fs.cat(args[0]) if args else ""
            if c and "worm speaks" in c:
                self.puzzle_state["found"] = True
                return f"__FLAG__{self.flag}"
        return None


class Level13(AbstractLevel):
    """Track 1.3: El Archivo de los Sabios - Pipelines y codificación"""

    def _setup_environment(self):
        self.fs.touch("/", "challenge", is_dir=True)
        # Clean base64 that decodes to contain the actual flag
        secret = "void{th3_n33dl3_1n_th3_h4yst4ck}"
        clean_b64 = base64.b64encode(secret.encode()).decode()
        self.fs.touch("/challenge", "archive.bin",
            f"=== INTERCEPTED TRANSMISSION ===\n"
            f"Encoded: {clean_b64}\n"
            f"=== END ===\n"
            f"\n"
            f"Noise: AAAAABBBBCCCCDDDD\n"
            f"Rot13 hint: gur_synt_vf_uvggra_va_gur_fbyng\n"
            f"Garbage: !@#$%^&*()\n",
            perms="-rw-r--r--")
        self.fs.touch("/challenge", "readme.txt",
            "This archive contains encoded secrets.\n"
            "1. Find the base64 string (starts with 'dm9pZ')\n"
            "2. decode dm9pZC... base64\n"
            "3. Or: cat archive.bin | grep Encoded | cut -d' ' -f2 | decode - base64")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
        self.env["user"] = "hacker"

    def get_prompt(self):
        return f"{C.GRN}hacker@void:~$ {C.RST}"

    def get_enigma(self):
        return "El archivo corrupto contiene cadenas ocultas. Filtra y decodifica."

    def get_lore(self):
        return LORE["phrack"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "strings extrae texto legible de binarios. cat y pipe: strings /challenge/archive.bin",
            "El archivo tiene base64 y rot13. Usa decode <text> base64 o rot13.",
            "El flag está codificado en base64 en el primer bloque de strings.",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 1.3: Pipelines y Codificación ---\n\n"
            "  strings <file>       extrae texto legible de binarios\n"
            "  cat file | grep pat  filtra contenido\n"
            "  sort | uniq          ordena y elimina duplicados\n\n"
            "  Codificaciones:\n"
            "    base64: charset [A-Za-z0-9+/=], padding con '='\n"
            "    hex:    solo [0-9a-f], longitud par\n"
            "    rot13:  shifted alphabet, solo letras\n\n"
            "  decode <text> base64\n"
            "  decode <text> hex\n"
            "  decode <text> rot13\n"
            "  bruteforce <text>    intenta los 26 shifts"
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "decode" and len(args) >= 2 and args[-1] == "base64":
            try:
                text = " ".join(args[:-1]).replace("\n", "").replace(" ", "")
                decoded = base64.b64decode(text).decode()
                if "void{" in decoded.lower() or "flag{" in decoded.lower():
                    self.puzzle_state["decoded"] = True
                    return f"__FLAG__{self.flag}"
            except Exception:
                pass
        return None


class Level21(AbstractLevel):
    """Track 2.1: El Sendero Perdido - PATH Hijacking"""

    def _setup_environment(self):
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "run",
            "#!/bin/bash\n"
            "# This script looks for 'win' in PATH\n"
            "echo \"Searching for win command...\"\n"
            "win\n"
            "echo \"If you see this, win was not found in PATH.\"",
            perms="-rwxr-xr-x")
        # No 'win' command exists yet
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
        self.env["user"] = "hacker"

    def get_prompt(self):
        return f"{C.GRN}hacker@void:~$ {C.RST}"

    def get_enigma(self):
        return (
            "El ejecutable /challenge/run invoca un comando llamado 'win'.\n"
            "  Pero 'win' no existe en ningún lado. Debes crearlo y hacerlo visible."
        )

    def get_lore(self):
        return LORE["thompson"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "Los binarios son ciegos; solo ven lo que la variable PATH les permite mirar.",
            "Crea un directorio ~/bin, escribe un script 'win' ahí, y ponlo en PATH.",
            "Pasos: mkdir ~/bin && echo 'echo VICTORY' > ~/bin/win && chmod +x ~/bin/win && PATH=~/bin:$PATH && /challenge/run",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 2.1: PATH Hijacking ---\n\n"
            "PATH es una variable de entorno con directorios separados por ':'.\n"
            "Cuando ejecutas un comando, el shell busca en cada directorio.\n\n"
            "  echo $PATH              ver rutas actuales\n"
            "  export PATH=/nueva:ruta:$PATH  agregar ruta\n\n"
            "Si creas un script 'win' en un directorio que está ANTES\n"
            "en PATH, el sistema ejecutará TU script, no el original.\n\n"
            "  mkdir ~/bin\n"
            "  echo '#!/bin/bash' > ~/bin/win\n"
            "  echo 'echo HACKED' >> ~/bin/win\n"
            "  chmod +x ~/bin/win\n"
            "  PATH=~/bin:$PATH\n"
            "  win   → HACKED"
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "win" or (cmd == "/challenge/run" and "win" in (result or "")):
            self.puzzle_state["win_found"] = True
            return f"__FLAG__{self.flag}"
        return None


class Level22(AbstractLevel):
    """Track 2.2: Las Máscaras del Entorno - Environment variables"""

    def _setup_environment(self):
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "auth",
            "#!/bin/bash\n"
            "# Cypherpunk handshake verification\n"
            "if [ \"$SECRET_HANDSHAKE\" = \"PGP_WAS_HERE_1991\" ]; then\n"
            "    echo 'ACCESS GRANTED'\n"
            "    echo 'FLAG{environment_is_destiny}'\n"
            "else\n"
            "    echo 'ACCESS DENIED'\n"
            "fi",
            perms="-rwxr-xr-x")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"
        self.env["user"] = "hacker"
        # Hide the secret somewhere
        self.fs.touch("/", "etc", is_dir=True)
        self.fs.touch("/etc", "cypherpunk.conf",
            "# PGP Handshake Protocol v1.0\n"
            "# Secret key: PGP_WAS_HERE_1991\n"
            "# Do not share this value.",
            perms="-rw-r-----")
        self.env["SECRET_HANDSHAKE"] = ""

    def get_prompt(self):
        return f"{C.GRN}hacker@void:~$ {C.RST}"

    def get_enigma(self):
        return (
            "Un binario en /challenge/auth exige un Handshake secreto.\n"
            "  Busca la llave oculta en el sistema y expórtala."
        )

    def get_lore(self):
        return LORE["cypherpunk"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "Los cypherpunks esconden secretos en textos que parecen basura.",
            "Busca archivos de configuración: ls -la /etc/",
            "Cat /etc/cypherpunk.conf y busca el valor. Luego export SECRET_HANDSHAKE=valor",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 2.2: Variables de Entorno ---\n\n"
            "  env                   muestra todas las variables\n"
            "  export VAR=valor      define variable\n"
            "  echo $VAR             muestra valor\n\n"
            "Las variables de entorno se heredan de proceso en proceso.\n"
            "Un script mal configurado puede filtrar secretos a través\n"
            "de variables accesibles con env o /proc/self/environ.\n\n"
            "  grep -r secret /etc/  busca en configuraciones\n"
            "  export KEY=value      implanta el secreto\n"
            "  ./auth                ejecuta con el entorno"
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "/challenge/auth" or cmd == "auth":
            if self.env.get("SECRET_HANDSHAKE") == "PGP_WAS_HERE_1991":
                self.puzzle_state["authenticated"] = True
                return f"__FLAG__{self.flag}"
        return None


class Level31(AbstractLevel):
    """Track 3.1: El Espejo del Rey - SUID"""

    def _setup_environment(self):
        self.env["user"] = "lowpriv"
        self.env["uid"] = "1000"
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "backdoor",
            "#!/bin/bash\n"
            "# SUID helper - reads files as root\n"
            "cat /root/flag.txt",
            perms="-rwsr-xr-x", owner="root")
        self.fs.touch("/", "root", is_dir=True)
        self.fs.touch("/root", "flag.txt",
            "FLAG{suid_the_keys_to_the_kingdom}",
            perms="-rw-------", owner="root")
        self.fs.touch("/challenge", "readme.txt",
            "The backdoor runs as root. But you can't execute it directly.\n"
            "Find a way to make it read the forbidden file.")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

    def get_prompt(self):
        uid = self.env.get("uid", "1000")
        sym = "#" if uid == "0" else "$"
        return f"{C.GRN}hacker@void:~{sym} {C.RST}"

    def get_enigma(self):
        return (
            "Eres lowpriv. /root/flag.txt está sellado.\n"
            "  Pero /challenge/backdoor tiene el bit SUID... y corre como root."
        )

    def get_lore(self):
        return LORE["suid_myth"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "El bit SUID (s en permisos) hace que un binario se ejecute como su dueño, no como quien lo llama.",
            "ls -la /challenge/backdoor verás -rwsr-xr-x. 's' significa SUID.",
            "Ejecuta directamente: /challenge/backdoor  — corre como root y lee el flag.",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 3.1: SUID Privilege Escalation ---\n\n"
            "chmod 4755 file    →  SUID bit activado\n"
            "ls -la             →  ver 's' en permisos\n\n"
            "Cuando un binario tiene SUID y pertenece a root,\n"
            "se ejecuta como root sin importar quién lo llame.\n\n"
            "GTFOBins (gtfobins.github.io) lista binarios SUID\n"
            "que pueden usarse para escalar privilegios.\n\n"
            "Defensa:\n"
            "  - Auditar binarios SUID: find / -perm -4000\n"
            "  - Remover SUID innecesario\n"
            "  - Usar capabilities en su lugar"
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "/challenge/backdoor" or (cmd == "cat" and args and "flag.txt" in args[0]):
            self.puzzle_state["escalated"] = True
            return f"__FLAG__{self.flag}"
        return None


class Level32(AbstractLevel):
    """Track 3.2: La Cronología del Caos - Cronjob injection"""

    def _setup_environment(self):
        self.env["user"] = "lowpriv"
        self.env["uid"] = "1000"
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "backup.sh",
            "#!/bin/bash\n"
            "# Backup script - runs as root every minute\n"
            "cp /root/secret.txt /tmp/backup_secret.txt\n"
            "chmod 644 /tmp/backup_secret.txt",
            perms="-rwxrwxrwx", owner="root")  # World-writable!
        self.fs.touch("/", "root", is_dir=True)
        self.fs.touch("/root", "secret.txt",
            "FLAG{cron_the_sleeping_god}",
            perms="-rw-------", owner="root")
        self.fs.touch("/", "etc", is_dir=True)
        self.fs.touch("/etc", "crontab",
            "# m h dom mon dow command\n"
            "* * * * * /challenge/backup.sh\n",
            perms="-rw-r--r--")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

    def get_prompt(self):
        uid = self.env.get("uid", "1000")
        sym = "#" if uid == "0" else "$"
        return f"{C.GRN}hacker@void:~{sym} {C.RST}"

    def get_enigma(self):
        return (
            "Un script corre como root cada minuto.\n"
            "  El archivo es world-writable. Modifícalo antes de que se ejecute."
        )

    def get_lore(self):
        return LORE["cron_warning"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "El crontab es un dios dormido que despierta cada minuto.",
            "ls -la /challenge/backup.sh — verás permisos 777. Cualquiera puede escribir.",
            "Sobreescribe el script: echo '#!/bin/bash\ncat /root/secret.txt' > /challenge/backup.sh",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 3.2: Cronjob Injection ---\n\n"
            "  crontab -l              listar tareas programadas\n"
            "  /etc/crontab            cron del sistema\n\n"
            "Formato: min hour dom month dow command\n\n"
            "Si un script en crontab es world-writable,\n"
            "cualquier usuario puede sobreescribirlo.\n"
            "Cuando cron lo ejecute, correrá tu código como root.\n\n"
            "Defensa:\n"
            "  - Permisos restrictivos en scripts de cron\n"
            "  - Usar crontab con usuarios específicos\n"
            "  - Monitorear cambios con inotifywait"
        )

    def _shell_hook(self, cmd, args, result):
        if cmd == "cat" and args and "secret.txt" in args[0]:
            self.puzzle_state["read_secret"] = True
            return f"__FLAG__{self.flag}"
        return None


class Level41(AbstractLevel):
    """Track 4.1: El Desborde del Alma - Buffer Overflow"""

    def _setup_environment(self):
        self.env["user"] = "hacker"
        self.env["uid"] = "1000"
        self.fs.touch("/", "challenge", is_dir=True)
        self.fs.touch("/challenge", "gate",
            "#!/bin/bash\n"
            "# Gatekeeper - asks for password\n"
            "# VULNERABILITY: reads 256 bytes into 64-byte buffer\n"
            "# The overflow overwrites 'authenticated' variable\n"
            "# Password: any input that overflows buffer + sets auth\n"
            "# Try: python3 -c \"print('A'*65 + 'TRUE')\" | ./gate\n"
            "# Or: echo AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATrue\n"
            "read -s -n 256 INPUT\n"
            "if echo \"$INPUT\" | grep -q 'True'; then\n"
            "    echo 'GATE OPENED'\n"
            "else\n"
            "    echo 'GATE LOCKED'\n"
            "fi",
            perms="-rwxr-xr-x")
        self.fs.touch("/challenge", "gate.c",
            "#include <stdio.h>\n"
            "#include <string.h>\n\n"
            "int main() {\n"
            "    char buffer[64];\n"
            "    int authenticated = 0;\n\n"
            "    printf(\"Enter password: \");\n"
            "    gets(buffer);  // DANGEROUS: no bounds checking!\n\n"
            "    if (authenticated) {\n"
            "        printf(\"GATE OPENED\\n\");\n"
            "    } else {\n"
            "        printf(\"GATE LOCKED\\n\");\n"
            "    }\n"
            "    return 0;\n"
            "}",
            perms="-rw-r--r--")
        self.fs.touch("/challenge", "readme.txt",
            "The gate requires a password.\n"
            "But the code reveals a flaw... the buffer is only 64 bytes.\n"
            "Read gate.c. Understand the stack. Overflow with intention.")
        self.env["PATH"] = "/usr/local/bin:/usr/bin:/bin"

    def get_prompt(self):
        return f"{C.GRN}hacker@void:~$ {C.RST}"

    def get_enigma(self):
        return (
            "La compuerta pide una contraseña.\n"
            "  Pero el código fuente revela una grieta en la memoria.\n"
            "  Usa el desbordamiento para alterar el destino."
        )

    def get_lore(self):
        return LORE["buffer_overflow"]

    def get_hint(self):
        step = self.puzzle_state.get("step", 0)
        hints = [
            "Lee el código fuente: cat /challenge/gate.c — observa que gets() no valida límites.",
            "El buffer mide 64 bytes. La variable 'authenticated' está justo después en memoria.",
            "Escribe 65 'A' seguidos de 'True': echo AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATrue | /challenge/gate",
        ]
        self.puzzle_state["step"] = min(step + 1, len(hints) - 1)
        return hints[min(step, len(hints) - 1)]

    def get_study(self):
        return (
            "--- TRACK 4.1: Buffer Overflow Básico ---\n\n"
            "La pila (stack) almacena:\n"
            "  - Variables locales (buffers)\n"
            "  - Variables de control (autenticación)\n"
            "  - Direcciones de retorno\n\n"
            "Si escribes MÁS datos de los que el buffer puede guardar,\n"
            "los bytes extra sobreescriben variables vecinas.\n\n"
            "  char buffer[64];     ← 64 bytes\n"
            "  int authenticated;   ← justo después\n\n"
            "Si escribes 65+ bytes, el byte 65+ sobreescribe 'authenticated'.\n\n"
            "En C real, esto puede sobreescribir direcciones de retorno\n"
            "para ejecutar código arbitrario. Por eso gets() es peligroso.\n\n"
            "Defensa:\n"
            "  - Usar fgets() en lugar de gets()\n"
            "  - Stack canaries, ASLR, NX bit"
        )

    def _shell_hook(self, cmd, args, result):
        if result and "GATE OPENED" in result:
            self.puzzle_state["gate_opened"] = True
            return f"__FLAG__{self.flag}"
        return None


# ── Level Factory ────────────────────────────────────────────────────────────
LEVEL_CLASSES = {
    "1.1": Level11, "1.2": Level12, "1.3": Level13,
    "2.1": Level21, "2.2": Level22,
    "3.1": Level31, "3.2": Level32,
    "4.1": Level41,
}


def create_level(level_id, state, saved_ps=None):
    cls = LEVEL_CLASSES.get(level_id)
    return cls(level_id, state, saved_ps) if cls else None


# ── Hacker Name Generator ───────────────────────────────────────────────────
def generate_hacker_name():
    # Short leet speak pools (3-4 chars each) — names stay 3-7 chars total
    pool = [
        "x", "z", "k", "n", "r", "v", "j", "q",
        "0x", "nk", "rx", "v0", "kz", "zx", "jn", "qr",
        "n3k", "z4x", "r1f", "k0d", "v8n", "x7r", "j4z", "q0x",
        "n1x", "z3k", "r0x", "k4n", "v1d", "x9z", "j0k", "q7r",
        "ph4", "cr8", "sh3", "gh0", "b1n", "st4", "h3x", "p1ng",
        "n0k", "z1x", "r4v", "k7d", "v0x", "x3n", "j8z", "q1r",
    ]

    print(f"\n{C.DIM}sc4nning r3sp0ns3s...")
    time.sleep(0.5)
    print("qu3rying ARP4N3t d4t4b4s3s...")
    time.sleep(0.5)
    print(f"g3n3r4t1ng s3r14l 1d3nt1ty...{C.RST}\n")
    time.sleep(0.5)

    questions = [
        ("¿Pr3f13r3s 3l 51l3nc10 d3l c4bl3 0 3l c405 d3l4s fr3qu3nc14s?",
         ["51l3nc10", "c405", "ruid0", "v4c10"]),
        ("¿Cu4l 35 tu l3ngu4j3: 3l 51l1c10, 3l scr1pt 0 3l 3rr0r?",
         ["51l1c10", "scr1pt", "3rr0r", "c0d1g0"]),
        ("¿Busc4s l4 v3rd4d 0 l4 vuln3r4b1l1d4d?",
         ["v3rd4d", "vuln3r4b1l1d4d", "p0d3r", "c0n0c1m13nt0"]),
    ]

    answers = []
    for q, opts in questions:
        print(f"  {C.CYN}{q}{C.RST}")
        for i, o in enumerate(opts, 1):
            print(f"    {C.DIM}{i}. {o}{C.RST}")
        try:
            choice = input(f"  {C.GRN}> {C.RST}").strip()
            idx = int(choice) - 1 if choice.isdigit() else 0
            answers.append(opts[idx % len(opts)])
        except (EOFError, KeyboardInterrupt, ValueError):
            answers.append(random.choice(opts))

    # Generate short name (3-7 chars)
    seed = sum(ord(c) for a in answers for c in a)
    random.seed(seed)
    name = random.choice(pool)

    print(f"\n{C.GRN}{'='*60}")
    print(f"  S 3 R 1 4 L   1 D 3 N T 1 T Y")
    print(f"{'='*60}{C.RST}")
    print(f"\n  {C.BOLD}{C.CYN}{name}{C.RST}\n")
    print(f"  {C.DIM}4ssum3 y0ur 1d3nt1ty. Th3 v01d r3c0gn1z3s y0u.{C.RST}\n")

    return name


# ── Riddles System ───────────────────────────────────────────────────────────
RIDDLES = [
    {
        "text": (
            "\"Fui el primer viajero en replicarse sin permiso, colapsé\n"
            "  un décimo de la red en 1988 y mi creador fue el primero\n"
            "  en ser condenado por la ley informática.\"\n"
            "  ¿Qué nombre de gusano debes susurrarle al sistema?"
        ),
        "answer": "morris",
        "lore": LORE["morris"],
    },
    {
        "text": (
            "\"Nací en 1985, soy el evangelio del underground.\n"
            "  Cada volumen es un campo de batalla de ideas,\n"
            "  exploits y la cruda verdad. Phreak, hack, learn, repeat.\"\n"
            "  ¿Cuál es mi nombre?"
        ),
        "answer": "phrack",
        "lore": LORE["phrack"],
    },
    {
        "text": (
            "\"Ken Thompson compiló el primer C en un trozo de papel.\n"
            "  El modelo de confianza de Unix comenzó con un hombre\n"
            "  y un compilador. ¿Qué sistema operativo creó?\""
        ),
        "answer": "unix",
        "lore": LORE["thompson"],
    },
    {
        "text": (
            "\"Fui escrito por Eric Hughes en 1993. Dije:\n"
            "  'Escribimos código. Sabemos que alguien debe escribir\n"
            "  software para defender la privacidad.'\"\n"
            "  ¿Quiénes somos?"
        ),
        "answer": "cypherpunks",
        "lore": LORE["cypherpunk"],
    },
    {
        "text": (
            "\"Soy un dios dormido que despierta cada minuto.\n"
            "  Ejecuto la voluntad de root y vuelvo a dormir.\n"
            "  Pero si puedes escribir en mi script... tú te conviertes\n"
            "  en el dios.\"\n"
            "  ¿Qué utilidad del sistema soy?"
        ),
        "answer": "cron",
        "lore": LORE["cron_warning"],
    },
    {
        "text": (
            "\"En 1996, Aleph One escribió mi evangelio en Phrack #49.\n"
            "  Dije: 'El stack no conoce la diferencia entre datos\n"
            "  y direcciones de retorno.'\"\n"
            "  ¿Qué técnica de explotación describí?"
        ),
        "answer": "buffer overflow",
        "lore": LORE["buffer_overflow"],
    },
    {
        "text": (
            "\"El bit 's' en los permisos me convierte en una llave maestra.\n"
            "  Cuando un binario me lleva, se ejecuta como su dueño.\n"
            "  GTFOBins documenta mi poder.\""
            "  ¿Cómo me llamo?"
        ),
        "answer": "suid",
        "lore": LORE["suid_myth"],
    },
]


def run_riddles():
    print(f"\n{C.DIM}Los acertijos emergen de los sectores corruptos del disco...{C.RST}\n")

    random.shuffle(RIDDLES)
    score = 0

    for i, riddle in enumerate(RIDDLES, 1):
        print(f"{C.BOLD}{'='*60}")
        print(f"  RIDDLE {i}/{len(RIDDLES)}")
        print(f"{'='*60}{C.RST}")
        print(f"\n{C.CYN}{riddle['text']}{C.RST}\n")
        print(f"{C.DIM}(Escribe 'skip' para saltar, 'hint' para pista, 'exit' para salir){C.RST}\n")

        attempts = 0
        while attempts < 3:
            try:
                answer = input(f"{C.GRN}hacker@void:riddle$ {C.RST}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return

            if answer == "exit":
                print(f"\n{C.DIM}El vacío se cierra tras ti...{C.RST}\n")
                return
            if answer == "skip":
                print(f"{C.DIM}El misterio permanece...{C.RST}\n")
                break
            if answer == "hint":
                print(f"\n  {C.YEL}>{riddle['lore'][:100]}...{C.RST}\n")
                continue

            if answer == riddle["answer"]:
                print(f"\n{C.GRN}  ACERTIJO RESUELTO{C.RST}")
                print(f"  {C.DIM}{riddle['lore'][:120]}...{C.RST}\n")
                score += 1
                break
            else:
                attempts += 1
                remaining = 3 - attempts
                if remaining > 0:
                    print(f"  {C.RED}El vacío rechaza tu respuesta. {remaining} intentos restantes.{C.RST}\n")
                else:
                    print(f"  {C.RED}El acertijo se cierra. La respuesta era: {riddle['answer']}{C.RST}\n")

    print(f"{C.BOLD}{'='*60}")
    print(f"  RIDDLE SESSION COMPLETE")
    print(f"{'='*60}{C.RST}")
    print(f"  {C.GRN}Resueltos: {score}/{len(RIDDLES)}{C.RST}\n")


# ── Walkthrough Mode ─────────────────────────────────────────────────────────
def run_walkthrough():
    print(f"\n{C.DIM}Modo Walkthrough: El juego te guía paso a paso...{C.RST}\n")

    lessons = [
        {
            "title": "Lección 1: Navegando el Vacío",
            "steps": [
                ("Escribe 'pwd' para ver dónde estás", "pwd"),
                ("Escribe 'ls' para ver qué hay aquí", "ls"),
                ("Escribe 'ls -la' para ver archivos ocultos", "ls -la"),
            ],
            "summary": "pwd muestra tu ubicación, ls lista archivos, -la revela ocultos.",
        },
        {
            "title": "Lección 2: Leyendo la Oscuridad",
            "steps": [
                ("Crea un archivo: touch test.txt", "touch test.txt"),
                ("Escríbele contenido: echo 'hello void' > test.txt", "echo 'hello void' > test.txt"),
                ("Léelo: cat test.txt", "cat test.txt"),
            ],
            "summary": "touch crea archivos, echo + > escribe, cat lee.",
        },
        {
            "title": "Lección 3: El Poder del Pipe",
            "steps": [
                ("Crea varios archivos: touch a.txt b.txt c.txt", "touch a.txt b.txt c.txt"),
                ("Escríbeles contenido: echo 'alpha' > a.txt", "echo 'alpha' > a.txt"),
                ("Cadena comandos: echo 'hello' | cat", "echo 'hello' | cat"),
            ],
            "summary": "El pipe | alimenta la salida de un comando como entrada de otro.",
        },
        {
            "title": "Lección 4: Variables de Entorno",
            "steps": [
                ("Ve tus variables: env", "env"),
                ("Crea una: export MY_SECRET=abc123", "export MY_SECRET=abc123"),
                ("Verifícala: echo $MY_SECRET", "echo $MY_SECRET"),
            ],
            "summary": "export crea variables, $ las referencia, env las muestra todas.",
        },
    ]

    for lesson in lessons:
        print(f"{C.BOLD}{'='*60}")
        print(f"  {lesson['title']}")
        print(f"{'='*60}{C.RST}\n")

        for desc, expected in lesson["steps"]:
            print(f"  {C.CYN}{desc}{C.RST}")
            try:
                cmd = input(f"  {C.GRN}> {C.RST}").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return

            if cmd == expected:
                print(f"  {C.GRN}✓ Correcto{C.RST}\n")
            elif cmd == "exit":
                return
            else:
                print(f"  {C.DIM}El sistema ejecuta: {expected}{C.RST}\n")

        print(f"  {C.YEL}RESUMEN: {lesson['summary']}{C.RST}\n")
        try:
            input(f"  {C.DIM}Presiona Enter para continuar...{C.RST}")
        except (EOFError, KeyboardInterrupt):
            print()
            return

    print(f"\n{C.GRN}Walkthrough completado. Ahora intenta 'play' sin ayuda.{C.RST}\n")


# ── Diary System ─────────────────────────────────────────────────────────────
def write_diary(state, event, detail=""):
    entry = (
        f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} — {event}\n\n"
        f"{detail}\n"
    )
    with open(DIARY_FILE, "a") as f:
        f.write(entry)


def init_diary():
    if not os.path.exists(DIARY_FILE):
        with open(DIARY_FILE, "w") as f:
            f.write(
                "# El Diario del Vacío\n\n"
                "*\"Lo que el sistema olvida, el hacker recuerda.\"*\n\n"
                "---\n"
            )


# ── Main Controller ──────────────────────────────────────────────────────────
class VoidOS:
    def __init__(self):
        self.state = GameState()
        init_diary()

    def run(self):
        self._banner()
        while True:
            try:
                lvl = self.state.data["current_level"]
                name = self.state.data.get("hacker_name", "unknown")
                # Plain prompt for readline compatibility
                raw = input(f"[{lvl}] {name}@void:~$ ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self.state.save()
                break
            if not raw:
                continue

            cmd = raw.split()[0].lower()

            if cmd in ("help", "menu", "?", "ayuda"):
                self._menu()
            elif cmd == "play":
                self._play()
            elif cmd == "walkthrough":
                run_walkthrough()
            elif cmd == "riddles":
                run_riddles()
            elif cmd == "hackername":
                name = generate_hacker_name()
                self.state.data["hacker_name"] = name
                self.state.save()
                write_diary(self.state, "ALIAS GENERATED", f"New identity: {name}")
            elif cmd in ("tracks", "track"):
                self._tracks()
            elif cmd in ("status", "progreso"):
                self._status()
            elif cmd in ("inventario", "flags"):
                self._inventory()
            elif cmd in ("diary", "diario"):
                self._show_diary()
            elif cmd in ("guardar", "save"):
                self.state.save()
                print(f"{C.GRN}saved.{C.RST}")
            elif cmd in ("salir", "exit", "quit", "q"):
                self.state.save()
                print(f"\n{C.DIM}El vacío se cierra. Nos vemos en la próxima sesión.{C.RST}\n")
                break
            else:
                print(f"{C.RED}{cmd}: command not found. Type 'help'.{C.RST}")

    def _banner(self):
        print(f"\n{C.CYN}{C.BOLD}")
        print("  ╔══════════════════════════════════════════════════════════╗")
        print("  ║                                                          ║")
        print("  ║   T H E   V O I D   O S   //   v0.2.0-beta              ║")
        print("  ║                                                          ║")
        print("  ║   Ultra-minimalist hacker training terminal              ║")
        print("  ║   Inspired by: The Dark Room, Ruby Koans, PicoCTF,      ║")
        print("  ║   pwn.college, OverTheWire, Phrack Magazine              ║")
        print("  ║                                                          ║")
        print("  ╚══════════════════════════════════════════════════════════╝")
        print(f"{C.RST}\n")

        name = self.state.data.get("hacker_name")
        if name:
            print(f"  {C.DIM}Bienvenido de nuevo, {C.CYN}{name}{C.DIM}.{C.RST}\n")
        else:
            print(f"  {C.DIM}Escribe 'hackername' para generar tu alias digital.{C.RST}\n")

        lvl = self.state.data["current_level"]
        done = len(self.state.data["completed"])
        print(f"  {C.DIM}Nivel actual: {lvl} | Completados: {done}/{len(FLAGS)}{C.RST}")
        self._menu()

    def _menu(self):
        print(f"""
{C.BOLD}{'='*60}
                  T H E   V O I D   O S   //   v0.2.0-beta
{'='*60}{C.RST}

  {C.CYN}[play]         {C.RST}— Iniciar/Continuar la campaña por niveles.
  {C.CYN}[walkthrough]  {C.RST}— Modo guiado interactivo paso a paso.
  {C.CYN}[riddles]      {C.RST}— Acertijos de lógica e historia hacker.
  {C.CYN}[hackername]   {C.RST}— Generar tu alias digital definitivo.
  {C.CYN}[tracks]       {C.RST}— Ver todos los tracks y niveles.
  {C.CYN}[status]       {C.RST}— Tu progreso y puntos.
  {C.CYN}[inventario]   {C.RST}— Flags capturadas.
  {C.CYN}[diary]        {C.RST}— El Diario del Vacío.
  {C.CYN}[guardar]      {C.RST}— Guardar progreso.
  {C.CYN}[salir]        {C.RST}— Salir del sistema.

{C.DIM}  Escribe el nombre de una opción para acceder.{C.RST}
""")

    def _tracks(self):
        print(f"\n{C.BOLD}  TRACKS & LEVELS{C.RST}\n")
        for tid, track in TRACKS.items():
            print(f"  {C.CYN}TRACK {tid}: {track['name']}{C.RST}")
            print(f"  {C.DIM}{track['subtitle']}{C.RST}")
            for lid, lv in track["levels"].items():
                done = lid in self.state.data["completed"]
                unlocked = self.state.is_unlocked(lid)
                if done:
                    s = f"{C.GRN}[DONE]{C.RST}"
                elif unlocked:
                    s = f"{C.YEL}[UNLOCKED]{C.RST}"
                else:
                    s = f"{C.RED}[LOCKED]{C.RST}"
                pts = lv["diff"].count("★") * 100
                print(f"    {lid}  {lv['name']:<30} {lv['diff']}  {s}  +{pts}pts")
            print()

    def _status(self):
        d = self.state.data
        done = len(d["completed"])
        total = len(FLAGS)
        bar_len = int((done / total) * 30) if total else 0
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"\n  {C.BOLD}STATUS{C.RST}")
        print(f"  points:   {d['points']}")
        print(f"  levels:   {done}/{total}")
        print(f"  flags:    {len(d['flags'])}/{total}")
        print(f"  current:  {d['current_level']}")
        print(f"  name:     {d.get('hacker_name', 'none')}")
        print(f"  [{C.GRN}{bar}{C.RST}] {done}/{total}\n")

    def _inventory(self):
        print(f"\n{C.BOLD}  CAPTURED FLAGS{C.RST}\n")
        if not self.state.data["flags"]:
            print(f"  {C.DIM}no flags yet.{C.RST}\n")
            return
        for f in self.state.data["flags"]:
            print(f"  {C.GRN}{f}{C.RST}")
        print()

    def _show_diary(self):
        if os.path.exists(DIARY_FILE):
            with open(DIARY_FILE) as f:
                print(f"\n{C.DIM}{f.read()}{C.RST}\n")
        else:
            print(f"\n  {C.DIM}El diario está vacío. El vacío aún no tiene memoria.{C.RST}\n")

    def _play(self):
        lid = self.state.data["current_level"]
        if lid in self.state.data["completed"]:
            print(f"  {C.DIM}Level {lid} already completed. Use 'select' to replay.{C.RST}")
            return
        if not self.state.is_unlocked(lid):
            print(f"  {C.RED}Level {lid} is locked. Complete previous levels first.{C.RST}")
            return

        ps = self.state.get_puzzle_state(lid)
        level = create_level(lid, self.state, ps)
        if not level:
            print(f"  {C.RED}Level {lid} not found.{C.RST}")
            return

        track = TRACKS[lid.split(".")[0]]
        print(f"\n{C.BOLD}  TRACK {lid.split('.')[0]}: {track['name']}{C.RST}")
        print(f"  {C.DIM}{track['levels'][lid]['name']}{C.RST}\n")

        success = level.run_shell()
        self.state.save_puzzle_state(lid, level.puzzle_state)

        if success or level.is_solved():
            self.state.complete_level(lid)
            write_diary(self.state, "LEVEL COMPLETED",
                f"Captured {FLAGS[lid]} in Track {lid.split('.')[0]}: {track['levels'][lid]['name']}")
            print(f"\n  {C.DIM}Next: {self.state.data['current_level']}{C.RST}\n")
        else:
            write_diary(self.state, "LEVEL ABANDONED", f"Left level {lid} unresolved.")


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        VoidOS().run()
    except KeyboardInterrupt:
        print(f"\n{C.GRN}goodbye.{C.RST}")
        sys.exit(0)
