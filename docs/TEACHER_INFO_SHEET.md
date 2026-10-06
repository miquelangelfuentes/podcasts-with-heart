# Pedagogical Disclosure & Teacher Information Sheet: «Podcasts with Heart»

This document is a **comprehensive context and instructional reference guide** designed for:
1. Providing teachers, school administrators, and educators with a clear, rigorous, and practical overview of the application.
2. Serving as a **context document for Large Language Models (LLMs such as ChatGPT, Claude, Gemini, Mistral, or Llama)** to generate educational materials, classroom announcements, curriculum plans, or social media summaries.

---

## 1. Executive Summary & Fast Sheet

| Parameter | Details |
| :--- | :--- |
| **Tool Name** | Podcasts with Heart |
| **Software Type** | Standalone desktop application for Windows and Linux (no cloud dependencies required) |
| **Primary Purpose** | Fast, intuitive, and professional creation of educational podcasts and audio lessons in English using local neural AI speech synthesis |
| **Target Audience** | Primary, Secondary, High School, Vocational Education, Language Academies, Universities, Adult Education, and pedagogical content creators |
| **Language & Accents** | English in major global varieties: American (US), British (UK), and Australian accents |
| **Voice Engines** | 1. **Kokoro-82M** (11 studio-quality neural voices in ONNX format, 100% offline, flagship engine)<br>2. **Piper Neural** (4 lightweight pedagogical voices: Lessac, Amy, Ryan, Alan, 100% offline)<br>3. **Microsoft Neural English** (cloud-connected streaming service with 8 expressively tuned voices)<br>4. **English Normalizer & Audio Processor** (number, date, acronym expansions, stereo pan, and EBU R128 mastering) |
| **Privacy & Security** | **100% local and confidential** when using Kokoro-82M or Piper models (zero text, audio, or student names leave the computer). Dedicated **🏫 School Mode** switch in the header disables cloud options completely (GDPR, FERPA & COPPA compliant for minors) |
| **Accessibility** | Global keyboard shortcuts (`Ctrl+G`, `Ctrl+S`, `Ctrl+O`, `F1`, `Escape`) for seamless mouse-free operation |
| **Updates** | Integrated "Check Version" button querying GitHub Releases directly for 1-click updates |
| **Music & Ambience** | Background track support (MP3, WAV, OGG, FLAC) with seamless looping, dynamic volume slider, instant preview, and studio fade-in/fade-out |
| **Cost & License** | Free, open-source software under GNU AGPL v3 |
| **Official Repository** | [GitHub: miquelangelfuentes/podcasts-with-heart](https://github.com/miquelangelfuentes/podcasts-with-heart) |

---

## 2. Why Is This Tool Unique for Educators?

1. **Autonomous Offline Execution (100% Offline):**
   - Requires zero internet connection once model files are downloaded.
   - Usable in classrooms, on laptops without Wi-Fi, or in restricted school networks with complete reliability.
   - **School Mode** (button 🏫 in the header) locks the interface to local engines, displaying the **🛡️ School Mode: 0% Internet Data (GDPR & Privacy Protected)** badge.

2. **Multi-Speaker Radio Studio Architecture (1, 2, or 3 Voices):**
   - Enables structured formats: instructional monologues (1 voice), co-hosted lessons or peer interviews (2 voices), or moderated roundtable discussions (3 voices).
   - Automatic stereo spatialization (panning Host in the center, guests to the left and right) recreates a genuine broadcast studio atmosphere.

3. **Built-in Audio Engineering & Broadcast Mastering:**
   - Automatically normalizes numbers, ordinal rankings, dates, abbreviations, and common educational acronyms into fluent English phonetic equivalents.
   - Masters every generated podcast to international broadcasting standards (**EBU R128 at -16 LUFS**), ensuring balanced, broadcast-grade listening volume across smartphones, headphones, and smart boards.

4. **Background Music and Atmospheric Soundscapes:**
   - Easily import background music or ambient sounds (rain, classroom, calm piano, electronic synths).
   - Seamless loop engine with 20 ms cross-fades eliminates audible clicks or interruptions.
   - Calibrated default volume (15%) ensures vocal clarity is never overshadowed.

---

## 3. Catalog of Voice Engines and Voices

### Engine 1: ❤️ Kokoro-82M (100% Offline — Studio Quality Heart Engine)
- **Model:** 82M-parameter compact ONNX neural model (~115 MB).
- **Features:** Studio-grade expressive intonation, natural breathing, human warmth, and CPU inference under 500 ms per utterance.
- **11 English Voices:**
  - **American (US):**
    - `af_heart` (Female, studio flagship — warm, expressive, ideal for lessons)
    - `af_bella` (Female, conversational & friendly)
    - `af_nicole` (Female, relaxed & narrative)
    - `af_sarah` (Female, poised narrator)
    - `af_sky` (Female, energetic youth)
    - `am_adam` (Male, deep, articulate & resonant)
    - `am_michael` (Male, clear & authentic)
  - **British (UK):**
    - `bf_emma` (Female, refined, poised & elegant)
    - `bf_isabella` (Female, gentle & storybook)
    - `bm_george` (Male, classic documentary narrator)
    - `bm_lewis` (Male, engaging & crisp)

### Engine 2: 🎙️ Piper Neural (100% Offline — Fast & Lightweight)
- **Model:** Piper ONNX neural voices (~60 MB each).
- **Features:** High clarity, pedagogical pacing, low CPU utilization.
- **Voices:**
  - `lessac` (US Female, academic & articulate)
  - `amy` (US Female, natural & friendly)
  - `ryan` (US Male, dynamic & crisp)
  - `alan` (British Male, classic storytelling)

### Engine 3: ☁️ Microsoft Neural English (Online Streaming)
- **Model:** Cloud TTS connection via Edge TTS endpoints.
- **Features:** 0 MB local storage, online streaming, 8 multi-accent voices (US, UK, Australia).
- **Voices:** Jenny, Guy, Aria, Davis, Sonia, Ryan, Libby, Natasha.

---

## 4. Educational Applications in the Classroom

1. **Instructional Capsules & Flipped Classrooms:**
   - Bite-sized (3–5 minute) audio lessons explaining key grammar points, historical events, scientific discoveries, or weekly reading tasks.

2. **Simulated Role-Play & Socratic Debates:**
   - Recreate historical dialogues (e.g., debates between thinkers), scientific panels, or literature analysis with distinctive speaker roles and stereo separation.

3. **Universal Design for Learning (UDL) & Accessibility:**
   - **Reading Accommodations:** Essential support for students with dyslexia, visual impairments, or reading comprehension challenges.
   - **Dual-Modal Learning:** Students read the written text while listening to fluent pronunciation and prosody.

4. **English as a Second / Foreign Language (ESL / EFL):**
   - Authentic pronunciation models with selectable American, British, and Australian accents.
   - Configurable speed (`speed=0.8` to `1.2`) for listening comprehension exercises at beginner, intermediate, and advanced levels.

5. **Student-Led Podcast Projects & Audio Journalism:**
   - Students act as scriptwriters, researching topics, organizing dialogue turns, and choosing matching musical themes. The application renders their scripts into polished audio without complex audio workstation software.

---

## 5. Technical Requirements & Recommendations

- **Operating Systems:** Windows 10, Windows 11, and Linux distributions (Ubuntu, Debian, Fedora, Arch, Linux Mint).
- **Hardware:** Runs smoothly on standard Intel or AMD multi-core CPUs. No dedicated GPU required. Recommended 4 GB RAM (8 GB optimal) and ~500 MB free disk space.
- **Script Formatting:** Uses clean dialogue script format with colon separation (`Host: ...`, `Speaker 1: ...`). Insert pauses with `[PAUSE: 500ms]` or adjust pacing with `speed=1.0`.
- **Keyboard Accessibility:** `Ctrl+G` (generate podcast), `Ctrl+S` (save script), `Ctrl+O` (open script), `F1` (SSML guide), and `Escape` (cancel generation).

---

## 6. Ethical AI and Student Data Privacy

1. **Student Data Privacy (GDPR, FERPA, COPPA):**
   - Offline engines (Kokoro-82M and Piper) process all audio strictly in local memory. No personal data, student voices, or text queries are transmitted to third parties or cloud servers.
2. **AI Transparency:**
   - Educators and students should disclose that the synthesized voices are generated by neural AI models.
3. **Responsible Creation:**
   - The tool is designed strictly for creative, pedagogical, and educational purposes. Defamatory content, unauthorized impersonation, or deceptive deepfakes are strictly prohibited.

---

## 7. License & Credits

- **Neural Voice Models:** Kokoro-82M created by hexgrad, Piper TTS created by Michael Hansen (Rhasspy community).
- **Application Author:** Developed using intention-driven vibe coding with Google Antigravity by **Miquel Àngel Fuentes**, following Responsible Educational Vibe Coding guidelines.
- **Source Code License:** Free Software distributed under the **GNU AGPL v3** license on GitHub.
- **Documentation & Educational Examples:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
