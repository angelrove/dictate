# Dictar - Voz a Texto

Script de dictado por voz para Linux/Wayland. Transcribe voz a texto y lo copia al portapapeles automáticamente.

## Cómo funciona

- **Pulsar atajo una vez**: Inicia el dictado (suena confirmación)
- **Pulsar atajo de nuevo**: Detiene el dictado, copia texto al portapapeles (suena confirmación)
- **Pegar manualmente**: `Ctrl+V` donde quieras el texto

## Instalación

### 1. Dependencias del sistema

```bash
sudo apt install -y wl-clipboard pipewire-audio-client-libraries
```

### 2. Paquetes de Python

```bash
pip3 install sounddevice vosk
```

### 3. Descargar modelo Vosk (español)

```bash
mkdir -p ~/.cache/vosk
cd ~/.cache/vosk
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
rm vosk-model-small-es-0.42.zip
```

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
5. **Comando**: `python3 /home/TU_USUARIO/scripts/dictar.py`
6. Al pulsar "Definir atajo", presionar la tecla **Pause** (o la que prefieras)

## Requisitos

- Linux con Wayland (GNOME, KDE, Sway, etc.)
- Python 3.8+
- Micrófono configurado

## Dependencias

| Paquete | Función |
|---|---|
| `sounddevice` | Captura de audio del micrófono |
| `vosk` | Motor de reconocimiento de voz |
| `wl-clipboard` | Copiar texto al portapapeles de Wayland |
| `pipewire` | Reproducir sonidos de confirmación |

## Modelo

- **vosk-model-small-es-0.42** (39MB) - Español, streaming en tiempo real
- Se descarga automáticamente a `~/.cache/vosk/`

## Personalización

### Cambiar el sonido de confirmación

Editar las líneas con `pw-play` en el script. Sonidos disponibles:

```
/usr/share/sounds/freedesktop/stereo/bell.oga
/usr/share/sounds/freedesktop/stereo/complete.oga
/usr/share/sounds/freedesktop/stereo/camera-shutter.oga
/usr/share/sounds/freedesktop/stereo/message-new-instant.oga
```

### Cambiar el modelo de idioma

Descargar otro modelo de https://alphacephei.com/vosk/models y actualizar la ruta en el script:

```python
model_path = os.path.expanduser("~/.cache/vosk/vosk-model-small-en-us-0.15")
```
