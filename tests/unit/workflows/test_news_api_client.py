import os
import sys

# Ensure Airflow-style DAG imports work in unit tests.
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("dags"))

import requests

from dags.utils.news_api_client import NewsAPIClient


class _DummyResponse:
    def __init__(self, status_code: int, payload, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


def test_news_api_client_returns_empty_without_key(monkeypatch):
    client = NewsAPIClient(api_key="", base_url="https://newsapi.org/v2/everything", timeout=1)
    assert client.fetch_news(ticker="AAPL", max_items=3) == []


def test_news_api_client_parses_articles(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        assert url == "https://newsapi.org/v2/everything"
        assert params["q"] == "AAPL"
        assert params["apiKey"] == "test_key"
        assert params["pageSize"] == 2
        return _DummyResponse(
            200,
            {
                "status": "ok",
                "totalResults": 2,
                "articles": [
                    {
                        "source": {"id": None, "name": "Example"},
                        "author": "a",
                        "title": "AAPL headline",
                        "description": "Short description",
                        "url": "https://example.com/aapl",
                        "publishedAt": "2025-01-01T00:00:00Z",
                        "content": "Longer content",
                    },
                    {
                        "source": {"name": "Another"},
                        "title": "Second headline",
                        "description": "",
                        "url": "https://example.com/2",
                        "publishedAt": "2025-01-02T00:00:00Z",
                        "content": "Content 2",
                    },
                ],
            },
        )

    monkeypatch.setattr(requests, "get", fake_get)
    client = NewsAPIClient(api_key="test_key", base_url="https://newsapi.org/v2/everything", timeout=1)
    news = client.fetch_news(ticker="AAPL", max_items=2)

    assert len(news) == 2
    assert news[0]["ticker"] == "AAPL"
    assert news[0]["title"] == "AAPL headline"
    assert news[0]["summary"] == "Short description"
    assert news[0]["publisher"] == "Example"
    assert news[0]["published_at"] == "2025-01-01T00:00:00Z"
    assert news[0]["url"] == "https://example.com/aapl"

    assert news[1]["summary"] == "Content 2"

