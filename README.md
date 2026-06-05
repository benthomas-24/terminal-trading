# Terminal Trading

A terminal UI for your [Public.com](https://public.com) brokerage account, built with [Textual](https://textual.textualize.io/).

View your account balance, positions, portfolio, and live quotes — all from the terminal.

> **Status:** Read-only, phase 1. No trade execution yet.

---

## Requirements

- Python 3.11+
- A [Public.com](https://public.com) account with API access enabled

---

## Setup

**1. Get your API secret**

Go to Public.com → Settings → Security → API and generate a secret key.

**2. Set the environment variable**

Option A — add to your shell profile (recommended for personal use):
```bash
export PUBLIC_API_SECRET=your_secret_key_here
```

Option B — create a `.env` file in the project root:
```bash
cp .env.example .env
# Edit .env and fill in PUBLIC_API_SECRET
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Running

```bash
python -m tt
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Account tab |
| `2` | Positions tab |
| `3` | Portfolio tab |
| `4` | Quote tab |
| `r` | Refresh active tab |
| `q` | Quit |
| `Enter` | Fetch quote (on Quote tab) |

---

## Tabs

- **Account** — cash, buying power, total portfolio value, account number
- **Positions** — open positions table with cost basis, market value, and P&L (green/red)
- **Portfolio** — portfolio summary with total value breakdown and holdings
- **Quote** — type any symbol and press Enter for a live price quote

---

## Project Structure

```
tt/
├── api.py           # Public.com API client (auth + all requests)
├── main.py          # Textual App entry point
└── widgets/
    ├── account.py
    ├── positions.py
    ├── portfolio.py
    └── quote.py
```

---

## Security

- API secrets are loaded from environment variables or `.env` — never hardcoded
- `.env` is in `.gitignore` and will never be committed
- See `.env.example` for required variable names
