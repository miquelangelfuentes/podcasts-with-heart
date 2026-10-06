"""
Visual Components with High-Contrast Accessible Design (High-Contrast Clean UI).
Strict WCAG AAA compliance for Podcasts with Heart:
- Red / Crimson backgrounds -> ALWAYS pure white text (#FFFFFF).
- Light / White backgrounds -> ALWAYS crisp dark contrast text (#261316).
"""

import customtkinter as ctk
from typing import List, Callable, Optional
from ui.theme import HeartTheme

class PillSelector(ctk.CTkFrame):
    """Pill selector with maximum contrast between active and inactive states."""

    def __init__(
        self,
        master,
        values: List[str],
        default_val: Optional[str] = None,
        command: Optional[Callable[[str], None]] = None,
        height: int = 32,
        font_size: int = 10,
        expand_buttons: bool = False,
        btn_width: Optional[int] = None,
        **kwargs
    ):
        super().__init__(master, fg_color=HeartTheme.PRIMARY_LIGHT, corner_radius=int(height / 2), **kwargs)
        self.values = values
        self.command = command
        self.selected_value = default_val or (values[0] if values else "")
        self.buttons = {}
        self.height = height
        self.font_size = font_size
        self.expand_buttons = expand_buttons

        for val in values:
            b_width = btn_width if btn_width is not None else (0 if expand_buttons else 140)
            btn_kwargs = {
                "master": self,
                "text": val,
                "height": height - 6,
                "corner_radius": int((height - 6) / 2),
                "font": ("Segoe UI", font_size, "bold"),
                "command": lambda v=val: self.select(v)
            }
            if expand_buttons or btn_width is not None:
                btn_kwargs["width"] = b_width

            btn = ctk.CTkButton(**btn_kwargs)
            if expand_buttons:
                btn.pack(side="left", expand=True, fill="both", padx=1, pady=2)
            else:
                btn.pack(side="left", padx=2, pady=3)
            self.buttons[val] = btn

        self._update_styles()

    def select(self, val: str):
        if val not in self.values:
            return
        self.selected_value = val
        self._update_styles()
        if self.command:
            self.command(val)

    def set(self, val: str):
        if val in self.values:
            self.selected_value = val
            self._update_styles()

    def get(self) -> str:
        return self.selected_value

    def _update_styles(self):
        for val, btn in self.buttons.items():
            if val == self.selected_value:
                # ACTIVE: Warm crimson background with pure white text
                btn.configure(
                    fg_color=HeartTheme.PRIMARY,
                    hover_color=HeartTheme.PRIMARY_HOVER,
                    text_color="#FFFFFF"
                )
            else:
                # INACTIVE: Transparent with dark legible text
                btn.configure(
                    fg_color="transparent",
                    hover_color="#F8DEE2",
                    text_color=HeartTheme.TEXT_MAIN
                )

class CleanButton(ctk.CTkButton):
    """Button with predefined accessible contrast styles."""

    def __init__(self, master, style="primary", **kwargs):
        height = kwargs.pop("height", 32)
        corner_radius = kwargs.pop("corner_radius", int(height / 2))
        font = kwargs.pop("font", ("Segoe UI", 10, "bold"))

        if style == "primary":
            fg_color = HeartTheme.PRIMARY
            hover_color = HeartTheme.PRIMARY_HOVER
            text_color = "#FFFFFF"
            border_width = 0
            border_color = None
        elif style == "accent":
            fg_color = HeartTheme.ACCENT_CORAL
            hover_color = HeartTheme.ACCENT_CORAL_HOVER
            text_color = "#FFFFFF"
            border_width = 0
            border_color = None
        elif style == "danger":
            fg_color = HeartTheme.ACCENT_DANGER
            hover_color = "#B82729"
            text_color = "#FFFFFF"
            border_width = 0
            border_color = None
        elif style == "ghost":
            fg_color = "#FFFFFF"
            hover_color = HeartTheme.BG_CARD_HOVER
            text_color = HeartTheme.TEXT_MAIN
            border_width = 1
            border_color = HeartTheme.BORDER_CARD
        else:  # "subtle"
            fg_color = HeartTheme.PRIMARY_LIGHT
            hover_color = "#F8DEE2"
            text_color = HeartTheme.TEXT_MAIN
            border_width = 1
            border_color = HeartTheme.ENTRY_BORDER

        kwargs["height"] = height
        kwargs["corner_radius"] = corner_radius
        kwargs["font"] = font
        kwargs["fg_color"] = fg_color
        kwargs["hover_color"] = hover_color
        kwargs["text_color"] = text_color
        kwargs["border_width"] = border_width
        if border_color is not None:
            kwargs["border_color"] = border_color

        super().__init__(master, **kwargs)

    def configure(self, **kwargs):
        if "style" in kwargs:
            style = kwargs.pop("style")
            if style == "primary":
                kwargs.update({
                    "fg_color": HeartTheme.PRIMARY,
                    "hover_color": HeartTheme.PRIMARY_HOVER,
                    "text_color": "#FFFFFF",
                    "border_width": 0,
                })
            elif style == "accent":
                kwargs.update({
                    "fg_color": HeartTheme.ACCENT_CORAL,
                    "hover_color": HeartTheme.ACCENT_CORAL_HOVER,
                    "text_color": "#FFFFFF",
                    "border_width": 0,
                })
            elif style == "danger":
                kwargs.update({
                    "fg_color": HeartTheme.ACCENT_DANGER,
                    "hover_color": "#B82729",
                    "text_color": "#FFFFFF",
                    "border_width": 0,
                })
            elif style == "ghost":
                kwargs.update({
                    "fg_color": "#FFFFFF",
                    "hover_color": HeartTheme.BG_CARD_HOVER,
                    "text_color": HeartTheme.TEXT_MAIN,
                    "border_width": 1,
                    "border_color": HeartTheme.BORDER_CARD,
                })
            else:  # "subtle"
                kwargs.update({
                    "fg_color": HeartTheme.PRIMARY_LIGHT,
                    "hover_color": "#F8DEE2",
                    "text_color": HeartTheme.TEXT_MAIN,
                    "border_width": 1,
                    "border_color": HeartTheme.ENTRY_BORDER,
                })
        return super().configure(**kwargs)

    def config(self, **kwargs):
        return self.configure(**kwargs)
