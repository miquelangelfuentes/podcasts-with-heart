"""
Microsoft Neural English Cloud Engine (Edge-TTS).
Uses Microsoft's neural voices (US, UK, and Australian accents) with pitch, rate,
and expressive prosody modulation.
"""

import os
import io
import math
import asyncio
import tempfile
import numpy as np
import scipy.signal
import soundfile as sf
from typing import Dict, List, Optional, Callable, Tuple, Any

import edge_tts
from core.text_normalizer import EnglishTextNormalizer
from core.model_downloader import ModelDownloader

class MicrosoftNeuralEnglishEngine:
    """Cloud English TTS engine powered by Edge-TTS."""

    ENGLISH_VOICES = {
        "jenny": {
            "name": "Jenny (US English)",
            "gender": "Female",
            "accent": "US (Warm & Conversational)",
            "base_voice": "en-US-JennyNeural",
            "rate_offset": 0,
            "pitch_offset": 0
        },
        "guy": {
            "name": "Guy (US English)",
            "gender": "Male",
            "accent": "US (Dynamic & Clear)",
            "base_voice": "en-US-GuyNeural",
            "rate_offset": 2,
            "pitch_offset": 0
        },
        "aria": {
            "name": "Aria (US English)",
            "gender": "Female",
            "accent": "US (Expressive Storyteller)",
            "base_voice": "en-US-AriaNeural",
            "rate_offset": 1,
            "pitch_offset": 2
        },
        "davis": {
            "name": "Davis (US English)",
            "gender": "Male",
            "accent": "US (Academic & Calm)",
            "base_voice": "en-US-DavisNeural",
            "rate_offset": -2,
            "pitch_offset": -2
        },
        "sonia": {
            "name": "Sonia (British English)",
            "gender": "Female",
            "accent": "UK (Articulate & Professional)",
            "base_voice": "en-GB-SoniaNeural",
            "rate_offset": 0,
            "pitch_offset": 0
        },
        "ryan": {
            "name": "Ryan (British English)",
            "gender": "Male",
            "accent": "UK (Classic Storyteller)",
            "base_voice": "en-GB-RyanNeural",
            "rate_offset": 1,
            "pitch_offset": 0
        },
        "libby": {
            "name": "Libby (British English)",
            "gender": "Female",
            "accent": "UK (Lively & Youthful)",
            "base_voice": "en-GB-LibbyNeural",
            "rate_offset": 2,
            "pitch_offset": 3
        },
        "natasha": {
            "name": "Natasha (Australian English)",
            "gender": "Female",
            "accent": "AU (Natural & Friendly)",
            "base_voice": "en-AU-NatashaNeural",
            "rate_offset": 0,
            "pitch_offset": 0
        }
    }

    def __init__(self, models_dir: Optional[str] = None):
        self.name = "Microsoft Neural (English)"
        self.sample_rate = 22050
        self.text_normalizer = EnglishTextNormalizer()
        self.downloader = ModelDownloader(models_dir)

    def get_speakers(self) -> List[Dict[str, Any]]:
        """Returns list of speaker metadata for UI."""
        return [
            {
                "id": k,
                "name": v["name"],
                "gender": v["gender"],
                "accent": v["accent"],
                "desc": f"{v['accent']} • {v['gender']} neural cloud voice"
            }
            for k, v in self.ENGLISH_VOICES.items()
        ]

    def ensure_loaded(self, speaker_id: Optional[str] = None):
        """No heavy local load needed for cloud engine."""
        pass

    async def _synthesize_async(
        self,
        text: str,
        voice: str,
        rate_str: str,
        pitch_str: str,
        out_path: str
    ):
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate_str,
            pitch=pitch_str
        )
        await communicate.save(out_path)

    def synthesize_utterance(
        self,
        text: str,
        voice_id: str = "jenny",
        speed: float = 1.0,
        pitch: float = 0.0
    ) -> np.ndarray:
        """Synthesizes an English utterance into audio samples."""
        text = self.text_normalizer.normalize(text)
        if not text.strip():
            return np.zeros(int(0.2 * self.sample_rate), dtype=np.float32)

        v_info = self.ENGLISH_VOICES.get(voice_id.lower(), self.ENGLISH_VOICES["jenny"])
        azure_voice = v_info["base_voice"]

        total_rate = int(round((speed - 1.0) * 100)) + v_info.get("rate_offset", 0)
        rate_str = f"{total_rate:+d}%"

        total_pitch = int(round(pitch * 8)) + v_info.get("pitch_offset", 0)
        pitch_str = f"{total_pitch:+d}Hz"

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._synthesize_async(text, azure_voice, rate_str, pitch_str, tmp_path)
                )
            finally:
                loop.close()

            audio_data, sr = sf.read(tmp_path, dtype="float32")
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Resample to standard 22,050 Hz if needed
            if sr != self.sample_rate:
                num_target = int(len(audio_data) * (self.sample_rate / sr))
                audio_data = scipy.signal.resample(audio_data, num_target)

            return audio_data

        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
