#!/usr/bin/env python3
import os
import sys
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import signal
import time

# Tu ruta de librerías (Python 3.14)
sys.path.append(os.path.expanduser("~/.local/lib/python3.14/site-packages"))

PID_FILE = "/tmp/dictar.pid"

QUESTION_WORDS = ["qué", "como", "cuándo", "dónde", "quién", "cuál", "cuánto", "cuántos", "cuántas", "es que", "puede", "puedes", "podría", "quieres", "sabe", "sabes", "hay", "tiene", "tienes"]

def add_question_marks(text):
    sentences = text.split(". ")
    result = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        first_words = s.lower().split()[:3]
        is_question = any(s.startswith(w) for w in QUESTION_WORDS) or any(w in first_words for w in QUESTION_WORDS)
        if is_question and not s.endswith("?"):
            s = "¿" + s[0].upper() + s[1:] + "?"
        elif not s.endswith("."):
            s = s[0].upper() + s[1:] + "."
        result.append(s)
    return ". ".join(result)

def replace_punctuation_words(text):
    text = text.replace(" coma ", ", ")
    text = text.replace(" dos puntos ", ": ")
    return text

def save_and_exit(signum, frame):
    # Sonido de confirmación al terminar
    os.system("pw-play /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null")

    global rec
    result = json.loads(rec.FinalResult())
    texto = result.get("text", "").strip()

    if texto:
        # Reemplazar palabras de puntuación por símbolos
        texto = replace_punctuation_words(texto)
        # Procesar puntuación básica (signos de interrogación y puntos)
        texto = add_question_marks(texto)
        # Copiamos al portapapeles de Wayland
        os.system(f"wl-copy '{texto}'")

    # Limpieza antes de salir
    if os.path.exists(PID_FILE): os.remove(PID_FILE)
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

# Cargar el modelo de Vosk
model_path = os.path.expanduser("~/.cache/vosk/vosk-model-small-es-0.42")
model = Model(model_path)
q = queue.Queue()

def callback(indata, frames, time, status):
    q.put(bytes(indata))

# Registrar la señal de apagado
signal.signal(signal.SIGUSR1, save_and_exit)

try:
    device_info = sd.query_devices(None, "input")
    samplerate = int(device_info["default_samplerate"])
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000,
                            dtype="int16", channels=1, callback=callback):
        # Sonido de confirmación cuando el micrófono está listo
        os.system("pw-play /usr/share/sounds/freedesktop/stereo/message-new-instant.oga 2>/dev/null")
        rec = KaldiRecognizer(model, samplerate)
        while True:
            data = q.get()
            rec.AcceptWaveform(data)
except Exception:
    if os.path.exists(PID_FILE): os.remove(PID_FILE)
    sys.exit(1)