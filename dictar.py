#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import time
import wave
import sounddevice as sd

# Tu ruta de librerías (Python 3.14)
sys.path.append(os.path.expanduser("~/.local/lib/python3.14/site-packages"))

PID_FILE = "/tmp/dictar.pid"
WAV_FILE = "/tmp/dictar.wav"
TRANSCRIBE_TIMEOUT = 30  # segundos máximos para transcribir

WHISPER_DIR = os.path.expanduser("~/.local/src/whisper.cpp")
WHISPER_BIN = os.path.join(WHISPER_DIR, "build", "bin", "whisper-cli")
MODEL_PATH = os.path.join(WHISPER_DIR, "models", "ggml-large-v3-turbo.bin")

# Vocabulario técnico para sesgar el modelo hacia palabras informáticas frecuentes
PROMPT = (
    "Git, npm, bun, yarn, pnpm, Node.js, Python, JavaScript, TypeScript, "
    "React, Vue, Angular, Svelte, Next.js, Nuxt, Astro, Tailwind, Docker, "
    "Kubernetes, kubectl, Podman, Linux, Ubuntu, Debian, Arch, Fedora, "
    "VS Code, Neovim, Vim, Emacs, terminal, shell, bash, zsh, fish, "
    "API, REST, GraphQL, SQL, Postgres, MySQL, MongoDB, Redis, SQLite, "
    "JSON, YAML, XML, CSV, HTML, CSS, SCSS, Sass, Less, "
    "async, await, Promise, callback, function, class, const, let, var, "
    "import, export, module, package, dependency, repository, commit, "
    "push, pull, merge, branch, tag, release, deploy, pipeline, CI/CD, "
    "GitHub, GitLab, Bitbucket, Pull Request, issue, bug, fix, refactor."
)

# Configuración
LANGUAGE = "es"
THREADS = os.cpu_count() or 4

# Procesos globales para poder limpiarlos al salir
stream = None
wav_file = None
whisper_proc = None


def play_sound(path):
    subprocess.run(
        ["pw-play", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def transcribe_audio():
    """Transcribe el WAV con whisper.cpp y devuelve el texto limpio."""
    if not os.path.exists(WAV_FILE) or os.path.getsize(WAV_FILE) < 1024:
        return ""

    cmd = [
        WHISPER_BIN,
        "-m", MODEL_PATH,
        "-f", WAV_FILE,
        "-l", LANGUAGE,
        "-t", str(THREADS),
        "--prompt", PROMPT,
        "-nt",      # no timestamps
        "-np",      # no prints extra
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        text = result.stdout.strip()
        # whisper-cli puede devolver líneas en blanco o metadata; nos quedamos con el texto
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("read_audio_data:")
        ]
        if lines:
            return " ".join(lines)
        return ""
    except Exception as e:
        print(f"Error transcribiendo: {e}", file=sys.stderr)
        return ""


def save_and_exit(signum, frame):
    global stream, wav_file

    # Sonido de confirmación al terminar
    play_sound("/usr/share/sounds/freedesktop/stereo/bell.oga")

    # Detener grabación y cerrar WAV
    try:
        if stream is not None:
            stream.stop()
            stream.close()
        if wav_file is not None:
            wav_file.close()
    except Exception:
        pass

    texto = transcribe_audio()

    if texto:
        # Copiamos al portapapeles de Wayland
        subprocess.run(
            ["wl-copy", texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    # Limpieza antes de salir
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    if os.path.exists(WAV_FILE):
        os.remove(WAV_FILE)

    os._exit(0)


# Lógica de detección de doble pulsación
if os.path.exists(PID_FILE):
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        os.kill(pid, signal.SIGUSR1)
        sys.exit(0)
    except (ProcessLookupError, ValueError):
        pass

# Guardar el PID del proceso actual
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

# Registrar la señal de apagado
signal.signal(signal.SIGUSR1, save_and_exit)

stream = None
wav_file = None

try:
    device_info = sd.query_devices(None, "input")
    samplerate = int(device_info["default_samplerate"])

    # Preparar archivo WAV
    wav_file = wave.open(WAV_FILE, "wb")
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)  # 16 bits
    wav_file.setframerate(samplerate)

    def callback(indata, frames, time_info, status):
        wav_file.writeframes(bytes(indata))

    with sd.RawInputStream(
        samplerate=samplerate,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=callback,
    ) as stream:
        # Sonido de confirmación cuando el micrófono está listo
        play_sound("/usr/share/sounds/freedesktop/stereo/message-new-instant.oga")

        # Mantener el proceso vivo hasta que llegue SIGUSR1
        # Usamos un bucle en lugar de signal.pause() para evitar problemas con
        # los threads internos de sounddevice/PortAudio.
        while True:
            time.sleep(0.1)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    if wav_file is not None:
        try:
            wav_file.close()
        except Exception:
            pass
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    if os.path.exists(WAV_FILE):
        os.remove(WAV_FILE)
    sys.exit(1)
