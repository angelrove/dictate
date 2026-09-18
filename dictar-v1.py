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
    global whisper_proc

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
        whisper_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = whisper_proc.communicate(timeout=TRANSCRIBE_TIMEOUT)
        text = stdout.strip()
        # whisper-cli puede devolver líneas en blanco o metadata; nos quedamos con el texto
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("read_audio_data:")
        ]
        if lines:
            return " ".join(lines)
        return ""
    except subprocess.TimeoutExpired:
        print(f"[dictar] La transcripción tardó más de {TRANSCRIBE_TIMEOUT}s. Cancelando.", file=sys.stderr)
        if whisper_proc is not None:
            whisper_proc.kill()
            try:
                whisper_proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        return ""
    except Exception as e:
        print(f"[dictar] Error transcribiendo: {e}", file=sys.stderr)
        if whisper_proc is not None:
            try:
                whisper_proc.kill()
            except Exception:
                pass
        return ""
    finally:
        whisper_proc = None


def cleanup(kill_whisper=True):
    """Limpia recursos, archivos temporales y procesos hijos."""
    global stream, wav_file, whisper_proc

    # Detener grabación y cerrar WAV
    try:
        if stream is not None:
            stream.stop()
            stream.close()
    except Exception:
        pass
    try:
        if wav_file is not None:
            wav_file.close()
    except Exception:
        pass

    # Matar whisper-cli si aún está corriendo
    if kill_whisper and whisper_proc is not None:
        try:
            if whisper_proc.poll() is None:
                whisper_proc.kill()
                whisper_proc.communicate(timeout=5)
        except Exception:
            pass

    # Eliminar archivos temporales
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
    if os.path.exists(WAV_FILE):
        try:
            os.remove(WAV_FILE)
        except Exception:
            pass


def save_and_exit(signum, frame):
    # Ignorar señales adicionales mientras terminamos para evitar reentrada
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)

    # Sonido de confirmación al terminar
    play_sound("/usr/share/sounds/freedesktop/stereo/bell.oga")

    texto = transcribe_audio()

    if texto:
        # Copiamos al portapapeles de Wayland
        subprocess.run(
            ["wl-copy", texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

    cleanup(kill_whisper=True)
    os._exit(0)


def signal_handler(signum, frame):
    """Maneja SIGTERM/SIGINT limpiando antes de salir."""
    cleanup(kill_whisper=True)
    os._exit(0)


def kill_orphan_whisper_processes():
    """Mata procesos whisper-cli huérfanos de ejecuciones anteriores."""
    subprocess.run(
        ["pkill", "-f", f"{WHISPER_BIN}.*{WAV_FILE}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


# Lógica de detección de doble pulsación
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        if pid != os.getpid():
            try:
                os.kill(pid, signal.SIGUSR1)
                sys.exit(0)
            except ProcessLookupError:
                # El proceso ya no existe; limpiar archivo obsoleto
                os.remove(PID_FILE)
            except ValueError:
                os.remove(PID_FILE)
    except (ValueError, OSError):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

# Matar whisper-cli huérfanos y guardar el PID del proceso actual
kill_orphan_whisper_processes()
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

# Registrar señales
signal.signal(signal.SIGUSR1, save_and_exit)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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
    cleanup(kill_whisper=True)
    sys.exit(1)
