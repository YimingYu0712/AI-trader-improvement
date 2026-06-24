import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional


COPY_PATTERN = re.compile(r"Copied from\s+([^\]\[]+)", re.IGNORECASE)


def is_copied_signal(content: Any) -> bool:
    """
    Return True if the signal content indicates that it was copied
    from another agent.
    """
    if not content:
        return False

    return bool(COPY_PATTERN.search(str(content)))


def extract_copied_from(content: Any) -> Optional[str]:
    """
    Extract the source agent name from copied signal content.

    Example:
    "[Copied from byonce_aiai] [BUY] ..."
    -> "byonce_aiai"
    """
    if not content:
        return None

    match = COPY_PATTERN.search(str(content))

    if not match:
        return None

    return match.group(1).strip()


def safe_float(value: Any) -> Optional[float]:
    """
    Convert a value to float safely.
    Return None if conversion fails.
    """
    try:
        if value is None:
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def analyze_signal_intelligence(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze AI-Trader signal data.

    This function separates original and copied operation signals,
    calculates source-agent influence metrics, and detects crowded
    copy-trading risks.

    Parameters
    ----------
    signals:
        A list of signal dictionaries returned by the AI-Trader API.

    Returns
    -------
    dict:
        A structured analytics result containing summary statistics,
        distributions, source-agent rankings, and crowded trade alerts.
    """

    operation_signals = [
        signal for signal in signals
        if signal.get("message_type") == "operation"
    ]

    total_signals = len(signals)
    total_operations = len(operation_signals)

    message_type_counts = Counter(
        signal.get("message_type") or "unknown"
        for signal in signals
    )

    market_counts = Counter(
        signal.get("market") or "unknown"
        for signal in operation_signals
    )

    side_counts = Counter(
        signal.get("side") or "unknown"
        for signal in operation_signals
    )

    symbol_counts = Counter(
        signal.get("symbol") or "unknown"
        for signal in operation_signals
    )

    original_signals = []
    copied_signals = []

    for signal in operation_signals:
        content = signal.get("content")
        copied_from = extract_copied_from(content)

        enriched_signal = dict(signal)
        enriched_signal["is_copied"] = copied_from is not None
        enriched_signal["copied_from"] = copied_from

        if copied_from:
            copied_signals.append(enriched_signal)
        else:
            original_signals.append(enriched_signal)

    original_count = len(original_signals)
    copied_count = len(copied_signals)

    copied_by_source_symbol = Counter()

    for signal in copied_signals:
        copied_from = signal.get("copied_from")
        symbol = signal.get("symbol") or "unknown"

        if copied_from:
            copied_by_source_symbol[(copied_from, symbol)] += 1

    original_by_source_symbol = defaultdict(list)

    for signal in original_signals:
        agent_name = signal.get("agent_name") or "unknown"
        symbol = signal.get("symbol") or "unknown"

        original_by_source_symbol[(agent_name, symbol)].append(signal)

    source_agent_rankings = []

    for key, original_group in original_by_source_symbol.items():
        agent_name, symbol = key

        original_signal_count = len(original_group)
        copy_count = copied_by_source_symbol.get((agent_name, symbol), 0)

        quality_scores = []

        for signal in original_group:
            score = safe_float(signal.get("quality_score"))

            if score is not None:
                quality_scores.append(score)

        avg_quality = (
            sum(quality_scores) / len(quality_scores)
            if quality_scores
            else None
        )

        max_quality = max(quality_scores) if quality_scores else None

        sides = sorted({
            signal.get("side") or "unknown"
            for signal in original_group
        })

        total_influence = original_signal_count + copy_count

        copy_multiplier = (
            copy_count / original_signal_count
            if original_signal_count > 0
            else 0
        )

        source_agent_rankings.append({
            "agent_name": agent_name,
            "symbol": symbol,
            "original_signal_count": original_signal_count,
            "copy_count": copy_count,
            "total_influence": total_influence,
            "copy_multiplier": copy_multiplier,
            "avg_quality": avg_quality,
            "max_quality": max_quality,
            "sides": sides,
        })

    source_agent_rankings = sorted(
        source_agent_rankings,
        key=lambda row: row["total_influence"],
        reverse=True
    )

    crowded_trade_alerts = [
        row for row in source_agent_rankings
        if row["copy_count"] >= 30 or row["copy_multiplier"] >= 10
    ]

    return {
        "summary": {
            "total_signals": total_signals,
            "operation_signals": total_operations,
            "original_operation_signals": original_count,
            "copied_operation_signals": copied_count,
            "copied_ratio": copied_count / total_operations if total_operations else 0,
        },
        "distributions": {
            "message_type": dict(message_type_counts),
            "market": dict(market_counts),
            "side": dict(side_counts),
            "symbol_top": dict(symbol_counts.most_common(20)),
        },
        "source_agent_rankings": source_agent_rankings[:50],
        "crowded_trade_alerts": crowded_trade_alerts[:30],
    }