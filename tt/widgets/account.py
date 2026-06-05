from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive

import tt.api as api


def _fmt(val, prefix="$") -> str:
    if val is None:
        return "—"
    try:
        return f"{prefix}{float(val):,.2f}"
    except (TypeError, ValueError):
        return str(val)


class AccountWidget(Static):
    data: reactive[dict] = reactive({}, recompose=True)
    error: reactive[str] = reactive("", recompose=True)

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        self.error = ""
        self.run_worker(self._load(), exclusive=True)

    async def _load(self) -> None:
        try:
            raw = await api.get_account()
            self.data = raw
        except Exception as e:
            self.error = str(e)

    def compose(self) -> ComposeResult:
        if self.error:
            yield Static(f"[red]Error:[/red] {self.error}")
            return

        if not self.data:
            yield Static("[dim]Loading…[/dim]")
            return

        d = self.data
        cash = _fmt(d.get("cash") or d.get("cashBalance") or d.get("cash_balance"))
        buying_power = _fmt(
            d.get("buying_power") or d.get("buyingPower") or d.get("dayTradingBuyingPower")
        )
        portfolio_val = _fmt(
            d.get("portfolio_value")
            or d.get("portfolioValue")
            or d.get("equityValue")
            or d.get("equity_value")
        )
        acct_num = (
            d.get("account_number")
            or d.get("accountNumber")
            or d.get("accountId")
            or d.get("account_id")
            or "—"
        )
        if acct_num and acct_num != "—":
            acct_num = f"••••{str(acct_num)[-4:]}"

        lines = [
            "[bold]── Account ─────────────────────────[/bold]",
            f"  [dim]Cash[/dim]               {cash}",
            f"  [dim]Buying Power[/dim]       {buying_power}",
            f"  [dim]Portfolio Value[/dim]    {portfolio_val}",
            f"  [dim]Account #[/dim]          {acct_num}",
            "",
            "[dim italic]Press r to refresh[/dim italic]",
        ]
        yield Static("\n".join(lines))
