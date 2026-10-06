#!/usr/bin/env bash
# ==============================================================================
# Launcher Script for Linux: Podcasts with Heart
# Automatically checks and sets up Python virtualenv and starts the application.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  🎙️❤️ Podcasts with Heart (Linux)"
echo "============================================================"

# 1. Python 3 check
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed on this system."
    echo "Install it using: sudo apt install python3 python3-pip python3-venv python3-tk libsndfile1 espeak-ng"
    exit 1
fi

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Detected Python version: $PYTHON_VER"

# 2. Virtual environment (.venv) creation
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv || {
        echo "[ERROR] Could not create virtual environment."
        echo "Please install python3-venv:"
        echo "  sudo apt install python3-venv python3-tk libsndfile1 espeak-ng"
        exit 1
    }
fi

source .venv/bin/activate

# 3. Check system Tkinter
python3 -c "import tkinter" 2>/dev/null || {
    echo "[WARNING] Tkinter is not available in Python."
    echo "On Debian/Ubuntu systems run:"
    echo "  sudo apt update && sudo apt install -y python3-tk libsndfile1 espeak-ng"
    echo "On Fedora:"
    echo "  sudo dnf install python3-tkinter libsndfile espeak-ng"
    echo "On Arch Linux:"
    echo "  sudo pacman -S tk libsndfile espeak-ng"
    exit 1
}

# 4. Install dependencies if needed
if [ ! -f ".venv/.deps_installed" ]; then
    echo "Installing requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .venv/.deps_installed
    echo "[OK] Dependencies installed successfully."
fi

# 5. Launch application
echo "Starting application..."
exec python3 app.py "$@"
