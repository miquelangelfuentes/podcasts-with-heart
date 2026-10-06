# Informe d'avaluació VCER: Podcasts with Heart

Rúbrica VCER: Recomendable (100 %)  
Versió avaluada: v1.0.0 (commit `2f4ee3eb6aa92d9451d08777fc87762320228065`), octubre de 2026.  
Significat del resultat: **Recomendable**: compleix de manera excel·lent tots els principis de la guia de Vibe Coding Educatiu Responsable (VCER) i és plenament apte per a la seva distribució i ús en entorns escolars i acadèmics.

---

## 1. Inventari del recurs

1. **Dades personals:**
   - No demana dades que identifiquin cap persona.
   - Tot el processament d'àudio i de guions es realitza a la memòria local i en fitxers temporals del sistema.
   - Exportació d'àudio (MP3/WAV) directa a la carpeta que triï la persona usuària al disc local.
   - No conté analítica, telemetria ni galetes.
   - Disposa de l'interruptor **🏫 School Mode** que desactiva de soca-rel les crides al núvol i garanteix el 100 % de processament local sota el RGPD i la normativa FERPA/COPPA per a menors.

2. **Elements multimèdia:**
   - **Icones:** `assets/icon.ico` i `assets/icon.png` (disseny original minimalista amb auriculars i cor vermell pastel, sense marques alienes).
   - **Mostres d'àudio (`assets/previews/`):** 15 arxius WAV sintetitzats directament amb els models oberts integrats (Kokoro-82M i Piper Neural).
   - **Tipografies:** Tipografies del sistema administrades per CustomTkinter (Segoe UI a Windows, tipografia del sistema a Linux); no descarrega fonts de tercers.

3. **Connexions externes:**
   - En obrir el recurs: 0 connexions externes.
   - En obrir `📦 Models` -> `🔍 Check My System`: capçalera HTTP de diagnòstic a `https://huggingface.co`.
   - En prémer descàrrega de models: connexió a `https://huggingface.co/rhasspy/piper-voices` o `https://github.com/thewh1teagle/kokoro-onnx`.
   - En prémer «Comprova versió»: consulta HTTP GET a l'API pública de GitHub (`api.github.com/repos/miquelangelfuentes/podcasts-with-heart`).
   - En utilitzar el motor al núvol opcional: connexió WebSocket/HTTPS a Microsoft Azure Edge TTS (desactivable amb el botó «School Mode»).

---

## 2. Avaluació detallada segons la rúbrica VCER

| Criteri | Puntuació | Justificació |
| :--- | :---: | :--- |
| **1. Contingut (eliminatori)** | **2** | No es detecten errors en els conceptes transmesos: les plantilles i guions didàctics expliquen amb precisió la narrativa radiofònica, l'espacialització estèreo, la masterització EBU R128 a -16 LUFS i el control prosòdic SSML. |
| **2. Dades personals (eliminatori)** | **2** | No recull cap dada que identifiqui l'alumnat, no fa servir telemetria i disposa de l'interruptor «School Mode» que blindatza el 100 % del processament local sense eixir cap dada de l'ordinador. |
| **3. Entendre què fa** | **2** | Es descriu amb claredat: és un estudi de ràdio d'escriptori autònom per crear podcasts educatius en anglès d'1, 2 o 3 veus amb models neuronals locals i al núvol, pistes de música en bucle i masterització professional. El codi compleix exactament allò declarat. |
| **4. Dependències** | **2** | Totes les dependències i serveis externs estan documentats a `docs/CREDITS.md` i `README.md`. L'aplicació és completament autònoma i funciona al 100 % en mode avió sense connexió a internet amb els seus models locals. |
| **5. Accesibilitat** | **2** | Disposa de control complet mitjançant el teclat (`Ctrl+G`, `Ctrl+S`, `Ctrl+O`, `F1`, `Escape`), contrast elevat en la paleta HeartTheme, etiquetes clares i adaptació a pantalles compactes i escalat DPI. |
| **6. Material aliè** | **2** | Tot el material aliè (models Kokoro-82M, Piper Neural i llibreries) està rigorosament desglossat a `docs/CREDITS.md` amb autoria, procedència i llicències lliures compatibles (Apache 2.0, MIT, BSD, LGPL). |
| **7. Rastre** | **2** | Compta amb el document de registre de decisions d'arquitectura `docs/DECISIONS.md`, on s'explica detalladament el motiu de cada elecció tecnològica. |
| **8. Ús d'IA** | **2** | Indica de forma visible que s'ha creat mitjançant vibe coding amb Google Antigravity i detalla les quatre validacions humanes manuals dutes a terme per l'autor (fonètica, lingüística, acústica i privadesa). |
| **9. Llicència** | **2** | Llicència GNU AGPL v3 per al codi i CC BY-SA 4.0 per a la documentació i continguts inclosa físicament al fitxer `LICENSE` de l'arrel i enllaçada al README. |
| **10. Reutilització** | **2** | Codi font completament disponible, estructurat i comentat, acompanyat d'una bateria de tests automatitzada (`py test_features.py`) i guies completes de compilació i llançament a Windows i Linux. |

**Puntuació total: 20 / 20 (100 %)** — **Recomendable**

---

*Avaluació efectuada seguint la guia oficial de Vibe Coding Educatiu Responsable (VCER).*
