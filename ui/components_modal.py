"""
Models and Voice Manager Modal for Podcasts with Heart.
Inspects local voice models (Piper English), disk status, and downloads voices from Hugging Face.
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Dict, Any, Optional

from ui.theme import HeartTheme
from core.model_downloader import ModelDownloader

class ComponentsManagerModal(ctk.CTkToplevel):
    """Modal dialog managing offline English voice models."""

    def __init__(self, parent, on_update_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.on_update_callback = on_update_callback
        self.downloader = ModelDownloader()

        self.title("📦 Voice Models Manager — Podcasts with Heart")
        self.geometry("700x560")
        self.minsize(620, 480)
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self.active_download_key = None
        self._build_ui()
        self._refresh_components()

    def _build_ui(self):
        # Header panel
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
            text="Manage offline neural models. Download once and generate podcasts 100% locally with zero internet.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY
        )
        desc_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # Scrollable container for voice components
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        # Bottom actions
        bottom_bar = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        bottom_bar.pack(fill="x", padx=18, pady=(0, 16))

        close_btn = ctk.CTkButton(
            bottom_bar,
            text="Close",
            fg_color=HeartTheme.PRIMARY,
            hover_color=HeartTheme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=HeartTheme.FONT_SMALL_BOLD,
            width=100,
            command=self.destroy
        )
        close_btn.pack(side="right", padx=14, pady=10)

    def _refresh_components(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for key in self.downloader.MODEL_REPOSITORIES.keys():
            status = self.downloader.get_component_status(key)
            self._create_component_card(status)

    def _create_component_card(self, status: Dict[str, Any]):
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD
        )
        card.pack(fill="x", pady=6)

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=14, pady=(10, 4))

        name_lbl = ctk.CTkLabel(
            header_row,
            text=status["name"],
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        name_lbl.pack(side="left")

        is_cloud = status.get("is_cloud", False)
        is_installed = status["is_installed"]

        if is_cloud:
            badge_text = "☁️ Cloud Service (Online)"
            badge_fg = "#E3F2FD"
            badge_tc = "#1565C0"
        elif is_installed:
            inst_mb = status.get("installed_size_mb", 0)
            badge_text = f"✓ Installed ({inst_mb} MB)"
            badge_fg = HeartTheme.PRIMARY_LIGHT
            badge_tc = HeartTheme.PRIMARY
        else:
            exp_mb = status.get("expected_size_mb", 0)
            badge_text = f"⬇ Not Downloaded (~{exp_mb} MB)"
            badge_fg = "#FFF8E7"
            badge_tc = "#8C5C00"

        badge = ctk.CTkLabel(
            header_row,
            text=badge_text,
            font=HeartTheme.FONT_TINY,
            fg_color=badge_fg,
            text_color=badge_tc,
            corner_radius=8,
            padx=8,
            pady=2
        )
        badge.pack(side="right")

        desc_lbl = ctk.CTkLabel(
            card,
            text=status["desc"],
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            wraplength=600,
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=14, pady=(0, 8))

        # Controls row
        ctrl_row = ctk.CTkFrame(card, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=14, pady=(0, 10))

        if not status.get("is_cloud"):
            size_txt = f"Size: ~{status['expected_size_mb']} MB"
            size_lbl = ctk.CTkLabel(
                ctrl_row,
                text=size_txt,
                font=HeartTheme.FONT_TINY,
                text_color=HeartTheme.TEXT_MUTED
            )
            size_lbl.pack(side="left")

            if is_installed:
                del_btn = ctk.CTkButton(
                    ctrl_row,
                    text="Delete",
                    fg_color="transparent",
                    border_width=1,
                    border_color=HeartTheme.BORDER_CARD,
                    hover_color=HeartTheme.BG_CARD_HOVER,
                    text_color=HeartTheme.TEXT_MUTED,
                    width=75,
                    height=26,
                    font=HeartTheme.FONT_TINY,
                    command=lambda k=status["key"]: self._delete_voice(k)
                )
                del_btn.pack(side="right")
            else:
                dl_btn = ctk.CTkButton(
                    ctrl_row,
                    text="⬇ Download",
                    fg_color=HeartTheme.PRIMARY,
                    hover_color=HeartTheme.PRIMARY_HOVER,
                    text_color="#FFFFFF",
                    width=95,
                    height=26,
                    font=HeartTheme.FONT_TINY,
                    command=lambda k=status["key"]: self._download_voice(k)
                )
                dl_btn.pack(side="right")
        else:
            cloud_lbl = ctk.CTkLabel(
                ctrl_row,
                text="☁️ Online Cloud Service · 0 MB local storage · Requires internet connection (Edge TTS)",
                font=HeartTheme.FONT_TINY,
                text_color="#1565C0"
            )
            cloud_lbl.pack(side="left")

    def _download_voice(self, model_key: str):
        if self.active_download_key:
            messagebox.showwarning("Busy", "Another download is already in progress.")
            return

        self.active_download_key = model_key

        def worker():
            success = self.downloader.download_model(model_key)
            self.active_download_key = None
            self.after(0, self._on_download_complete, success)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _on_download_complete(self, success: bool):
        if success:
            messagebox.showinfo("Success", "Voice model downloaded successfully!")
            self._refresh_components()
            if self.on_update_callback:
                self.on_update_callback()
        else:
            messagebox.showerror("Download Error", f"Download failed: {self.downloader.last_error}")
            self._refresh_components()

    def _delete_voice(self, model_key: str):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this voice model from local disk?")
        if confirm:
            self.downloader.delete_model(model_key)
            self._refresh_components()
            if self.on_update_callback:
                self.on_update_callback()
