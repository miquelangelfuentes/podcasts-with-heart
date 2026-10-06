"""
Kokoro-TTS English Offline Engine for Podcasts with Heart.
Provides 100% offline, local, private, and studio-quality speech synthesis
using Kokoro-82M ONNX models and style vectors.

Kokoro (心, Japanese for "Heart") is the heart and soul of this application.
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
    from kokoro_onnx import Kokoro
    HAS_KOKORO = True
except ImportError:
    HAS_KOKORO = False

from core.text_normalizer import EnglishTextNormalizer
from core.model_downloader import ModelDownloader

class KokoroEnglishEngine:
    """Autonomous offline English TTS engine powered by Kokoro-82M ONNX."""

    KOKORO_SPEAKERS = {
        "af_heart": {
            "name": "Heart (US English — Studio Flagship)",
            "gender": "Female",
            "accent": "US (Studio & Expressive)",
            "desc": "Flagship studio voice with unparalleled emotional resonance and expressive clarity."
        },
        "af_bella": {
            "name": "Bella (US English — Warm & Natural)",
            "gender": "Female",
            "accent": "US (Warm & Friendly)",
            "desc": "Natural conversational American English female voice, ideal for dialogues."
        },
        "af_nicole": {
            "name": "Nicole (US English — Conversational)",
            "gender": "Female",
            "accent": "US (Casual & Friendly)",
            "desc": "Relaxed and engaging female voice for co-hosting."
        },
        "af_sarah": {
            "name": "Sarah (US English — Poised Narrator)",
            "gender": "Female",
            "accent": "US (Poised & Articulate)",
            "desc": "Calm, clear narrative American voice for educational content."
        },
        "af_sky": {
            "name": "Sky (US English — Dynamic & Fresh)",
            "gender": "Female",
            "accent": "US (Dynamic & Youthful)",
            "desc": "Energetic and crisp female voice for introductions and lively segments."
        },
        "am_adam": {
            "name": "Adam (US English — Resonant & Confident)",
            "gender": "Male",
            "accent": "US (Resonant & Deep)",
            "desc": "Deep, confident American male voice for host and primary narration."
        },
        "am_michael": {
            "name": "Michael (US English — Authentic & Clear)",
            "gender": "Male",
            "accent": "US (Clear & Direct)",
            "desc": "Authentic, relatable American male voice for interviews and lessons."
        },
        "bf_emma": {
            "name": "Emma (British English — Refined & Poised)",
            "gender": "Female",
            "accent": "UK (Refined & Elegant)",
            "desc": "Refined British English female voice with poise and clarity."
        },
        "bf_isabella": {
            "name": "Isabella (British English — Gentle Narrator)",
            "gender": "Female",
            "accent": "UK (Gentle & Narrative)",
            "desc": "Gentle British narration voice for literary and descriptive podcasts."
        },
        "bm_george": {
            "name": "George (British English — Classic Storyteller)",
            "gender": "Male",
            "accent": "UK (Classic & Articulate)",
            "desc": "Classic British English male narrator for documentaries and deep stories."
        },
        "bm_lewis": {
            "name": "Lewis (British English — Distinct Narrator)",
            "gender": "Male",
            "accent": "UK (Distinct & Engaging)",
            "desc": "Distinct British voice for interviews and co-hosting."
        }
    }

    MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx"
    VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

    def __init__(self, models_dir: Optional[str] = None):
        self.name = "Kokoro-TTS (Heart Engine, 100% Offline)"
        self.sample_rate = 22050
        self.native_sample_rate = 24000
        self.text_normalizer = EnglishTextNormalizer()
        self.downloader = ModelDownloader(models_dir)
        self.models_dir = self.downloader.cache_dir

        self.kokoro_dir = os.path.join(self.models_dir, "kokoro_voices")
        self.model_path = os.path.join(self.kokoro_dir, "kokoro-v1.0.int8.onnx")
        self.voices_path = os.path.join(self.kokoro_dir, "voices-v1.0.bin")

        self._kokoro = None
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
            for k, v in self.KOKORO_SPEAKERS.items()
        ]

    def _resolve_voice_id(self, voice_id: Any) -> str:
        """Resolves input string or alias to a valid Kokoro voice key."""
        v_str = str(voice_id).lower().strip()
        # Direct key match
        if v_str in self.KOKORO_SPEAKERS:
            return v_str
        # Partial match on key or name
        for k, info in self.KOKORO_SPEAKERS.items():
            if k == v_str or k.replace("af_", "").replace("am_", "").replace("bf_", "").replace("bm_", "") == v_str:
                return k
            if v_str in info["name"].lower():
                return k
        return "af_heart"

    def is_available(self) -> bool:
        """Checks if model files are downloaded."""
        if not os.path.exists(self.model_path) or not os.path.exists(self.voices_path):
            return False
        return os.path.getsize(self.model_path) > 50000000 and os.path.getsize(self.voices_path) > 10000000

    def ensure_loaded(self, voice_id: Optional[str] = None,
                      on_status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Loads Kokoro into memory, downloading files if necessary."""
        with self._load_lock:
            if self._kokoro is not None:
                return True

            if not self.is_available():
                if on_status_callback:
                    on_status_callback("Downloading Kokoro-82M Heart model files...")
                success = self._download_model_files(on_status_callback)
                if not success or not self.is_available():
                    print("Error: Could not obtain Kokoro model files.")
                    return False

            if not HAS_KOKORO:
                print("Error: kokoro-onnx package not available.")
                return False

            if on_status_callback:
                on_status_callback("Loading Kokoro-82M Heart engine into memory...")

            try:
                self._kokoro = Kokoro(self.model_path, self.voices_path)
                return True
            except Exception as e:
                print(f"Error initializing Kokoro: {e}")
                return False

    def _download_model_files(self, on_status_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Downloads Kokoro model and voice embeddings with SSL retry."""
        try:
            import requests
            import urllib3
            urllib3.disable_warnings()

            os.makedirs(self.kokoro_dir, exist_ok=True)
            session = requests.Session()

            def _get(url, stream=False):
                try:
                    return session.get(url, stream=stream, timeout=60, verify=True)
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, Exception):
                    return session.get(url, stream=stream, timeout=60, verify=False)

            # 1. Voices binary
            if not os.path.exists(self.voices_path) or os.path.getsize(self.voices_path) < 10000000:
                if on_status_callback:
                    on_status_callback("Downloading Kokoro voices styles (28 MB)...")
                r = _get(self.VOICES_URL, stream=True)
                r.raise_for_status()
                with open(self.voices_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            # 2. ONNX model
            if not os.path.exists(self.model_path) or os.path.getsize(self.model_path) < 50000000:
                if on_status_callback:
                    on_status_callback("Downloading Kokoro-82M neural model (88 MB)...")
                r = _get(self.MODEL_URL, stream=True)
                r.raise_for_status()
                with open(self.model_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

            return True
        except Exception as e:
            print(f"Error downloading Kokoro files: {e}")
            return False

    def synthesize_utterance(self, text: str, voice_id: Any = "af_heart",
                             speed: float = 1.0, pitch: float = 0.0) -> np.ndarray:
        """
        Synthesizes an English utterance into studio-grade audio samples.
        Audio is returned normalized to the project standard sample rate (22050 Hz).
        """
        if not text or not text.strip():
            return np.zeros(0, dtype=np.float32)

        normalized_text = self.text_normalizer.normalize(text)
        if not normalized_text:
            return np.zeros(0, dtype=np.float32)

        resolved_voice = self._resolve_voice_id(voice_id)

        if not self.ensure_loaded(voice_id=resolved_voice):
            print("Error: Could not load Kokoro-82M engine.")
            return np.zeros(0, dtype=np.float32)

        try:
            safe_speed = max(0.5, min(2.0, float(speed)))
            samples, sr = self._kokoro.create(
                normalized_text,
                voice=resolved_voice,
                speed=safe_speed,
                lang="en-us" if not resolved_voice.startswith("b") else "en-gb"
            )

            if samples is None or len(samples) == 0:
                return np.zeros(0, dtype=np.float32)

            audio = np.asarray(samples, dtype=np.float32)

            # Resample from Kokoro's native 24 kHz to project 22,050 Hz
            if sr != self.sample_rate:
                target_len = int(len(audio) * (self.sample_rate / sr))
                audio = scipy.signal.resample(audio, target_len).astype(np.float32)

            return audio

        except Exception as e:
            print(f"Error during Kokoro synthesis: {e}")
            return np.zeros(0, dtype=np.float32)

    def unload(self):
        """Frees Kokoro ONNX model from memory."""
        with self._load_lock:
            self._kokoro = None
            gc.collect()
