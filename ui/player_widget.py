"""
Audio Player and MP3 Export Widget for Podcasts with Heart.
Clean, modern, and accessible design in HeartTheme.
"""

import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pygame
import soundfile as sf
import numpy as np
from typing import Optional

from ui.theme import HeartTheme
from ui.components import CleanButton

class AudioPlayerWidget(ctk.CTkFrame):
    """Visual component to preview, track, and export generated podcasts."""

    def __init__(self, parent, audio_processor, **kwargs):
        height = kwargs.pop("height", 1)
        super().__init__(
            parent,
            fg_color=HeartTheme.BG_CARD,
            corner_radius=HeartTheme.CARD_RADIUS,
            border_width=1,
            border_color=HeartTheme.BORDER_CARD,
            height=height,
            **kwargs
        )
        self.audio_processor = audio_processor

        self.current_audio_stereo: Optional[np.ndarray] = None
        self.temp_wav_path: Optional[str] = None
        self.is_playing = False
        self.duration_seconds = 0.0
        self.current_position = 0.0
        self.stop_requested = False
        self.is_tracking = False

        self._init_mixer()
        self._build_ui()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
        except Exception as e:
            print("Warning initializing pygame.mixer:", e)

    def _build_ui(self):
        # Header row
        title_row = ctk.CTkFrame(self, fg_color="transparent", height=1)
        title_row.pack(fill="x", padx=18, pady=(12, 4))

        title_lbl = ctk.CTkLabel(
            title_row,
            text="🎧 Podcast Audio Player",
            font=HeartTheme.FONT_SUBTITLE,
            text_color=HeartTheme.TEXT_MAIN
        )
        title_lbl.pack(side="left")

        self.status_badge = ctk.CTkLabel(
            title_row,
            text="No audio loaded",
            font=HeartTheme.FONT_SMALL,
            text_color=HeartTheme.TEXT_MUTED,
            fg_color=HeartTheme.BG_CARD_SUBTLE,
            corner_radius=10,
            padx=10,
            pady=3
        )
        self.status_badge.pack(side="right")

        # Time progress slider row
        prog_row = ctk.CTkFrame(self, fg_color="transparent", height=1)
        prog_row.pack(fill="x", padx=18, pady=(2, 6))

        self.time_current_lbl = ctk.CTkLabel(
            prog_row,
            text="00:00",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_SECONDARY
        )
        self.time_current_lbl.pack(side="left")

        self.progress_slider = ctk.CTkSlider(
            prog_row,
            from_=0.0,
            to=100.0,
            height=14,
            progress_color=HeartTheme.PRIMARY,
            button_color=HeartTheme.PRIMARY,
            button_hover_color=HeartTheme.PRIMARY_HOVER,
            fg_color=HeartTheme.PROGRESS_BG,
            command=self._on_seek
        )
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=12)
        self.progress_slider.set(0.0)

        self.time_total_lbl = ctk.CTkLabel(
            prog_row,
            text="00:00",
            font=HeartTheme.FONT_SMALL_BOLD,
            text_color=HeartTheme.TEXT_SECONDARY
        )
        self.time_total_lbl.pack(side="right")

        # Control and export row
        controls_row = ctk.CTkFrame(self, fg_color="transparent", height=1)
        controls_row.pack(fill="x", padx=18, pady=(2, 12))

        btn_frame = ctk.CTkFrame(controls_row, fg_color="transparent", height=1)
        btn_frame.pack(side="left")

        self.play_btn = CleanButton(
            btn_frame,
            style="primary",
            text="▶ Play",
            width=110,
            height=32,
            state="disabled",
            command=self.toggle_play_pause
        )
        self.play_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = CleanButton(
            btn_frame,
            style="ghost",
            text="■ Stop",
            width=75,
            height=32,
            state="disabled",
            command=self.stop
        )
        self.stop_btn.pack(side="left")

        self.export_btn = CleanButton(
            controls_row,
            style="accent",
            text="💾 Save MP3 (160k)",
            height=32,
            state="disabled",
            command=self._export_mp3_dialog
        )
        self.export_btn.pack(side="right")

    def load_audio(self, stereo_audio: np.ndarray, title: str = "Podcast"):
        """Loads newly synthesized stereo audio into player."""
        self.stop()
        self.current_audio_stereo = stereo_audio
        num_samples = stereo_audio.shape[1]
        self.duration_seconds = float(num_samples) / float(self.audio_processor.sample_rate)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass

        tmp_dir = os.path.join(os.path.expanduser("~"), ".podcasts_heart")
        os.makedirs(tmp_dir, exist_ok=True)
        self.temp_wav_path = os.path.join(tmp_dir, f"podcast_{int(time.time() * 1000)}.wav")

        audio_clipped = np.clip(stereo_audio.T, -1.0, 1.0)
        sf.write(self.temp_wav_path, audio_clipped, self.audio_processor.sample_rate, subtype='PCM_16')

        self.time_total_lbl.configure(text=self._format_time(self.duration_seconds))
        self.time_current_lbl.configure(text="00:00")
        self.progress_slider.configure(to=max(1.0, self.duration_seconds))
        self.progress_slider.set(0.0)

        self.play_btn.configure(state="normal", text="▶ Play")
        self.stop_btn.configure(state="normal")
        self.export_btn.configure(state="normal")
        self.status_badge.configure(
            text=f"Ready ({self._format_time(self.duration_seconds)})",
            text_color=HeartTheme.PRIMARY
        )

    def toggle_play_pause(self):
        if not self.temp_wav_path or not os.path.exists(self.temp_wav_path):
            return

        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_btn.configure(text="▶ Play")
            self.status_badge.configure(text="Paused", text_color=HeartTheme.TEXT_MUTED)
        else:
            if self.is_tracking:
                pygame.mixer.music.unpause()
            else:
                try:
                    pygame.mixer.music.load(self.temp_wav_path)
                    pygame.mixer.music.play(start=self.current_position)
                    self._start_tracker()
                except Exception as e:
                    messagebox.showerror("Audio Error", f"Could not play audio: {e}")
                    return

            self.is_playing = True
            self.play_btn.configure(text="⏸ Pause")
            self.status_badge.configure(text="Playing", text_color=HeartTheme.PRIMARY)

    def stop(self):
        self.stop_requested = True
        self.is_playing = False
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        self.current_position = 0.0
        self.progress_slider.set(0.0)
        self.time_current_lbl.configure(text="00:00")
        self.play_btn.configure(text="▶ Play")
        if self.current_audio_stereo is not None:
            self.status_badge.configure(text="Stopped", text_color=HeartTheme.TEXT_MUTED)

    def _on_seek(self, val):
        self.current_position = float(val)
        self.time_current_lbl.configure(text=self._format_time(self.current_position))
        if self.is_playing:
            try:
                pygame.mixer.music.play(start=self.current_position)
            except Exception:
                pass

    def _start_tracker(self):
        self.is_tracking = True
        self.stop_requested = False
        thread = threading.Thread(target=self._tracker_worker, daemon=True)
        thread.start()

    def _tracker_worker(self):
        start_time = time.time() - self.current_position
        while not self.stop_requested and self.is_tracking:
            if self.is_playing:
                elapsed = time.time() - start_time
                self.current_position = elapsed

                if elapsed >= self.duration_seconds:
                    self.current_position = self.duration_seconds
                    self._safe_update_ui()
                    self.stop()
                    break

                self._safe_update_ui()
            else:
                start_time = time.time() - self.current_position

            time.sleep(0.05)

        self.is_tracking = False

    def _safe_update_ui(self):
        try:
            self.after(0, self._apply_ui_update)
        except Exception:
            pass

    def _apply_ui_update(self):
        self.progress_slider.set(self.current_position)
        self.time_current_lbl.configure(text=self._format_time(self.current_position))

    def _format_time(self, seconds: float) -> str:
        s = int(seconds)
        m = s // 60
        s %= 60
        return f"{m:02d}:{s:02d}"

    def _export_mp3_dialog(self):
        if self.current_audio_stereo is None:
            return

        out_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Audio (*.mp3)", "*.mp3"), ("WAV Audio (*.wav)", "*.wav")],
            initialfile="podcast_episode.mp3",
            title="Save Podcast Audio"
        )
        if not out_path:
            return

        try:
            if out_path.lower().endswith(".wav"):
                sf.write(out_path, self.current_audio_stereo.T, self.audio_processor.sample_rate)
            else:
                self.audio_processor.export_mp3(self.current_audio_stereo, out_path, bitrate="160k")

            messagebox.showinfo("Export Complete", f"Your podcast audio was saved successfully to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export audio: {e}")
