import os
import webbrowser
from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Label, ListView, ListItem, Markdown

import tt.api as api

# Fast, strong model for streaming the outlook. Change here to swap models.
OUTLOOK_MODEL = "claude-sonnet-4-6"


def _ago(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return ""
    delta = datetime.now(timezone.utc) - dt
    secs = int(delta.total_seconds())
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


def _yf_news_symbol(symbol: str, asset_type: str | None) -> str:
    symbol = symbol.upper()
    if asset_type and asset_type.upper().startswith("CRYPTO"):
        return f"{symbol}-USD"
    return symbol


class NewsWidget(Static):
    """Headlines for held positions + a streaming, Claude-generated outlook."""

    DEFAULT_CSS = """
    NewsWidget { height: 1fr; }
    #news-list {
        height: 1fr;
        min-height: 6;
        border: round $primary;
        border-title-color: $accent;
    }
    #outlook-scroll {
        height: 1fr;
        border: round $accent;
        border-title-color: $accent;
        padding: 0 1;
    }
    .news-headline { padding: 0 1; }
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._urls: list[str] = []

    def compose(self) -> ComposeResult:
        lv = ListView(id="news-list")
        lv.border_title = "Headlines · Enter to open in browser"
        yield lv
        scroll = VerticalScroll(id="outlook-scroll")
        scroll.border_title = "AI Outlook"
        with scroll:
            yield Markdown("", id="outlook")

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        self.run_worker(self._load(), exclusive=True)

    async def _load(self) -> None:
        lv = self.query_one("#news-list", ListView)
        await lv.clear()
        self._urls = []
        await lv.append(ListItem(Label("[dim]Loading news…[/dim]")))

        try:
            positions = await api.get_positions()
        except Exception as e:
            await lv.clear()
            await lv.append(ListItem(Label(f"[red]Error:[/red] {e}")))
            return

        symbols = [
            _yf_news_symbol(p["symbol"], p.get("type"))
            for p in positions
            if p.get("symbol")
        ]
        articles = await api.get_news(symbols, limit=20)

        await lv.clear()
        if not articles:
            await lv.append(ListItem(Label("[dim]No recent news found.[/dim]")))
        for a in articles:
            self._urls.append(a["url"])
            icon = api.icon_for(
                next(
                    (p.get("type") for p in positions if p.get("symbol") == a["symbol"]),
                    None,
                )
            )
            meta = " · ".join(filter(None, [a["publisher"], _ago(a["published"])]))
            label = Label(
                f"{icon} [b]{a['symbol']}[/b]  {a['title']}\n      [dim]{meta}[/dim]",
                classes="news-headline",
            )
            await lv.append(ListItem(label))

        # Kick off the AI outlook once headlines are on screen.
        self.run_worker(self._stream_outlook(positions, articles), exclusive=False)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        index = event.list_view.index
        if index is not None and 0 <= index < len(self._urls):
            webbrowser.open(self._urls[index])

    # ── AI outlook ─────────────────────────────────────────────────────

    def _build_prompt(self, positions: list[dict], articles: list[dict]) -> str:
        holdings_lines = []
        for p in positions:
            holdings_lines.append(
                f"- {p.get('symbol')}: total P&L {p.get('unrealizedPnlPercent', '?')}%, "
                f"today {p.get('dayChangePercent', '?')}%"
            )
        news_lines = []
        for a in articles[:20]:
            news_lines.append(
                f"- [{a['symbol']}] {a['title']} ({a['publisher']}, {_ago(a['published'])})"
            )
        holdings = "\n".join(holdings_lines) or "(none)"
        news = "\n".join(news_lines) or "(no recent headlines)"
        return (
            "You are a concise financial analyst. Using ONLY the holdings and "
            "recent headlines below, explain what is driving each asset and give a "
            "brief directional outlook for 1D, 3D, 5D, 1W, and 1M timeframes.\n\n"
            "Format as Markdown: one `##` section per asset. Under each, a short "
            "'Why' sentence grounded in the headlines, then a compact list of the "
            "five timeframes each with a direction (up/down/flat) and a few words "
            "of reasoning. Be specific to these holdings, not the broad market. "
            "Acknowledge uncertainty; this is not financial advice.\n\n"
            f"## Holdings\n{holdings}\n\n## Recent headlines\n{news}"
        )

    async def _stream_outlook(self, positions: list[dict], articles: list[dict]) -> None:
        outlook = self.query_one("#outlook", Markdown)
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            await outlook.update(
                "_Set `ANTHROPIC_API_KEY` in your environment or `.env` to enable "
                "the AI outlook._"
            )
            return

        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            await outlook.update("_`anthropic` package not installed._")
            return

        await outlook.update("_Analyzing your assets…_")
        client = AsyncAnthropic(api_key=key)
        prompt = self._build_prompt(positions, articles)
        text = ""
        try:
            async with client.messages.stream(
                model=OUTLOOK_MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                async for chunk in stream.text_stream:
                    text += chunk
                    await outlook.update(text)
        except Exception as e:
            await outlook.update(f"_Outlook unavailable: {e}_")
