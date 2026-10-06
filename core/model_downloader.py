"""
Model Downloader and Integrity Manager for Podcasts with Heart.
Handles asynchronous downloads and validation of neural TTS voices from Hugging Face.
"""

import os
import sys
import time
import requests
import threading
from typing import Callable, Optional, Dict, Any, List

class ModelDownloader:
    """Download and integrity management for English TTS voice models."""

    HF_BASE_URL = "https://huggingface.co"

    MODEL_REPOSITORIES = {
        "kokoro_heart": {
            "name": "Kokoro-82M Heart (Studio Quality, 100% Offline)",
            "provider": "Hexgrad Kokoro",
            "repo_id": "thewh1teagle/kokoro-onnx",
            "files": {
                "kokoro-v1.0.int8.onnx": "kokoro-v1.0.int8.onnx",
                "voices-v1.0.bin": "voices-v1.0.bin"
            },
            "desc": "Studio-quality 82M neural TTS engine with 11 expressive voices including the flagship 'Heart' voice (115 MB). Completely autonomous, zero internet required.",
            "expected_size_mb": 115.0,
            "category": "Offline Heart Engine (Kokoro ONNX)",
            "is_cloud": False
        },
        "piper_lessac": {
            "name": "Lessac (US English Female, 100% Offline)",
            "provider": "Rhasspy Piper",
            "repo_id": "rhasspy/piper-voices",
            "files": {
                "en/en_US/lessac/medium/en_US-lessac-medium.onnx": "en_US-lessac-medium.onnx",
                "en/en_US/lessac/medium/en_US-lessac-medium.onnx.json": "en_US-lessac-medium.onnx.json"
            },
            "desc": "Academic, clear, articulate American English female voice (63 MB). Completely autonomous, zero internet required.",
            "expected_size_mb": 63.2,
            "category": "Offline Voice (Piper ONNX)",
            "is_cloud": False
        },
        "piper_amy": {
            "name": "Amy (US English Female, 100% Offline)",
            "provider": "Rhasspy Piper",
            "repo_id": "rhasspy/piper-voices",
            "files": {
                "en/en_US/amy/medium/en_US-amy-medium.onnx": "en_US-amy-medium.onnx",
                "en/en_US/amy/medium/en_US-amy-medium.onnx.json": "en_US-amy-medium.onnx.json"
            },
            "desc": "Warm, natural conversational American English voice (63 MB).",
            "expected_size_mb": 63.2,
            "category": "Offline Voice (Piper ONNX)",
            "is_cloud": False
        },
        "piper_ryan": {
            "name": "Ryan (US English Male, 100% Offline)",
            "provider": "Rhasspy Piper",
            "repo_id": "rhasspy/piper-voices",
            "files": {
                "en/en_US/ryan/medium/en_US-ryan-medium.onnx": "en_US-ryan-medium.onnx",
                "en/en_US/ryan/medium/en_US-ryan-medium.onnx.json": "en_US-ryan-medium.onnx.json"
            },
            "desc": "Dynamic and narrative American English male voice (63 MB).",
            "expected_size_mb": 63.2,
            "category": "Offline Voice (Piper ONNX)",
            "is_cloud": False
        },
        "piper_alan": {
            "name": "Alan (British English Male, 100% Offline)",
            "provider": "Rhasspy Piper",
            "repo_id": "rhasspy/piper-voices",
            "files": {
                "en/en_GB/alan/medium/en_GB-alan-medium.onnx": "en_GB-alan-medium.onnx",
                "en/en_GB/alan/medium/en_GB-alan-medium.onnx.json": "en_GB-alan-medium.onnx.json"
            },
            "desc": "Classic, articulate British English storytelling voice (63 MB).",
            "expected_size_mb": 63.2,
            "category": "Offline Voice (Piper ONNX)",
            "is_cloud": False
        },
        "edge_tts_cloud": {
            "name": "Microsoft Neural English (Online)",
            "provider": "Microsoft Edge Cloud",
            "repo_id": "microsoft/edge-tts",
            "files": {},
            "desc": "High-fidelity cloud voices (Jenny, Guy, Aria, Davis, Sonia, Ryan). Requires internet, zero local disk space.",
            "expected_size_mb": 0.0,
            "category": "Cloud Voice (Online)",
            "is_cloud": True
        }
    }

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.cache_dir = os.path.abspath(cache_dir)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.cache_dir = os.path.join(base_dir, "models")
        os.makedirs(self.cache_dir, exist_ok=True)
        self._cancel_requested = False
        self.last_error = ""

    def cancel_download(self):
        """Requests cancellation of ongoing download."""
        self._cancel_requested = True

    def get_model_path(self, model_key: str, filename: str) -> str:
        """Returns local path for a model file."""
        sub = "kokoro_voices" if "kokoro" in model_key.lower() else "piper_voices"
        return os.path.join(self.cache_dir, sub, filename)

    def is_model_downloaded(self, model_key: str) -> bool:
        """Checks if all files for a model exist and have positive size."""
        if model_key not in self.MODEL_REPOSITORIES:
            return False
        model_info = self.MODEL_REPOSITORIES[model_key]
        if model_info.get("is_cloud"):
            return True
        for local_file in model_info["files"].values():
            full_path = self.get_model_path(model_key, local_file)
            if not os.path.exists(full_path) or os.path.getsize(full_path) == 0:
                return False
        return True

    def get_component_status(self, model_key: str) -> Dict[str, Any]:
        """Returns component status for the UI."""
        if model_key not in self.MODEL_REPOSITORIES:
            raise ValueError(f"Unknown model: {model_key}")

        info = self.MODEL_REPOSITORIES[model_key]
        total_installed_bytes = 0
        files_detail = []
        is_complete = True

        for remote_name, local_file in info["files"].items():
            path = self.get_model_path(model_key, local_file)
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            total_installed_bytes += size
            if not exists or size == 0:
                is_complete = False
            files_detail.append({
                "remote_name": remote_name,
                "local_file": local_file,
                "path": path,
                "exists": exists,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2)
            })

        return {
            "key": model_key,
            "name": info["name"],
            "provider": info["provider"],
            "desc": info["desc"],
            "category": info["category"],
            "is_cloud": info.get("is_cloud", False),
            "is_installed": is_complete or info.get("is_cloud", False),
            "installed_size_mb": round(total_installed_bytes / (1024 * 1024), 2),
            "expected_size_mb": info["expected_size_mb"],
            "files": files_detail
        }

    def download_model(
        self,
        model_key: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        speed_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """Synchronously downloads a model from Hugging Face with progress callbacks."""
        if model_key not in self.MODEL_REPOSITORIES:
            self.last_error = f"Model {model_key} not recognized."
            return False

        model_info = self.MODEL_REPOSITORIES[model_key]
        if model_info.get("is_cloud"):
            return True

        self._cancel_requested = False
        repo_id = model_info["repo_id"]
        files = model_info["files"]

        sub_dir = os.path.join(self.cache_dir, "kokoro_voices" if "kokoro" in model_key.lower() else "piper_voices")
        os.makedirs(sub_dir, exist_ok=True)

        for remote_subpath, local_filename in files.items():
            if self._cancel_requested:
                self.last_error = "Download cancelled by user."
                return False

            if "thewh1teagle" in repo_id:
                url = f"https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/{remote_subpath}"
            elif remote_subpath.startswith("http://") or remote_subpath.startswith("https://"):
                url = remote_subpath
            else:
                url = f"{self.HF_BASE_URL}/{repo_id}/resolve/main/{remote_subpath}"

            dest_path = os.path.join(sub_dir, local_filename)
            temp_path = dest_path + ".part"

            success = self._download_file(url, dest_path, temp_path, progress_callback, speed_callback)
            if not success:
                return False

        return True

    def _download_file(
        self,
        url: str,
        dest_path: str,
        temp_path: str,
        progress_callback: Optional[Callable[[float, str], None]],
        speed_callback: Optional[Callable[[float], None]]
    ) -> bool:
        try:
            import urllib3
            urllib3.disable_warnings()
            session = requests.Session()
            headers = {"User-Agent": "PodcastsWithHeart/1.0"}
            resume_byte_pos = 0

            if os.path.exists(temp_path):
                resume_byte_pos = os.path.getsize(temp_path)
                headers["Range"] = f"bytes={resume_byte_pos}-"

            def _fetch(h):
                try:
                    return session.get(url, headers=h, stream=True, timeout=30, verify=True)
                except requests.exceptions.SSLError:
                    return session.get(url, headers=h, stream=stream if 'stream' in locals() else True, timeout=30, verify=False)

            response = _fetch(headers)

            if response.status_code == 416: # Range not satisfiable, restart
                resume_byte_pos = 0
                headers.pop("Range", None)
                response = _fetch(headers)

            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0)) + resume_byte_pos
            mode = "ab" if resume_byte_pos > 0 else "wb"

            downloaded = resume_byte_pos
            start_time = time.time()
            bytes_since_sample = 0
            last_sample_time = start_time

            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if self._cancel_requested:
                        return False
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        bytes_since_sample += len(chunk)

                        now = time.time()
                        if now - last_sample_time >= 0.4:
                            speed = bytes_since_sample / (now - last_sample_time)
                            if speed_callback:
                                speed_callback(speed)
                            bytes_since_sample = 0
                            last_sample_time = now

                        if progress_callback and total_size > 0:
                            ratio = downloaded / total_size
                            progress_callback(ratio, f"{downloaded / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB")

            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.rename(temp_path, dest_path)
            return True

        except Exception as e:
            self.last_error = str(e)
            return False

    def delete_model(self, model_key: str) -> bool:
        """Removes local files for a model."""
        if model_key not in self.MODEL_REPOSITORIES:
            return False
        model_info = self.MODEL_REPOSITORIES[model_key]
        for local_file in model_info["files"].values():
            full_path = self.get_model_path(model_key, local_file)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception:
                pass
        return True
