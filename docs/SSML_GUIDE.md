# SSML Prosody, Voice Pacing & Acoustic Guide — Podcasts with Heart

This comprehensive guide details **Speech Synthesis Markup Language (SSML)**, speaker speed/pitch control, prosodic pacing, and audio mastering options available in **Podcasts with Heart**.

The application powers multi-speaker English podcasts using three specialized neural engines:
1. **💖 Kokoro-82M Heart Engine (100% Offline)**: Studio-quality 82M parameter neural model with 11 expressive voices (flagship engine).
2. **🎙️ Piper Neural English (100% Offline)**: Fast, lightweight ONNX voices (Lessac, Amy, Ryan, Alan).
3. **☁️ Microsoft Neural English (Online)**: High-fidelity cloud service with US, UK, and Australian accents.

---

## 1. Speaker Pacing & Pitch Configuration (`[VOICE_CONFIG]`)

You can set each speaker's default voice, stereo pan, speaking speed, and pitch directly in the technical header of the script:

```text
[VOICE_CONFIG]
Host: voice=af_heart pan=0% speed=0.95 pitch=0
Speaker 1: voice=bf_emma pan=-25% speed=1.10 pitch=+1
Speaker 2: voice=am_adam pan=+25% speed=1.00 pitch=0
```

### Parameters Reference:
- **`voice=`**: Identifier of the voice model (e.g. `af_heart`, `am_adam`, `bf_emma`, `lessac`, `amy`, `ryan`, `alan`, `jenny`, `guy`).
- **`pan=`**: Stereo positioning:
  - `pan=0%`: Center (facing listener, recommended for Host).
  - `pan=-25%`: Left conversational position (Speaker 1).
  - `pan=+25%`: Right conversational position (Speaker 2).
  - `pan=-50%` / `pan=+50%`: Wide left/right for panel guests.
- **`speed=`** (or `rate=`): Speaking speed multiplier:
  - `speed=1.0`: Standard conversational speed.
  - `speed=0.85` – `0.95`: Calm, pedagogical, instructional or narrative pace.
  - `speed=1.05` – `1.20`: Energetic, dynamic, enthusiastic co-host delivery.
  - Allowed range: `0.5` to `2.0`.
- **`pitch=`** (or `tone=`): Voice fundamental frequency shift:
  - `pitch=0`: Natural voice pitch.
  - `pitch=+1` to `+3`: Slightly higher tone (expressive, youthful, joyful).
  - `pitch=-1` to `-3`: Deeper, authoritative, or broadcast radio tone.

---

## 2. Natural Punctuation as Acoustic Prosody

All neural models in Podcasts with Heart derive natural prosodic cues from standard punctuation marks:
- **Comma `,`**: Inserts a gentle rising melodic contour and an organic ~150–250 ms breath pause.
- **Period `.`**: Triggers a conclusive, downward declarative cadence.
- **Question Mark `?`**: Generates a distinctive rising questioning pitch curve.
- **Exclamation Mark `!`**: Increases vocal energy and attack.
- **Ellipsis `...`**: Elongates the preceding vowel to simulate thoughtful hesitation or pedagogical reflection.
- **Em Dash `—`**: Introduces an abrupt parenthetical pause without resetting baseline sentence pitch.

---

## 3. Pacing, Pauses & SSML Tags

Podcasts with Heart provides two complementary approaches to control pacing: **dedicated bracket tags** (supported across all engines including 100% offline Kokoro-82M and Piper) and **inline SSML tags** (supported natively by the online Microsoft Neural engine):

### A. Dedicated Pause Lines (`[PAUSE: ...]`) — Recommended (Universal)
Supported uniformly by all offline and online engines. Insert dedicated pause lines anywhere in the dialogue:
```text
Host: That wraps up our first case study.

[PAUSE: 800ms]

Speaker 1: Moving right along to the second example...
```
- **Format**: `[PAUSE: 350ms]` or `[PAUSE: 1.2s]`.
- **Recommended Guidelines**:
  - `150ms – 250ms`: Brief breath pause within a complex sequence.
  - `400ms – 650ms`: Natural topic shift or thought transition between speakers.
  - `800ms – 1.5s`: Dramatic silence for listeners to absorb a key takeaway.

---

### B. Speaker-Level Speed & Pitch (`[VOICE_CONFIG]` & UI) — Universal
The primary and most reliable way to modulate speed and pitch across **all engines** (Kokoro-82M, Piper, and Microsoft Neural):
- **Via the UI**: Select speed directly on each speaker card (`0.8x`, `0.9x`, `1.0x`, `1.1x`, `1.2x`).
- **Via the Script Header**:
  ```ini
  [VOICE_CONFIG]
  Host: voice=af_heart pan=0% speed=0.95 pitch=0
  Speaker 1: voice=bf_emma pan=-25% speed=1.05 pitch=+1
  ```

---

### C. Inline SSML Tags (Cloud Neural Engine)
When using the online **Microsoft Neural English** engine, standard SSML tags can be embedded directly within sentences:
- **Exact silences (`<break time="..."/>`)**:
  ```xml
  Speaker 1: Let me reflect on that for a second... <break time="800ms"/> Now that makes complete sense!
  ```
- **Speed & pitch shifts (`<prosody rate="..." pitch="...">`)**:
  ```xml
  Host: <prosody rate="0.9">This definition is essential for the entire curriculum.</prosody>
  Speaker 1: <prosody rate="1.15" pitch="+1st">Brilliant! We solved the puzzle in record time!</prosody>
  ```
- **Emphasis (`<emphasis level="strong">`)**:
  ```xml
  Host: This is not just an update; this is a <emphasis level="strong">structural paradigm shift</emphasis>.
  ```
> [!NOTE]
> Offline neural engines (Kokoro-82M and Piper) synthesize speech from normalized phonetic text. For offline synthesis, always use `[VOICE_CONFIG] speed=... pitch=...` and `[PAUSE: ...ms]` tags for 100% predictable, natural pacing.

---

## 4. Background Music & Ambience Integration

- **Continuous Looping**: Background audio tracks loop seamlessly with automatic 20 ms cross-fades.
- **Smooth Fades**: Automated 1-second fade-in at the start and 2-second fade-out at the conclusion.
- **Calibrated Volume**: Adjustable via the live slider (recommended default: **15%** so voice clarity is never compromised).
- **Instant Audition**: Press `▶ Test` in the background card to preview the mix before running full generation.

---

## 5. Broadcast Mastering (EBU R128)

Every synthesized podcast passes through the professional broadcast mastering pipeline:
- **EBU R128 Loudness**: Normalized to **-16 LUFS** (standard for podcasts and streaming services).
- **True Peak Limiting**: Capped at **-1.0 dBTP** to prevent inter-sample clipping and MP3 encoding artifacts.
- **Stereo Spatialization**: Constant Power Panning Law applied across all multi-speaker stems.
- **Export Specifications**: **160 kbps CBR Stereo MP3** (ISO MPEG-2 Layer 3 compliant) or uncompressed WAV.

---

## 6. Keyboard Shortcuts & Accessibility

| Shortcut | Action |
| :--- | :--- |
| `Ctrl+G` or `Ctrl+Enter` | Generate Full Podcast |
| `Ctrl+S` | Save Podcast Script |
| `Ctrl+O` | Open Existing Script |
| `F1` | Open this SSML Guide |
| `Esc` | Cancel ongoing generation |
