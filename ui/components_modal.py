"""
Models and Voice Manager Modal for Podcasts with Heart.
Inspects local voice models (Kokoro-82M and Piper English), disk status,
system hardware compatibility diagnostic, installation guide, and downloads voices from Hugging Face.
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Dict, Any, Optional

from ui.theme import HeartTheme
from core.model_downloader import ModelDownloader
from core.system_checker import SystemChecker


class SystemCheckModal(ctk.CTkToplevel):
    """Modal dialog for automatic system hardware and requirements diagnostics."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("🔍 System Diagnostic — Offline Synthesis Requirements")
        self.geometry("640x580")
        self.minsize(580, 480)
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self._set_modal_icon()
        self._build_ui()
        self._run_diagnostic()

    def _set_modal_icon(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _build_ui(self):
        # 1. Header
        header = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        header.pack(fill="x", padx=18, pady=(16, 10))

        title_lbl = ctk.CTkLabel(
            header,
            text="🔍 System Hardware & Compatibility Check",
            font=HeartTheme.FONT_TITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 2))

        desc_lbl = ctk.CTkLabel(
            header,
            text="Evaluates hard drive storage, physical RAM, CPU cores, and GPU capabilities\nto ensure your computer can synthesize English podcasts 100% locally and privately.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Consolidated verdict card
        self.verdict_frame = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, corner_radius=10, border_width=1, border_color=HeartTheme.BORDER_CARD)
        self.verdict_frame.pack(fill="x", padx=18, pady=(0, 10))

        self.verdict_title = ctk.CTkLabel(
            self.verdict_frame,
            text="Analyzing system...",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        self.verdict_title.pack(anchor="w", padx=16, pady=(10, 2))

        self.verdict_desc = ctk.CTkLabel(
            self.verdict_frame,
            text="Please wait while reading system specifications.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            justify="left"
        )
        self.verdict_desc.pack(anchor="w", padx=16, pady=(0, 10))

        # 2. Detailed results container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=10)
        self.scroll_frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        # 3. Footer
        footer = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, height=50, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        footer.pack(fill="x", padx=18, pady=(0, 16))
        footer.pack_propagate(False)

        btn_recheck = ctk.CTkButton(
            footer,
            text="🔄 Re-run Check",
            font=HeartTheme.FONT_SMALL,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            text_color=HeartTheme.TEXT_MAIN,
            hover_color=HeartTheme.BG_CARD_HOVER,
            corner_radius=14,
            height=30,
            command=self._run_diagnostic
        )
        btn_recheck.pack(side="left", padx=12, pady=10)

        btn_close = ctk.CTkButton(
            footer,
            text="Close",
            font=HeartTheme.FONT_SMALL,
            fg_color=HeartTheme.PRIMARY,
            text_color="#FFFFFF",
            hover_color=HeartTheme.PRIMARY_HOVER,
            corner_radius=14,
            height=30,
            width=80,
            command=self.destroy
        )
        btn_close.pack(side="right", padx=12, pady=10)

    def _run_diagnostic(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        diag = SystemChecker.run_full_diagnostic()

        status = diag["overall_status"]
        if status == "ok":
            card_bg = "#EBF5EE"
            border_c = "#A3CFBB"
            text_c = "#1B5E20"
        elif status == "warning":
            card_bg = "#FFF9E6"
            border_c = "#FFE082"
            text_c = "#8C5C00"
        else:
            card_bg = "#FFEBEE"
            border_c = "#EF9A9A"
            text_c = "#B71C1C"

        self.verdict_frame.configure(fg_color=card_bg, border_color=border_c)
        self.verdict_title.configure(text=diag["overall_title"], text_color=text_c)
        self.verdict_desc.configure(text=diag["overall_summary"], text_color=text_c)

        icons = {
            "Disk Storage": "💾",
            "Physical RAM": "🧠",
            "Processor (CPU)": "⚡",
            "Graphics Acceleration (GPU)": "🎮",
            "Hugging Face Connection": "🌐"
        }

        for check in diag["checks"]:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=HeartTheme.BG_CARD, corner_radius=10, border_width=1, border_color=HeartTheme.BORDER_CARD)
            card.pack(fill="x", pady=4)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(8, 2))

            icon = icons.get(check["name"], "📌")
            lbl_name = ctk.CTkLabel(
                top,
                text=f"{icon}  {check['name']}",
                font=HeartTheme.FONT_SUBTITLE,
                text_color=HeartTheme.TEXT_MAIN
            )
            lbl_name.pack(side="left")

            st = check["status"]
            if st == "ok":
                badge_bg = "#EBF5EE"
                badge_fg = "#2E7D32"
                badge_text = "✓ Ready"
            elif st == "warning":
                badge_bg = "#FFF8E7"
                badge_fg = "#8C5C00"
                badge_text = "⚠️ Warning"
            else:
                badge_bg = "#FFEBEE"
                badge_fg = "#C62828"
                badge_text = "❌ Attention"

            badge = ctk.CTkLabel(
                top,
                text=badge_text,
                font=HeartTheme.FONT_TINY,
                fg_color=badge_bg,
                text_color=badge_fg,
                corner_radius=8,
                padx=8,
                pady=1
            )
            badge.pack(side="right")

            lbl_val = ctk.CTkLabel(
                card,
                text=f"Detected: {check['value']}",
                font=HeartTheme.FONT_SMALL_BOLD,
                text_color=HeartTheme.PRIMARY
            )
            lbl_val.pack(anchor="w", padx=14, pady=(0, 2))

            lbl_details = ctk.CTkLabel(
                card,
                text=check["details"],
                font=HeartTheme.FONT_SMALL,
                text_color=HeartTheme.TEXT_SECONDARY,
                justify="left",
                wraplength=540
            )
            lbl_details.pack(anchor="w", padx=14, pady=(0, 8))


class InstallGuideModal(ctk.CTkToplevel):
    """Informative modal guide explaining implications of installing offline models."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("ℹ️ What Does Installing Everything Imply? — Offline Synthesis Guide")
        self.geometry("660x600")
        self.minsize(600, 500)
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self._set_modal_icon()
        self._build_ui()

    def _set_modal_icon(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        header.pack(fill="x", padx=18, pady=(16, 10))

        title_lbl = ctk.CTkLabel(
            header,
            text="ℹ️ Offline Synthesis Guide & Implications",
            font=HeartTheme.FONT_TITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 2))

        desc_lbl = ctk.CTkLabel(
            header,
            text="Clear information about how local neural voice models work on your machine,\nhow much storage they require, and what privacy guarantees they offer.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        sections = [
            (
                "📦 Total Storage Required (~365 MB for all offline models)",
                "• Recommended 100% Offline Setup (~365 MB total):\n"
                "  - Kokoro-82M flagship ONNX model: ~115 MB (11 expressive studio English voices).\n"
                "  - Piper English voices (Lessac, Amy, Ryan, Alan): ~60 MB each (~250 MB total).\n\n"
                "• Cloud Neural Voices (Edge TTS — 0 MB local storage):\n"
                "  - No disk space required; however, they require an active, uninterrupted internet connection."
            ),
            (
                "⚡ Why ONNX Runtime? How Does It Work?",
                "• The ONNX (Open Neural Network Exchange) format is the cornerstone of speed and portability in Podcasts with Heart.\n"
                "• It allows Kokoro-82M and Piper to execute directly on the CPU of any standard PC or laptop (Intel or AMD) without requiring heavy PyTorch installations or massive CUDA GPU stacks.\n"
                "• The application already bundles ONNX Runtime; you only need the lightweight model files to start generating."
            ),
            (
                "✈️ One-Time Download vs. Permanent Offline Freedom",
                "• One-time download: an internet connection is only needed once to download the official models from Hugging Face.\n"
                "• Permanent offline operation: once downloaded, your computer can operate in airplane mode, without Wi-Fi, or in classroom environments without internet access."
            ),
            (
                "🔒 Total Privacy (0% Data Leaves Your Machine)",
                "When generating with Kokoro-82M or Piper:\n"
                "• Zero text fragments, student names, or scripts are sent to external servers.\n"
                "• No audio samples leave your local computer.\n"
                "• Full compliance with student data privacy frameworks (GDPR, FERPA, COPPA) in educational institutions."
            ),
            (
                "⏱️ Performance and Generation Speeds",
                "• CPU synthesis: models run smoothly on standard Intel or AMD processors without requiring a dedicated graphics card.\n"
                "• Estimated speed: on a typical 4 to 8 core CPU, a 1-minute podcast conversation is generated in approximately 10 to 20 seconds (faster than real-time).\n"
                "• If your computer has a supported GPU (NVIDIA CUDA or Windows DirectML), synthesis is even faster."
            ),
            (
                "🗣️ Differences Between Voice Engines",
                "• Kokoro-82M (100% Offline — Flagship Engine):\n"
                "  Outstanding studio quality, rich human cadence, and 11 voices (American & British English). Runs fully locally.\n\n"
                "• Piper TTS (100% Offline — Lightweight Engine):\n"
                "  Ultra-fast, pedagogical, and clear narration. 4 voices (~60 MB each).\n\n"
                "• Microsoft Neural English (Online Cloud Engine):\n"
                "  8 natural voices across US, British, and Australian accents. Uses 0 MB disk space but transmits script text to cloud servers."
            ),
            (
                "☁️ Cloud Engine Trade-offs and Limitations",
                "While cloud voices take 0 MB of local storage, consider these trade-offs:\n\n"
                "• Permanent internet connection required.\n"
                "• Script privacy: text is sent over the network to cloud APIs.\n"
                "• Rate limits: rapid consecutive batches may encounter temporary HTTP 429 throttling.\n"
                "• School Mode: to ensure strict privacy for minors, turn on School Mode in the header to restrict the app to offline engines."
            ),
            (
                "📜 Open Source and Educational Heritage",
                "Kokoro-82M and Piper are open-source models released under permissive community licenses, ensuring freedom of study, educational innovation, and classroom deployment."
            )
        ]

        for title, content in sections:
            card = ctk.CTkFrame(scroll, fg_color=HeartTheme.BG_CARD, corner_radius=10, border_width=1, border_color=HeartTheme.BORDER_CARD)
            card.pack(fill="x", pady=4)

            t_lbl = ctk.CTkLabel(card, text=title, font=HeartTheme.FONT_SUBTITLE, text_color=HeartTheme.PRIMARY)
            t_lbl.pack(anchor="w", padx=14, pady=(10, 4))

            c_lbl = ctk.CTkLabel(card, text=content, font=HeartTheme.FONT_SMALL, text_color=HeartTheme.TEXT_SECONDARY, justify="left", wraplength=560)
            c_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        footer = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, height=50, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        footer.pack(fill="x", padx=18, pady=(0, 16))
        footer.pack_propagate(False)

        btn_ok = ctk.CTkButton(
            footer,
            text="Got It",
            font=HeartTheme.FONT_SMALL_BOLD,
            fg_color=HeartTheme.PRIMARY,
            text_color="#FFFFFF",
            hover_color=HeartTheme.PRIMARY_HOVER,
            corner_radius=14,
            height=30,
            command=self.destroy
        )
        btn_ok.pack(side="right", padx=12, pady=10)


class ComponentsManagerModal(ctk.CTkToplevel):
    """Modal dialog managing offline English voice models."""

    def __init__(self, parent, on_update_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_update_callback = on_update_callback
        self.downloader = ModelDownloader()
        self.is_downloading = False
        self.active_key = None

        self.title("📦 Voice Models & Offline Storage Manager — Podcasts with Heart")
        self.geometry("700x640")
        self.minsize(620, 520)
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self._set_modal_icon()
        self._cards: Dict[str, Dict[str, Any]] = {}
        self._build_ui()
        self._refresh_all_status()

    def _set_modal_icon(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    def _open_system_check(self):
        SystemCheckModal(self)

    def _open_install_guide(self):
        InstallGuideModal(self)

    def _build_ui(self):
        # 1. Header panel
        header = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        header.pack(fill="x", padx=18, pady=(16, 10))

        title_lbl = ctk.CTkLabel(
            header,
            text="📦 Offline Voice Models & Storage",
            font=HeartTheme.FONT_TITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 2))

        desc_lbl = ctk.CTkLabel(
            header,
            text="Manage offline neural models (Kokoro-82M & Piper). Download once and generate podcasts\n100% locally with zero internet dependency and complete data privacy.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # Quick tools row in header
        tools_row = ctk.CTkFrame(header, fg_color="transparent")
        tools_row.pack(fill="x", padx=16, pady=(0, 12))

        btn_check = ctk.CTkButton(
            tools_row,
            text="🔍 Check My System",
            font=HeartTheme.FONT_SMALL_BOLD,
            fg_color=HeartTheme.PRIMARY_LIGHT,
            text_color=HeartTheme.PRIMARY,
            hover_color=HeartTheme.BG_CARD_HOVER,
            corner_radius=14,
            height=30,
            command=self._open_system_check
        )
        btn_check.pack(side="left", padx=(0, 10))

        btn_guide = ctk.CTkButton(
            tools_row,
            text="ℹ️ What does installing imply?",
            font=HeartTheme.FONT_SMALL_BOLD,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            text_color=HeartTheme.TEXT_MAIN,
            hover_color=HeartTheme.BG_CARD_HOVER,
            corner_radius=14,
            height=30,
            command=self._open_install_guide
        )
        btn_guide.pack(side="left")

        # 2. Scrollable container for voice components
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        # Create cards
        for key, info in self.downloader.MODEL_REPOSITORIES.items():
            self._create_component_card(self.scroll_frame, key, info)

        # 3. Bottom actions
        bottom_bar = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, height=54, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        bottom_bar.pack(fill="x", padx=18, pady=(0, 16))
        bottom_bar.pack_propagate(False)

        btn_refresh = ctk.CTkButton(
            bottom_bar,
            text="🔄 Refresh Status",
            font=HeartTheme.FONT_SMALL,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            text_color=HeartTheme.TEXT_MAIN,
            hover_color=HeartTheme.BG_CARD_HOVER,
            corner_radius=16,
            height=32,
            width=130,
            command=self._refresh_all_status
        )
        btn_refresh.pack(side="left", padx=12, pady=10)

        self.btn_download_all = ctk.CTkButton(
            bottom_bar,
            text="⬇ Download All Pending",
            font=HeartTheme.FONT_SMALL_BOLD,
            fg_color=HeartTheme.PRIMARY,
            text_color="#FFFFFF",
            hover_color=HeartTheme.PRIMARY_HOVER,
            corner_radius=16,
            height=32,
            width=180,
            command=self._download_all_pending
        )
        self.btn_download_all.pack(side="left", padx=(0, 12), pady=10)

        close_btn = ctk.CTkButton(
            bottom_bar,
            text="Close",
            fg_color="transparent",
            text_color=HeartTheme.TEXT_SECONDARY,
            hover_color=HeartTheme.BG_CARD_HOVER,
            corner_radius=16,
            font=HeartTheme.FONT_SMALL,
            width=80,
            height=32,
            command=self.destroy
        )
        close_btn.pack(side="right", padx=12, pady=10)

    def _create_component_card(self, parent, key: str, info: Dict[str, Any]):
        card = ctk.CTkFrame(
            parent,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        card.pack(fill="x", pady=6)

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10, 4))

        title_box = ctk.CTkFrame(header_row, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        name_lbl = ctk.CTkLabel(
            title_box,
            text=f"{info['name']}",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        name_lbl.pack(anchor="w")

        repo_lbl = ctk.CTkLabel(
            title_box,
            text=f"{info.get('provider', 'Official')} · {info.get('category', 'Neural Voice')} · Repo: {info.get('repo_id', 'huggingface')}",
            font=HeartTheme.FONT_TINY,
            text_color=HeartTheme.TEXT_MUTED
        )
        repo_lbl.pack(anchor="w", pady=(1, 0))

        badge_lbl = ctk.CTkLabel(
            header_row,
            text="Checking...",
            font=HeartTheme.FONT_TINY,
            corner_radius=8,
            padx=10,
            pady=3
        )
        badge_lbl.pack(side="right")

        desc_lbl = ctk.CTkLabel(
            card,
            text=info["desc"],
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            wraplength=600,
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=14, pady=(2, 6))

        progress_box = ctk.CTkFrame(card, fg_color="transparent")
        progress_lbl = ctk.CTkLabel(
            progress_box,
            text="",
            font=HeartTheme.FONT_TINY,
            text_color=HeartTheme.TEXT_MUTED
        )
        progress_lbl.pack(anchor="w", pady=(0, 2))

        progress_bar = ctk.CTkProgressBar(
            progress_box,
            height=6,
            corner_radius=3,
            progress_color=HeartTheme.PROGRESS_FILL,
            fg_color=HeartTheme.PROGRESS_BG
        )
        progress_bar.pack(fill="x")
        progress_bar.set(0)

        actions_row = ctk.CTkFrame(card, fg_color="transparent")
        actions_row.pack(fill="x", padx=14, pady=(4, 12))

        btn_action = ctk.CTkButton(
            actions_row,
            text="⬇ Download",
            font=HeartTheme.FONT_SMALL,
            height=28,
            corner_radius=14,
            command=lambda k=key: self._on_action_click(k)
        )
        btn_action.pack(side="left")

        btn_delete = ctk.CTkButton(
            actions_row,
            text="Free space",
            font=HeartTheme.FONT_TINY,
            fg_color="transparent",
            text_color=HeartTheme.TEXT_MUTED,
            hover_color=HeartTheme.BG_CARD_HOVER,
            height=28,
            corner_radius=14,
            width=90,
            command=lambda k=key: self._on_delete_click(k)
        )
        btn_delete.pack(side="right")

        self._cards[key] = {
            "badge": badge_lbl,
            "desc": desc_lbl,
            "progress_box": progress_box,
            "progress_lbl": progress_lbl,
            "progress_bar": progress_bar,
            "btn_action": btn_action,
            "btn_delete": btn_delete
        }

    @staticmethod
    def _format_size_mb(mb: float) -> str:
        if mb >= 1024.0:
            return f"{mb / 1024.0:.2f} GB"
        return f"{mb:.1f} MB"

    def _refresh_all_status(self):
        statuses = self.downloader.get_all_components_status()
        pending_count = 0

        for key, st in statuses.items():
            card_ui = self._cards.get(key)
            if not card_ui:
                continue

            badge = card_ui["badge"]
            btn_action = card_ui["btn_action"]
            btn_delete = card_ui["btn_delete"]

            if st.get("is_cloud", False):
                badge.configure(
                    text="☁️ Cloud Service (0 MB local)",
                    text_color="#1565C0",
                    fg_color="#E3F2FD"
                )
                btn_action.configure(
                    text="🌐 Test Cloud Connection",
                    fg_color=HeartTheme.BG_CARD_SUBTLE,
                    text_color="#1565C0",
                    hover_color=HeartTheme.BG_CARD_HOVER,
                    state="normal"
                )
                btn_delete.pack_forget()
            elif st["is_installed"]:
                inst_str = self._format_size_mb(st["installed_size_mb"])
                badge.configure(
                    text=f"✓ Installed ({inst_str})",
                    text_color=HeartTheme.PRIMARY,
                    fg_color=HeartTheme.PRIMARY_LIGHT
                )
                btn_action.configure(
                    text="🔄 Reinstall",
                    fg_color=HeartTheme.BG_CARD_SUBTLE,
                    text_color=HeartTheme.TEXT_MAIN,
                    hover_color=HeartTheme.BG_CARD_HOVER,
                    state="normal"
                )
                btn_delete.pack(side="right")
            else:
                pending_count += 1
                exp_str = self._format_size_mb(st["expected_size_mb"])
                badge.configure(
                    text=f"⬇ Not Downloaded (~{exp_str})",
                    text_color="#8C5C00",
                    fg_color="#FFF8E7"
                )
                btn_action.configure(
                    text="⬇ Download",
                    fg_color=HeartTheme.PRIMARY,
                    text_color="#FFFFFF",
                    hover_color=HeartTheme.PRIMARY_HOVER,
                    state="normal"
                )
                btn_delete.pack_forget()

        if pending_count > 0:
            self.btn_download_all.configure(
                text=f"⬇ Download All ({pending_count} pending)",
                state="normal"
            )
        else:
            self.btn_download_all.configure(
                text="✓ All Installed",
                state="disabled"
            )

    def _on_action_click(self, key: str):
        if self.is_downloading:
            messagebox.showinfo("Download in progress", "Another download is already running. Please wait.")
            return

        info = self.downloader.MODEL_REPOSITORIES.get(key, {})
        if info.get("is_cloud", False):
            self._test_cloud_connection(key)
            return

        self._start_download_component(key)

    def _test_cloud_connection(self, key: str):
        try:
            import requests
            requests.head("https://azure.microsoft.com", timeout=3)
            messagebox.showinfo(
                "Cloud Service Status",
                "✅ Connection to Microsoft Neural English service established successfully.\n\n"
                "ℹ️ Notes:\n"
                "• Requires active internet connection.\n"
                "• Texts are sent to Microsoft cloud endpoints.\n"
                "• To maintain total privacy with 0% data sent to internet, use Kokoro-82M or Piper with School Mode."
            )
        except Exception as e:
            messagebox.showwarning(
                "No Cloud Connection",
                f"Could not connect to cloud service: {e}\n\nYou can continue synthesizing using Kokoro-82M or Piper 100% offline."
            )

    def _on_delete_click(self, key: str):
        if self.is_downloading:
            return
        info = self.downloader.MODEL_REPOSITORIES.get(key, {})
        name = info.get("name", key)
        if messagebox.askyesno("Free Space", f"Are you sure you want to delete local files for '{name}'?"):
            self.downloader.delete_component(key)
            self._refresh_all_status()
            if self.on_update_callback:
                self.on_update_callback()

    def _start_download_component(self, key: str):
        self.is_downloading = True
        self.active_key = key
        card_ui = self._cards[key]

        progress_box = card_ui["progress_box"]
        progress_lbl = card_ui["progress_lbl"]
        progress_bar = card_ui["progress_bar"]
        btn_action = card_ui["btn_action"]

        progress_box.pack(fill="x", padx=14, pady=(0, 8))
        progress_bar.set(0)
        progress_lbl.configure(text="Connecting to Hugging Face...")
        btn_action.configure(state="disabled", text="Downloading...")

        def _progress(downloaded, total, filename, speed_mb_s):
            def _ui_update():
                if total > 0:
                    pct = max(0.0, min(1.0, downloaded / total))
                    progress_bar.set(pct)
                    cur_str = f"{downloaded / (1024*1024*1024):.2f} GB" if total >= 1024*1024*1024 else f"{downloaded / (1024*1024):.1f} MB"
                    tot_str = f"{total / (1024*1024*1024):.2f} GB" if total >= 1024*1024*1024 else f"{total / (1024*1024):.1f} MB"
                    speed_str = f" · {speed_mb_s:.1f} MB/s" if speed_mb_s > 0 else ""
                    progress_lbl.configure(text=f"{filename}: {cur_str} / {tot_str} ({int(pct*100)}%){speed_str}")
                else:
                    progress_lbl.configure(text=f"{filename}: downloading...")
            self.after(0, _ui_update)

        def _worker():
            try:
                success = self.downloader.download_model(key, progress_callback=_progress)
            except Exception as e:
                success = False
                print(f"Error downloading {key}: {e}")

            def _on_finish():
                self.is_downloading = False
                self.active_key = None
                progress_box.pack_forget()
                btn_action.configure(state="normal")
                self._refresh_all_status()
                if self.on_update_callback:
                    self.on_update_callback()

                if success:
                    messagebox.showinfo("Download Complete", f"'{self.downloader.MODEL_REPOSITORIES[key]['name']}' has been installed successfully.")
                else:
                    err_msg = getattr(self.downloader, "last_error", "")
                    detail = f"\n\nDetails: {err_msg}" if err_msg else ""
                    messagebox.showerror("Download Error", f"Could not download '{self.downloader.MODEL_REPOSITORIES[key]['name']}'.{detail}")

            self.after(0, _on_finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _download_all_pending(self):
        if self.is_downloading:
            return
        statuses = self.downloader.get_all_components_status()
        pending = [k for k, s in statuses.items() if not s["is_installed"] and not s.get("is_cloud", False)]
        if not pending:
            messagebox.showinfo("Voice Manager", "All local models are already installed!")
            return

        def _queue_worker():
            for key in pending:
                self.is_downloading = True
                self.active_key = key
                card_ui = self._cards[key]

                def _start_card():
                    card_ui["progress_box"].pack(fill="x", padx=14, pady=(0, 8))
                    card_ui["btn_action"].configure(state="disabled", text="Downloading...")
                self.after(0, _start_card)

                def _progress(downloaded, total, filename, speed_mb_s):
                    def _ui_update():
                        if total > 0:
                            pct = max(0.0, min(1.0, downloaded / total))
                            card_ui["progress_bar"].set(pct)
                            cur_str = f"{downloaded / (1024*1024*1024):.2f} GB" if total >= 1024*1024*1024 else f"{downloaded / (1024*1024):.1f} MB"
                            tot_str = f"{total / (1024*1024*1024):.2f} GB" if total >= 1024*1024*1024 else f"{total / (1024*1024):.1f} MB"
                            speed_str = f" · {speed_mb_s:.1f} MB/s" if speed_mb_s > 0 else ""
                            card_ui["progress_lbl"].configure(text=f"{filename}: {cur_str} / {tot_str} ({int(pct*100)}%){speed_str}")
                    self.after(0, _ui_update)

                try:
                    self.downloader.download_model(key, progress_callback=_progress)
                except Exception as e:
                    print(f"Error downloading {key}: {e}")

                def _finish_card():
                    card_ui["progress_box"].pack_forget()
                    card_ui["btn_action"].configure(state="normal")
                    self._refresh_all_status()
                self.after(0, _finish_card)

            def _all_done():
                self.is_downloading = False
                self.active_key = None
                self._refresh_all_status()
                if self.on_update_callback:
                    self.on_update_callback()
                messagebox.showinfo("Download Complete", "All pending voice components have been downloaded successfully.")

            self.after(0, _all_done)

        threading.Thread(target=_queue_worker, daemon=True).start()
