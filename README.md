# ❤️ Podcasts with Heart

> **Autonomous desktop podcast studio for Windows and Linux to craft 1, 2, or 3-voice educational podcasts in English, with 100% offline privacy and no duration limits.**  
> Styled in a modern, warm pastel red & rose studio aesthetic (*HeartTheme*).

---

## 🌟 Key Features

- **Flexible Multi-Speaker Structures**:
  - **1 Voice (Monologue)**: Centered host (`pan=0%`) for instructional capsules, summaries, and audio essays.
  - **2 Voices (Dialogue)**: Dual-host peer conversations (`-25%` and `+25%`) without requiring an extra moderator.
  - **3 Voices (Roundtable)**: Centered host (`pan=0%`) with side guest panelists (`-25%` and `+25%`).
- **100% Offline & Private (School Mode)**:
  - Toggle **🏫 School Mode** with a single click in the header.
  - Automatically restricts synthesis to local **Piper ONNX** models and hides cloud engines.
  - Guarantees **0% internet data transmission** (fully compliant with student data privacy & GDPR).
- **Triple Voice Engines (Offline & Cloud)**:
  - **💖 Kokoro-82M Heart Engine (100% Offline, Studio Quality)**: Flagship 82M parameter neural TTS engine with 11 expressive voices (Heart, Bella, Nicole, Sarah, Sky, Adam, Michael, Emma, Isabella, George, Lewis). Zero internet required.
  - **🎙️ Piper Neural English (100% Offline)**: Lightweight (~63 MB/voice) ONNX models for US and British English (Lessac, Amy, Ryan, Alan).
  - **☁️ Microsoft Neural English (Online)**: Studio-grade cloud voices with US, UK, and Australian accents (Jenny, Guy, Aria, Davis, Sonia, Ryan, Natasha).
- **Background Music & Ambience Track**:
  - Load background soundtrack (MP3, WAV, OGG, FLAC) in continuous loop with seamless cross-fading.
  - Dynamic volume slider (default 15% to maintain vocal clarity) and instant live preview button.
- **Broadcast EBU R128 Loudness Mastering**:
  - Automatic stereo spatialization (*panning*).
  - Broadcast-standard **EBU R128 loudness normalization (-16 LUFS, -1 dBTP peak)**.
  - Direct export to **160 kbps CBR Stereo MP3**.
- **Global Keyboard Accessibility**:
  - `Ctrl+G` / `Ctrl+Enter`: Generate full podcast.
  - `Ctrl+S`: Save script.
  - `Ctrl+O`: Open script.
  - `F1`: Open SSML prosody guide.
  - `Esc`: Cancel ongoing generation.

---

## 🚀 Quick Start (Running from Source)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch application
python app.py
```

---

## 📁 Project Structure

```
📁 PodcastsWithHeart/
├── 📄 app.py                     # Application entry point
├── 📁 core/                      # Processing engines
│   ├── 📄 script_parser.py       # Podcast script parser
│   ├── 📄 text_normalizer.py     # English text & SSML normalizer
│   ├── 📄 kokoro_engine.py       # Kokoro-82M Heart engine (100% Offline)
│   ├── 📄 edge_tts_engine.py     # Microsoft Neural English engine (Online)
│   ├── 📄 piper_engine.py        # Piper ONNX English engine (100% Offline)
│   ├── 📄 audio_processor.py     # Stereo panning, loop music, EBU R128 & MP3
│   ├── 📄 voice_preview.py       # Instant preview player
│   └── 📄 model_downloader.py    # Hugging Face model downloader
├── 📁 ui/                        # User interface (HeartTheme)
│   ├── 📄 theme.py               # Pastel red & warm rose theme palette
│   ├── 📄 main_window.py         # Main studio window & layout
│   ├── 📄 components.py          # PillSelector & CleanButton
│   ├── 📄 player_widget.py       # Interactive audio player
│   └── 📄 components_modal.py    # Voice models manager dialog
├── 📁 assets/                    # Icons and audio previews
├── 📁 examples/                  # 1-voice, 2-voice, and 3-voice script templates
├── 📁 docs/                      # SSML guide & LLM scriptwriting guide
└── 📄 test_features.py           # Automated test suite
```

---

## 📜 License & Credits

- Built with CustomTkinter, Piper TTS, and Edge-TTS.
- Open-source under GNU AGPL v3.
