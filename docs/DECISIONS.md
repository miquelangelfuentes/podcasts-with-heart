# Architectural Decision Records (ADR): Podcasts with Heart

This document records the architectural and design decisions made during the development of **Podcasts with Heart**, explaining both **what** was built and **why** specific technical choices were made.

---

## ADR 01: Desktop Application Framework (CustomTkinter)

### Context
Educators and students need a modern, distraction-free desktop environment that runs smoothly across both Windows and Linux without requiring a web browser, Node.js runtimes, or client-server local port listeners.

### Decision
We selected **CustomTkinter** (a modern Python wrapper over Tkinter) styled with a customized warm palette (`HeartTheme`).

### Rationale
- **Zero Heavy Runtime Overhead:** Tkinter is integrated directly into standard Python, avoiding the memory footprint of Electron (~150–300 MB extra RAM).
- **Native High-DPI Support:** Crisp rendering on standard and high-resolution monitors (100%, 125%, 150% scaling).
- **Cross-Platform Portability:** Runs identically on Windows 10/11 and Linux distributions (Ubuntu, Debian, Fedora, Arch) without OS-specific UI code.

---

## ADR 02: Neural Engine Selection (Kokoro-82M ONNX + Piper)

### Context
Synthesizing natural, expressive English voices usually requires massive deep-learning dependencies (such as PyTorch with CUDA, taking 3–6 GB of disk space) or permanent cloud subscriptions that violate student data privacy (GDPR/FERPA).

### Decision
We adopted **Kokoro-82M** via **ONNX Runtime** as the flagship offline engine, complemented by lightweight **Piper Neural** voices.

### Rationale
- **Ultra-Lightweight Footprint:** The quantized Kokoro-82M INT8 ONNX model is only ~115 MB in size, while Piper models are ~63 MB each.
- **Fast CPU Inference:** Thanks to ONNX Runtime optimizations, voice inference runs faster than real-time on standard Intel and AMD laptop CPUs without requiring dedicated GPUs.
- **Studio Quality Sound:** Kokoro-82M utilizes StyleTTS2 architecture with an integrated neural vocoder delivering 24 kHz studio clarity and human-like expressive pauses.
- **100% Privacy Independence:** Zero data is sent to external servers; schools can operate safely in offline mode or behind strict network firewalls.

---

## ADR 03: Multi-Speaker Format & Automatic Spatialization

### Context
Educational podcasts benefit significantly from interactive dialogue formats, but traditional multi-track digital audio workstations (DAWs) are difficult for teachers and students to configure properly.

### Decision
We built automated stereo spatialization (*panning*) directly into the audio pipeline:
- **1-Voice Monologue:** Host centered at `pan=0%`.
- **2-Voice Dialogue:** Interlocutors separated at `pan=-25%` and `pan=+25%`.
- **3-Voice Roundtable:** Moderator centered at `pan=0%`, guest panelists positioned at `pan=-25%` and `pan=+25%`.

### Rationale
- Recreates a physical radio broadcast table acoustic environment.
- Enhances vocal distinction and cognitive retention for listeners without cognitive fatigue.

---

## ADR 04: Audio Mastering Standard (EBU R128 at -16 LUFS)

### Context
Inconsistent volume levels across different voice engines, background music tracks, and playback devices (smartphones, headphones, classroom smart boards) create jarring listening experiences.

### Decision
We standardized final episode mastering to **EBU R128 (-16 LUFS integrated loudness, -1 dBTP true peak limit)** with export to **160 kbps CBR Stereo MP3**.

### Rationale
- **International Broadcasting Compliance:** -16 LUFS is the global standard for podcast distribution (Apple Podcasts, Spotify, YouTube).
- **No Digital Clipping:** Integrated soft-knee peak limiter prevents distortion when mixing foreground speech with looping background music.

---

## ADR 05: Dedicated "School Mode" Switch

### Context
While the optional Microsoft Neural cloud engine provides convenient zero-storage voices, strict educational regulations (GDPR in Europe, FERPA and COPPA in the US) strictly forbid sending student personal data or classroom writing to third-party cloud servers without enterprise data processing agreements.

### Decision
We introduced a prominent **🏫 School Mode** button in the application header.

### Rationale
- **Single-Click Privacy Lockdown:** Disables cloud endpoints, hides cloud options from the dropdown, and restricts synthesis strictly to local ONNX models.
- **Visual Assurance for Educators:** Displays a persistent green privacy badge (`🛡️ School Mode: 0% Internet Data`), ensuring teachers and administrators can verify data safety at a glance.

---

## ADR 06: Keyboard Accessibility & Keyboard-Driven Workflow

### Context
Educators with repetitive strain injuries or visual impairments need full accessibility without relying on mouse navigation.

### Decision
We implemented global keybindings:
- `Ctrl+G` / `Ctrl+Enter`: Trigger full generation.
- `Ctrl+S`: Save script file.
- `Ctrl+O`: Open script file.
- `F1`: Open SSML reference manual.
- `Escape`: Cancel ongoing generation.

### Rationale
Enables fluid, accessible classroom workflows adhering to WCAG and VCER accessibility standards.
