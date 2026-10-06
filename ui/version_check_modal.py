"""
Version Check and Self-Update Modal for Podcasts with Heart.
Checks the official repository (miquelangelfuentes/podcasts-with-heart) for the latest release/commits.
"""

import os
import sys
import time
import json
import zipfile
import tempfile
import threading
import subprocess
import webbrowser
import requests
import customtkinter as ctk
from typing import Optional, Dict, Any

from ui.theme import HeartTheme
from ui.components import CleanButton

APP_VERSION = "1.0.0"
GITHUB_OWNER = "miquelangelfuentes"
GITHUB_REPO = "podcasts-with-heart"

class VersionCheckModal(ctk.CTkToplevel):
    """Modal dialog to check for updates and view recent releases."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Check for Updates — Podcasts with Heart")
        self.geometry("640x560")
        self.minsize(580, 480)
        self.configure(fg_color=HeartTheme.BG_MAIN)
        self.transient(parent)
        self.grab_set()

        self._set_modal_icon()
        self._update_available = False
        self._latest_commit_sha = ""
        self._latest_commit_msg = ""
        self._latest_release_tag = ""
        self._is_updating = False

        self._build_ui()
        self._start_check_thread()

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
            text="Check for Updates & Releases",
            font=HeartTheme.FONT_TITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        title_lbl.pack(anchor="w", padx=16, pady=(12, 2))

        desc_lbl = ctk.CTkLabel(
            header,
            text="Check for new features, voice enhancements, or bug fixes\non the official GitHub repository.",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_SECONDARY,
            justify="left"
        )
        desc_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        self.status_card = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, corner_radius=10, border_width=1, border_color=HeartTheme.BORDER_CARD)
        self.status_card.pack(fill="x", padx=18, pady=(0, 10))

        ver_row = ctk.CTkFrame(self.status_card, fg_color="transparent")
        ver_row.pack(fill="x", padx=16, pady=(12, 6))

        local_lbl = ctk.CTkLabel(
            ver_row,
            text=f"Installed Version:  v{APP_VERSION}",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        local_lbl.pack(side="left")

        self.state_lbl = ctk.CTkLabel(
            self.status_card,
            text="Connecting to GitHub to verify the latest releases...",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED,
            wraplength=580,
            justify="left"
        )
        self.state_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        self.prog_bar = ctk.CTkProgressBar(self.status_card, height=6, corner_radius=3, fg_color=HeartTheme.BG_CARD_SUBTLE, progress_color=HeartTheme.PRIMARY)
        self.prog_bar.pack(fill="x", padx=16, pady=(0, 12))
        self.prog_bar.configure(mode="indeterminate")
        self.prog_bar.start()

        changes_header = ctk.CTkFrame(self, fg_color="transparent")
        changes_header.pack(fill="x", padx=18, pady=(4, 4))

        self.changes_title = ctk.CTkLabel(
            changes_header,
            text="Recent Project Activity & Changes:",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_MAIN
        )
        self.changes_title.pack(side="left")

        self.commits_box = ctk.CTkTextbox(
            self,
            fg_color=HeartTheme.BG_CARD,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD,
            corner_radius=8,
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MAIN,
            wrap="word",
            activate_scrollbars=True
        )
        self.commits_box.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        self.commits_box.insert("1.0", "Fetching latest updates...")
        self.commits_box.configure(state="disabled")

        footer = ctk.CTkFrame(self, fg_color=HeartTheme.BG_CARD, height=52, corner_radius=12, border_width=1, border_color=HeartTheme.BORDER_CARD)
        footer.pack(fill="x", padx=18, pady=(0, 16))
        footer.pack_propagate(False)

        self.btn_github = CleanButton(
            footer,
            style="ghost",
            text="🌐 Open on GitHub",
            width=140,
            height=32,
            command=self._open_github_repo
        )
        self.btn_github.pack(side="left", padx=12, pady=10)

        btn_close = CleanButton(
            footer,
            style="ghost",
            text="Close",
            width=80,
            height=32,
            command=self.destroy
        )
        btn_close.pack(side="right", padx=12, pady=10)

    def _start_check_thread(self):
        t = threading.Thread(target=self._check_github_worker, daemon=True)
        t.start()

    def _check_github_worker(self):
        time.sleep(0.3)
        try:
            headers = {"User-Agent": "PodcastsWithHeart-Updater"}
            commits_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?per_page=5"

            res = requests.get(commits_url, headers=headers, timeout=12)
            if res.status_code == 200:
                commits = res.json()
                if commits and len(commits) > 0:
                    latest = commits[0]
                    self._latest_commit_sha = latest.get("sha", "")[:7]
                    commit_msg = latest.get("commit", {}).get("message", "").split("\n")[0]
                    self._latest_commit_msg = commit_msg
                    change_lines = []
                    for c in commits:
                        sha = c.get("sha", "")[:7]
                        msg = c.get("commit", {}).get("message", "").split("\n")[0]
                        dt = c.get("commit", {}).get("author", {}).get("date", "")[:10]
                        change_lines.append(f"• [{sha}] {msg}\n  ({dt})")

                    changes_text = "\n\n".join(change_lines)
                    self.after(0, lambda: self._on_check_success(self._latest_commit_sha, commit_msg, changes_text))
                    return

            rel_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            r_rel = requests.get(rel_url, headers=headers, timeout=10)
            if r_rel.status_code == 200:
                rel = r_rel.json()
                tag = rel.get("tag_name", "v1.0.0")
                body = rel.get("body", "No release notes available.")
                self.after(0, lambda: self._on_check_success(tag, tag, body))
                return

            self.after(0, lambda: self._on_check_error(f"GitHub status code: {res.status_code}"))

        except Exception as e:
            self.after(0, lambda: self._on_check_error(str(e)))

    def _on_check_success(self, version_or_sha: str, summary: str, details: str):
        try:
            self.prog_bar.stop()
            self.prog_bar.configure(mode="determinate")
            self.prog_bar.set(1.0)
        except Exception:
            pass

        self.state_lbl.configure(
            text=f"Latest GitHub Status: {version_or_sha}\n{summary}",
            wraplength=580,
            text_color=HeartTheme.TEXT_MAIN
        )
        self.commits_box.configure(state="normal")
        self.commits_box.delete("1.0", "end")
        self.commits_box.insert("1.0", details)
        self.commits_box.configure(state="disabled")

    def _on_check_error(self, err_msg: str):
        try:
            self.prog_bar.stop()
            self.prog_bar.configure(mode="determinate")
            self.prog_bar.set(0.0)
        except Exception:
            pass
        self.state_lbl.configure(
            text=f"Could not reach GitHub releases: {err_msg}",
            wraplength=580,
            text_color=HeartTheme.TEXT_MUTED
        )
        self.commits_box.configure(state="normal")
        self.commits_box.delete("1.0", "end")
        self.commits_box.insert("1.0", "Check your internet connection or visit the GitHub repository directly.")
        self.commits_box.configure(state="disabled")

    def _open_github_repo(self):
        webbrowser.open_new_tab(f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}")
