import sys
import os

from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane

from tt.widgets.account import AccountWidget
from tt.widgets.positions import PositionsWidget
from tt.widgets.portfolio import PortfolioWidget
from tt.widgets.quote import QuoteWidget

load_dotenv()


class TradingApp(App):
    TITLE = "Terminal Trading"
    SUB_TITLE = "Public.com"

    CSS = """
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 1 2;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("Account", id="tab-account"):
                yield AccountWidget(id="account")
            with TabPane("Positions", id="tab-positions"):
                yield PositionsWidget(id="positions")
            with TabPane("Portfolio", id="tab-portfolio"):
                yield PortfolioWidget(id="portfolio")
            with TabPane("Quote", id="tab-quote"):
                yield QuoteWidget(id="quote")
        yield Footer()

    def action_refresh(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "tab-account":
            self.query_one(AccountWidget).refresh_data()
        elif active == "tab-positions":
            self.query_one(PositionsWidget).refresh_data()
        elif active == "tab-portfolio":
            self.query_one(PortfolioWidget).refresh_data()
        elif active == "tab-quote":
            self.query_one(QuoteWidget).refresh_data()


def main() -> None:
    secret = os.getenv("PUBLIC_API_SECRET")
    token = os.getenv("PUBLIC_ACCESS_TOKEN")
    if not secret and not token:
        print(
            "Error: PUBLIC_API_SECRET is not set.\n"
            "  Add it to a .env file or export it in your shell:\n"
            "  export PUBLIC_API_SECRET=your_secret_key_here",
            file=sys.stderr,
        )
        sys.exit(1)
    TradingApp().run()


if __name__ == "__main__":
    main()
