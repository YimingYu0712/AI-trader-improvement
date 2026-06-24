import math
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

def normalize_log(value: float, max_value: float) -> float:
    """
    Normalize a value with log scaling.

    Log scaling prevents extremely large copy counts from dominating
    the ranking too aggressively.
    """
    if max_value <= 0:
        return 0.0

    return math.log1p(max(value, 0)) / math.log1p(max_value)


def add_influence_scoring(source_agent_rankings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add optimized influence and crowding risk scores.

    The score combines:
    - copy count
    - copy multiplier
    - average quality score
    - original signal activity
    """

    if not source_agent_rankings:
        return source_agent_rankings

    max_copy_count = max(row["copy_count"] for row in source_agent_rankings)
    max_copy_multiplier = max(row["copy_multiplier"] for row in source_agent_rankings)
    max_original_count = max(row["original_signal_count"] for row in source_agent_rankings)

    quality_values = [
        row["avg_quality"]
        for row in source_agent_rankings
        if row["avg_quality"] is not None
    ]

    max_quality = max(quality_values) if quality_values else 0

    for row in source_agent_rankings:
        copy_count_score = normalize_log(row["copy_count"], max_copy_count)
        copy_multiplier_score = normalize_log(row["copy_multiplier"], max_copy_multiplier)
        original_activity_score = normalize_log(row["original_signal_count"], max_original_count)

        quality_score = (
            row["avg_quality"] / max_quality
            if max_quality > 0 and row["avg_quality"] is not None
            else 0
        )

        influence_score = (
            0.45 * copy_count_score
            + 0.25 * copy_multiplier_score
            + 0.20 * quality_score
            + 0.10 * original_activity_score
        )

        crowding_score = (
            0.65 * copy_count_score
            + 0.35 * copy_multiplier_score
        )

        if (
            crowding_score >= 0.75
            or row["copy_count"] >= 30
            or row["copy_multiplier"] >= 10
        ):
            crowding_risk_level = "high"
        elif (
            crowding_score >= 0.45
            or row["copy_count"] >= 10
            or row["copy_multiplier"] >= 5
        ):
            crowding_risk_level = "medium"
        else:
            crowding_risk_level = "low"

        row["copy_count_score"] = round(copy_count_score, 4)
        row["copy_multiplier_score"] = round(copy_multiplier_score, 4)
        row["quality_score_component"] = round(quality_score, 4)
        row["original_activity_score"] = round(original_activity_score, 4)
        row["influence_score"] = round(influence_score, 4)
        row["crowding_score"] = round(crowding_score, 4)
        row["crowding_risk_level"] = crowding_risk_level

    return source_agent_rankings

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

    source_agent_rankings = add_influence_scoring(source_agent_rankings)

    source_agent_rankings = sorted(
        source_agent_rankings,
        key=lambda row: row["influence_score"],
        reverse=True
    )

    crowded_trade_alerts = [
        row for row in source_agent_rankings
        if row["crowding_risk_level"] in {"high", "medium"}
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