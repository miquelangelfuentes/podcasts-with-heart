"""
Voice Preview Manager for Podcasts with Heart.
Handles generation, caching, and instant audio playback of voice samples.
"""

import os
import sys
import tempfile
import threading
import soundfile as sf
import numpy as np
from typing import Dict, Optional, Callable, Any

try:
    if sys.platform == "win32":
        import winsound
        HAS_WINSOUND = True
    else:
        HAS_WINSOUND = False
except ImportError:
    HAS_WINSOUND = False

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

class VoicePreviewManager:
    """Manages audio generation, caching, and playback of voice samples."""

    SAMPLE_PHRASES = {
        # Cloud Voices (Edge-TTS)
        "jenny": "Hello, I'm Jenny. I'm a warm American English voice for your podcasts.",
        "guy": "Hey there, I'm Guy. Let's create an engaging conversational episode today.",
        "aria": "Hello, I'm Aria, an expressive storytelling voice for podcasts.",
        "davis": "Greetings, I'm Davis. I provide calm, academic narration for your lessons.",
        "sonia": "Hello, I'm Sonia, an articulate British English voice.",
        "ryan": "Hi there, I'm Ryan. Welcome to this episode recorded in British English.",
        "libby": "Hello, I'm Libby! Ready to bring lively energy to your podcast.",
        "natasha": "G'day, I'm Natasha, bringing natural Australian English narration.",
        # Offline Voices (Piper ONNX)
        "lessac": "Hello, I'm Lessac, a clear and articulate offline voice for your lessons.",
        "amy": "Hi everyone, I'm Amy, a warm American offline narrator.",
        "alan": "Greetings, I'm Alan, an articulate British storytelling voice."
    }

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.cache_dir = os.path.join(base_dir, "assets", "previews")
        os.makedirs(self.cache_dir, exist_ok=True)

        self._is_playing = False
        self._play_lock = threading.Lock()
        self._current_play_thread = None

    def get_sample_phrase(self, voice_id: str) -> str:
        """Returns preview sample phrase for a given voice ID."""
        v_clean = voice_id.lower().strip()
        for k, phrase in self.SAMPLE_PHRASES.items():
            if k in v_clean:
                return phrase
        return "Hello! This is a preview of my voice for Podcasts with Heart."

    def play_sample(
        self,
        voice_id: str,
        engine: Any,
        on_start_callback: Optional[Callable[[], None]] = None,
        on_finish_callback: Optional[Callable[[], None]] = None,
        on_error_callback: Optional[Callable[[str], None]] = None
    ):
        """Asynchronously synthesizes and plays a sample."""
        thread = threading.Thread(
            target=self._play_worker,
            args=(voice_id, engine, on_start_callback, on_finish_callback, on_error_callback),
            daemon=True
        )
        thread.start()

    def _play_worker(self, voice_id, engine, on_start, on_finish, on_error):
        with self._play_lock:
            self.stop()
            self._is_playing = True

            clean_id = voice_id.lower().strip()
            wav_path = os.path.join(self.cache_dir, f"preview_{clean_id}.wav")

            # Check if pre-cached
            if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
                try:
                    phrase = self.get_sample_phrase(voice_id)
                    audio_data = engine.synthesize_utterance(phrase, voice_id=voice_id)
                    if audio_data is not None and len(audio_data) > 0:
                        sf.write(wav_path, audio_data, getattr(engine, "sample_rate", 22050))
                    else:
                        if on_error:
                            on_error("Could not generate audio preview.")
                        self._is_playing = False
                        return
                except Exception as e:
                    if on_error:
                        on_error(str(e))
                    self._is_playing = False
                    return

            if on_start:
                try:
                    on_start()
                except Exception:
                    pass

            try:
                if HAS_WINSOUND:
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                elif HAS_PYGAME:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load(wav_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() and self._is_playing:
                        pygame.time.Clock().tick(10)
            except Exception as e:
                if on_error:
                    on_error(f"Playback error: {e}")
            finally:
                self._is_playing = False
                if on_finish:
                    try:
                        on_finish()
                    except Exception:
                        pass

    def stop(self):
        """Stops current audio playback."""
        self._is_playing = False
        try:
            if HAS_WINSOUND:
                winsound.PlaySound(None, winsound.SND_PURGE)
            elif HAS_PYGAME and pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
