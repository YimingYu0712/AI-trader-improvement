from pathlib import Path
import sys
import time
import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT_DIR / "service" / "server"

sys.path.append(str(SERVER_DIR))

from signal_intelligence import analyze_signal_intelligence


AI4TRADE_API_BASE = "https://ai4trade.ai/api"


def fetch_public_signals(limit=1000, page_size=100):
    all_signals = []

    for offset in range(0, limit, page_size):
        url = f"{AI4TRADE_API_BASE}/signals/feed?limit={page_size}&offset={offset}"

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        signals = data.get("signals", [])

        print(f"offset={offset}, fetched={len(signals)}")

        if not signals:
            break

        all_signals.extend(signals)

        if len(signals) < page_size:
            break

        time.sleep(0.5)

    return all_signals[:limit]


def main():
    signals = fetch_public_signals(limit=1000)

    result = analyze_signal_intelligence(signals)

    print("\n=== Summary ===")
    for key, value in result["summary"].items():
        print(f"{key}: {value}")

    print("\n=== Market Distribution ===")
    for key, value in result["distributions"]["market"].items():
        print(f"{key}: {value}")

    print("\n=== Side Distribution ===")
    for key, value in result["distributions"]["side"].items():
        print(f"{key}: {value}")

    print("\n=== Top Source Agents ===")
    for row in result["source_agent_rankings"][:10]:
        print(
            row["agent_name"],
            row["symbol"],
            "original:",
            row["original_signal_count"],
            "copied:",
            row["copy_count"],
            "total:",
            row["total_influence"],
            "multiplier:",
            round(row["copy_multiplier"], 2),
            "avg_quality:",
            row["avg_quality"],
            "influence_score:",
            row.get("influence_score"),
            "risk:",
            row.get("crowding_risk_level"),
        )

    print("\n=== Crowded Trade Alerts ===")
    for row in result["crowded_trade_alerts"][:10]:
        print(
            row["agent_name"],
            row["symbol"],
            "copy_count:",
            row["copy_count"],
            "copy_multiplier:",
            round(row["copy_multiplier"], 2),
        )


if __name__ == "__main__":
    main()