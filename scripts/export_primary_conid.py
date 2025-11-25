#!/usr/bin/env python3
"""
Resolve IBKR primary CONID for the workflow.

This helper inspects the configured PostgreSQL database (preferring NEON_DATABASE,
falling back to DATABASE_URL) and reads the first symbol from STOCK_SYMBOLS to
locate a matching `codes` or `symbols` row. The resulting CONID is printed to
stdout so shell scripts can capture and export IBKR_PRIMARY_CONID before
starting Docker Compose / Airflow.
"""

import os
import sys
from typing import Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(f"[ibkr] psycopg2 is required to resolve CONIDs: {exc}\n")
    sys.exit(90)


def _normalize_db_url(value: str) -> str:
    """Convert SQLAlchemy-style URLs into psycopg2-compatible DSNs."""
    clean = value.strip().strip('"').strip("'")
    return clean.replace("+psycopg2", "")


def _resolve_symbol() -> str:
    """Return the primary symbol we should lookup."""
    preferred = os.getenv("IBKR_PRIMARY_SYMBOL") or os.getenv("PRIMARY_SYMBOL")
    if preferred:
        return preferred.strip().upper()
    stock_symbols = os.getenv("STOCK_SYMBOLS", "TSLA")
    first_symbol = stock_symbols.split(",")[0].strip()
    return first_symbol.upper()


def _fetch_conid(cursor, table: str, symbol: str) -> Optional[int]:
    """Query the requested table for the symbol, returning a CONID if found."""
    if table == "codes":
        cursor.execute(
            """
            SELECT conid FROM codes
            WHERE UPPER(symbol) = %s
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 1
            """,
            (symbol,),
        )
    else:
        cursor.execute(
            """
            SELECT conid FROM symbols
            WHERE UPPER(symbol) = %s
            ORDER BY last_updated DESC NULLS LAST
            LIMIT 1
            """,
            (symbol,),
        )
    row = cursor.fetchone()
    if not row:
        return None
    value = row.get("conid") if isinstance(row, dict) else row[0]
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    db_url = os.getenv("NEON_DATABASE") or os.getenv("DATABASE_URL")
    if not db_url:
        sys.stderr.write("[ibkr] NEON_DATABASE or DATABASE_URL is required\n")
        return 1
    dsn = _normalize_db_url(db_url)
    symbol = _resolve_symbol()

    try:
        conn = psycopg2.connect(dsn)
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"[ibkr] Unable to connect to database: {exc}\n")
        return 2

    conid: Optional[int] = None
    try:
        conn.autocommit = True
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            conid = _fetch_conid(cursor, "codes", symbol)
            if not conid:
                conid = _fetch_conid(cursor, "symbols", symbol)
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"[ibkr] Failed to resolve CONID: {exc}\n")
        return 3
    finally:
        conn.close()

    if not conid:
        sys.stderr.write(
            f"[ibkr] No CONID found for symbol '{symbol}' in codes/symbols tables\n"
        )
        return 4

    # Success: print CONID for callers (stdout only) and exit.
    sys.stdout.write(str(conid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
