"""User-editable config: keybinding cheatsheet + persisted settings.

Bundled defaults live next to this module. Users may override them by placing
files in ``~/.config/terminal-trading/`` — that directory always wins.
"""

import tomllib
from pathlib import Path

_BUNDLED = Path(__file__).parent
_USER_DIR = Path.home() / ".config" / "terminal-trading"

_KEYBINDINGS = "keybindings.toml"
_SETTINGS = "settings.toml"

DEFAULT_THEME = "tt-terminal"


def _read_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def load_keybindings() -> list[dict]:
    """Cheatsheet rows: [{key, description}], user file preferred over bundled."""
    user = _USER_DIR / _KEYBINDINGS
    path = user if user.exists() else _BUNDLED / _KEYBINDINGS
    return _read_toml(path).get("bindings", [])


def load_settings() -> dict:
    """Persisted settings (currently just active_theme)."""
    return _read_toml(_USER_DIR / _SETTINGS)


def get_active_theme() -> str:
    return load_settings().get("active_theme", DEFAULT_THEME)


def save_active_theme(theme: str) -> None:
    """Persist the chosen theme to the user settings file (best effort)."""
    try:
        _USER_DIR.mkdir(parents=True, exist_ok=True)
        (_USER_DIR / _SETTINGS).write_text(f'active_theme = "{theme}"\n')
    except OSError:
        pass
