#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DICTAR_PY="${SCRIPT_DIR}/dictar.py"
TARGET_DIR="${HOME}/scripts"
TARGET_LINK="${TARGET_DIR}/dictar.py"
ENV_FILE="${SCRIPT_DIR}/.env"

# Comprobar que estamos en Ubuntu
if ! grep -qE '^ID(_LIKE)?=.*(ubuntu|debian)' /etc/os-release 2>/dev/null; then
    echo "Este script está pensado para Ubuntu/Debian."
    echo "Abortando."
    exit 1
fi

echo "==> Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y \
    wl-clipboard \
    pipewire-audio-client-libraries \
    python3 \
    python3-pip

echo "==> Instalando dependencias de Python..."
pip3 install --user --break-system-packages -r "${SCRIPT_DIR}/requirements.txt"

echo "==> Configurando enlace simbólico en ${TARGET_DIR}..."
mkdir -p "${TARGET_DIR}"
if [[ -L "${TARGET_LINK}" ]]; then
    rm "${TARGET_LINK}"
fi
ln -s "${DICTAR_PY}" "${TARGET_LINK}"
chmod +x "${DICTAR_PY}"

echo "==> Configurando fichero .env..."
if [[ -f "${ENV_FILE}" ]]; then
    echo "    ${ENV_FILE} ya existe, no se modifica."
else
    cat > "${ENV_FILE}" <<EOF
OPENAI_API_KEY=
EOF
    chmod 600 "${ENV_FILE}"
    echo "    Creado ${ENV_FILE}"
fi

echo ""
echo "=========================================="
echo "Instalación completada."
echo ""
echo "Pasos pendientes:"
echo "  1. Edita el archivo .env:"
echo "     ${ENV_FILE}"
echo "     y añade tu OPENAI_API_KEY."
echo ""
echo "  2. Configura el atajo de teclado en:"
echo "     Configuración → Teclado → Atajos personalizados"
echo "     Nombre: Dictar"
echo "     Comando: python3 ${TARGET_LINK}"
echo "=========================================="
