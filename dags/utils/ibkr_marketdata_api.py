"""HTTP helper for IBKR Client Portal market data endpoints.

Mirrors the reference/webapp/services/api_service.py helpers so that the
Airflow workflow can fetch the same live snapshots and historical bars
through the REST gateway when ib_insync is unavailable or incomplete.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

import requests

DEFAULT_SNAPSHOT_FIELDS: Sequence[str] = ("31", "84", "85", "86", "88", "7059")
LOGGER = logging.getLogger(__name__)


class IBKRMarketDataAPI:
    """Minimal REST client for the IBKR Client Portal Gateway."""

    def __init__(
        self,
        base_url: Optional[str],
        verify_ssl: bool = False,
        timeout: int = 15,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.verify = verify_ssl

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _request(self, method: str, path: str, **kwargs) -> Any:
        if not self.is_configured():
            raise RuntimeError("IBKRMarketDataAPI is not configured; set IBKR_API_BASE_URL")
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def search_contracts(self, symbol: str) -> List[Dict[str, Any]]:
        """Search for contracts by ticker symbol."""
        params = {"symbol": symbol, "name": "true"}
        result = self._request("GET", "/iserver/secdef/search", params=params)
        if isinstance(result, list):
            return result
        return []

    def resolve_conid(self, symbol: str, preferred_conid: Optional[int] = None) -> Optional[int]:
        """Return the primary conid for a symbol, preferring explicit overrides."""
        if preferred_conid:
            return preferred_conid
        contracts = self.search_contracts(symbol)
        for contract in contracts:
            try:
                conid = int(contract.get("conid"))
            except (TypeError, ValueError):
                continue
            # Prefer stock contracts (secType == 'STK') when available.
            sec_type = (contract.get("secType") or contract.get("sectype") or "").upper()
            symbol_match = (contract.get("symbol") or contract.get("description") or "").upper()
            if sec_type in {"", "STK"} and symbol.upper() in symbol_match:
                return conid
        # Fallback: first entry with a parsable conid
        for contract in contracts:
            try:
                return int(contract.get("conid"))
            except (TypeError, ValueError):
                continue
        return None

    def fetch_historical_bars(
        self,
        conid: int,
        period: str = "1y",
        bar: str = "1d",
        outside_rth: str = "false",
    ) -> Dict[str, Any]:
        params = {
            "conid": conid,
            "period": period,
            "bar": bar,
            "outsideRth": outside_rth,
        }
        return self._request("GET", "/iserver/marketdata/history", params=params)

    def get_live_snapshot(
        self,
        conids: Union[int, Sequence[int]],
        fields: Optional[Sequence[str]] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        if isinstance(conids, int):
            conid_list = [conids]
        else:
            conid_list = list(conids)
        field_list = list(fields or DEFAULT_SNAPSHOT_FIELDS)
        params = {
            "conids": ",".join(str(c) for c in conid_list),
            "fields": ",".join(field_list),
        }
        return self._request("GET", "/iserver/marketdata/snapshot", params=params)

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get list of available accounts."""
        return self._request("GET", "/portfolio/accounts")

    def get_portfolio_summary(self, account_id: str) -> Dict[str, Any]:
        """Get account summary/ledger."""
        return self._request("GET", f"/portfolio/{account_id}/summary")

    def get_portfolio_positions(self, account_id: str, page_id: int = 0) -> List[Dict[str, Any]]:
        """Get account positions."""
        return self._request("GET", f"/portfolio/{account_id}/positions/{page_id}")

    def place_order(self, account_id: str, order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Place an order."""
        payload = {"orders": [order]}
        return self._request("POST", f"/iserver/account/{account_id}/orders", json=payload)

    def get_orders(self) -> List[Dict[str, Any]]:
        """Get recent orders."""
        response = self._request("GET", "/iserver/account/orders")
        return response.get("orders", [])

    def cancel_order(self, account_id: str, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        return self._request("DELETE", f"/iserver/account/{account_id}/order/{order_id}")


def extract_last_price(snapshot_entry: Dict[str, Any]) -> Optional[float]:
    """Extract last/bid/ask price in order of preference from snapshot data."""
    for field in ("31", "84", "85"):
        value = snapshot_entry.get(field)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None
