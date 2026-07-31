# The Void OS

Ultra-minimalist, poetic, dark interactive terminal game for training elite hackers through real Linux command simulation.

## Inspirations

- **The Dark Room** — incremental text adventure
- **Ruby Koans** — learn by doing
- **pwn.college** — hands-on security training
- **PicoCTF** — beginner-friendly CTF
- **Hacker 101** — web security fundamentals
- **OverTheWire** — wargames for learning
- **Phrack Magazine** — underground hacker lore

## Quick Start

### CLI Mode (terminal)
```bash
cd ~/void_os
./play.sh

# or directly:
python3 void_os.py
```

### Web Mode (browser)
```bash
cd ~/void_os
./play.sh --web

# Open http://localhost:8080
```
...
Termux
pkg update -y && pkg install python curl -y
curl -sL https://raw.githubusercontent.com/mrivaslezama/thevoid/main/install.sh | bash
source ~/.bashrc
....


Full terminal emulator in your browser with xterm.js, TAB completion, colors, and scrollback.

## Game Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Play** | `play` | Main campaign — 8 levels across 4 tracks |
| **Walkthrough** | `walkthrough` | Guided tutorial, step by step |
| **Riddles** | `riddles` | Logic puzzles about hacker history |
| **Hackername** | `hackername` | Generate your serial alias |

## Tracks & Levels

### Track 1: SENSING THE VOID
Flujos, Archivos y Arqueología Hacker

| Level | Name | Concept | Difficulty |
|-------|------|---------|------------|
| 1.1 | El Despertar del Eco | Redirección `>` `>>` | ★☆☆ |
| 1.2 | Los Archivos Fantasma | Archivos ocultos `find -size` | ★★☆ |
| 1.3 | El Archivo de los Sabios | Pipelines `strings`, `decode` | ★★★ |

### Track 2: ALTERING REALITY
Variables, Rutas y Entornos

| Level | Name | Concept | Difficulty |
|-------|------|---------|------------|
| 2.1 | El Sendero Perdido | PATH Hijacking | ★★☆ |
| 2.2 | Las Máscaras del Entorno | Variables `env`, `export` | ★★☆ |

### Track 3: PRIVILEGE ESCALATION
El Mito de Prometeo / Acceso Root

| Level | Name | Concept | Difficulty |
|-------|------|---------|------------|
| 3.1 | El Espejo del Rey | SUID `chmod u+s` | ★★★ |
| 3.2 | La Cronología del Caos | Cronjob injection | ★★★ |

### Track 4: MEMORY REVERSING
El Inframundo del Silicio

| Level | Name | Concept | Difficulty |
|-------|------|---------|------------|
| 4.1 | El Desborde del Alma | Buffer Overflow | ★★★★ |

## Shell Commands

### Navigation
```
ls [-la] [path]       List directory
cd <path>             Change directory
pwd                   Print working dir
find [-name x]        Search files
```

### File Operations
```
cat <file>            Read file
echo <text>           Print text
echo X > file         Write to file
echo X >> file        Append to file
touch <name>          Create empty file
mkdir <name>          Create directory
chmod <perm> <file>   Change permissions
```

### Analysis
```
file <file>           Identify file type
stat <file>           File metadata
wc <file>             Word/line count
strings <file>        Extract printable strings
grep <pattern>        Search contents
```

### Crypto
```
decode <text> <type>  Decode (base64/hex/rot13)
encode <text> <type>  Encode (base64/hex/rot13)
caesar <text> <shift> Caesar cipher
bruteforce <text>     Try all 26 shifts
hash <text> [algo]    Hash (md5/sha1/sha256)
```

### System
```
env                   Show environment
export VAR=val        Set variable
whoami / id           User info
man <command>         Manual page
hint                  Get level hint
submit FLAG{...}      Submit flag
```

## Flags

Each level has a unique flag in the format `FLAG{descriptive_text}`. Capture all 8 to complete the game.

## Files

```
void_os/
├── void_os.py      Main game engine
├── play.sh         Launcher script
├── README.md       This file
├── man/
│   └── walkthrough.md   Full walkthrough guide
├── .void_state.json     Save file (auto-created)
├── .void_history        Command history (auto-created)
└── .void_diary.md       Game diary (auto-created)
```

## Requirements

- Python 3.6+
- Terminal with ANSI color support
- Readline (for TAB completion)

## License

MIT
# thevoid
