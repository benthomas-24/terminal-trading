from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle
from textual.screen import ModalScreen
from textual.widgets import Static, DataTable

from tt.config import load_keybindings


class CheatsheetScreen(ModalScreen):
    """Modal overlay listing keybindings, loaded from a user-editable TOML file."""

    CSS = """
    CheatsheetScreen {
        align: center middle;
        background: $background 60%;
    }
    #cheatsheet-card {
        width: 60;
        height: auto;
        max-height: 80%;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    #cheatsheet-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #cheatsheet-table {
        height: auto;
    }
    #cheatsheet-hint {
        margin-top: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("question_mark", "dismiss", "Close", show=False),
        Binding("escape", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Middle():
            with Center():
                with Static(id="cheatsheet-card"):
                    yield Static("⌨  Keyboard Shortcuts", id="cheatsheet-title")
                    yield DataTable(
                        id="cheatsheet-table",
                        show_header=True,
                        cursor_type="none",
                        zebra_stripes=True,
                    )
                    yield Static(
                        "Edit ~/.config/terminal-trading/keybindings.toml  ·  "
                        "esc or ? to close",
                        id="cheatsheet-hint",
                    )

    def on_mount(self) -> None:
        table = self.query_one("#cheatsheet-table", DataTable)
        table.add_columns("Key", "Action")
        for row in load_keybindings():
            key = str(row.get("key", ""))
            desc = str(row.get("description", ""))
            table.add_row(f"[bold]{key}[/bold]", desc)
