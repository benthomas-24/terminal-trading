"""Async ticker autocomplete with asset-type icons.

`SymbolAutoComplete` drives the dropdown from a cache that a debounced
background worker fills via `api.search_symbols`, so typing never blocks on
the network. Each row shows an icon (by asset type) to the left of the
symbol and company name, but only the bare symbol is inserted on selection.
"""

from textual.content import Content
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

import tt.api as api


class SymbolItem(DropdownItem):
    """A dropdown row that displays 'icon symbol name' but completes to symbol."""

    def __init__(self, symbol: str, name: str, icon: str) -> None:
        self._symbol = symbol
        main = Content.from_markup(
            "[b]$sym[/b]  [dim]$name[/dim]", sym=symbol, name=name
        )
        super().__init__(main=main, prefix=Content(f"{icon} "))

    @property
    def value(self) -> str:
        return self._symbol


class SymbolAutoComplete(AutoComplete):
    """Network-backed symbol search dropdown."""

    def __init__(self, target, *, id: str | None = None) -> None:
        super().__init__(target, id=id)
        self._items: list[DropdownItem] = []
        self._token = 0

    # The dropdown always renders whatever the latest search produced.
    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        return self._items

    # Results are already matched server-side, so accept them all (no local
    # fuzzy filtering that could hide valid hits).
    def match(self, query: str, candidate: str) -> tuple[float, tuple[int, ...]]:
        return (1.0, ())

    def _handle_target_update(self) -> None:
        super()._handle_target_update()
        query = self.get_search_string(self._get_target_state()).strip()
        if query:
            self._token += 1
            self.run_worker(
                self._search(query, self._token), exclusive=True, name="symbol-search"
            )

    async def _search(self, query: str, token: int) -> None:
        import asyncio

        # Debounce: wait briefly and bail if the user typed more in the meantime.
        await asyncio.sleep(0.25)
        if token != self._token:
            return
        try:
            results = await api.search_symbols(query, limit=8)
        except Exception:
            return
        if token != self._token:
            return
        self._items = [
            SymbolItem(r["symbol"], r["name"], api.icon_for(r["type"]))
            for r in results
        ]
        self._align_and_rebuild()
        if self.get_search_string(self._get_target_state()).strip():
            self.action_show()
