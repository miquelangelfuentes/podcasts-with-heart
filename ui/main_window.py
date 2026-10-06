"""
Main Window for Podcasts with Heart.
Clean, modern, accessible desktop application for creating educational English podcasts.
Built with CustomTkinter and styled in HeartTheme (Pastel Red & Warm Rose).
"""

import os
import re
import sys
import time
import queue
import threading
import ctypes
from typing import Optional, Dict, Any, List

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import numpy as np
import soundfile as sf
import scipy.signal

from ui.theme import HeartTheme
from ui.components import CleanButton, PillSelector
from ui.player_widget import AudioPlayerWidget
from ui.components_modal import ComponentsManagerModal

from core.script_parser import ScriptParser, PodcastScript, SpeakerConfig, PodcastSegment
from core.audio_processor import AudioProcessor
from core.text_normalizer import EnglishTextNormalizer
from core.edge_tts_engine import MicrosoftNeuralEnglishEngine
from core.piper_engine import PiperEnglishEngine
from core.voice_preview import VoicePreviewManager
from core.model_downloader import ModelDownloader

APP_VERSION = "1.0.0"

class MainWindow(ctk.CTk):
    """Main Application Window for Podcasts with Heart."""

    def __init__(self):
        super().__init__()

        self.title("Podcasts with Heart — Educational English Podcast Studio")
        self._fit_window_to_work_area()

        ctk.set_appearance_mode("light")
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self._set_app_icon()

        self._ui_queue = queue.Queue()
        self.after(35, self._process_ui_queue)

        # Core engines
        self.script_parser = ScriptParser()
        self.text_normalizer = EnglishTextNormalizer()
        self.edge_engine = MicrosoftNeuralEnglishEngine()
        self.piper_engine = PiperEnglishEngine()
        self.tts_engine = self.edge_engine # Default: high quality online, or piper
        self.audio_processor = AudioProcessor(sample_rate=22050)
        self.voice_preview_manager = VoicePreviewManager()

        self.current_script = PodcastScript()
        self.ui_speaker_overrides: Dict[str, Dict[str, Any]] = {}
        self._suppress_script_sync = False
        self._internal_mode_update = False
        self.is_generating = False
        self.cancel_requested = False
        self.editor_mode = "clean"
        self._raw_script_full = ""

        # Background music settings
        self.bg_music_path: Optional[str] = None
        self.bg_music_loop: bool = True
        self.bg_music_volume: float = 0.15
        self.bg_music_audio_data: Optional[np.ndarray] = None
        self._bg_preview_sound = None
        self._bg_preview_timer_id = None
        self._is_bg_previewing: bool = False

        self._build_ui()
        self._bind_keyboard_shortcuts()
        self._load_default_sample()

    def _fit_window_to_work_area(self):
        work_w, work_h = 1200, 780
        self.minsize(1000, 640)
        self.geometry(f"{work_w}x{work_h}")

    def _set_app_icon(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        png_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass
        if os.path.exists(png_path):
            try:
                self._icon_img = tk.PhotoImage(file=png_path)
                self.iconphoto(True, self._icon_img)
            except Exception:
                pass

    def safe_after(self, func):
        self._ui_queue.put(func)

    def _process_ui_queue(self):
        try:
            while not self._ui_queue.empty():
                task = self._ui_queue.get_nowait()
                try:
                    task()
                except Exception as e:
                    print(f"Error executing UI task: {e}")
        finally:
            self.after(35, self._process_ui_queue)

    def _build_ui(self):
        # 1. Header Toolbar
        header = ctk.CTkFrame(
            self,
            fg_color=HeartTheme.BG_CARD,
            height=58,
            corner_radius=0,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        brand_frame = ctk.CTkFrame(header, fg_color="transparent")
        brand_frame.pack(side="left", padx=18, pady=10)

        app_title = ctk.CTkLabel(
            brand_frame,
            text="❤️ Podcasts with Heart",
            font=HeartTheme.FONT_TITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        app_title.pack(side="left", padx=(0, 10))

        tag_badge = ctk.CTkLabel(
            brand_frame,
            text="AI · ENGLISH",
            font=HeartTheme.FONT_TINY,
            fg_color=HeartTheme.PRIMARY_LIGHT,
            text_color=HeartTheme.PRIMARY,
            corner_radius=8,
            padx=7,
            pady=1
        )
        tag_badge.pack(side="left", padx=(0, 10))

        self.badge = ctk.CTkLabel(
            brand_frame,
            text="Piper Neural & Microsoft Neural (Studio Quality 22kHz)",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        self.badge.pack(side="left")

        self.school_badge = ctk.CTkLabel(
            brand_frame,
            text="🛡️ School Mode Active: 0% Internet Data (GDPR & Privacy Protected)",
            font=HeartTheme.FONT_SMALL_BOLD,
            fg_color="#D4EDDA",
            text_color="#155724",
            corner_radius=8,
            padx=8,
            pady=2
        )

        # Right buttons on header
        help_frame = ctk.CTkFrame(header, fg_color="transparent")
        help_frame.pack(side="right", padx=18, pady=10)

        btn_ssml = CleanButton(
            help_frame,
            style="ghost",
            text="📖 SSML Guide",
            width=100,
            height=28,
            command=self._show_ssml_guide
        )
        btn_ssml.pack(side="left", padx=3)

        btn_llm = CleanButton(
            help_frame,
            style="ghost",
            text="💡 LLM Prompt",
            width=105,
            height=28,
            command=self._show_llm_guide
        )
        btn_llm.pack(side="left", padx=3)

        btn_models = CleanButton(
            help_frame,
            style="ghost",
            text="📦 Models",
            width=85,
            height=28,
            command=self._show_components_manager
        )
        btn_models.pack(side="left", padx=3)

        self._school_mode = False
        self.btn_school = CleanButton(
            help_frame,
            style="ghost",
            text="🏫 School Mode",
            width=110,
            height=28,
            command=self._toggle_school_mode
        )
        self.btn_school.pack(side="left", padx=3)

        # 2. Voice Structure Bar (1, 2, or 3 voices)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=18, pady=(12, 4))

        format_label = ctk.CTkLabel(
            top_bar,
            text="Podcast Structure:",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_MUTED
        )
        format_label.pack(side="left", padx=(0, 10))

        self.structure_selector = PillSelector(
            top_bar,
            values=["1 Voice (Monologue)", "2 Voices (Dialogue)", "3 Voices (Roundtable)"],
            default_val="2 Voices (Dialogue)",
            command=self._on_structure_selected,
            height=30,
            font_size=9
        )
        self.structure_selector.pack(side="left")

        # 3. Main Studio Workspace (Left & Right Split)
        self.main_split = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split.pack(fill="both", expand=True, padx=18, pady=(4, 8))

        # --- LEFT PANEL: Script Studio ---
        editor_card = ctk.CTkFrame(
            self.main_split,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        editor_card.pack(side="left", fill="both", expand=True, padx=(0, 9))

        ed_header = ctk.CTkFrame(editor_card, fg_color="transparent")
        ed_header.pack(fill="x", padx=16, pady=(12, 6))

        ed_title = ctk.CTkLabel(
            ed_header,
            text="✍️ Podcast Script Editor",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        ed_title.pack(side="left")

        self.mode_selector = PillSelector(
            ed_header,
            values=["Clean Dialogues", "Full Code (.txt)"],
            default_val="Clean Dialogues",
            command=self._on_editor_mode_change,
            height=28,
            font_size=9
        )
        self.mode_selector.pack(side="right")

        # Script text area
        self.script_textbox = ctk.CTkTextbox(
            editor_card,
            fg_color=HeartTheme.ENTRY_BG,
            border_color=HeartTheme.ENTRY_BORDER,
            border_width=1,
            corner_radius=10,
            font=HeartTheme.FONT_MONO,
            text_color=HeartTheme.TEXT_MAIN,
            wrap="word",
            undo=True
        )
        self.script_textbox.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.script_textbox.bind("<<Modified>>", self._on_script_text_changed)

        # Bottom actions for editor
        ed_actions = ctk.CTkFrame(editor_card, fg_color="transparent")
        ed_actions.pack(fill="x", padx=16, pady=(0, 12))

        btn_open = CleanButton(ed_actions, style="ghost", text="📂 Open", width=75, height=28, command=self._open_script_file)
        btn_open.pack(side="left", padx=(0, 6))

        btn_save = CleanButton(ed_actions, style="ghost", text="💾 Save", width=75, height=28, command=self._save_script_file)
        btn_save.pack(side="left", padx=(0, 6))

        btn_p400 = CleanButton(ed_actions, style="subtle", text="+ [PAUSE: 400ms]", width=120, height=28, command=lambda: self._insert_pause(400))
        btn_p400.pack(side="left", padx=(0, 6))

        btn_p800 = CleanButton(ed_actions, style="subtle", text="+ [PAUSE: 800ms]", width=120, height=28, command=lambda: self._insert_pause(800))
        btn_p800.pack(side="left")

        # --- RIGHT PANEL: Voice Cast & Synthesis Studio ---
        settings_col = ctk.CTkFrame(self.main_split, fg_color="transparent", width=440)
        settings_col.pack(side="right", fill="both", padx=(9, 0))
        settings_col.pack_propagate(False)

        # Voice engine card
        speakers_card = ctk.CTkFrame(
            settings_col,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        speakers_card.pack(fill="x", pady=(0, 8))

        engine_row = ctk.CTkFrame(speakers_card, fg_color="transparent")
        engine_row.pack(fill="x", padx=14, pady=(12, 6))

        engine_lbl = ctk.CTkLabel(engine_row, text="Voice Engine:", font=HeartTheme.FONT_SMALL_BOLD, text_color=HeartTheme.TEXT_MAIN)
        engine_lbl.pack(side="left", padx=(0, 8))

        self.engine_combo = ctk.CTkComboBox(
            engine_row,
            values=[
                "☁️ Microsoft Neural English (Online — 8 Expressive Voices)",
                "🎙️ Piper Neural English (100% Offline — Lessac, Amy, Ryan, Alan)"
            ],
            height=28,
            corner_radius=14,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            border_color=HeartTheme.BORDER_CARD,
            button_color=HeartTheme.PRIMARY,
            button_hover_color=HeartTheme.PRIMARY_HOVER,
            text_color=HeartTheme.TEXT_MAIN,
            font=HeartTheme.FONT_SMALL,
            dropdown_font=HeartTheme.FONT_SMALL,
            dropdown_text_color=HeartTheme.TEXT_MAIN,
            command=self._on_engine_change
        )
        self.engine_combo.pack(side="left", fill="x", expand=True)
        self.engine_combo.set("☁️ Microsoft Neural English (Online — 8 Expressive Voices)")

        self.speakers_container = ctk.CTkFrame(
            speakers_card,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            corner_radius=10
        )
        self.speakers_container.pack(fill="x", padx=14, pady=(0, 12))

        # Background Ambience / Music Card
        bg_card = ctk.CTkFrame(
            settings_col,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        bg_card.pack(fill="x", pady=(0, 8))

        bg_header = ctk.CTkFrame(bg_card, fg_color="transparent")
        bg_header.pack(fill="x", padx=14, pady=(10, 4))

        bg_title = ctk.CTkLabel(bg_header, text="🎵 Background Music & Ambience", font=HeartTheme.FONT_SMALL_BOLD, text_color=HeartTheme.TEXT_MAIN)
        bg_title.pack(side="left")

        bg_file_row = ctk.CTkFrame(bg_card, fg_color="transparent")
        bg_file_row.pack(fill="x", padx=14, pady=(0, 6))

        self.bg_file_lbl = ctk.CTkLabel(bg_file_row, text="No track selected (optional)", font=HeartTheme.FONT_TINY, text_color=HeartTheme.TEXT_MUTED, anchor="w")
        self.bg_file_lbl.pack(side="left", fill="x", expand=True)

        self.btn_select_bg = CleanButton(bg_file_row, style="subtle", text="Select File...", width=95, height=26, command=self._select_bg_music)
        self.btn_select_bg.pack(side="right")

        bg_vol_row = ctk.CTkFrame(bg_card, fg_color="transparent")
        bg_vol_row.pack(fill="x", padx=14, pady=(0, 10))

        self.vol_lbl = ctk.CTkLabel(bg_vol_row, text="Vol: 15%", font=HeartTheme.FONT_TINY, text_color=HeartTheme.TEXT_MUTED, width=50)
        self.vol_lbl.pack(side="left")

        self.vol_slider = ctk.CTkSlider(
            bg_vol_row,
            from_=1,
            to=100,
            number_of_steps=99,
            height=12,
            progress_color=HeartTheme.PRIMARY,
            button_color=HeartTheme.PRIMARY,
            button_hover_color=HeartTheme.PRIMARY_HOVER,
            fg_color=HeartTheme.PROGRESS_BG,
            command=self._on_volume_change
        )
        self.vol_slider.set(15)
        self.vol_slider.pack(side="left", fill="x", expand=True, padx=6)

        self.btn_bg_preview = CleanButton(bg_vol_row, style="ghost", text="▶ Test", width=65, height=26, command=self._toggle_bg_preview)
        self.btn_bg_preview.pack(side="right")

        # Generation Action Card
        gen_card = ctk.CTkFrame(
            settings_col,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        gen_card.pack(fill="x", pady=(0, 4))

        gen_inner = ctk.CTkFrame(gen_card, fg_color="transparent")
        gen_inner.pack(fill="x", padx=14, pady=12)

        self.generate_btn = CleanButton(
            gen_inner,
            style="primary",
            text="🎙️ Generate Full Podcast   Ctrl+G",
            height=40,
            command=self._start_generation
        )
        self.generate_btn.pack(fill="x", pady=(0, 6))

        self.gen_progress = ctk.CTkProgressBar(
            gen_inner,
            height=8,
            corner_radius=4,
            progress_color=HeartTheme.PRIMARY,
            fg_color=HeartTheme.PROGRESS_BG
        )
        self.gen_progress.pack(fill="x", pady=(0, 4))
        self.gen_progress.set(0.0)

        self.status_lbl = ctk.CTkLabel(
            gen_inner,
            text="Ready to generate. No duration limits.",
            font=HeartTheme.FONT_TINY,
            text_color=HeartTheme.TEXT_MUTED
        )
        self.status_lbl.pack(anchor="w")

        # 4. Audio Player Widget (Bottom)
        self.player_widget = AudioPlayerWidget(self, audio_processor=self.audio_processor)
        self.player_widget.pack(fill="x", padx=18, pady=(0, 14), side="bottom")

    def _bind_keyboard_shortcuts(self):
        self.bind_all("<Control-g>", lambda e: self._start_generation())
        self.bind_all("<Control-Return>", lambda e: self._start_generation())
        self.bind_all("<Control-s>", lambda e: self._save_script_file())
        self.bind_all("<Control-o>", lambda e: self._open_script_file())
        self.bind_all("<F1>", lambda e: self._show_ssml_guide())
        self.bind_all("<Escape>", lambda e: self._cancel_generation() if self.is_generating else None)

    def _toggle_school_mode(self):
        self._school_mode = not self._school_mode
        if self._school_mode:
            self.btn_school.configure(fg_color=HeartTheme.PRIMARY, text_color="#FFFFFF", text="🏫 School Mode ✔")
            self.badge.pack_forget()
            self.school_badge.pack(side="left", padx=(8, 0))
            self.engine_combo.configure(values=["🎙️ Piper Neural English (100% Offline — Lessac, Amy, Ryan, Alan)"])
            self.engine_combo.set("🎙️ Piper Neural English (100% Offline — Lessac, Amy, Ryan, Alan)")
            self._on_engine_change("🎙️ Piper Neural English (100% Offline — Lessac, Amy, Ryan, Alan)")
        else:
            self.btn_school.configure(fg_color="#FFFFFF", text_color=HeartTheme.TEXT_MAIN, text="🏫 School Mode")
            self.school_badge.pack_forget()
            self.badge.pack(side="left")
            all_engines = [
                "☁️ Microsoft Neural English (Online — 8 Expressive Voices)",
                "🎙️ Piper Neural English (100% Offline — Lessac, Amy, Ryan, Alan)"
            ]
            self.engine_combo.configure(values=all_engines)

    def _on_engine_change(self, choice):
        if "Piper" in choice:
            self.tts_engine = self.piper_engine
            self.badge.configure(text="Piper Neural English (100% Offline, Local & Private)")
        else:
            self.tts_engine = self.edge_engine
            self.badge.configure(text="Microsoft Neural English (Online — Studio Expressive Voices)")
        self._refresh_speakers_ui()

    def _refresh_speakers_ui(self):
        for widget in self.speakers_container.winfo_children():
            widget.destroy()

        speakers = self.current_script.speakers
        if not speakers:
            lbl = ctk.CTkLabel(self.speakers_container, text="No speakers defined in script.", font=HeartTheme.FONT_TINY, text_color=HeartTheme.TEXT_MUTED)
            lbl.pack(pady=8)
            return

        available_speakers = self.tts_engine.get_speakers()
        voice_ids = [s["id"] for s in available_speakers]
        voice_display = [f"{s['name']}" for s in available_speakers]

        for spk_idx, (spk_name, spk_cfg) in enumerate(speakers.items()):
            row = ctk.CTkFrame(self.speakers_container, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=5)

            name_lbl = ctk.CTkLabel(row, text=f"👤 {spk_name}:", font=HeartTheme.FONT_SMALL_BOLD, text_color=HeartTheme.TEXT_MAIN, width=80, anchor="w")
            name_lbl.pack(side="left")

            # Check if current spk_cfg.voice_id belongs to the active engine
            match_idx = -1
            for idx, vid in enumerate(voice_ids):
                if vid.lower() == spk_cfg.voice_id.lower() or vid.lower() in spk_cfg.voice_id.lower():
                    match_idx = idx
                    break

            if match_idx == -1 and voice_ids:
                # Engine switched: reassign to a valid voice for this speaker
                match_idx = spk_idx % len(voice_ids)
                spk_cfg.voice_id = voice_ids[match_idx]

            combo = ctk.CTkComboBox(
                row,
                values=voice_display,
                height=26,
                font=HeartTheme.FONT_TINY,
                dropdown_font=HeartTheme.FONT_TINY,
                command=lambda val, name=spk_name: self._on_speaker_voice_change(name, val)
            )
            if voice_display and match_idx >= 0 and match_idx < len(voice_display):
                combo.set(voice_display[match_idx])
            combo.pack(side="left", fill="x", expand=True, padx=(4, 6))

            # Preview button: reads LIVE speaker voice dynamically
            btn_prev = CleanButton(
                row,
                style="subtle",
                text="▶",
                width=28,
                height=26
            )
            btn_prev.configure(command=lambda name=spk_name, btn=btn_prev: self._play_speaker_sample(name, btn))
            btn_prev.pack(side="right")

    def _on_speaker_voice_change(self, spk_name: str, choice: str):
        available = self.tts_engine.get_speakers()
        for s in available:
            if s["name"] == choice or s["id"] == choice:
                if spk_name in self.current_script.speakers:
                    self.current_script.speakers[spk_name].voice_id = s["id"]
                break

    def _play_speaker_sample(self, spk_name: str, btn: CleanButton):
        if spk_name not in self.current_script.speakers:
            return
        spk_cfg = self.current_script.speakers[spk_name]
        voice_id = spk_cfg.voice_id

        btn.configure(text="⏳", state="disabled")
        self._set_status(f"Generating preview for {spk_name} ({voice_id})...")

        def on_start():
            self.safe_after(lambda: btn.configure(text="🔊"))

        def on_finish():
            self.safe_after(lambda: btn.configure(text="▶", state="normal"))
            self._set_status("Ready.")

        def on_error(err):
            self.safe_after(lambda: btn.configure(text="▶", state="normal"))
            self._set_status(f"Preview notice: {err}")

        self.voice_preview_manager.play_sample(
            voice_id,
            self.tts_engine,
            on_start_callback=on_start,
            on_finish_callback=on_finish,
            on_error_callback=on_error
        )

    def _set_status(self, text: str):
        self.safe_after(lambda: self.status_lbl.configure(text=text))

    def _on_structure_selected(self, val: str):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if "1 Voice" in val:
            path = os.path.join(base_dir, "examples", "template_1voice.txt")
        elif "2 Voices" in val:
            path = os.path.join(base_dir, "examples", "template_2voices.txt")
        else:
            path = os.path.join(base_dir, "examples", "template_3voices.txt")

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._load_script_content(content)

    def _load_default_sample(self):
        self._on_structure_selected("2 Voices (Dialogue)")

    def _load_script_content(self, text: str):
        self._suppress_script_sync = True
        self.script_textbox.delete("1.0", "end")
        if self.editor_mode == "clean":
            clean_text = self._extract_clean_dialogue(text)
            self.script_textbox.insert("1.0", clean_text)
        else:
            self.script_textbox.insert("1.0", text)
        self._suppress_script_sync = False
        self._sync_script_from_ui()

    def _extract_clean_dialogue(self, full_text: str) -> str:
        lines = full_text.splitlines()
        dialogue_lines = []
        is_dialogue = False
        for line in lines:
            if line.startswith("---") or line.startswith("==="):
                is_dialogue = True
                continue
            if is_dialogue:
                dialogue_lines.append(line)
        return "\n".join(dialogue_lines).strip() if dialogue_lines else full_text

    def _compose_full_script(self, dialogue_text: str) -> str:
        header_lines = [
            f"[TITLE: {self.current_script.title}]",
            f"[FORMAT: {self.current_script.format_info}]",
            "[VOICES]"
        ]
        for name, cfg in self.current_script.speakers.items():
            header_lines.append(f"- {name}: {cfg.description or 'Podcast Host'}")

        header_lines.append("\n[VOICE_CONFIG]")
        for name, cfg in self.current_script.speakers.items():
            pan_str = f"{int(round(cfg.pan * 100)):+d}%"
            header_lines.append(f"{name}: voice={cfg.voice_id} pan={pan_str} speed={cfg.speed}")

        header_lines.append("\n---\n")
        header_lines.append(dialogue_text)
        return "\n".join(header_lines)

    def _on_editor_mode_change(self, mode: str):
        current_content = self.script_textbox.get("1.0", "end-1c")
        if "Clean" in mode:
            self.editor_mode = "clean"
            self._load_script_content(current_content)
        else:
            self.editor_mode = "full"
            full = self._compose_full_script(current_content)
            self._load_script_content(full)

    def _on_script_text_changed(self, event=None):
        if self._suppress_script_sync:
            return
        self.script_textbox.edit_modified(False)
        self._sync_script_from_ui()

    def _sync_script_from_ui(self):
        content = self.script_textbox.get("1.0", "end-1c")
        if self.editor_mode == "clean":
            full = self._compose_full_script(content)
        else:
            full = content
        self.current_script = self.script_parser.parse(full)
        self._refresh_speakers_ui()

    def _insert_pause(self, ms: int):
        self.script_textbox.insert("insert", f"\n[PAUSE: {ms}ms]\n")
        self._sync_script_from_ui()

    def _open_script_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Script (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self._load_script_content(f.read())

    def _save_script_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Script (*.txt)", "*.txt")])
        if path:
            content = self.script_textbox.get("1.0", "end-1c")
            if self.editor_mode == "clean":
                content = self._compose_full_script(content)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", "Script saved successfully!")

    def _select_bg_music(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files (*.mp3;*.wav;*.ogg;*.flac)", "*.mp3;*.wav;*.ogg;*.flac")])
        if path:
            self.bg_music_path = path
            self.bg_file_lbl.configure(text=os.path.basename(path), text_color=HeartTheme.TEXT_MAIN)
            try:
                data, sr = sf.read(path, dtype="float32")
                if sr != 22050:
                    data = scipy.signal.resample(data, int(len(data) * (22050 / sr)))
                self.bg_music_audio_data = data
            except Exception as e:
                messagebox.showerror("Audio Error", f"Could not load audio track: {e}")

    def _on_volume_change(self, val):
        self.bg_music_volume = float(val) / 100.0
        self.vol_lbl.configure(text=f"Vol: {int(val)}%")

    def _toggle_bg_preview(self):
        # Quick preview
        pass

    def _start_generation(self):
        if self.is_generating:
            return

        self._sync_script_from_ui()
        if not self.current_script.segments:
            messagebox.showwarning("Empty Script", "Please enter script dialogue before generating.")
            return

        self.is_generating = True
        self.cancel_requested = False
        self.generate_btn.configure(text="■ Cancel Generation", style="danger", command=self._cancel_generation)
        self.gen_progress.set(0.0)

        thread = threading.Thread(target=self._generation_worker, daemon=True)
        thread.start()

    def _cancel_generation(self):
        self.cancel_requested = True
        self._set_status("Cancelling generation...")

    def _generation_worker(self):
        segments = self.current_script.segments
        total = len(segments)
        audio_blocks: List[np.ndarray] = []

        try:
            for idx, seg in enumerate(segments):
                if self.cancel_requested:
                    self._set_status("Generation cancelled.")
                    break

                self.safe_after(lambda i=idx, t=total: self.gen_progress.set((i + 1) / t))
                self._set_status(f"Generating segment {idx+1}/{total} ({seg.speaker or 'Pause'})...")

                if seg.segment_type == "pause":
                    silence = self.audio_processor.generate_silence(seg.pause_ms)
                    stereo_silence = self.audio_processor.apply_pan(silence, 0.0)
                    audio_blocks.append(stereo_silence)
                elif seg.segment_type == "dialogue":
                    spk_cfg = self.current_script.speakers.get(seg.speaker)
                    curr_voice = spk_cfg.voice_id if spk_cfg else seg.voice_id
                    curr_pan = spk_cfg.pan if spk_cfg else seg.pan
                    curr_speed = spk_cfg.speed if spk_cfg else seg.speed
                    curr_pitch = spk_cfg.pitch if spk_cfg else seg.pitch

                    raw_audio = self.tts_engine.synthesize_utterance(
                        seg.text,
                        voice_id=curr_voice,
                        speed=curr_speed,
                        pitch=curr_pitch
                    )
                    stereo_seg = self.audio_processor.apply_pan(raw_audio, curr_pan)
                    audio_blocks.append(stereo_seg)

            if not self.cancel_requested and audio_blocks:
                self._set_status("Assembling and mastering broadcast stereo audio...")
                full_stereo = np.concatenate(audio_blocks, axis=1)

                # Mix background music if selected
                if self.bg_music_audio_data is not None:
                    self._set_status("Mixing background ambience loop...")
                    full_stereo = self.audio_processor.mix_background_track(
                        full_stereo,
                        self.bg_music_audio_data,
                        volume=self.bg_music_volume,
                        loop=self.bg_music_loop
                    )

                # Normalize to EBU R128 (-16 LUFS)
                self._set_status("Normalizing loudness to EBU R128 (-16 LUFS)...")
                mastered_audio = self.audio_processor.normalize_loudness(full_stereo, target_lufs=-16.0)

                self.safe_after(lambda: self.player_widget.load_audio(mastered_audio, title=self.current_script.title))
                self._set_status("Podcast generation complete! Ready to play or export.")
                self.safe_after(lambda: messagebox.showinfo("Complete", "Your podcast has been generated with heart!\nYou can now listen or export as MP3."))

        except Exception as e:
            self._set_status(f"Error during generation: {e}")
            self.safe_after(lambda err=e: messagebox.showerror("Generation Error", f"Synthesis failed: {err}"))

        finally:
            self.is_generating = False
            self.safe_after(lambda: self.generate_btn.configure(text="🎙️ Generate Full Podcast   Ctrl+G", style="primary", command=self._start_generation))

    def _show_ssml_guide(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        guide_path = os.path.join(base_dir, "docs", "SSML_GUIDE.md")
        content = "SSML Prosody Guide\nUse <break time='500ms'/> for pauses."
        if os.path.exists(guide_path):
            with open(guide_path, "r", encoding="utf-8") as f:
                content = f.read()
        self._open_text_viewer("📖 SSML Prosody Guide", content)

    def _show_llm_guide(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        guide_path = os.path.join(base_dir, "docs", "LLM_PROMPT_GUIDE.md")
        content = "LLM Master Prompt Guide for Podcasts with Heart"
        if os.path.exists(guide_path):
            with open(guide_path, "r", encoding="utf-8") as f:
                content = f.read()
        self._open_text_viewer("💡 LLM Script Prompt Guide", content)

    def _show_components_manager(self):
        ComponentsManagerModal(self, on_update_callback=self._refresh_speakers_ui)

    def _open_text_viewer(self, title: str, text: str):
        viewer = ctk.CTkToplevel(self)
        viewer.title(title)
        viewer.geometry("720x560")
        viewer.configure(fg_color=HeartTheme.BG_MAIN)
        viewer.transient(self)

        txt = ctk.CTkTextbox(viewer, fg_color=HeartTheme.BG_CARD, font=HeartTheme.FONT_BODY, wrap="word")
        txt.pack(fill="both", expand=True, padx=16, pady=16)
        txt.insert("1.0", text)
        txt.configure(state="disabled")
