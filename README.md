# Dictar - Voz a Texto con OpenAI API

Script de dictado por voz para Linux/Wayland. Graba tu voz mientras mantienes un atajo, envía el audio a la API de **OpenAI (`gpt-transcribe`)** y copia el resultado al portapapeles.

## Características

- **Pulsar atajo una vez**: inicia la grabación (suena confirmación).
- **Pulsar atajo de nuevo**: detiene la grabación, transcribe con IA y copia el texto al portapapeles (suena confirmación).
- **Pegar manualmente**: `Ctrl+V` donde quieras el texto.
- **Puntuación automática**: el modelo añade comas, puntos, interrogaciones y mayúsculas.
- **Multilingüe**: entiende español mezclado con palabras sueltas en inglés.
- **Rápido**: la transcripción corre en los servidores de OpenAI, no en tu CPU.

## Requisitos

- Linux con Wayland (GNOME, KDE, Sway, etc.)
- Python 3.8+
- Micrófono configurado
- Conexión a internet
- Una **API key de OpenAI** con crédito disponible

## Dependencias

| Paquete | Función |
|---|---|
| `sounddevice` | Captura de audio del micrófono |
| `openai` | Cliente de la API de OpenAI |
| `wl-clipboard` | Copiar texto al portapapeles de Wayland |
| `pipewire` | Reproducir sonidos de confirmación |

## Instalación

### 1. Dependencias del sistema

```bash
sudo apt install -y wl-clipboard pipewire-audio-client-libraries
```

### 2. Paquetes de Python

```bash
pip3 install --user --break-system-packages openai sounddevice
```

### 3. Configurar la API key de OpenAI

Obtén una API key en [platform.openai.com](https://platform.openai.com).

Añade esto a tu `~/.bashrc` o `~/.zshrc`:

```bash
export OPENAI_API_KEY="sk-..."
```

Recarga la configuración:

```bash
source ~/.bashrc
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

## Uso

1. Pulsa el atajo configurado.
2. Habla con naturalidad. Puedes mezclar español con palabras en inglés.
3. Vuelve a pulsar el atajo.
4. Espera 1-2 segundos mientras OpenAI transcribe.
5. Pega el texto con `Ctrl+V`.

## Coste

El script usa el modelo **`gpt-transcribe`**, que cuesta aproximadamente **$0.0045 por minuto de audio**.

| Uso estimado | Coste mensual aproximado |
|---|---|
| 20 segundos × 50 dictados/día × 20 días | ~$1.5 |
| 1 hora de dictado | ~$0.27 |

Consulta la [página de precios de OpenAI](https://openai.com/api/pricing/) para tarifas actualizadas.

## Personalización

### Cambiar el prompt de contexto

Edita la variable `PROMPT` en `dictar.py` para darle contexto al modelo:

```python
PROMPT = "Dictado informal de un desarrollador de software."
```

### Cambiar el idioma

Edita la variable `LANGUAGES` en `dictar.py`:

```python
LANGUAGES = ["es", "en"]  # español e inglés
```

Otros ejemplos:

- `["es"]` — solo español
- `["en"]` — solo inglés
- `["es", "en", "fr"]` — español, inglés y francés

### Cambiar el sonido de confirmación

Edita las llamadas a `play_sound(...)` en `dictar.py`. Algunos sonidos disponibles:

```
/usr/share/sounds/freedesktop/stereo/bell.oga
/usr/share/sounds/freedesktop/stereo/complete.oga
/usr/share/sounds/freedesktop/stereo/camera-shutter.oga
/usr/share/sounds/freedesktop/stereo/message-new-instant.oga
```

## Solución de problemas

### "Error: no se encontró OPENAI_API_KEY"

La variable de entorno no está definida. Verifica:

```bash
echo $OPENAI_API_KEY
```

Si está vacía, añádela a tu `~/.bashrc` y recarga.

### "Error de autenticación con OpenAI"

Tu API key es inválida o ha sido revocada. Genera una nueva en [platform.openai.com](https://platform.openai.com).

### "No se pudo conectar con OpenAI"

Comprueba tu conexión a internet. El script requiere acceso a `api.openai.com`.

### "You have no credits remaining"

Tu API key es válida pero la cuenta no tiene crédito. Añade crédito en [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing).

### No se copia al portapapeles

Verifica que `wl-copy` está instalado:

```bash
which wl-copy
```

## Log de eventos

El script guarda un log de la última ejecución en la misma carpeta donde esté `dictar.py`:

```
dictar.log
```

Úsalo para depurar problemas:

```bash
cat /ruta/a/dictar/dictar.log
```

El log se reinicia en cada ejecución, por lo que solo contiene información de la última vez que usaste el dictado. No guarda el texto transcrito.

## Nota sobre privacidad

Este script envía el audio grabado a los servidores de OpenAI para su transcripción. No uses esta versión si necesitas que el audio permanezca en tu equipo.

## Licencia

El script `dictar.py` es de uso libre.
