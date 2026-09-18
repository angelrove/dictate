# Dictar - Voz a Texto con Whisper

Script de dictado por voz para Linux/Wayland. Graba tu voz mientras mantienes un atajo, transcribe el audio con **OpenAI Whisper** ejecutándose localmente y copia el resultado al portapapeles.

## Características

- **Pulsar atajo una vez**: inicia la grabación (suena confirmación).
- **Pulsar atajo de nuevo**: detiene la grabación, transcribe con IA y copia el texto al portapapeles (suena confirmación).
- **Pegar manualmente**: `Ctrl+V` donde quieras el texto.
- **Puntuación automática**: Whisper añade comas, puntos, interrogaciones y mayúsculas sin reglas manuales.
- **Multilingüe**: entiende español mezclado con palabras sueltas en inglés.
- **Vocabulario técnico**: incluye un *prompt* con términos informáticos (Git, npm, bun, Docker, Kubernetes, etc.) para mejorar el reconocimiento.
- **Todo local**: no se envía nada a la nube.

## Requisitos

- Linux con Wayland (GNOME, KDE, Sway, etc.)
- Python 3.8+
- Micrófono configurado
- ~2.5 GB de RAM libres para el modelo `large-v3-turbo`
- ~1.6 GB de espacio en disco para el modelo descargado

## Dependencias

| Paquete | Función |
|---|---|
| `sounddevice` | Captura de audio del micrófono |
| `wl-clipboard` | Copiar texto al portapapeles de Wayland |
| `pipewire` | Reproducir sonidos de confirmación |
| `build-essential`, `cmake`, `git` | Compilar whisper.cpp |

## Instalación

### 1. Dependencias del sistema

```bash
sudo apt install -y build-essential cmake git wl-clipboard pipewire-audio-client-libraries
```

> Si no puedes usar `sudo`, instala `cmake` con `pip3 install --user --break-system-packages cmake` y asegúrate de que `~/.local/bin` esté en tu `PATH`.

### 2. Paquetes de Python

```bash
pip3 install sounddevice
```

### 3. Compilar whisper.cpp y descargar el modelo

```bash
mkdir -p ~/.local/src
git clone https://github.com/ggerganov/whisper.cpp.git ~/.local/src/whisper.cpp
cd ~/.local/src/whisper.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j --config Release
bash models/download-ggml-model.sh large-v3-turbo
```

Esto descarga el modelo `ggml-large-v3-turbo.bin` (~1.6 GB), un buen equilibrio entre precisión y velocidad en CPU.

### 4. Colocar el script

```bash
mkdir -p ~/scripts
cp dictar.py ~/scripts/dictar.py
chmod +x ~/scripts/dictar.py
```

### 5. Configurar atajo de teclado (GNOME)

1. Ir a **Configuración → Teclado → Atajos de teclado**
2. Bajar a **Atajos personalizados**
3. Pulsar **+** para añadir uno nuevo
4. **Nombre**: `Dictar`
5. **Comando**: `python3 /home/TU_USUARIO/dictate/dictar.py`
6. Al pulsar "Definir atajo", presionar la tecla **Pause** (o la que prefieras)

## Uso

1. Pulsa el atajo configurado.
2. Habla con naturalidad. Puedes mezclar español con palabras en inglés.
3. Vuelve a pulsar el atajo.
4. Espera un segundo mientras Whisper transcribe.
5. Pega el texto con `Ctrl+V`.

## Personalización

### Cambiar el modelo

Edita la variable `MODEL_PATH` en `dictar.py` o descarga otro modelo:

```bash
cd ~/.local/src/whisper.cpp
bash models/download-ggml-model.sh medium
```

Modelos recomendados:

| Modelo | Precisión | Velocidad en CPU | RAM aprox. |
|---|---|---|---|
| `small` | Buena | Rápida | ~1 GB |
| `medium` | Muy buena | Media | ~2.1 GB |
| `large-v3-turbo` | Excelente | Rápida | ~2.3 GB |
| `large-v3` | Máxima | Lenta | ~3.9 GB |

### Cambiar el idioma

Edita la variable `LANGUAGE` en `dictar.py`. Algunos valores útiles:

- `"es"` — español (predeterminado)
- `"en"` — inglés
- `"auto"` — detección automática (añade algo de latencia)

### Añadir vocabulario propio

Edita la variable `PROMPT` en `dictar.py` con palabras o frases que uses habitualmente. Esto ayuda a Whisper a reconocer nombres propios, tecnologías o jerga de tu campo.

```python
PROMPT = (
    "Git, npm, bun, Docker, Kubernetes, "
    "aquí tus propias palabras."
)
```

### Cambiar el sonido de confirmación

Edita las llamadas a `play_sound(...)` en `dictar.py`. Algunos sonidos disponibles:

```
/usr/share/sounds/freedesktop/stereo/bell.oga
/usr/share/sounds/freedesktop/stereo/complete.oga
/usr/share/sounds/freedesktop/stereo/camera-shutter.oga
/usr/share/sounds/freedesktop/stereo/message-new-instant.oga
```

## Solución de problemas

### whisper-cli no se encuentra

Asegúrate de que whisper.cpp se compiló correctamente:

```bash
ls ~/.local/src/whisper.cpp/build/bin/whisper-cli
```

### El modelo no se encuentra

```bash
ls ~/.local/src/whisper.cpp/models/ggml-large-v3-turbo.bin
```

### La transcripción tarda mucho

- Prueba un modelo más pequeño (`medium` o `small`).
- Asegúrate de que whisper.cpp se compiló con soporte OpenMP/AVX (debería hacerlo por defecto en x86_64).

### No se copia al portapapeles

Verifica que `wl-copy` está instalado:

```bash
which wl-copy
```

## Licencia

El script `dictar.py` es de uso libre. whisper.cpp y los modelos Whisper tienen sus propias licencias (MIT y CC BY-SA 4.0 respectivamente).
