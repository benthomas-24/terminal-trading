"""Custom Textual themes for Terminal Trading.

These use Textual's native theme system (App.register_theme / App.theme), so
colors, contrast ramps, and transitions are all handled by the framework —
nothing the terminal isn't built for. Cycle them at runtime with `t`.
"""

from textual.theme import Theme

# A muted, terminal-desk palette (the default).
TT_TERMINAL = Theme(
    name="tt-terminal",
    primary="#4FB286",
    secondary="#3A7CA5",
    accent="#E0A458",
    success="#4FB286",
    warning="#E0A458",
    error="#D7263D",
    foreground="#C5D1C0",
    background="#0B0F0D",
    surface="#121815",
    panel="#161E1A",
    dark=True,
    variables={
        "block-cursor-foreground": "#0B0F0D",
        "border": "#2A3A32",
    },
)

# Bright green-on-black, Matrix aesthetic.
TT_HACKER = Theme(
    name="tt-hacker",
    primary="#00FF66",
    secondary="#00CC55",
    accent="#39FF14",
    success="#00FF66",
    warning="#CCFF00",
    error="#FF0033",
    foreground="#00FF66",
    background="#000000",
    surface="#020A02",
    panel="#031003",
    dark=True,
    variables={
        "block-cursor-foreground": "#000000",
        "border": "#00FF66",
    },
)

# Warm Solarized Dark.
TT_SOLARIZED = Theme(
    name="tt-solarized",
    primary="#268BD2",
    secondary="#2AA198",
    accent="#B58900",
    success="#859900",
    warning="#CB4B16",
    error="#DC322F",
    foreground="#93A1A1",
    background="#002B36",
    surface="#073642",
    panel="#073642",
    dark=True,
)

# Clean light theme.
TT_LIGHT = Theme(
    name="tt-light",
    primary="#1A7F4B",
    secondary="#2563EB",
    accent="#B45309",
    success="#15803D",
    warning="#B45309",
    error="#B91C1C",
    foreground="#1F2937",
    background="#FBFBF9",
    surface="#F1F1EC",
    panel="#E8E8E2",
    dark=False,
)

# Registration order == cycle order for the `t` key.
THEMES = [TT_TERMINAL, TT_HACKER, TT_SOLARIZED, TT_LIGHT]
THEME_NAMES = [t.name for t in THEMES]
