# SSML Prosody & Acoustic Guide — Podcasts with Heart

This guide details Speech Synthesis Markup Language (SSML), prosodic pacing, and emotional modulation in **Podcasts with Heart**.

---

## 1. Natural Punctuation as Prosody

Neural TTS engines derive cadence and intonation directly from standard punctuation:
- **Comma `,`**: Creates a gentle rising inflection and a 150–250 ms natural pause.
- **Period `.`**: Declares a concluding downward cadence.
- **Question Mark `?`**: Generates a characteristic rising questioning pitch.
- **Ellipsis `...`**: Elongates the preceding vowel to reflect contemplation or transition.

---

## 2. SSML Tags in Dialogue Lines

You can embed SSML tags directly within character dialogue lines:

### A. Pauses & Silences (`<break>`)
Control the exact length of silence before the voice continues:
```xml
Host: First, let us look at the primary thesis. <break time="400ms"/> Second, we will review the data.
Speaker 1: Give me a moment to think... <break time="1s"/> Now that makes complete sense!
```
- Recommended durations:
  - `150ms – 300ms`: Brief conversational pause within long sentences.
  - `400ms – 700ms`: Subtopic transition.
  - `800ms – 1.5s`: Dramatic silence for listeners to absorb a key question.

---

## 3. Stereo Spatialization (Panning)

Podcasts with Heart simulates an authentic acoustic studio table:

| Position | Technical Value | Recommended Usage | Acoustic Sensation |
| :--- | :--- | :--- | :--- |
| **Center** | `pan=0%` | Host / Monologue | Directly facing the listener |
| **Slight Left** | `pan=-25%` | Speaker 1 (Interviews & Dialogues) | Left side of the studio table |
| **Slight Right** | `pan=+25%` | Speaker 2 (Interviews & Dialogues) | Right side of the studio table |
| **Wide Left** | `pan=-50%` | Guest 1 (Roundtables) | Spaced out to prevent vocal overlap |
| **Wide Right** | `pan=+50%` | Guest 2 (Roundtables) | Far right panelist |

---

## 4. EBU R128 Broadcast Loudness & Audio Export

Every generated podcast passes through an automated broadcast mastering pipeline:
- **Looping Background Ambience**: Blends user-selected music (MP3, WAV, OGG, FLAC) with a 20 ms cross-fade, 1s fade-in, and 2s fade-out.
- **EBU R128 Loudness Normalization**: Targets standard podcast loudness at **-16 LUFS** with a **-1 dBTP** true peak ceiling.
- **Turn Breathing Pauses**: Automatically inserts natural breathing space between speaker switches.
- **Export Format**: Broadcast-standard **MP3 stereo at 160 kbps CBR** at 22,050 Hz.
