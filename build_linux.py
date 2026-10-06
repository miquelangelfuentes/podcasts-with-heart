"""
Automated PyInstaller Build Script for Linux (Standalone package / tar.gz).
Creates a standalone, autonomous distribution of 'Podcasts with Heart' for Linux distributions
(Ubuntu, Debian, Fedora, Arch, Linux Mint, etc.).
"""

import os
import sys
import shutil
import subprocess
import tarfile
import time

APP_VERSION = "1.0.0"


def build_linux():
    print("=" * 60)
    print(f"  Starting build for 'Podcasts with Heart' v{APP_VERSION} (Linux)")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")

    target_dist = os.path.join(dist_dir, "PodcastsWithHeart-Linux")
    if os.path.exists(target_dist):
        shutil.rmtree(target_dist, ignore_errors=True)

    # In Linux, PyInstaller add-data path separator is ':' rather than ';'
    sep = ":" if sys.platform != "win32" else ";"

    # Locate piper espeak-ng-data if present
    piper_data_arg = []
    try:
        import piper
        piper_data_dir = os.path.join(os.path.dirname(piper.__file__), "espeak-ng-data")
        if os.path.exists(piper_data_dir):
            piper_data_arg = [f"--add-data={piper_data_dir}{sep}piper/espeak-ng-data"]
    except Exception:
        pass

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=PodcastsWithHeart",
        "--noconsole",
        "--onedir",
        "--clean",
        "-y",
        f"--distpath={dist_dir}",
        f"--add-data={os.path.join(base_dir, 'assets')}{sep}assets",
        f"--add-data={os.path.join(base_dir, 'docs')}{sep}docs",
        f"--add-data={os.path.join(base_dir, 'examples')}{sep}examples",
        f"--add-data={os.path.join(base_dir, 'models')}{sep}models",
        *piper_data_arg,
        "--collect-all=customtkinter",
        "--collect-all=imageio_ffmpeg",
        "--collect-all=soundfile",
        "--collect-all=edge_tts",
        "--collect-all=piper",
        "--collect-all=kokoro_onnx",
        "--collect-all=espeakng_loader",
        "--collect-all=phonemizer",
        "--collect-all=pathvalidate",
        "--exclude-module=piper.train",
        "--exclude-module=torch",
        "--hidden-import=kokoro_onnx",
        "--hidden-import=espeakng_loader",
        "--hidden-import=phonemizer",
        "--hidden-import=piper",
        "--hidden-import=piper.voice",
        "--hidden-import=scipy.signal",
        "--hidden-import=scipy.special",
        "--hidden-import=pygame",
        "--hidden-import=onnxruntime",
        "--hidden-import=yaml",
        "--hidden-import=requests",
        "--hidden-import=aiohttp",
        "--hidden-import=aiohappyeyeballs",
        "--hidden-import=uuid",
        "--hidden-import=asyncio",
        "--hidden-import=edge_tts",
        os.path.join(base_dir, "app.py")
    ]

    print("Running PyInstaller for Linux...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode == 0:
        built_dir = os.path.join(dist_dir, "PodcastsWithHeart")
        tar_name = f"PodcastsWithHeart-v{APP_VERSION}-Linux-x86_64.tar.gz"
        tar_path = os.path.join(dist_dir, tar_name)

        print(f"\nCompressing to standalone tar.gz archive: {tar_name}...")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(built_dir, arcname="PodcastsWithHeart")

        tar_mb = os.path.getsize(tar_path) / (1024 * 1024)
        print("\n" + "=" * 60)
        print("  [OK] Linux build COMPLETED SUCCESSFULLY!")
        print(f"  Archive created at: {tar_path} ({tar_mb:.1f} MB)")
        print("=" * 60)
    else:
        print("\n[ERROR] Linux build failed.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build_linux()
