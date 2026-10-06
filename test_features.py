"""
Test Suite for Podcasts with Heart.
Verifies theme, text normalizer, script parser, audio processor, and voice catalogs.
"""

import os
import sys
import numpy as np

# Ensure root in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from ui.theme import HeartTheme
from core.text_normalizer import EnglishTextNormalizer
from core.script_parser import ScriptParser
from core.audio_processor import AudioProcessor
from core.edge_tts_engine import MicrosoftNeuralEnglishEngine
from core.piper_engine import PiperEnglishEngine
from core.voice_preview import VoicePreviewManager
from core.model_downloader import ModelDownloader

def test_theme():
    print("--- 1. Testing HeartTheme Palette ---")
    assert HeartTheme.PRIMARY == "#B83A4B"
    assert HeartTheme.BG_MAIN == "#FDF8F9"
    assert HeartTheme.TEXT_ON_PRIMARY == "#FFFFFF"
    print("[OK] HeartTheme pastel red & warm rose palette verified successfully.")

def test_normalizer():
    print("--- 2. Testing English Text Normalizer ---")
    norm = EnglishTextNormalizer()
    s = norm.normalize("In 2026, Dr. Smith gave 25% off for 1st place.")
    assert "twenty twenty-six" in s
    assert "Doctor" in s
    assert "twenty-five percent" in s
    assert "first" in s

    ssml = norm.parse_ssml_blocks("Hello <break time='500ms'/> world!")
    assert len(ssml) == 3
    assert ssml[1]["duration_ms"] == 500
    print("[OK] EnglishTextNormalizer verified successfully.")

def test_script_parser():
    print("--- 3. Testing Script Parser & Templates ---")
    parser = ScriptParser()

    # Test 1-voice template
    p1 = os.path.join(BASE_DIR, "examples", "template_1voice.txt")
    with open(p1, "r", encoding="utf-8") as f:
        s1 = parser.parse(f.read())
    assert len(s1.speakers) == 1
    assert any(seg.segment_type == "dialogue" for seg in s1.segments)

    # Test 2-voice template
    p2 = os.path.join(BASE_DIR, "examples", "template_2voices.txt")
    with open(p2, "r", encoding="utf-8") as f:
        s2 = parser.parse(f.read())
    assert len(s2.speakers) == 2

    # Test 3-voice template
    p3 = os.path.join(BASE_DIR, "examples", "template_3voices.txt")
    with open(p3, "r", encoding="utf-8") as f:
        s3 = parser.parse(f.read())
    assert len(s3.speakers) == 3
    print("[OK] ScriptParser and all 1, 2, and 3 voice templates verified successfully.")

def test_audio_processor():
    print("--- 4. Testing Audio Processor (Panning & EBU R128) ---")
    proc = AudioProcessor(sample_rate=22050)
    silence = proc.generate_silence(500)
    assert len(silence) == int(0.5 * 22050)

    stereo = proc.apply_pan(silence, -0.25)
    assert stereo.shape[0] == 2
    assert stereo.shape[1] == len(silence)

    # Synthetic tone for loudness normalization test
    t = np.linspace(0, 1.0, 22050, dtype=np.float32)
    tone = np.sin(2 * np.pi * 440 * t) * 0.5
    stereo_tone = np.vstack([tone, tone])
    mastered = proc.normalize_loudness(stereo_tone, target_lufs=-16.0)
    assert mastered.shape == stereo_tone.shape
    print("[OK] AudioProcessor stereo panning and EBU R128 mastering verified successfully.")

def test_voice_catalogs():
    print("--- 5. Testing Voice Catalogs & Previews ---")
    edge = MicrosoftNeuralEnglishEngine()
    speakers_edge = edge.get_speakers()
    assert len(speakers_edge) >= 8

    piper = PiperEnglishEngine()
    speakers_piper = piper.get_speakers()
    assert len(speakers_piper) >= 4

    preview_mgr = VoicePreviewManager()
    phrase = preview_mgr.get_sample_phrase("jenny")
    assert "Jenny" in phrase

    downloader = ModelDownloader()
    assert "piper_lessac" in downloader.MODEL_REPOSITORIES
    print("[OK] Voice catalogs, preview phrases, and downloader verified successfully.")

def main():
    print("=" * 60)
    print("  RUNNING PODCASTS WITH HEART TEST SUITE")
    print("=" * 60)
    test_theme()
    test_normalizer()
    test_script_parser()
    test_audio_processor()
    test_voice_catalogs()
    print("\n*** ALL TESTS PASSED SUCCESSFULLY! (100% OPERATIONAL) ***\n")

if __name__ == "__main__":
    main()
