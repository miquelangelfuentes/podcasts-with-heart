"""
Automated PyInstaller Build Script to Windows Executable (.exe).
Creates a standalone, autonomous distribution of 'Podcasts with Heart'.
"""

import os
import sys
import shutil
import subprocess
import time
import zipfile

APP_VERSION = "1.0.0"

def build():
    print("=" * 60)
    print("  Starting build for 'Podcasts with Heart' (.exe)")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")
    icon_path = os.path.join(base_dir, "assets", "icon.ico")

    # Terminate any previously running instances on Windows
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "PodcastsWithHeart.exe"], capture_output=True)
        except Exception:
            pass
        time.sleep(1)

    # Clean target dist folder
    target_dist = os.path.join(dist_dir, "PodcastsWithHeart")
    if os.path.exists(target_dist):
        for _ in range(5):
            try:
                shutil.rmtree(target_dist, ignore_errors=True)
                if not os.path.exists(target_dist):
                    break
            except Exception:
                pass
            time.sleep(1)

    staging_dist = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "pwh_stg")
    if os.path.exists(staging_dist):
        shutil.rmtree(staging_dist, ignore_errors=True)

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=PodcastsWithHeart",
        "--noconsole",
        "--onedir",
        "--clean",
        "-y",
        f"--icon={icon_path}",
        f"--distpath={staging_dist}",
        # Assets and data
        f"--add-data={os.path.join(base_dir, 'assets')};assets",
        f"--add-data={os.path.join(base_dir, 'docs')};docs",
        f"--add-data={os.path.join(base_dir, 'examples')};examples",
        f"--add-data={os.path.join(base_dir, 'models')};models",
        f"--add-data={os.path.join(os.path.dirname(__import__('piper').__file__), 'espeak-ng-data')};piper/espeak-ng-data",
        # Dependencies
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
        # Hidden imports
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

    print("Running PyInstaller...")
    print(" ".join(cmd))
    print("-" * 60)

    def robust_copy(src, dst):
        if sys.platform == "win32":
            subprocess.run(["robocopy", src, dst, "/MIR", "/R:2", "/W:1", "/NP"], check=False)
        else:
            shutil.copytree(src, dst, dirs_exist_ok=True)

    result = subprocess.run(cmd, cwd=base_dir)
    if result.returncode == 0:
        built_dir = os.path.join(staging_dist, "PodcastsWithHeart")
        new_dist = os.path.join(dist_dir, "PodcastsWithHeart")
        os.makedirs(new_dist, exist_ok=True)
        print(f"\nCopying built files to {new_dist}...")
        robust_copy(built_dir, new_dist)

        exe_path = os.path.join(new_dist, "PodcastsWithHeart.exe")
        print("\n" + "=" * 60)
        print("  [OK] Build of PodcastsWithHeart COMPLETED SUCCESSFULLY!")
        print(f"  Executable generated at:")
        print(f"  {exe_path}")

        # Package to official ZIP archive
        zip_name = f"PodcastsWithHeart-v{APP_VERSION}-Windows.zip"
        zip_path = os.path.join(dist_dir, zip_name)
        print(f"\n  Packaging into official ZIP archive: {zip_name}...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(new_dist):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, dist_dir)
                    zipf.write(full_path, rel_path)
        zip_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"  [OK] ZIP file generated ({zip_mb:.1f} MB):")
        print(f"  {zip_path}")

        # Synchronize direct copy to user's Downloads directory
        user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(user_downloads):
            try:
                dest_zip_downloads = os.path.join(user_downloads, zip_name)
                shutil.copy2(zip_path, dest_zip_downloads)
                print(f"  [OK] Download archive synchronized to: {dest_zip_downloads}")
                # Also extract for immediate execution
                unzipped_target = os.path.join(user_downloads, f"PodcastsWithHeart-v{APP_VERSION}-Windows", "PodcastsWithHeart")
                if os.path.exists(os.path.dirname(unzipped_target)):
                    robust_copy(new_dist, unzipped_target)
                    print(f"  [OK] Unzipped runtime folder updated at: {unzipped_target}")
            except Exception as e:
                print(f"  [NOTICE] Could not copy to Downloads: {e}")

        # Clean staging dir
        try:
            shutil.rmtree(staging_dist, ignore_errors=True)
        except Exception:
            pass

        print("=" * 60)
    else:
        print("\n[ERROR] Build failed.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
