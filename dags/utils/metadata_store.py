"""Neon-backed metadata storage for FinAgent workflows."""
from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import Json

from .config import config

logger = logging.getLogger(__name__)


class FinAgentMetadataStore:
    """Simple helper that persists FinAgent metadata snapshots to Neon Postgres."""

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or config.neon_database_dsn
        self.available = bool(self.dsn)
        if self.available:
            self._ensure_table()
        else:
            logger.info("FinAgent metadata store disabled (no NEON_DATABASE provided)")

    def _ensure_table(self) -> None:
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS finagent_metadata (
                            id BIGSERIAL PRIMARY KEY,
                            symbol TEXT NOT NULL,
                            run_id TEXT,
                            execution_id TEXT,
                            kind TEXT NOT NULL,
                            payload JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                conn.commit()
        except Exception as exc:
            self.available = False
            logger.warning("Disabling FinAgent metadata persistence: %s", exc)

    @contextmanager
    def connection(self):
        if not self.dsn:
            raise RuntimeError("FinAgent metadata store requires NEON_DATABASE to be configured")
        conn = psycopg2.connect(self.dsn)
        try:
            yield conn
        finally:
            conn.close()

    def record(
        self,
        *,
        symbol: str,
        kind: str,
        payload: Dict[str, Any],
        run_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> None:
        if not self.available:
            return
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO finagent_metadata (symbol, kind, payload, run_id, execution_id)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            symbol,
                            kind,
                            Json(payload, dumps=lambda value: json.dumps(value, default=str)),
                            run_id,
                            execution_id,
                        ),
                    )
                conn.commit()
        except Exception as exc:
            logger.warning("Failed to persist %s snapshot for %s: %s", kind, symbol, exc)

    def record_market_snapshot(self, symbol: str, data: Dict[str, Any], *, run_id: Optional[str], execution_id: Optional[str]) -> None:
        self.record(symbol=symbol, kind="market_data", payload=data, run_id=run_id, execution_id=execution_id)

    def record_import_data(self, symbol: str, data: Dict[str, Any], *, run_id: Optional[str], execution_id: Optional[str]) -> None:
        self.record(symbol=symbol, kind="import_data", payload=data, run_id=run_id, execution_id=execution_id)

    def record_prompt(self, symbol: str, prompt: str, response: str, *, stage: str, run_id: Optional[str], execution_id: Optional[str]) -> None:
        payload = {
            "stage": stage,
            "prompt": prompt,
            "response": response,
        }
        self.record(symbol=symbol, kind="llm_prompt", payload=payload, run_id=run_id, execution_id=execution_id)


metadata_store = FinAgentMetadataStore()
