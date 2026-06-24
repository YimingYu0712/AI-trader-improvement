import time
from typing import Any, Dict, List

import requests
from fastapi import FastAPI, HTTPException, Query

from signal_intelligence import analyze_signal_intelligence


AI4TRADE_API_BASE = "https://ai4trade.ai/api"


def fetch_public_signals(limit: int = 1000, page_size: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch recent public AI-Trader signals from the public signal feed.
    """

    all_signals = []

    for offset in range(0, limit, page_size):
        url = f"{AI4TRADE_API_BASE}/signals/feed?limit={page_size}&offset={offset}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch public AI-Trader signals: {exc}",
            )

        data = response.json()
        signals = data.get("signals", [])

        if not signals:
            break

        all_signals.extend(signals)

        if len(signals) < page_size:
            break

        time.sleep(0.2)

    return all_signals[:limit]


def register_signal_intelligence_routes(app: FastAPI):
    """
    Register Signal Intelligence analytics endpoints.
    """

    @app.get("/api/analytics/signal-intelligence")
    def get_signal_intelligence(
        limit: int = Query(default=1000, ge=100, le=3000)
    ):
        """
        Analyze recent AI-Trader signals.

        Returns:
        - original vs copied signal summary
        - market / side / symbol distributions
        - source-agent influence ranking
        - crowded trade alerts
        """

        signals = fetch_public_signals(limit=limit)
        result = analyze_signal_intelligence(signals)

        return result