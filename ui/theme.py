"""
Color Palette and Visual Styling: Modern Heart Studio (Pastel Red & Warm Rose).
Clean contemporary Scandinavian / Japanese studio design.
Strict WCAG AAA compliance:
- Red / dark backgrounds -> ALWAYS pure white text (#FFFFFF).
- Light / white backgrounds -> ALWAYS crisp dark contrast text (#261316).
"""

class HeartTheme:
    # Backgrounds and surfaces
    BG_MAIN = "#FDF8F9"         # Soft warm porcelain with delicate rose tint
    BG_CARD = "#FFFFFF"         # Pure white for main cards and panels
    BG_CARD_HOVER = "#FBF2F4"   # Subtle hover surface
    BG_CARD_SUBTLE = "#FAF0F2"  # Background for internal speaker cards and lists
    BORDER_CARD = "#F3E1E4"     # Elegant 1px hairline border
    BORDER_FOCUS = "#B83A4B"    # Clean focus outline
    CARD_RADIUS = 14            # Modern smooth 14px rounded corners
    PILL_RADIUS = 16            # Modern pill buttons

    # Core Heart Crimson / Coral Reds (Deep, refined, warm contrast)
    PRIMARY = "#B83A4B"         # Refined warm crimson heart red
    PRIMARY_HOVER = "#9E2E3D"   # Rich darker tone on hover
    PRIMARY_ACTIVE = "#852230"  # Active / pressed state
    PRIMARY_LIGHT = "#FCEBEC"   # Delicate blush background for active pills & tags
    PRIMARY_MUTED = "#C76573"   # Soft muted berry for secondary borders/icons

    # Complementary warm accents
    ACCENT_CORAL = "#E06D53"    # Warm terracotta coral
    ACCENT_CORAL_HOVER = "#C9573E"
    ACCENT_BERRY = "#8C2535"    # Deep berry tone
    ACCENT_DANGER = "#D9383A"   # Crisp red for stop/cancel actions

    # High contrast typography (WCAG AAA)
    TEXT_MAIN = "#261316"       # Deep warm espresso-charcoal on light surfaces
    TEXT_SECONDARY = "#5C3E43"  # Soft berry-charcoal for subtitles and labels
    TEXT_MUTED = "#82666B"      # Discreet muted text for hints and secondary badges
    TEXT_ON_PRIMARY = "#FFFFFF" # Pure white on crimson / dark backgrounds

    # Input controls and text areas
    ENTRY_BG = "#FFFAFB"        # Light neutral ivory-rose for script editor
    ENTRY_BORDER = "#E8D3D6"

    # Audio player
    PROGRESS_BG = "#F5E3E6"
    PROGRESS_FILL = "#B83A4B"

    # Button styles
    BUTTON_PRIMARY_BG = "#B83A4B"
    BUTTON_PRIMARY_HOVER = "#9E2E3D"
    BUTTON_PRIMARY_TEXT = "#FFFFFF"

    BUTTON_SUBTLE_BG = "#FFFFFF"
    BUTTON_SUBTLE_HOVER = "#FBF2F4"
    BUTTON_SUBTLE_BORDER = "#E8D3D6"
    BUTTON_SUBTLE_TEXT = "#261316"

    # Modern typography system
    FONT_FAMILY = "Segoe UI"
    FONT_TITLE = ("Segoe UI", 16, "bold")
    FONT_SUBTITLE = ("Segoe UI", 12, "bold")
    FONT_SECTION = ("Segoe UI", 11, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_BODY_BOLD = ("Segoe UI", 11, "bold")
    FONT_SMALL = ("Segoe UI", 10)
    FONT_SMALL_BOLD = ("Segoe UI", 10, "bold")
    FONT_TINY = ("Segoe UI", 9)
    FONT_MONO = ("Consolas", 11)
