"""NewsAPI client helpers for FinAgent workflows.

Reference: https://ithelp.ithome.com.tw/articles/10375805 (NewsAPI `/v2/everything` usage pattern).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from utils.config import config

logger = logging.getLogger(__name__)


class NewsAPIClient:
    """Minimal client for fetching recent news items for a ticker symbol."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self.api_key = (api_key or config.news_api_key or "").strip()
        self.base_url = (base_url or config.news_api_base_url or "").strip()
        self.timeout = int(timeout or config.news_api_timeout)

    def fetch_news(self, *, ticker: str, max_items: Optional[int] = None) -> List[Dict[str, str]]:
        if not self.api_key:
            logger.info("NEWS_API_KEY is not configured; skipping NewsAPI fetch")
            return []
        if not self.base_url:
            logger.warning("NEWS_API_BASE_URL is empty; skipping NewsAPI fetch")
            return []

        page_size = int(max_items or config.news_api_page_size or 10)
        params = {
            "q": ticker,
            "language": config.news_api_language,
            "sortBy": config.news_api_sort_by,
            "apiKey": self.api_key,
            "pageSize": page_size,
        }

        try:
            resp = requests.get(self.base_url, params=params, timeout=self.timeout)
        except Exception as exc:  # pragma: no cover - network/timeout dependent
            logger.warning("NewsAPI request failed: %s", exc)
            return []

        if resp.status_code != 200:
            logger.warning("NewsAPI request failed: status=%s body=%s", resp.status_code, (resp.text or "")[:500])
            return []

        try:
            payload: Dict[str, Any] = resp.json()
        except Exception as exc:  # pragma: no cover - unexpected payload
            logger.warning("NewsAPI JSON decode failed: %s", exc)
            return []

        results: List[Dict[str, str]] = []
        for item in (payload.get("articles") or []):
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            description = (item.get("description") or "").strip()
            content = (item.get("content") or "").strip()
            published_at = (item.get("publishedAt") or "").strip()
            url = (item.get("url") or "").strip()
            source = item.get("source") if isinstance(item.get("source"), dict) else {}
            publisher = (source.get("name") or "").strip() if isinstance(source, dict) else ""

            summary = description or content
            if not title and not summary:
                continue

            results.append(
                {
                    "ticker": ticker.upper(),
                    "title": title,
                    "summary": summary,
                    "publisher": publisher,
                    "published_at": published_at,
                    "url": url,
                }
            )

        return results


__all__ = ["NewsAPIClient"]

