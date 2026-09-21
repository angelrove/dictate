# Dictar - Voz a Texto con OpenAI API

Script de dictado por voz para Linux/Wayland. Graba tu voz mientras mantienes un atajo, envía el audio a la API de **OpenAI (`gpt-transcribe`)** y copia el resultado al portapapeles.

## Características

- **Pulsar atajo una vez**: inicia la grabación (suena confirmación).
- **Pulsar atajo de nuevo**: detiene la grabación y transcribe con IA. Suena un aviso y el texto se pega automáticamente donde tengas el cursor.
- **Aviso de "listo"**: un tono distinto suena justo cuando el texto ya está en el portapapeles, para que sepas cuándo puedes pegar.
- **Pegado automático**: envía `Ctrl+Shift+V` con `ydotool` al terminar (se puede desactivar).
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
| `ydotool` | Pegar automáticamente el texto (opcional, requiere `ydotoold` activo) |

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO> ~/dictar
cd ~/dictar
```

### 2. Ejecutar el script de instalación

```bash
./install.sh
```

Este script:
- Instala las dependencias del sistema (`wl-clipboard`, `pipewire-audio-client-libraries`, `python3`, `python3-pip`).
- Instala las dependencias de Python desde `requirements.txt`.
- Crea un enlace simbólico en `~/scripts/dictar.py`.
- Crea un fichero `.env` vacío para la API key.

> Requiere `sudo` para instalar paquetes del sistema.

### 3. Configurar la API key de OpenAI

Obtén una API key en [platform.openai.com](https://platform.openai.com).

Edita el fichero `.env` creado en el paso anterior:

```bash
nano /ruta/a/dictar/.env
```

Y añade tu clave:

```bash
OPENAI_API_KEY=sk-...
```

> El permiso `600` hace que solo tu usuario pueda leer la API key.

El script lee automáticamente `.env` si la variable de entorno no está definida, así que funciona tanto desde la terminal como desde atajos de teclado del escritorio.

### 4. Configurar atajo de teclado (GNOME)

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
4. Espera 1-2 segundos mientras OpenAI transcribe. Al terminar suena un aviso y el texto se pega solo donde tengas el cursor.
5. Si tienes el pegado automático desactivado, pega el texto con `Ctrl+Shift+V` (terminales) o `Ctrl+V` (apps gráficas).

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

Hay tres momentos con sonido:

- Al iniciar la grabación: `message-new-instant.oga`.
- Al dejar de grabar (mientras transcribe): `bell.oga`.
- Cuando el texto ya está listo: la constante `READY_SOUND` (`complete.oga`).

### Activar o desactivar el pegado automático

El pegado automático usa `ydotool` para enviar `Ctrl+Shift+V` a la ventana con foco. Para desactivarlo, edita `dictar.py`:

```python
AUTO_PASTE = False
```

Otras constantes relacionadas:

```python
PASTE_DELAY = 0.3   # segundos de margen antes de pegar
PASTE_COMMAND = ["ydotool", "key", "29:1", "42:1", "47:1", "47:0", "42:0", "29:0"]  # Ctrl+Shift+V
```

`ydotool` necesita el demonio `ydotoold` en ejecución. Compruébalo con:

```bash
pgrep ydotoold
```

Si no aparece, actívalo como servicio de usuario:

```bash
systemctl --user enable --now ydotoold
```

> `Ctrl+Shift+V` es el pegado habitual en terminales (como la consola de OpenCode). En aplicaciones gráficas normales el pegado suele ser `Ctrl+V`; si dictas sobre todo en ellas, cambia `PASTE_COMMAND` por `["ydotool", "key", "29:1", "47:1", "47:0", "29:0"]`.

## Solución de problemas

### "Error: no se encontró OPENAI_API_KEY"

La variable de entorno no está definida y el script no ha podido leer el fichero `.env`.

Verifica que existe:

```bash
ls -la /ruta/a/dictar/.env
```

Y que contiene la línea:

```bash
OPENAI_API_KEY=sk-...
```

Si está vacía, configúrala siguiendo el paso 3 de instalación.

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

### El texto no se pega automáticamente

Comprueba que `ydotool` está instalado y que el demonio `ydotoold` está activo:

```bash
which ydotool
pgrep ydotoold
```

Si `ydotoold` no está corriendo:

```bash
systemctl --user enable --now ydotoold
```

También verifica el log `dictar.log`; si aparece `Error al pegar automáticamente`, revisa los permisos de `/dev/uinput` (tu usuario debe pertenecer al grupo `input`). Si no consigues que funcione, pon `AUTO_PASTE = False` y pega con `Ctrl+Shift+V` o `Ctrl+V`.

## Log de eventos

El script guarda un log de la última ejecución en la misma carpeta donde esté `dictar.py`:

```
dictar.log
```

Úsalo para depurar problemas:

```bash
cat /ruta/a/dictar/dictar.log
```

El log añade nuevas entradas en cada ejecución (modo append), por lo que conserva el historial de las últimas ejecuciones. No guarda el texto transcrito.

## Nota sobre privacidad

Este script envía el audio grabado a los servidores de OpenAI para su transcripción. No uses esta versión si necesitas que el audio permanezca en tu equipo.

## Licencia

El script `dictar.py` es de uso libre.
