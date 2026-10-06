"""
Main Window for Podcasts with Heart.
Clean, modern, accessible desktop application for creating educational English podcasts.
Built with CustomTkinter and styled in HeartTheme (Pastel Red & Warm Rose).
Faithful parity with Podcasts amb Matxa UI/UX, features, and workflows.
"""

import os
import re
import sys
import time
import queue
import threading
import tempfile
import ctypes
import webbrowser
from typing import Optional, Dict, Any, List

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import numpy as np
import soundfile as sf
import scipy.signal

# High-DPI support on Windows
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from ui.theme import HeartTheme
from ui.components import CleanButton, PillSelector
from ui.player_widget import AudioPlayerWidget
from ui.components_modal import ComponentsManagerModal
from ui.version_check_modal import VersionCheckModal, APP_VERSION

from core.script_parser import ScriptParser, PodcastScript, SpeakerConfig, PodcastSegment
from core.audio_processor import AudioProcessor
from core.text_normalizer import EnglishTextNormalizer
from core.kokoro_engine import KokoroEnglishEngine
from core.piper_engine import PiperEnglishEngine
from core.edge_tts_engine import MicrosoftNeuralEnglishEngine
from core.voice_preview import VoicePreviewManager
from core.model_downloader import ModelDownloader

class MainWindow(ctk.CTk):
    """Main Application Window for Podcasts with Heart."""

    KOKORO_VOICE_DESCRIPTIONS = {
        "af_heart": "Heart — US English (Studio Flagship, warm & expressive)",
        "af_bella": "Bella — US English (Warm, friendly & natural)",
        "af_nicole": "Nicole — US English (Conversational & relaxed)",
        "af_sarah": "Sarah — US English (Poised & articulate narrator)",
        "af_sky": "Sky — US English (Dynamic & fresh youth)",
        "am_adam": "Adam — US English (Deep, resonant & confident)",
        "am_michael": "Michael — US English (Authentic & direct)",
        "bf_emma": "Emma — British English (Refined, poised & elegant)",
        "bf_isabella": "Isabella — British English (Gentle & narrative)",
        "bm_george": "George — British English (Classic storyteller & documentaries)",
        "bm_lewis": "Lewis — British English (Distinct, engaging & crisp)"
    }

    PIPER_VOICE_DESCRIPTIONS = {
        "lessac": "Lessac — US English (Academic, clear & pedagogical)",
        "amy": "Amy — US English (Natural, conversational & warm)",
        "ryan": "Ryan — US English (Dynamic, energetic & crisp)",
        "alan": "Alan — British English (Classic, articulate & storytelling)"
    }

    CLOUD_VOICE_DESCRIPTIONS = {
        "jenny": "Jenny — Microsoft Neural (US English, warm & conversational)",
        "guy": "Guy — Microsoft Neural (US English, dynamic & clear)",
        "aria": "Aria — Microsoft Neural (US English, expressive storyteller)",
        "davis": "Davis — Microsoft Neural (US English, academic & calm)",
        "sonia": "Sonia — Microsoft Neural (British English, articulate)",
        "ryan": "Ryan — Microsoft Neural (British English, classic narrator)",
        "libby": "Libby — Microsoft Neural (British English, lively & youthful)",
        "natasha": "Natasha — Microsoft Neural (Australian English, friendly)"
    }

    def __init__(self):
        super().__init__()

        self.title(f"Podcasts with Heart v{APP_VERSION}")
        self._fit_window_to_work_area()

        ctk.set_appearance_mode("light")
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self._set_app_icon()

        self._ui_queue = queue.Queue()
        self.after(35, self._process_ui_queue)

        # Core engines
        self.script_parser = ScriptParser()
        self.text_normalizer = EnglishTextNormalizer()
        self.kokoro_engine = KokoroEnglishEngine()
        self.piper_engine = PiperEnglishEngine()
        self.edge_engine = MicrosoftNeuralEnglishEngine()
        self.tts_engine = self.kokoro_engine # Flagship Studio Heart Engine by default
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

    def _get_logical_work_area(self):
        """Returns work area in logical CustomTkinter units."""
        try:
            window_scale = max(float(self._get_window_scaling()), 0.1)
        except Exception:
            window_scale = 1.0

        physical_w = self.winfo_screenwidth()
        physical_h = self.winfo_screenheight()

        if sys.platform.startswith("win"):
            try:
                from ctypes import wintypes
                rect = wintypes.RECT()
                SPI_GETWORKAREA = 0x0030
                ok = ctypes.windll.user32.SystemParametersInfoW(
                    SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
                )
                if ok:
                    physical_w = rect.right - rect.left
                    physical_h = rect.bottom - rect.top
            except Exception:
                pass

        return int(physical_w / window_scale), int(physical_h / window_scale)

    def _fit_window_to_work_area(self):
        """Prevents window from exceeding screen work area under Windows display scaling."""
        work_w, work_h = self._get_logical_work_area()
        target_w = max(1000, min(1280, work_w - 24))
        target_h = max(620, min(840, work_h - 24))

        min_w = min(1020, target_w)
        min_h = min(620, target_h)
        self.minsize(min_w, min_h)
        self.geometry(f"{target_w}x{target_h}")

    def _set_app_icon(self):
        """Sets application window and taskbar icons."""
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

        # Header icon if available
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        png_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(png_path):
            try:
                pil_icon = Image.open(png_path)
                self._header_icon_img = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(24, 24))
                icon_lbl = ctk.CTkLabel(brand_frame, image=self._header_icon_img, text="")
                icon_lbl.pack(side="left", padx=(0, 8))
            except Exception:
                pass

        app_title = ctk.CTkLabel(
            brand_frame,
            text="Podcasts with Heart",
            font=("Segoe UI", 16, "bold"),
            text_color=HeartTheme.TEXT_MAIN
        )
        app_title.pack(side="left", padx=(0, 6))

        version_badge = ctk.CTkLabel(
            brand_frame,
            text=f"v{APP_VERSION}",
            font=HeartTheme.FONT_TINY,
            fg_color=HeartTheme.PRIMARY_LIGHT,
            text_color=HeartTheme.PRIMARY,
            corner_radius=8,
            padx=7,
            pady=1
        )
        version_badge.pack(side="left", padx=(0, 8))

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
            text="❤️ Kokoro-TTS (100% Offline Heart Engine — 11 Studio Voices)",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        self.badge.pack(side="left")

        self.school_badge = ctk.CTkLabel(
            brand_frame,
            text="🛡️ School Mode: 0% Internet Data (GDPR & Privacy Protected)",
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

        scale_lbl = ctk.CTkLabel(
            help_frame,
            text="Size:",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_MUTED
        )
        scale_lbl.pack(side="left", padx=(0, 4))

        self.scale_combo = ctk.CTkComboBox(
            help_frame,
            values=["100%", "125%", "150%", "175%", "200%"],
            width=80,
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
            command=self._on_scale_change
        )
        self.scale_combo.pack(side="left", padx=(0, 10))
        self.scale_combo.set("100%")

        btn_ssml = CleanButton(
            help_frame,
            style="ghost",
            text="SSML Guide",
            width=90,
            height=28,
            command=self._show_ssml_guide
        )
        btn_ssml.pack(side="left", padx=3)

        btn_llm = CleanButton(
            help_frame,
            style="ghost",
            text="LLM Prompt",
            width=95,
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

        btn_version = CleanButton(
            help_frame,
            style="ghost",
            text="🔄 Check Updates",
            width=120,
            height=28,
            command=self._show_version_check_modal
        )
        btn_version.pack(side="left", padx=3)

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
        format_label.pack(side="left", padx=(4, 10))

        self.structure_selector = PillSelector(
            top_bar,
            values=["👤 1 Voice (Monologue)", "👥 2 Voices (Dialogue)", "👥👥 3 Voices (Roundtable)"],
            default_val="👥 2 Voices (Dialogue)",
            command=self._on_structure_selected,
            height=32,
            font_size=10
        )
        self.structure_selector.pack(side="left")

        # 3. Footer Bar with authorship and licenses
        footer = ctk.CTkFrame(
            self,
            fg_color=HeartTheme.BG_CARD,
            height=32,
            corner_radius=0,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        footer_box = ctk.CTkFrame(footer, fg_color="transparent")
        footer_box.pack(anchor="center", pady=6)

        lbl_author = ctk.CTkLabel(
            footer_box,
            text="Created through intentional coding with Google Antigravity by Miquel Àngel Fuentes · ",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        lbl_author.pack(side="left")

        lbl_code = ctk.CTkLabel(
            footer_box,
            text="Code License: ",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        lbl_code.pack(side="left")

        link_agpl = ctk.CTkLabel(
            footer_box,
            text="AGPL v3",
            font=(HeartTheme.FONT_FAMILY, 10, "underline"),
            text_color=HeartTheme.PRIMARY,
            cursor="hand2"
        )
        link_agpl.pack(side="left")
        link_agpl.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://www.gnu.org/licenses/agpl-3.0.en.html"))

        lbl_sep = ctk.CTkLabel(
            footer_box,
            text=" · Contents: ",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        lbl_sep.pack(side="left")

        link_cc = ctk.CTkLabel(
            footer_box,
            text="CC BY-SA 4.0",
            font=(HeartTheme.FONT_FAMILY, 10, "underline"),
            text_color=HeartTheme.PRIMARY,
            cursor="hand2"
        )
        link_cc.pack(side="left")
        link_cc.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://creativecommons.org/licenses/by-sa/4.0/"))

        lbl_credits = ctk.CTkLabel(
            footer_box,
            text=" · Models: Kokoro-82M Heart Engine & Piper Neural",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        lbl_credits.pack(side="left")

        # 4. Main Studio Split Container
        content_container = ctk.CTkFrame(self, fg_color="transparent")
        content_container.pack(fill="both", expand=True, padx=18, pady=(8, 8))

        # --- LEFT PANEL: Script Studio ---
        left_panel = ctk.CTkFrame(
            content_container,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._build_editor_panel(left_panel)

        # --- RIGHT PANEL: Voice Cast & Synthesis Studio ---
        right_panel = ctk.CTkFrame(content_container, fg_color="transparent", width=540)
        right_panel.pack(side="right", fill="both", padx=(10, 0))
        right_panel.pack_propagate(False)

        self._build_control_panel(right_panel)

    def _build_editor_panel(self, parent):
        # 1. Editor top toolbar
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", padx=18, pady=(14, 8))

        section_lbl = ctk.CTkLabel(
            toolbar,
            text="📝 Script Studio",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        section_lbl.pack(side="left")

        actions_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_box.pack(side="right")

        # 5-minute showcase button
        btn_sample = CleanButton(
            actions_box,
            style="primary",
            text="🌟 5-Min Script",
            height=28,
            command=self._load_default_sample
        )
        btn_sample.pack(side="left", padx=3)

        # Templates dropdown
        self.template_opt = ctk.CTkOptionMenu(
            actions_box,
            values=[
                "Templates...",
                "🌟 5-Min Showcase (App features & architecture)",
                "👤 1 Voice: How it works (Monologue)",
                "👥 2 Voices: How it works (Dialogue)",
                "👥👥 3 Voices: How it works (Roundtable)"
            ],
            width=150,
            height=28,
            corner_radius=14,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            button_color=HeartTheme.PRIMARY,
            button_hover_color=HeartTheme.PRIMARY_HOVER,
            text_color=HeartTheme.TEXT_MAIN,
            font=HeartTheme.FONT_SMALL,
            dropdown_font=HeartTheme.FONT_SMALL,
            dropdown_text_color=HeartTheme.TEXT_MAIN,
            command=self._on_template_selected
        )
        self.template_opt.pack(side="left", padx=3)
        self.template_opt.set("Templates...")

        btn_open = CleanButton(
            actions_box,
            style="ghost",
            text="Open",
            width=65,
            height=28,
            command=self._open_script_file
        )
        btn_open.pack(side="left", padx=3)

        btn_save = CleanButton(
            actions_box,
            style="ghost",
            text="Save",
            width=65,
            height=28,
            command=self._save_script_file
        )
        btn_save.pack(side="left", padx=3)

        # 2. Episode Title field
        title_box = ctk.CTkFrame(parent, fg_color="transparent")
        title_box.pack(fill="x", padx=18, pady=(0, 8))

        lbl_title = ctk.CTkLabel(
            title_box,
            text="Podcast Title:",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_SECONDARY
        )
        lbl_title.pack(side="left", padx=(0, 8))

        self.title_entry = ctk.CTkEntry(
            title_box,
            placeholder_text="Enter podcast episode title...",
            height=30,
            corner_radius=8,
            fg_color=HeartTheme.ENTRY_BG,
            border_color=HeartTheme.ENTRY_BORDER,
            text_color=HeartTheme.TEXT_MAIN,
            font=("Segoe UI", 11, "bold")
        )
        self.title_entry.pack(side="left", fill="x", expand=True)
        self.title_entry.bind("<KeyRelease>", self._on_title_modified)

        # 3. Script text editor
        self.script_textbox = ctk.CTkTextbox(
            parent,
            fg_color=HeartTheme.ENTRY_BG,
            border_color=HeartTheme.ENTRY_BORDER,
            border_width=1,
            text_color=HeartTheme.TEXT_MAIN,
            font=HeartTheme.FONT_MONO,
            wrap="word",
            corner_radius=10,
            undo=True
        )
        self.script_textbox.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        self.script_textbox.bind("<KeyRelease>", self._on_script_modified)

        # 4. Status and word count bar
        statusbar = ctk.CTkFrame(parent, fg_color="transparent")
        statusbar.pack(fill="x", padx=18, pady=(0, 12))

        self.stats_lbl = ctk.CTkLabel(
            statusbar,
            text="0 words · ~00:00 min · 0 voices",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        self.stats_lbl.pack(side="left")

        # Clean Dialogue vs Full Code Mode Toggle
        self.btn_toggle_view = CleanButton(
            statusbar,
            style="subtle",
            text="📝 Clean dialogue mode (active)",
            height=24,
            command=self._toggle_editor_mode
        )
        self.btn_toggle_view.pack(side="right")

    def _build_control_panel(self, parent):
        # 1. Audio Player widget anchored at bottom
        self.player_widget = AudioPlayerWidget(parent, self.audio_processor, height=1)
        self.player_widget.pack(side="bottom", fill="x", pady=(8, 0))

        # 2. Scrollable settings and voice cast studio
        self.controls_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            corner_radius=0,
            height=1
        )
        self.controls_scroll.pack(side="top", fill="both", expand=True)

        # 1. Voice Cast & Stereo Spatialization Card
        speakers_card = ctk.CTkFrame(
            self.controls_scroll,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        speakers_card.pack(fill="x", pady=(0, 8))

        spk_header = ctk.CTkFrame(speakers_card, fg_color="transparent", height=1)
        spk_header.pack(fill="x", padx=18, pady=(10, 4))

        spk_title = ctk.CTkLabel(
            spk_header,
            text="👥 Voice Cast & Stereo Spatialization",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        spk_title.pack(side="left")

        # Engine selector
        engine_row = ctk.CTkFrame(speakers_card, fg_color="transparent", height=1)
        engine_row.pack(fill="x", padx=18, pady=(2, 8))

        engine_lbl = ctk.CTkLabel(
            engine_row,
            text="Engine:",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_MUTED
        )
        engine_lbl.pack(side="left", padx=(0, 8))

        self.engine_combo = ctk.CTkComboBox(
            engine_row,
            values=[
                "❤️ Kokoro-TTS (100% Offline — Studio Quality Heart Engine)",
                "🎙️ Piper Neural English (100% Offline — Fast & Lightweight)",
                "☁️ Microsoft Neural English (Online — 8 Expressive Cloud Voices)"
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
        self.engine_combo.set("❤️ Kokoro-TTS (100% Offline — Studio Quality Heart Engine)")

        # Dynamic speakers container
        self.speakers_container = ctk.CTkFrame(
            speakers_card,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            corner_radius=10,
            height=1
        )
        self.speakers_container.pack(fill="x", padx=18, pady=(0, 10))

        # 2. Background Ambience / Music Card
        bg_card = ctk.CTkFrame(
            self.controls_scroll,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        bg_card.pack(fill="x", pady=(0, 8))

        bg_header = ctk.CTkFrame(bg_card, fg_color="transparent", height=1)
        bg_header.pack(fill="x", padx=18, pady=(10, 4))

        bg_title = ctk.CTkLabel(
            bg_header,
            text="🎵 Background Music & Ambience",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        bg_title.pack(side="left")

        # Row 1: File selection
        file_row = ctk.CTkFrame(bg_card, fg_color="transparent", height=1)
        file_row.pack(fill="x", padx=18, pady=(2, 6))

        self.btn_select_bg = CleanButton(
            file_row,
            style="subtle",
            text="📂 Choose Audio...",
            height=28,
            command=self._select_bg_audio
        )
        self.btn_select_bg.pack(side="left", padx=(0, 8))

        self.lbl_bg_file = ctk.CTkLabel(
            file_row,
            text="No background track selected",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED,
            anchor="w"
        )
        self.lbl_bg_file.pack(side="left", fill="x", expand=True)

        self.btn_clear_bg = CleanButton(
            file_row,
            style="ghost",
            text="✕",
            width=28,
            height=28,
            state="disabled",
            command=self._clear_bg_audio
        )
        self.btn_clear_bg.pack(side="right", padx=(4, 0))

        # Row 2: Loop checkbox + Preview button
        ctrl_row = ctk.CTkFrame(bg_card, fg_color="transparent", height=1)
        ctrl_row.pack(fill="x", padx=18, pady=(2, 6))

        self.cb_bg_loop = ctk.CTkCheckBox(
            ctrl_row,
            text="🔁 Play in continuous loop",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            checkmark_color=HeartTheme.TEXT_ON_PRIMARY,
            fg_color=HeartTheme.PRIMARY,
            hover_color=HeartTheme.PRIMARY_HOVER,
            corner_radius=4,
            command=self._on_bg_loop_toggle
        )
        self.cb_bg_loop.pack(side="left")
        self.cb_bg_loop.select()

        self.btn_bg_preview = CleanButton(
            ctrl_row,
            style="subtle",
            text="▶ Test",
            height=26,
            width=75,
            state="disabled",
            command=self._toggle_bg_preview
        )
        self.btn_bg_preview.pack(side="right")

        # Row 3: Volume label + Live Volume Slider
        vol_row = ctk.CTkFrame(bg_card, fg_color="transparent", height=1)
        vol_row.pack(fill="x", padx=18, pady=(2, 10))

        self.lbl_bg_volume = ctk.CTkLabel(
            vol_row,
            text="Vol: 15%",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_MAIN,
            width=80,
            anchor="w"
        )
        self.lbl_bg_volume.pack(side="left", padx=(0, 8))

        self.slider_bg_volume = ctk.CTkSlider(
            vol_row,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            height=14,
            progress_color=HeartTheme.PRIMARY,
            button_color=HeartTheme.PRIMARY,
            button_hover_color=HeartTheme.PRIMARY_HOVER,
            fg_color=HeartTheme.PROGRESS_BG,
            command=self._on_bg_volume_change
        )
        self.slider_bg_volume.pack(side="left", fill="x", expand=True)
        self.slider_bg_volume.set(0.15)

        # 3. Audio Mastering & Generation Action Card
        gen_card = ctk.CTkFrame(
            self.controls_scroll,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        gen_card.pack(fill="x", pady=(0, 2))

        gen_title = ctk.CTkLabel(
            gen_card,
            text="⚙ Audio Mastering & Production",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        gen_title.pack(anchor="w", padx=18, pady=(10, 4))

        # Inline options
        opts_row = ctk.CTkFrame(gen_card, fg_color="transparent", height=1)
        opts_row.pack(fill="x", padx=18, pady=(0, 8))

        self.cb_normalizer = ctk.CTkCheckBox(
            opts_row,
            text="Text Normalizer (Numbers, Currencies & Dates)",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            checkmark_color=HeartTheme.TEXT_ON_PRIMARY,
            fg_color=HeartTheme.PRIMARY,
            hover_color=HeartTheme.PRIMARY_HOVER,
            corner_radius=4
        )
        self.cb_normalizer.pack(side="left", padx=(0, 14))
        self.cb_normalizer.select()

        self.cb_lufs = ctk.CTkCheckBox(
            opts_row,
            text="EBU R128 (-16 LUFS Broadcast Standard)",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            checkmark_color=HeartTheme.TEXT_ON_PRIMARY,
            fg_color=HeartTheme.PRIMARY,
            hover_color=HeartTheme.PRIMARY_HOVER,
            corner_radius=4
        )
        self.cb_lufs.pack(side="left")
        self.cb_lufs.select()

        # Action Buttons
        btn_row = ctk.CTkFrame(gen_card, fg_color="transparent", height=1)
        btn_row.pack(fill="x", padx=18, pady=(0, 6))

        self.generate_btn = CleanButton(
            btn_row,
            style="primary",
            text="🎙️ Generate Full Podcast (Ctrl+G)",
            height=40,
            font=("Segoe UI", 12, "bold"),
            command=self._start_generation
        )
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = CleanButton(
            btn_row,
            style="danger",
            text="✕ Cancel",
            width=85,
            height=40,
            state="disabled",
            command=self._cancel_generation
        )
        self.cancel_btn.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            gen_card,
            height=6,
            corner_radius=3,
            progress_color=HeartTheme.PRIMARY,
            fg_color=HeartTheme.PROGRESS_BG
        )
        self.progress_bar.pack(fill="x", padx=18, pady=(3, 3))
        self.progress_bar.set(0.0)

        self.status_lbl = ctk.CTkLabel(
            gen_card,
            text="Ready to generate. No duration limits.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED
        )
        self.status_lbl.pack(anchor="w", padx=18, pady=(0, 10))

    def _bind_keyboard_shortcuts(self):
        self.bind_all("<Control-g>", lambda e: self._start_generation())
        self.bind_all("<Control-Return>", lambda e: self._start_generation())
        self.bind_all("<Control-s>", lambda e: self._save_script_file())
        self.bind_all("<Control-o>", lambda e: self._open_script_file())
        self.bind_all("<F1>", lambda e: self._show_ssml_guide())
        self.bind_all("<Escape>", lambda e: self._cancel_generation() if self.is_generating else None)

    def _on_scale_change(self, choice: str):
        mapping = {"100%": 1.0, "125%": 1.25, "150%": 1.5, "175%": 1.75, "200%": 2.0}
        factor = mapping.get(choice, 1.0)
        try:
            ctk.set_widget_scaling(factor)
            self._fit_window_to_work_area()
        except Exception as e:
            print(f"Error applying scaling: {e}")

    def _toggle_school_mode(self):
        self._school_mode = not self._school_mode
        if self._school_mode:
            self.btn_school.configure(fg_color=HeartTheme.PRIMARY, text_color="#FFFFFF", text="🏫 School Mode ✔")
            self.badge.pack_forget()
            self.school_badge.pack(side="left", padx=(8, 0))
            self.engine_combo.configure(values=[
                "❤️ Kokoro-TTS (100% Offline — Studio Quality Heart Engine)",
                "🎙️ Piper Neural English (100% Offline — Fast & Lightweight)"
            ])
            if "Microsoft" in self.engine_combo.get():
                self.engine_combo.set("❤️ Kokoro-TTS (100% Offline — Studio Quality Heart Engine)")
                self._on_engine_change("❤️ Kokoro-TTS (100% Offline — Studio Quality Heart Engine)")
        else:
            self.btn_school.configure(fg_color="#FFFFFF", text_color=HeartTheme.TEXT_MAIN, text="🏫 School Mode")
            self.school_badge.pack_forget()
            self.badge.pack(side="left")
            all_engines = [
                "❤️ Kokoro-TTS (100% Offline — Studio Quality Heart Engine)",
                "🎙️ Piper Neural English (100% Offline — Fast & Lightweight)",
                "☁️ Microsoft Neural English (Online — 8 Expressive Cloud Voices)"
            ]
            self.engine_combo.configure(values=all_engines)

    def _on_engine_change(self, choice):
        if "Kokoro" in choice or "Heart" in choice:
            self.tts_engine = self.kokoro_engine
            self.badge.configure(text="❤️ Kokoro-TTS (100% Offline Heart Engine — 11 Studio Voices)")
        elif "Piper" in choice:
            self.tts_engine = self.piper_engine
            self.badge.configure(text="🎙️ Piper Neural English (100% Offline, Fast & Private)")
        else:
            self.tts_engine = self.edge_engine
            self.badge.configure(text="☁️ Microsoft Neural English (Online — 8 Expressive Cloud Voices)")
        self._refresh_speakers_ui()

    def _get_voice_catalog(self) -> dict:
        choice = self.engine_combo.get() if hasattr(self, "engine_combo") else ""
        if "Piper" in choice:
            return self.PIPER_VOICE_DESCRIPTIONS
        elif any(k in choice for k in ["Online", "Microsoft", "Neural"]):
            return self.CLOUD_VOICE_DESCRIPTIONS
        return self.KOKORO_VOICE_DESCRIPTIONS

    def _get_voice_label(self, voice_id: str) -> str:
        cat = self._get_voice_catalog()
        v_key = str(voice_id).lower().strip()
        if v_key in cat:
            return cat[v_key]
        for k, v in cat.items():
            if k in v_key or v_key in k:
                return v
        return f"{v_key.capitalize()} — Voice"

    def _get_voice_id_from_label(self, label: str) -> str:
        cat = self._get_voice_catalog()
        for v_id, desc in cat.items():
            if desc == label:
                return v_id
        for full_cat in (self.KOKORO_VOICE_DESCRIPTIONS, self.PIPER_VOICE_DESCRIPTIONS, self.CLOUD_VOICE_DESCRIPTIONS):
            for v_id, desc in full_cat.items():
                if desc == label:
                    return v_id
        first_token = label.split(" — ")[0].strip().lower()
        if first_token in cat:
            return first_token
        return label.split(" — ")[0].split()[0].lower().strip()

    @staticmethod
    def _pan_val_to_label(pan_val: float) -> str:
        if pan_val <= -0.38:
            return "-50% L"
        elif pan_val <= -0.12:
            return "-25% L"
        elif pan_val >= 0.38:
            return "+50% R"
        elif pan_val >= 0.12:
            return "+25% R"
        else:
            return "Center"

    @staticmethod
    def _pan_label_to_val(label: str) -> float:
        mapping = {
            "-50% L": -0.50,
            "-25% L": -0.25,
            "Center": 0.0,
            "Centre": 0.0,
            "+25% R": 0.25,
            "+50% R": 0.50
        }
        return mapping.get(label, 0.0)

    @staticmethod
    def _pan_val_to_str(pan_val: float) -> str:
        if abs(pan_val) < 0.05:
            return "0%"
        elif pan_val < 0:
            return f"-{int(round(abs(pan_val)*100))}%"
        else:
            return f"+{int(round(pan_val*100))}%"

    def _extract_clean_dialogue(self, full_text: str) -> str:
        lines = full_text.splitlines()
        clean_lines = []
        is_dialogue = False

        for raw in lines:
            line = raw.strip()
            if not line:
                if is_dialogue:
                    clean_lines.append("")
                continue

            if line.startswith("---") or line.startswith("===") or line.startswith("***"):
                is_dialogue = True
                continue

            if line.startswith("[") and line.endswith("]"):
                if line.upper().startswith("[PAUSE") or line.upper().startswith("[PAUSA"):
                    if is_dialogue:
                        clean_lines.append(raw)
                continue

            if is_dialogue:
                clean_lines.append(raw)

        if not clean_lines:
            for raw in lines:
                line = raw.strip()
                if line.startswith("[") and line.endswith("]"):
                    if line.upper().startswith("[PAUSE"):
                        clean_lines.append(raw)
                    continue
                if ":" in line and not line.startswith("-"):
                    clean_lines.append(raw)

        return "\n".join(clean_lines).strip()

    def _compose_full_script(self, clean_dialogue: str) -> str:
        title = self.title_entry.get().strip() or "Educational Podcast"
        lines = [
            f"[TITLE: {title}]",
            "[FORMAT: Stereo 160kbps]",
            "[DEFAULT_PAUSE: 350ms]",
            "[INTERLOCUTOR_PAUSE: 700ms]",
            "",
            "[VOICE_CONFIG]"
        ]

        found_speakers = []
        dialogue_pattern = re.compile(r"^([A-Za-z0-9_\-\.\s]+?)\s*:\s*(.*)$")
        for raw in clean_dialogue.splitlines():
            line = raw.strip()
            if not line or line.startswith("[") or line.startswith("-") or line.startswith("*"):
                continue
            m = dialogue_pattern.match(line)
            if m:
                spk = m.group(1).strip()
                if (len(spk.split()) <= 3 and spk[0].isupper() and 
                    not any(c in spk for c in "[]{}()<>;=\"'") and 
                    spk not in found_speakers):
                    found_speakers.append(spk)

        choice = self.engine_combo.get() if hasattr(self, "engine_combo") else ""
        if "Piper" in choice:
            default_voices = ["lessac", "ryan", "amy", "alan"]
            pres_voice = "lessac"
        elif any(k in choice for k in ["Online", "Microsoft"]):
            default_voices = ["jenny", "guy", "aria", "davis", "sonia", "ryan"]
            pres_voice = "jenny"
        else:
            default_voices = ["af_heart", "am_adam", "af_bella", "bf_emma", "bm_george"]
            pres_voice = "af_heart"

        default_pans = [-0.25, 0.25, 0.0, -0.35, 0.35]
        assigned_idx = 0

        if found_speakers:
            for spk_name in found_speakers:
                if spk_name in self.current_script.speakers:
                    spk_cfg = self.current_script.speakers[spk_name]
                    voice_id = spk_cfg.voice_id
                    pan_str = self._pan_val_to_str(spk_cfg.pan)
                else:
                    is_host = any(h in spk_name.lower() for h in ["host", "present", "moderator"])
                    if is_host:
                        voice_id = pres_voice
                        pan_str = "0%"
                    else:
                        voice_id = default_voices[assigned_idx % len(default_voices)]
                        pan_str = self._pan_val_to_str(default_pans[assigned_idx % len(default_pans)])
                        assigned_idx += 1
                lines.append(f"{spk_name}: voice={voice_id} pan={pan_str}")
        else:
            speakers = self.current_script.speakers
            if speakers:
                for spk_name, spk_cfg in speakers.items():
                    pan_str = self._pan_val_to_str(spk_cfg.pan)
                    lines.append(f"{spk_name}: voice={spk_cfg.voice_id} pan={pan_str}")
            else:
                lines.append(f"Host: voice={pres_voice} pan=0%")
                lines.append(f"Speaker 1: voice={default_voices[0]} pan=-25%")
                lines.append(f"Speaker 2: voice={default_voices[1]} pan=+25%")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(clean_dialogue)
        return "\n".join(lines)

    def _toggle_editor_mode(self):
        current_content = self.script_textbox.get("1.0", "end-1c")
        if self.editor_mode == "clean":
            full_code = self._compose_full_script(current_content)
            self._raw_script_full = full_code
            self._suppress_script_sync = True
            try:
                self.script_textbox.delete("1.0", "end")
                self.script_textbox.insert("1.0", full_code)
                self.editor_mode = "full"
                self.btn_toggle_view.configure(text="⚙️ Full code .txt mode (active)")
            finally:
                self._suppress_script_sync = False
        else:
            clean_text = self._extract_clean_dialogue(current_content)
            self._suppress_script_sync = True
            try:
                self.script_textbox.delete("1.0", "end")
                self.script_textbox.insert("1.0", clean_text)
                self.editor_mode = "clean"
                self.btn_toggle_view.configure(text="📝 Clean dialogue mode (active)")
            finally:
                self._suppress_script_sync = False
        self._on_script_modified()

    def _on_title_modified(self, event=None):
        if self.editor_mode == "full":
            title = self.title_entry.get().strip()
            content = self.script_textbox.get("1.0", "end-1c")
            if re.search(r"^\[(?:TITLE|TITOL):\s*[^\]]+\]", content, flags=re.MULTILINE):
                content = re.sub(r"^\[(?:TITLE|TITOL):\s*[^\]]+\]", f"[TITLE: {title}]", content, flags=re.MULTILINE)
                self._suppress_script_sync = True
                try:
                    self.script_textbox.delete("1.0", "end")
                    self.script_textbox.insert("1.0", content)
                finally:
                    self._suppress_script_sync = False

    def _on_script_modified(self, event=None):
        if self._suppress_script_sync:
            return
        text = self.script_textbox.get("1.0", "end-1c")
        if self.editor_mode == "clean":
            full_to_parse = self._compose_full_script(text)
        else:
            full_to_parse = text

        self.current_script = self.script_parser.parse(full_to_parse)
        if self.current_script.title and not self.title_entry.get().strip():
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, self.current_script.title)

        for spk_name, overrides in self.ui_speaker_overrides.items():
            if spk_name in self.current_script.speakers:
                if "voice_id" in overrides:
                    self.current_script.speakers[spk_name].voice_id = overrides["voice_id"]
                if "pan" in overrides:
                    self.current_script.speakers[spk_name].pan = overrides["pan"]

        self._update_script_stats_and_ui()

    def _update_script_stats_and_ui(self):
        dialogue_words = sum(len(s.text.split()) for s in self.current_script.segments if s.segment_type == "dialogue")
        est_seconds = (dialogue_words / 145.0 * 60.0) + (len(self.current_script.segments) * 0.7)
        mins = int(est_seconds // 60)
        secs = int(est_seconds % 60)

        spk_count = len(self.current_script.speakers)
        spk_names = ", ".join(list(self.current_script.speakers.keys())[:3])
        if spk_count > 3:
            spk_names += f" (+{spk_count-3})"

        self.stats_lbl.configure(
            text=f"{dialogue_words} words · ~{mins:02d}:{secs:02d} min · {spk_count} voices ({spk_names})"
        )
        self._update_voice_structure_segment()
        self._refresh_speakers_ui()

    def _update_voice_structure_segment(self):
        count = len(self.current_script.speakers)
        self._internal_mode_update = True
        try:
            if count == 1:
                self.structure_selector.set("👤 1 Voice (Monologue)")
            elif count == 2:
                self.structure_selector.set("👥 2 Voices (Dialogue)")
            elif count >= 3:
                self.structure_selector.set("👥👥 3 Voices (Roundtable)")
        finally:
            self._internal_mode_update = False

    def _refresh_speakers_ui(self):
        for widget in self.speakers_container.winfo_children():
            widget.destroy()

        if not self.current_script.speakers:
            lbl = ctk.CTkLabel(
                self.speakers_container,
                text="Write lines like 'Host: text' or 'Name: text' to detect cast voices.",
                font=HeartTheme.FONT_SMALL,
                text_color=HeartTheme.TEXT_MUTED
            )
            lbl.pack(padx=10, pady=16)
            return

        cat = self._get_voice_catalog()
        available_labels = list(cat.values())
        available_ids = list(cat.keys())

        for spk_name, overrides in self.ui_speaker_overrides.items():
            if spk_name in self.current_script.speakers:
                if "voice_id" in overrides:
                    self.current_script.speakers[spk_name].voice_id = overrides["voice_id"]
                if "pan" in overrides:
                    self.current_script.speakers[spk_name].pan = overrides["pan"]

        for i, (spk_name, spk_cfg) in enumerate(self.current_script.speakers.items()):
            if spk_cfg.voice_id not in available_ids:
                spk_cfg.voice_id = available_ids[min(i, len(available_ids) - 1)]

            card = ctk.CTkFrame(
                self.speakers_container,
                fg_color=HeartTheme.BG_CARD,
                corner_radius=10,
                border_width=1,
                border_color=HeartTheme.BORDER_CARD,
                height=1
            )
            card.pack(fill="x", padx=4, pady=4)

            # Top Line: Speaker Name, ComboBox, Preview button
            top_line = ctk.CTkFrame(card, fg_color="transparent", height=1)
            top_line.pack(fill="x", padx=10, pady=(6, 2))

            is_host = any(h in spk_name.lower() for h in ["host", "present", "moderator"])
            spk_icon = "🎙️" if is_host else "👤"

            spk_lbl = ctk.CTkLabel(
                top_line,
                text=f"{spk_icon} {spk_name}",
                font=HeartTheme.FONT_BODY_BOLD,
                text_color=HeartTheme.PRIMARY if is_host else HeartTheme.TEXT_MAIN,
                width=135,
                anchor="w"
            )
            spk_lbl.pack(side="left")

            current_voice_label = self._get_voice_label(spk_cfg.voice_id)
            voice_combo = ctk.CTkComboBox(
                top_line,
                values=available_labels,
                height=26,
                corner_radius=13,
                fg_color=HeartTheme.BG_CARD_SUBTLE,
                border_color=HeartTheme.BORDER_CARD,
                button_color=HeartTheme.PRIMARY,
                button_hover_color=HeartTheme.PRIMARY_HOVER,
                text_color=HeartTheme.TEXT_MAIN,
                font=HeartTheme.FONT_SMALL,
                dropdown_font=HeartTheme.FONT_SMALL,
                dropdown_text_color=HeartTheme.TEXT_MAIN,
                command=lambda val, name=spk_name: self._on_speaker_voice_change(name, val)
            )
            voice_combo.pack(side="left", fill="x", expand=True, padx=(4, 6))
            voice_combo.set(current_voice_label)

            sample_btn = CleanButton(
                top_line,
                style="subtle",
                text="▶ Preview",
                width=76,
                height=26
            )
            sample_btn.configure(command=lambda name=spk_name, btn=sample_btn: self._play_speaker_sample(name, btn))
            sample_btn.pack(side="right")

            # Bottom Line: Stereo Pan PillSelector
            pan_line = ctk.CTkFrame(card, fg_color="transparent", height=1)
            pan_line.pack(fill="x", padx=10, pady=(2, 6))

            pan_lbl = ctk.CTkLabel(
                pan_line,
                text="Stereo stage:",
                font=HeartTheme.FONT_SMALL,
                text_color=HeartTheme.TEXT_MUTED,
                width=85,
                anchor="w"
            )
            pan_lbl.pack(side="left")

            pan_seg = PillSelector(
                pan_line,
                values=["-50% L", "-25% L", "Center", "+25% R", "+50% R"],
                default_val=self._pan_val_to_label(spk_cfg.pan),
                height=24,
                font_size=9,
                expand_buttons=True,
                command=lambda val, name=spk_name: self._on_speaker_pan_change(name, val)
            )
            pan_seg.pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _on_speaker_voice_change(self, spk_name: str, voice_label: str):
        voice_id = self._get_voice_id_from_label(voice_label)
        if spk_name in self.current_script.speakers:
            self.current_script.speakers[spk_name].voice_id = voice_id
        if spk_name not in self.ui_speaker_overrides:
            self.ui_speaker_overrides[spk_name] = {}
        self.ui_speaker_overrides[spk_name]["voice_id"] = voice_id
        self._sync_speaker_config_to_editor(spk_name)

    def _on_speaker_pan_change(self, spk_name: str, pan_label: str):
        pan_val = self._pan_label_to_val(pan_label)
        if spk_name in self.current_script.speakers:
            self.current_script.speakers[spk_name].pan = pan_val
        if spk_name not in self.ui_speaker_overrides:
            self.ui_speaker_overrides[spk_name] = {}
        self.ui_speaker_overrides[spk_name]["pan"] = pan_val
        self._sync_speaker_config_to_editor(spk_name)

    def _sync_speaker_config_to_editor(self, spk_name: str):
        if self.editor_mode != "full":
            return
        if spk_name not in self.current_script.speakers:
            return

        spk_cfg = self.current_script.speakers[spk_name]
        pan_str = self._pan_val_to_str(spk_cfg.pan)
        voice_id = spk_cfg.voice_id

        content = self.script_textbox.get("1.0", "end-1c")
        spk_line_pattern = re.compile(rf"^(\s*{re.escape(spk_name)}\s*:\s*)([^\r\n]*)", re.MULTILINE)
        m = spk_line_pattern.search(content)
        if m:
            prefix = m.group(1)
            rest = m.group(2)
            if re.search(r'\b(?:voice|veu)=([^\s]+)', rest, flags=re.IGNORECASE):
                rest = re.sub(r'\b(?:voice|veu)=([^\s]+)', f'voice={voice_id}', rest, flags=re.IGNORECASE)
            else:
                rest = f"voice={voice_id} " + rest
            if re.search(r'\b(?:pan|panning)=([^\s]+)', rest, flags=re.IGNORECASE):
                rest = re.sub(r'\b(?:pan|panning)=([^\s]+)', f'pan={pan_str}', rest, flags=re.IGNORECASE)
            else:
                rest = rest + f" pan={pan_str}"
            new_line = f"{prefix}{rest.strip()}"
            updated = content[:m.start()] + new_line + content[m.end():]

            self._suppress_script_sync = True
            try:
                self.script_textbox.delete("1.0", "end")
                self.script_textbox.insert("1.0", updated)
            finally:
                self._suppress_script_sync = False

    def _play_speaker_sample(self, spk_name: str, btn: CleanButton):
        if spk_name not in self.current_script.speakers:
            return
        voice_id = self.current_script.speakers[spk_name].voice_id

        btn.configure(text="🔊 ...", state="disabled", fg_color=HeartTheme.PRIMARY, text_color="#FFFFFF")
        self._set_status(f"Auditioning voice preview for {spk_name} ({voice_id})...")

        def on_start():
            self.safe_after(lambda: btn.configure(text="🔊 ..."))

        def on_finish():
            self.safe_after(lambda: btn.configure(text="▶ Preview", state="normal", fg_color=HeartTheme.BUTTON_SUBTLE_BG, text_color=HeartTheme.TEXT_MAIN))
            self._set_status("Ready to generate. No duration limits.")

        def on_error(err):
            self.safe_after(lambda: btn.configure(text="▶ Preview", state="normal", fg_color=HeartTheme.BUTTON_SUBTLE_BG, text_color=HeartTheme.TEXT_MAIN))
            self._set_status(f"Preview notice: {err}")

        self.voice_preview_manager.play_sample(
            voice_id,
            self.tts_engine,
            on_start_callback=on_start,
            on_finish_callback=on_finish,
            on_error_callback=on_error
        )

    def _set_status(self, text: str):
        if hasattr(self, "status_lbl") and self.status_lbl is not None:
            try:
                self.status_lbl.configure(text=text)
            except Exception:
                pass

    def _load_script_from_text(self, content: str, source_label: str = ""):
        parsed = self.script_parser.parse(content)
        self.current_script = parsed
        self.ui_speaker_overrides.clear()

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, parsed.title)

        self._suppress_script_sync = True
        try:
            self.script_textbox.delete("1.0", "end")
            if self.editor_mode == "clean":
                self.script_textbox.insert("1.0", self._extract_clean_dialogue(content))
            else:
                self.script_textbox.insert("1.0", content)
        finally:
            self._suppress_script_sync = False

        self._update_script_stats_and_ui()
        if source_label:
            self._set_status(f"Loaded: {source_label}")

    def _on_template_selected(self, choice: str):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        examples_dir = os.path.join(base_dir, "examples")

        if "5-Min" in choice or "Showcase" in choice:
            path = os.path.join(examples_dir, "sample_5min.txt")
        elif "1 Voice" in choice:
            path = os.path.join(examples_dir, "template_1voice.txt")
        elif "2 Voices" in choice:
            path = os.path.join(examples_dir, "template_2voices.txt")
        elif "3 Voices" in choice:
            path = os.path.join(examples_dir, "template_3voices.txt")
        else:
            return

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._load_script_from_text(content, f"Template: {choice}")
        self.template_opt.set("Templates...")

    def _on_structure_selected(self, choice: str):
        if self._internal_mode_update:
            return
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        examples_dir = os.path.join(base_dir, "examples")

        if "1 Voice" in choice:
            path = os.path.join(examples_dir, "template_1voice.txt")
            target_name = "1 Voice (Monologue with Host)"
        elif "2 Voices" in choice:
            path = os.path.join(examples_dir, "template_2voices.txt")
            target_name = "2 Voices (Dialogue between Speaker 1 and Speaker 2)"
        elif "3 Voices" in choice:
            path = os.path.join(examples_dir, "template_3voices.txt")
            target_name = "3 Voices (Roundtable with Host, Speaker 1, and Speaker 2)"
        else:
            return

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._load_script_from_text(content, f"Structure changed to {target_name}.")

    def _load_default_sample(self):
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "sample_5min.txt")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                content = f.read()
            self._load_script_from_text(content, "5-Minute Showcase Script loaded.")

    def _open_script_file(self):
        path = filedialog.askopenfilename(
            title="Open Podcast Script",
            filetypes=[("Text Files (*.txt)", "*.txt"), ("All Files (*.*)", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._load_script_from_text(content, os.path.basename(path))

    def _save_script_file(self):
        path = filedialog.asksaveasfilename(
            title="Save Podcast Script",
            defaultextension=".txt",
            filetypes=[("Text Files (*.txt)", "*.txt")]
        )
        if path:
            current_content = self.script_textbox.get("1.0", "end-1c")
            if self.editor_mode == "clean":
                full_to_save = self._compose_full_script(current_content)
            else:
                full_to_save = current_content

            with open(path, "w", encoding="utf-8") as f:
                f.write(full_to_save)
            messagebox.showinfo("Saved", "The podcast script has been saved successfully.")

    # Background audio actions
    def _select_bg_audio(self):
        path = filedialog.askopenfilename(
            title="Select Background Music or Ambience Track",
            filetypes=[
                ("Audio Files (*.mp3, *.wav, *.ogg, *.flac, *.m4a)", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                ("MP3 Files (*.mp3)", "*.mp3"),
                ("WAV Files (*.wav)", "*.wav"),
                ("All Files (*.*)", "*.*")
            ]
        )
        if not path:
            return

        self._stop_bg_preview()
        self.bg_music_path = path
        filename = os.path.basename(path)
        display_name = filename if len(filename) <= 28 else filename[:25] + "..."

        self.lbl_bg_file.configure(
            text=f"🎵 {display_name}",
            text_color=HeartTheme.TEXT_MAIN
        )
        self.btn_clear_bg.configure(state="normal")
        self.btn_bg_preview.configure(state="normal")
        self._set_status(f"Selected background track: {filename}")

        def _preload():
            try:
                audio = self.audio_processor.load_audio_file(path, target_sr=22050)
                self.bg_music_audio_data = audio
            except Exception as e:
                print(f"Preload background track warning: {e}")
                self.bg_music_audio_data = None

        threading.Thread(target=_preload, daemon=True).start()

    def _clear_bg_audio(self):
        self._stop_bg_preview()
        self.bg_music_path = None
        self.bg_music_audio_data = None
        self.lbl_bg_file.configure(
            text="No background track selected",
            text_color=HeartTheme.TEXT_MUTED
        )
        self.btn_clear_bg.configure(state="disabled")
        self.btn_bg_preview.configure(state="disabled")
        self._set_status("Background track cleared.")

    def _on_bg_loop_toggle(self):
        self.bg_music_loop = bool(self.cb_bg_loop.get())
        if getattr(self, "_is_bg_previewing", False):
            self._play_bg_preview_sound()

    def _on_bg_volume_change(self, val):
        self.bg_music_volume = float(val)
        pct = int(round(self.bg_music_volume * 100))
        self.lbl_bg_volume.configure(text=f"Vol: {pct}%")
        # Real-time live volume adjustment
        if getattr(self, "_is_bg_previewing", False):
            try:
                import pygame
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(self.bg_music_volume)
            except Exception:
                pass

    def _toggle_bg_preview(self):
        if getattr(self, "_is_bg_previewing", False):
            self._stop_bg_preview()
            self._set_status("Background music preview stopped.")
            return

        if not self.bg_music_path or not os.path.exists(self.bg_music_path):
            messagebox.showwarning("Notice", "Please select a background audio file first.")
            return

        self._play_bg_preview_sound()

    def _play_bg_preview_sound(self):
        if not self.bg_music_path or not os.path.exists(self.bg_music_path):
            return

        try:
            if self.bg_music_audio_data is not None:
                audio = self.bg_music_audio_data
            else:
                self._set_status("Loading audio track...")
                audio = self.audio_processor.load_audio_file(self.bg_music_path, target_sr=22050)
                self.bg_music_audio_data = audio

            if audio is None or audio.size == 0:
                self._stop_bg_preview()
                self._set_status("Could not load audio from selected file.")
                return

            max_samples = int(10.0 * 22050)
            chunk = np.copy(audio[:, :min(audio.shape[1], max_samples)])

            fade_samples = min(int(0.03 * 22050), chunk.shape[1] // 4)
            if fade_samples > 0:
                curve_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                curve_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
                chunk[:, :fade_samples] *= curve_in
                chunk[:, -fade_samples:] *= curve_out

            vol = max(0.0, min(1.0, float(self.bg_music_volume)))

            tmp_dir = os.path.join(tempfile.gettempdir(), "podcasts_heart_preview")
            os.makedirs(tmp_dir, exist_ok=True)
            self._bg_preview_tmp_wav = os.path.join(tmp_dir, f"bg_preview_{os.getpid()}.wav")
            sf.write(self._bg_preview_tmp_wav, chunk.T, 22050, subtype="PCM_16")

            self._is_bg_previewing = True
            played = False

            # Prioritize Pygame mixer for live dynamic volume
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=22050, size=-16, channels=chunk.shape[0], buffer=1024)
                pygame.mixer.music.load(self._bg_preview_tmp_wav)
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1 if self.bg_music_loop else 0)
                played = True
            except Exception as pe:
                print(f"Pygame preview warning: {pe}")

            if not played and sys.platform == "win32":
                try:
                    scaled = np.clip(chunk * vol, -1.0, 1.0)
                    sf.write(self._bg_preview_tmp_wav, scaled.T, 22050, subtype="PCM_16")
                    import winsound
                    flags = winsound.SND_FILENAME | winsound.SND_ASYNC
                    if self.bg_music_loop:
                        flags |= winsound.SND_LOOP
                    winsound.PlaySound(self._bg_preview_tmp_wav, flags)
                    played = True
                except Exception as we:
                    print(f"Winsound warning: {we}")

            if played:
                self.btn_bg_preview.configure(
                    text="■ Stop",
                    fg_color=HeartTheme.PRIMARY,
                    text_color="#FFFFFF"
                )
                dur_secs = chunk.shape[1] / 22050.0
                loop_text = "in loop" if self.bg_music_loop else f"{dur_secs:.1f}s"
                self._set_status(f"Playing background music preview ({loop_text}, volume {int(round(vol*100))}%)...")

                if not self.bg_music_loop:
                    dur_ms = int(dur_secs * 1000) + 150
                    if self._bg_preview_timer_id:
                        try:
                            self.after_cancel(self._bg_preview_timer_id)
                        except Exception:
                            pass
                    self._bg_preview_timer_id = self.after(dur_ms, self._on_bg_preview_finished)
            else:
                self._stop_bg_preview()
                self._set_status("Could not play sound on audio device.")

        except Exception as e:
            self._stop_bg_preview()
            self._set_status(f"Error previewing audio: {e}")

    def _on_bg_preview_finished(self):
        self._is_bg_previewing = False
        self._bg_preview_timer_id = None
        try:
            self.btn_bg_preview.configure(
                text="▶ Test",
                fg_color=HeartTheme.BUTTON_SUBTLE_BG,
                text_color=HeartTheme.TEXT_MAIN
            )
            self._set_status("Ready to generate. No duration limits.")
        except Exception:
            pass

    def _stop_bg_preview(self):
        self._is_bg_previewing = False
        if self._bg_preview_timer_id:
            try:
                self.after_cancel(self._bg_preview_timer_id)
            except Exception:
                pass
            self._bg_preview_timer_id = None

        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass

        try:
            self.btn_bg_preview.configure(
                text="▶ Test",
                fg_color=HeartTheme.BUTTON_SUBTLE_BG,
                text_color=HeartTheme.TEXT_MAIN
            )
        except Exception:
            pass

    # Generation pipeline
    def _start_generation(self):
        if self.is_generating:
            return

        self._stop_bg_preview()
        current_content = self.script_textbox.get("1.0", "end-1c")
        if self.editor_mode == "clean":
            full_to_process = self._compose_full_script(current_content)
        else:
            full_to_process = current_content

        self.current_script = self.script_parser.parse(full_to_process)

        for spk_name, overrides in self.ui_speaker_overrides.items():
            if spk_name in self.current_script.speakers:
                if "voice_id" in overrides:
                    self.current_script.speakers[spk_name].voice_id = overrides["voice_id"]
                if "pan" in overrides:
                    self.current_script.speakers[spk_name].pan = overrides["pan"]

        for seg in self.current_script.segments:
            if seg.segment_type == "dialogue" and seg.speaker in self.current_script.speakers:
                spk_cfg = self.current_script.speakers[seg.speaker]
                seg.voice_id = spk_cfg.voice_id
                seg.pan = spk_cfg.pan

        if not self.current_script.segments:
            messagebox.showwarning("Notice", "The script is empty or contains no dialogue lines.")
            return

        self.is_generating = True
        self.cancel_requested = False
        self.generate_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0.0)

        threading.Thread(target=self._generation_worker, daemon=True).start()

    def _cancel_generation(self):
        if self.is_generating:
            self.cancel_requested = True
            self.status_lbl.configure(text="Cancelling generation...")

    def _generation_worker(self):
        segments = self.current_script.segments
        total = len(segments)
        audio_blocks: List[np.ndarray] = []

        try:
            for idx, seg in enumerate(segments):
                if self.cancel_requested:
                    self.safe_after(lambda: self._on_generation_finished(None, "Generation cancelled by user."))
                    return

                pct = idx / max(1, total)
                self.safe_after(lambda p=pct, i=idx, t=total, s=seg: self._update_progress_ui(p, f"[{i+1}/{t}] Synthesizing {s.speaker or 'Pause'}..."))

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
                    should_normalize = bool(self.cb_normalizer.get())
                    raw_audio = self.tts_engine.synthesize_utterance(
                        seg.text,
                        voice_id=curr_voice,
                        speed=curr_speed,
                        pitch=curr_pitch,
                        normalize_text=should_normalize
                    )
                    if raw_audio is None or len(raw_audio) == 0:
                        raise RuntimeError(f"Speech synthesis returned empty audio for speaker '{seg.speaker}' with voice '{curr_voice}'.")

                    stereo_seg = self.audio_processor.apply_pan(raw_audio, curr_pan)
                    audio_blocks.append(stereo_seg)

            if not self.cancel_requested and audio_blocks:
                self.safe_after(lambda: self._update_progress_ui(0.92, "Assembling stereo broadcast tracks..."))
                full_stereo = np.concatenate(audio_blocks, axis=1)

                # Mix background music if selected
                if self.bg_music_path and os.path.exists(self.bg_music_path) and self.bg_music_volume > 0.0:
                    self.safe_after(lambda: self._update_progress_ui(0.96, "Mixing background soundtrack loop..."))
                    full_stereo = self.audio_processor.mix_background_track(
                        voice_audio=full_stereo,
                        bg_audio=self.bg_music_path,
                        volume=self.bg_music_volume,
                        loop=self.bg_music_loop
                    )

                # EBU R128 loudness normalization
                if bool(self.cb_lufs.get()):
                    self.safe_after(lambda: self._update_progress_ui(0.98, "Mastering loudness to EBU R128 (-16 LUFS)..."))
                    full_stereo = self.audio_processor.normalize_loudness(full_stereo, target_lufs=-16.0)

                self.safe_after(lambda: self._on_generation_finished(full_stereo, "Podcast generated with heart!"))

        except Exception as e:
            self.safe_after(lambda: self._on_generation_finished(None, f"Error during generation: {e}"))

    def _update_progress_ui(self, pct: float, status_text: str):
        self.progress_bar.set(pct)
        self.status_lbl.configure(text=status_text)

    def _on_generation_finished(self, stereo_audio, status_message):
        self.is_generating = False
        self.generate_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.status_lbl.configure(text=status_message)

        if stereo_audio is not None and stereo_audio.size > 0:
            self.progress_bar.set(1.0)
            self.player_widget.load_audio(stereo_audio, title=self.current_script.title)
            messagebox.showinfo("Podcast Completed", "Your podcast has been generated with heart!\nYou can now listen or export directly as a broadcast MP3 file.")

    def _show_ssml_guide(self):
        doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "SSML_GUIDE.md")
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "SSML Prosody Guide\nUse <break time='500ms'/> for pauses."
        self._open_text_viewer("SSML Prosody Guide", content)

    def _show_llm_guide(self):
        doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "LLM_PROMPT_GUIDE.md")
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "LLM Master Prompt Guide for Podcasts with Heart"
        self._open_text_viewer("LLM Prompt Guide (Podcasts with Heart)", content)

    def _show_components_manager(self):
        ComponentsManagerModal(self, on_update_callback=self._refresh_speakers_ui)

    def _show_version_check_modal(self):
        VersionCheckModal(self)

    def _open_text_viewer(self, title: str, text: str):
        viewer = ctk.CTkToplevel(self)
        viewer.title(title)
        viewer.geometry("720x560")
        viewer.configure(fg_color=HeartTheme.BG_MAIN)
        viewer.transient(self)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(ico_path):
            try:
                viewer.iconbitmap(ico_path)
                viewer.after(200, lambda: viewer.iconbitmap(ico_path))
            except Exception:
                pass

        txt = ctk.CTkTextbox(
            viewer,
            fg_color=HeartTheme.ENTRY_BG,
            text_color=HeartTheme.TEXT_MAIN,
            font=HeartTheme.FONT_MONO,
            wrap="word",
            corner_radius=10
        )
        txt.pack(fill="both", expand=True, padx=20, pady=20)
        txt.insert("1.0", text)
        txt.configure(state="disabled")
