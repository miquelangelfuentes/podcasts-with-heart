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

from core.update_manager import (
    extract_windows_release,
    get_windows_asset,
    is_newer_release,
    make_windows_update_script,
)

from ui.theme import HeartTheme
from ui.components import CleanButton

APP_VERSION = "1.0.2"
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
        self._latest_release_data = None
        self._pending_updater_script = None
        self._pending_update_stage = None
        self._updater_launched = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close_modal)
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
            text="Latest published release notes:",
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


        self.btn_update = CleanButton(
            footer,
            style="primary",
            text="⬇️ Update application",
            width=180,
            height=32,
            command=self._on_update_clicked,
        )
        self.btn_update.pack(side="left", padx=(12, 4), pady=10)
        self.btn_update.configure(state="disabled")

        self.btn_github = CleanButton(
            footer,
            style="ghost",
            text="🌐 Open on GitHub",
            width=140,
            height=32,
            command=self._open_github_repo
        )
        self.btn_github.pack(side="left", padx=4, pady=10)

        btn_close = CleanButton(
            footer,
            style="ghost",
            text="Close",
            width=80,
            height=32,
            command=self._close_modal
        )
        btn_close.pack(side="right", padx=12, pady=10)

    def _start_check_thread(self):
        threading.Thread(target=self._check_github_worker, daemon=True).start()

    def _check_github_worker(self):
        """Check the published release rather than unreleased commits."""
        try:
            url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            headers = {
                "User-Agent": "PodcastsWithHeart-Updater",
                "Accept": "application/vnd.github+json",
                "Cache-Control": "no-cache",
            }
            response = requests.get(url, headers=headers, timeout=(10, 20))
            response.raise_for_status()
            release = response.json()
            # Validate the release tag before enabling the update button.
            is_newer_release(APP_VERSION, release.get("tag_name", ""))
            self.after(0, lambda data=release: self._on_check_success(data))
        except Exception as e:
            error_message = str(e)
            self.after(0, lambda message=error_message: self._on_check_error(message))

    def _on_check_success(self, release: dict):
        self._latest_release_data = release
        self._latest_release_tag = release["tag_name"]
        self.prog_bar.stop()
        self.prog_bar.configure(mode="determinate")
        self.prog_bar.set(1.0)

        newer = is_newer_release(APP_VERSION, self._latest_release_tag)
        details = release.get("body") or "No release notes available."
        self.commits_box.configure(state="normal")
        self.commits_box.delete("1.0", "end")
        self.commits_box.insert("1.0", details)
        self.commits_box.configure(state="disabled")

        if newer:
            try:
                if getattr(sys, "frozen", False):
                    get_windows_asset(release)
            except ValueError as e:
                self._update_available = False
                self.state_lbl.configure(
                    text=f"A new release ({self._latest_release_tag}) is published but its Windows package is missing or invalid: {e}",
                    text_color="#c0392b",
                )
                self.btn_update.configure(state="disabled")
                return

            self._update_available = True
            self.state_lbl.configure(
                text=f"New release available: {self._latest_release_tag} (installed: v{APP_VERSION}).",
                text_color=HeartTheme.PRIMARY,
            )
            self.btn_update.configure(state="normal", text="⬇️ Update application")
        else:
            self._update_available = False
            self.state_lbl.configure(
                text=f"You're running the latest published version (v{APP_VERSION}).",
                text_color=HeartTheme.TEXT_MAIN,
            )
            self.btn_update.configure(state="disabled", text="✅ Up to date")

    def _on_check_error(self, err_msg: str):
        self.prog_bar.stop()
        self.prog_bar.configure(mode="determinate")
        self.prog_bar.set(0.0)
        self._update_available = False
        self.btn_update.configure(state="disabled")
        self.state_lbl.configure(
            text=f"Could not verify the latest published release:\n{err_msg}",
            wraplength=580,
            text_color="#c0392b",
        )
        self.commits_box.configure(state="normal")
        self.commits_box.delete("1.0", "end")
        self.commits_box.insert(
            "1.0",
            "You can download the Windows package manually from GitHub Releases.",
        )
        self.commits_box.configure(state="disabled")

    def _open_github_repo(self):
        webbrowser.open(f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest")

    def _on_update_clicked(self):
        if self._is_updating or not self._update_available:
            return
        if self._pending_updater_script and os.path.isfile(self._pending_updater_script):
            self._prompt_restart_updater(self._pending_updater_script)
            return

        # Do not overwrite source checkouts automatically.
        if not getattr(sys, "frozen", False):
            from tkinter import messagebox
            messagebox.showinfo(
                "Updating from source",
                "This installation runs from source. "
                "Use Git to update the checkout or download a packaged release from GitHub.",
            )
            self._open_github_repo()
            return

        self._is_updating = True
        self.btn_update.configure(state="disabled", text="⏳ Downloading...")
        threading.Thread(target=self._run_auto_update, daemon=True).start()

    def _run_auto_update(self):
        """Download a versioned Windows ZIP, validate it, and prepare the helper."""
        import shutil

        stage = None
        try:
            release = self._latest_release_data
            if not release or not is_newer_release(APP_VERSION, release["tag_name"]):
                raise RuntimeError("No newer published release has been confirmed.")
            asset = get_windows_asset(release)
            stage = tempfile.mkdtemp(prefix="podcasts_heart_update_")
            archive_path = os.path.join(stage, asset["name"])
            extract_path = os.path.join(stage, "extracted")

            self.after(0, lambda: self.state_lbl.configure(
                text=f"Downloading {release['tag_name']} from GitHub...",
                text_color=HeartTheme.PRIMARY,
            ))
            response = requests.get(
                asset["browser_download_url"],
                stream=True,
                headers={"User-Agent": "PodcastsWithHeart-Updater"},
                timeout=(15, 120),
            )
            response.raise_for_status()
            try:
                total_bytes = 0
                expected_bytes = int(response.headers.get("Content-Length", 0))
                last_reported_mb = 0
                with open(archive_path, "wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            total_bytes += len(chunk)
                            if total_bytes > 2 * 1024 * 1024 * 1024:
                                raise ValueError("The update package exceeds the allowed size (2 GB).")
                            output.write(chunk)
                            current_mb = total_bytes // (1024 * 1024)
                            if current_mb - last_reported_mb >= 10:
                                last_reported_mb = current_mb
                                total_mb = (expected_bytes + 1048575) // 1048576 if expected_bytes else 0
                                message = (
                                    f"Downloading {release['tag_name']}: {current_mb} of {total_mb} MB..."
                                    if total_mb else
                                    f"Downloading {release['tag_name']}: {current_mb} MB..."
                                )
                                self.after(0, lambda msg=message: self.state_lbl.configure(text=msg))
            finally:
                response.close()

            if not zipfile.is_zipfile(archive_path):
                raise RuntimeError("The downloaded file is not a valid ZIP archive.")
            self.after(0, lambda: self.state_lbl.configure(
                text="Verifying and unpacking the update archive...",
                text_color=HeartTheme.PRIMARY,
            ))
            source_dir = extract_windows_release(archive_path, extract_path)
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            # The helper is outside the staging folder so it can delete that folder.
            updater_file = tempfile.NamedTemporaryFile(
                mode="w", prefix="podcasts_heart_apply_", suffix=".ps1",
                encoding="utf-8-sig", delete=False,
            )
            script_path = updater_file.name
            updater_file.close()
            script = make_windows_update_script(
                source_dir=source_dir,
                install_dir=exe_dir,
                exe_path=os.path.abspath(sys.executable),
                parent_pid=os.getpid(),
                version=release["tag_name"],
                staging_dir=stage,
            )
            # BOM ensures PowerShell 5.1 handles Unicode file paths.
            with open(script_path, "w", encoding="utf-8-sig") as script_file:
                script_file.write(script)

            self._pending_updater_script = script_path
            self._pending_update_stage = stage
            self.after(0, lambda path=script_path: self._prompt_restart_updater(path))
        except Exception as e:
            error_message = str(e)
            if stage:
                shutil.rmtree(stage, ignore_errors=True)
            self.after(0, lambda message=error_message: self._on_update_error(message))
        finally:
            self._is_updating = False

    def _on_update_error(self, error_message: str):
        self.state_lbl.configure(
            text=f"Could not prepare update: {error_message}",
            text_color="#c0392b",
        )
        self.btn_update.configure(state="normal", text="Retry update")

    def _prompt_restart_updater(self, script_path: str):
        from tkinter import messagebox

        self.btn_update.configure(state="normal", text="Apply now")
        answer = messagebox.askyesno(
            "Restart to update",
            f"Release {self._latest_release_tag} was downloaded and verified.\n\n"
            "The application must close so Windows can replace its files. "
            "Your installed voice models will be preserved.\n\n"
            "Install the update and restart now?",
        )
        if not answer:
            self.state_lbl.configure(
                text="Update ready. Click Apply now when you want to restart.",
                text_color=HeartTheme.TEXT_MAIN,
            )
            return

        try:
            # Run an external helper that waits for this process to exit.
            subprocess.Popen(
                [
                    "powershell.exe", "-NoProfile", "-NonInteractive",
                    "-ExecutionPolicy", "Bypass", "-File", script_path,
                ],
                creationflags=0x08000000 | 0x00000200,
                close_fds=True,
            )
        except Exception as e:
            self._on_update_error(str(e))
            return

        self._updater_launched = True
        self.parent.destroy()
        sys.exit(0)

    def _close_modal(self):
        """Clean up deferred downloads if the dialog is closed."""
        import shutil
        if not self._updater_launched:
            if self._pending_update_stage:
                shutil.rmtree(self._pending_update_stage, ignore_errors=True)
                self._pending_update_stage = None
            if self._pending_updater_script:
                try:
                    os.unlink(self._pending_updater_script)
                except OSError:
                    pass
                self._pending_updater_script = None
        self.destroy()
