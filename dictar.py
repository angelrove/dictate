#!/usr/bin/env python3
import os
import sys
import signal
import subprocess
import time
import wave
import datetime
from io import BytesIO
import sounddevice as sd

# Tu ruta de librerías (Python 3.14)
sys.path.append(os.path.expanduser("~/.local/lib/python3.14/site-packages"))

from openai import OpenAI, AuthenticationError, APIConnectionError, APIError

PID_FILE = "/tmp/dictar.pid"
WAV_FILE = "/tmp/dictar.wav"
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "dictar.log")

_log_file = None


def _init_log():
    """Abre el archivo de log en modo escritura (reinicia en cada ejecución)."""
    global _log_file
    os.makedirs(LOG_DIR, exist_ok=True)
    _log_file = open(LOG_FILE, "w", encoding="utf-8")


def log(level, message, *args):
    """Escribe una línea en el log."""
    if _log_file is None:
        _init_log()
    if args:
        message = message % args
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _log_file.write(f"{timestamp} - {level} - {message}\n")
    _log_file.flush()


def log_info(message, *args):
    log("INFO", message, *args)


def log_warning(message, *args):
    log("WARNING", message, *args)


def log_error(message, *args):
    log("ERROR", message, *args)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = "gpt-transcribe"
PROMPT = "Dictado informal de un desarrollador de software."
LANGUAGES = ["es", "en"]
API_TIMEOUT = 30  # segundos máximo esperando respuesta de OpenAI

# Procesos globales para poder limpiarlos al salir
stream = None
wav_file = None
recording_start_time = None


def play_sound(path):
    subprocess.run(
        ["pw-play", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def transcribe_audio():
    """Envía el WAV a la API de OpenAI y devuelve el texto transcrito."""
    if not os.path.exists(WAV_FILE) or os.path.getsize(WAV_FILE) < 1024:
        log_warning("Archivo WAV no encontrado o demasiado pequeño")
        return ""

    if not OPENAI_API_KEY:
        msg = "No se encontró OPENAI_API_KEY. Exporta la variable de entorno antes de ejecutar el script."
        log_error(msg)
        print(f"[dictar] Error: {msg}", file=sys.stderr)
        return ""

    client = OpenAI(api_key=OPENAI_API_KEY)
    log_info("Enviando audio a OpenAI (modelo: %s, tamaño: %d bytes)", MODEL, os.path.getsize(WAV_FILE))

    try:
        # Leemos el archivo en memoria para evitar el error "Too much data for declared Content-Length"
        with open(WAV_FILE, "rb") as f:
            audio_bytes = BytesIO(f.read())
        transcription = client.audio.transcriptions.create(
            model=MODEL,
            file=("audio.wav", audio_bytes),
            prompt=PROMPT,
            languages=LANGUAGES,
            timeout=API_TIMEOUT,
        )
        log_info("Transcripción recibida correctamente")
        return transcription.text.strip()
    except AuthenticationError as e:
        log_error("Error de autenticación con OpenAI: %s", e)
        print(f"[dictar] Error de autenticación con OpenAI: {e}", file=sys.stderr)
    except APIConnectionError as e:
        log_error("No se pudo conectar con OpenAI: %s", e)
        print(f"[dictar] No se pudo conectar con OpenAI: {e}", file=sys.stderr)
    except APIError as e:
        log_error("Error de la API de OpenAI: %s", e)
        print(f"[dictar] Error de la API de OpenAI: {e}", file=sys.stderr)
    except Exception as e:
        log_error("Error inesperado transcribiendo: %s", e)
        print(f"[dictar] Error inesperado transcribiendo: {e}", file=sys.stderr)

    return ""


def cleanup():
    """Limpia recursos y archivos temporales."""
    global stream, wav_file

    try:
        if stream is not None:
            stream.stop()
            stream.close()
    except Exception as e:
        log_warning("Error deteniendo la grabación: %s", e)
    try:
        if wav_file is not None:
            wav_file.close()
    except Exception as e:
        log_warning("Error cerrando el archivo WAV: %s", e)

    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
            log_info("PID file eliminado")
        except Exception as e:
            log_warning("Error eliminando PID file: %s", e)
    if os.path.exists(WAV_FILE):
        try:
            os.remove(WAV_FILE)
            log_info("WAV file eliminado")
        except Exception as e:
            log_warning("Error eliminando WAV file: %s", e)

    try:
        if _log_file is not None:
            _log_file.close()
    except Exception:
        pass


def save_and_exit(signum, frame):
    # Ignorar señales adicionales mientras terminamos para evitar reentrada
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)

    if recording_start_time is not None:
        duration = time.time() - recording_start_time
        log_info("Grabación finalizada (duración: %.1fs)", duration)

    # Sonido de confirmación al terminar
    play_sound("/usr/share/sounds/freedesktop/stereo/bell.oga")

    texto = transcribe_audio()

    if texto:
        subprocess.run(
            ["wl-copy", texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        log_info("Texto copiado al portapapeles")
    else:
        log_info("No se copió nada al portapapeles (texto vacío)")

    cleanup()
    log_info("Proceso finalizado correctamente")
    os._exit(0)


def signal_handler(signum, frame):
    """Maneja SIGTERM/SIGINT limpiando antes de salir."""
    log_warning("Señal %s recibida. Limpiando y saliendo.", signum)
    cleanup()
    os._exit(0)


# Lógica de detección de doble pulsación
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        if pid != os.getpid():
            try:
                log_info("Segunda pulsación detectada, enviando señal al proceso %d", pid)
                os.kill(pid, signal.SIGUSR1)
                sys.exit(0)
            except ProcessLookupError:
                log_warning("PID file apunta a un proceso inexistente, limpiando")
                os.remove(PID_FILE)
            except ValueError:
                os.remove(PID_FILE)
    except (ValueError, OSError):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass

# Guardar el PID del proceso actual
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))
log_info("Proceso iniciado con PID %d", os.getpid())

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
        recording_start_time = time.time()
        log_info("Grabación iniciada (dispositivo: %s, samplerate: %d)",
                     device_info.get("name", "desconocido"), samplerate)

        # Sonido de confirmación cuando el micrófono está listo
        play_sound("/usr/share/sounds/freedesktop/stereo/message-new-instant.oga")

        # Mantener el proceso vivo hasta que llegue SIGUSR1
        while True:
            time.sleep(0.1)

except Exception as e:
    log_error("Error durante la grabación: %s", e)
    print(f"Error: {e}", file=sys.stderr)
    cleanup()
    sys.exit(1)
