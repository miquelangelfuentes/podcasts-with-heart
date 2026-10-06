import os
import sys
import ctypes

# Ensure project root is in Python sys.path and handle frozen runtime
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    try:
        os.chdir(BASE_DIR)
    except Exception:
        pass
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def enable_windows_dpi_awareness():
    """Enable High DPI awareness on Windows."""
    try:
        if sys.platform.startswith("win"):
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def main():
    enable_windows_dpi_awareness()
    from ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()

