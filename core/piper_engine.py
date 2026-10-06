"""
Piper Neural English Offline Engine for Podcasts with Heart.
Provides 100% offline, local, private, and high-fidelity speech synthesis
using Piper ONNX models (US and British English).
"""

import os
import sys
import gc
import re
import threading
import numpy as np
import scipy.signal
import soundfile as sf
from typing import Dict, List, Optional, Callable, Tuple, Any

try:
    from piper import PiperVoice, SynthesisConfig
    HAS_PIPER = True
except ImportError:
    HAS_PIPER = False

from core.text_normalizer import EnglishTextNormalizer
from core.model_downloader import ModelDownloader

class PiperEnglishEngine:
    """Autonomous offline English TTS engine powered by Piper ONNX."""

    PIPER_SPEAKERS = {
        "lessac": {
            "id": 0,
            "name": "Lessac (US English)",
            "gender": "Female",
            "accent": "US (Academic & Clear)",
            "desc": "High-clarity American English female voice, ideal for instruction and lessons",
            "model_file": "en_US-lessac-medium.onnx",
            "json_file": "en_US-lessac-medium.onnx.json",
            "url_subpath": "en/en_US/lessac/medium",
            "size_threshold": 60000000
        },
        "amy": {
            "id": 1,
            "name": "Amy (US English)",
            "gender": "Female",
            "accent": "US (Warm & Friendly)",
            "desc": "Natural conversational American English female voice",
            "model_file": "en_US-amy-medium.onnx",
            "json_file": "en_US-amy-medium.onnx.json",
            "url_subpath": "en/en_US/amy/medium",
            "size_threshold": 60000000
        },
        "ryan": {
            "id": 2,
            "name": "Ryan (US English)",
            "gender": "Male",
            "accent": "US (Dynamic & Crisp)",
            "desc": "Energetic American English male voice, great for interviews and co-hosting",
            "model_file": "en_US-ryan-medium.onnx",
            "json_file": "en_US-ryan-medium.onnx.json",
            "url_subpath": "en/en_US/ryan/medium",
            "size_threshold": 60000000
        },
        "alan": {
            "id": 3,
            "name": "Alan (British English)",
            "gender": "Male",
            "accent": "UK (Classic & Narrative)",
            "desc": "Articulate British English male voice for classic storytelling and documentaries",
            "model_file": "en_GB-alan-medium.onnx",
            "json_file": "en_GB-alan-medium.onnx.json",
            "url_subpath": "en/en_GB/alan/medium",
            "size_threshold": 60000000
        }
    }

    def __init__(self, models_dir: Optional[str] = None):
        self.name = "Piper English (100% Offline)"
        self.sample_rate = 22050
        self.text_normalizer = EnglishTextNormalizer()
        self.downloader = ModelDownloader(models_dir)
        self.models_dir = self.downloader.cache_dir

        self._voices: Dict[str, Any] = {}
        self._voice = None
        self._load_lock = threading.Lock()

    def get_speakers(self) -> List[Dict[str, Any]]:
        """Returns list of speaker descriptions for the UI."""
        return [
            {
                "id": k,
                "name": v["name"],
                "gender": v["gender"],
                "accent": v["accent"],
                "desc": v["desc"]
            }
            for k, v in self.PIPER_SPEAKERS.items()
        ]

    def _get_speaker_info(self, voice_id: Any) -> Dict[str, Any]:
        v_str = str(voice_id).lower()
        for k, info in self.PIPER_SPEAKERS.items():
            if k in v_str or info["name"].lower() in v_str:
                return info
        return self.PIPER_SPEAKERS["lessac"]

    def get_voice_paths(self, voice_key: str) -> Tuple[str, str]:
        spk_info = self.PIPER_SPEAKERS.get(voice_key, self.PIPER_SPEAKERS["lessac"])
        piper_dir = os.path.join(self.models_dir, "piper_voices")
        onnx_path = os.path.join(piper_dir, spk_info["model_file"])
        json_path = os.path.join(piper_dir, spk_info["json_file"])
        return onnx_path, json_path

    def is_voice_available(self, voice_key: str) -> bool:
        spk_info = self.PIPER_SPEAKERS.get(voice_key, self.PIPER_SPEAKERS["lessac"])
        onnx_path, json_path = self.get_voice_paths(voice_key)
        if not os.path.exists(onnx_path) or not os.path.exists(json_path):
            return False
        return os.path.getsize(onnx_path) >= spk_info["size_threshold"]

    def ensure_loaded(self, voice_id: Optional[str] = None,
                      on_status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Loads the ONNX model into memory, downloading it if absent."""
        spk_info = self._get_speaker_info(voice_id)
        v_key = "lessac"
        for k in self.PIPER_SPEAKERS:
            if k in spk_info["name"].lower() or k == str(voice_id).lower():
                v_key = k
                break

        with self._load_lock:
            if v_key in self._voices and self._voices[v_key] is not None:
                self._voice = self._voices[v_key]
                return True

            onnx_path, json_path = self.get_voice_paths(v_key)

            if not os.path.exists(onnx_path) or not os.path.exists(json_path):
                if on_status_callback:
                    on_status_callback(f"Downloading Piper voice {spk_info['name']}...")
                success = self._download_voice_files(v_key, onnx_path, json_path, on_status_callback)
                if not success or not os.path.exists(onnx_path):
                    print(f"Error: Could not obtain Piper model {spk_info['name']} at {onnx_path}")
                    return False

            if not HAS_PIPER:
                print("Error: piper-tts package not available.")
                return False

            if on_status_callback:
                on_status_callback(f"Loading {spk_info['name']} into memory...")

            try:
                voice_inst = PiperVoice.load(onnx_path, config_path=json_path)
                self._voices[v_key] = voice_inst
                self._voice = voice_inst
                return True
            except Exception as e:
                print(f"Error loading Piper voice {spk_info['name']}: {e}")
                return False

    def _download_voice_files(self, voice_key: str, onnx_path: str, json_path: str,
                              on_status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Downloads Piper ONNX and config JSON from Hugging Face with robust SSL fallback."""
        try:
            import requests
            import urllib3
            urllib3.disable_warnings()
            spk_info = self.PIPER_SPEAKERS.get(voice_key, self.PIPER_SPEAKERS["lessac"])
            os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
            base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{spk_info['url_subpath']}"

            session = requests.Session()

            def _get(url, stream=False):
                try:
                    return session.get(url, stream=stream, timeout=40, verify=True)
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, Exception):
                    return session.get(url, stream=stream, timeout=40, verify=False)

            # JSON config
            if not os.path.exists(json_path) or os.path.getsize(json_path) == 0:
                r = _get(f"{base_url}/{spk_info['json_file']}")
                r.raise_for_status()
                with open(json_path, "wb") as f:
                    f.write(r.content)

            # ONNX model
            if not os.path.exists(onnx_path) or os.path.getsize(onnx_path) < spk_info["size_threshold"]:
                r = _get(f"{base_url}/{spk_info['model_file']}", stream=True)
                r.raise_for_status()
                with open(onnx_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading Piper model {voice_key}: {e}")
            return False

    def unload(self, voice_id: Optional[str] = None):
        """Releases memory used by Piper models."""
        with self._load_lock:
            if voice_id:
                for k in self.PIPER_SPEAKERS:
                    if k in str(voice_id).lower():
                        self._voices.pop(k, None)
            else:
                self._voices.clear()
                self._voice = None
            gc.collect()

    def split_sentences(self, text: str) -> List[str]:
        """Splits English text into clean sentences."""
        text = re.sub(r"\b(Dr|Mr|Mrs|Ms|Prof|St|approx|vs|no|No)\.", r"\1__DOT__", text)
        sentences = re.split(r"([.!?;\n]+)", text)

        result = []
        current = ""
        for part in sentences:
            if not part:
                continue
            if re.match(r"^[.!?;\n]+$", part):
                current += part
                clean = current.replace("__DOT__", ".").strip()
                if clean:
                    result.append(clean)
                current = ""
            else:
                current += part

        if current.strip():
            result.append(current.replace("__DOT__", ".").strip())

        return result

    def synthesize_utterance(self, text: str, voice_id: Any = "lessac",
                             speed: float = 1.0, pitch: float = 0.0,
                             normalize_text: bool = True) -> np.ndarray:
        """Synthesizes an English utterance into audio samples."""
        if not text or not text.strip():
            return np.zeros(0, dtype=np.float32)

        normalized_text = self.text_normalizer.normalize(text) if normalize_text else text
        if not normalized_text:
            return np.zeros(0, dtype=np.float32)

        spk_info = self._get_speaker_info(voice_id)
        v_key = "lessac"
        for k in self.PIPER_SPEAKERS:
            if k in spk_info["name"].lower():
                v_key = k
                break

        if not self.ensure_loaded(voice_id=v_key):
            print(f"Error: Could not load Piper engine for voice '{v_key}'.")
            return np.zeros(0, dtype=np.float32)

        voice = self._voices.get(v_key)
        if voice is None:
            return np.zeros(0, dtype=np.float32)

        try:
            safe_speed = max(0.5, min(2.0, speed))
            length_scale = 1.0 / safe_speed
            syn_config = SynthesisConfig(length_scale=length_scale)

            chunks = list(voice.synthesize(normalized_text, syn_config=syn_config))
            if not chunks:
                return np.zeros(0, dtype=np.float32)

            audio_arrays = [c.audio_float_array for c in chunks if c.audio_float_array is not None]
            if not audio_arrays:
                return np.zeros(0, dtype=np.float32)

            audio = np.concatenate(audio_arrays)

            sr = voice.config.sample_rate
            if sr != self.sample_rate:
                num_samples = int(len(audio) * (self.sample_rate / sr))
                audio = scipy.signal.resample(audio, num_samples)

            # Smooth edges to prevent clicks
            fade_len = int(0.012 * self.sample_rate)
            if len(audio) > 2 * fade_len:
                audio[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
                audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

            return audio.astype(np.float32)

        except Exception as e:
            print(f"Error synthesizing with Piper ({v_key}): {e}")
            return np.zeros(0, dtype=np.float32)
