# Third-Party Attribution & Licenses: Podcasts with Heart

Podcasts with Heart integrates and builds upon several outstanding open-source projects, neural voice models, and libraries. This document provides full attribution, authorship, origins, and licensing information for all third-party components.

---

## 1. Neural Speech Models & Engines

### Kokoro-82M
- **Role:** Flagship 100% offline studio neural speech engine.
- **Authors:** hexgrad & thewh1teagle (Kokoro ONNX runtime).
- **Origin / Repository:**
  - [Hugging Face: hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
  - [GitHub: thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)
- **License:** Apache License 2.0.

### Piper Neural Voice Models
- **Role:** Fast, lightweight 100% offline pedagogical neural voices.
- **Author:** Michael Hansen (Rhasspy community).
- **Origin / Repository:** [GitHub: rhasspy/piper](https://github.com/rhasspy/piper)
- **Voice Datasets & Authors:**
  - `en_US-lessac`: University of Edinburgh / Lessac dataset (Public Domain / Open Data).
  - `en_US-amy`: M-AILABS speech dataset (Public Domain / BSD).
  - `en_US-ryan`: M-AILABS speech dataset (Public Domain / BSD).
  - `en_GB-alan`: Alan dataset (Creative Commons / MIT).
- **License:** MIT License / Open Data.

### Edge TTS (Microsoft Neural Client)
- **Role:** Cloud-based streaming voice connector.
- **Author:** rany2.
- **Origin / Repository:** [GitHub: rany2/edge-tts](https://github.com/rany2/edge-tts)
- **License:** GNU General Public License v3.0 (GPLv3).

---

## 2. Core Python Libraries

| Library | Purpose | Author / Organization | License |
| :--- | :--- | :--- | :--- |
| **CustomTkinter** | Modern UI components & widgets | Tom Schimansky | MIT License |
| **ONNX Runtime** | High-performance neural model inference | Microsoft Corporation | MIT License |
| **NumPy** | Array & digital signal manipulation | NumPy Developers | BSD 3-Clause |
| **SoundFile** | Audio file reading and writing | Bastiaan Willem Beverwijk | BSD 3-Clause |
| **SciPy** | Digital signal processing & resampling | SciPy Developers | BSD 3-Clause |
| **Pygame** | Instant audio playback & preview engine | Pygame Community | GNU LGPL v2.1 |
| **Requests** | HTTP client for model downloads | Kenneth Reitz | Apache License 2.0 |
| **Pillow (PIL)** | Image manipulation & icon loading | Jeffrey A. Clark (Alex) | HPND License |
| **Pathvalidate** | Filename sanitization | Tsuyoshi Hombashi | MIT License |
| **eSpeak-ng Loader** | Phonemizer backend loader | thewh1teagle | MIT License |

---

## 3. Compliance and Redistribution Notice

All integrated third-party libraries and models are distributed and used in full compliance with their respective open-source licenses. No proprietary or closed-source libraries are bundled.
