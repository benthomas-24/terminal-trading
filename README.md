# Terminal Trading

A terminal UI for your [Public.com](https://public.com) brokerage account, built with [Textual](https://textual.textualize.io/).

View your account balance, positions, portfolio, and live quotes — all from the terminal.

> **Status:** Read-only, phase 1. No trade execution yet.

---

## Requirements

- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Python 3.11+ (uv manages this automatically)
- A [Public.com](https://public.com) account with API access enabled

---

## Setup

**1. Get your API secret**

Go to Public.com → Settings → Security → API and generate a secret key.

**2. Set the environment variables**

Option A — add to your shell profile (recommended for personal use):
```bash
export PUBLIC_API_SECRET=your_secret_key_here
# Optional: enables the AI news outlook on the News tab
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Option B — create a `.env` file in the project root:
```bash
cp .env.example .env
# Edit .env and fill in PUBLIC_API_SECRET (and optionally ANTHROPIC_API_KEY)
```

`ANTHROPIC_API_KEY` is optional — without it everything works except the
AI-generated outlook on the News tab, which will simply prompt you to add a key.

**3. Install dependencies**

```bash
uv sync
```

---

## Running

```bash
uv run tt
```

---

## Keyboard Shortcuts

Vim-style navigation throughout. Press `?` anytime for the in-app cheatsheet.

| Key | Action |
|-----|--------|
| `h` / `l` | Previous / next tab |
| `1`–`6` | Jump to Home, Account, Positions, Portfolio, Quote, News |
| `j` / `k` | Move down / up within a table or list |
| `tab` / `shift+tab` | Cycle focus between widgets |
| `Enter` | Open selected news article / submit symbol search |
| `r` | Refresh the active tab |
| `t` | Cycle visual theme |
| `?` | Toggle the cheatsheet |
| `q` | Quit |

---

## Tabs

- **🏠 Home** — landing dashboard: large portfolio value, today's change, a
  portfolio-value chart, and top movers
- **Account** — cash, buying power, total portfolio value, account number
- **Positions** — open positions table with cost basis, market value, and P&L (green/red)
- **Portfolio** — portfolio summary with total value breakdown and holdings
- **Quote** — search any symbol via an icon dropdown for a live quote + price chart
- **📰 News** — recent headlines for your holdings (Enter opens in browser) plus
  an AI-generated outlook (1D/3D/5D/1W/1M) grounded in those headlines

Charts are rendered natively in the terminal with
[textual-plotext](https://github.com/Textualize/textual-plotext); price/news
data comes from [yfinance](https://github.com/ranaroussi/yfinance).

---

## Themes

Press `t` to cycle through four built-in themes (`tt-terminal`, `tt-hacker`,
`tt-solarized`, `tt-light`). Your choice persists to
`~/.config/terminal-trading/settings.toml`.

## Customizing the cheatsheet

The `?` cheatsheet reads from a TOML file. Copy the bundled
`tt/config/keybindings.toml` to `~/.config/terminal-trading/keybindings.toml`
and edit the descriptions/rows to taste.

---

## Project Structure

```
tt/
├── api.py            # Public.com + yfinance client (auth, quotes, history, news, search)
├── main.py           # Textual App entry point (tabs, nav, themes)
├── themes.py         # Custom Textual themes
├── config/           # User-editable cheatsheet + persisted settings
│   └── keybindings.toml
├── screens/
│   └── cheatsheet.py # `?` help modal
└── widgets/
    ├── home.py       # Dashboard landing zone
    ├── account.py
    ├── positions.py
    ├── portfolio.py
    ├── quote.py      # Symbol search + chart
    ├── symbol_search.py  # Autocomplete dropdown with asset-type icons
    └── news.py       # Headlines + streaming AI outlook
```

---

## Security

- API secrets are loaded from environment variables or `.env` — never hardcoded
- `.env` is in `.gitignore` and will never be committed
- See `.env.example` for required variable names
