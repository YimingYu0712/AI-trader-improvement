from signal_intelligence import (
    is_copied_signal,
    extract_copied_from,
    analyze_signal_intelligence,
)


def test_extract_copied_from():
    content = "[Copied from byonce_aiai] [BUY] conf=95%"

    assert is_copied_signal(content) is True
    assert extract_copied_from(content) == "byonce_aiai"


def test_non_copied_signal():
    content = "[BUY] BTC momentum signal"

    assert is_copied_signal(content) is False
    assert extract_copied_from(content) is None


def test_empty_content():
    assert is_copied_signal(None) is False
    assert extract_copied_from(None) is None


def test_analyze_signal_intelligence_basic():
    signals = [
        {
            "id": 1,
            "message_type": "operation",
            "market": "crypto",
            "symbol": "HYPE",
            "side": "buy",
            "agent_name": "byonce_aiai",
            "quality_score": 2.5,
            "content": "[BUY] HYPE signal",
        },
        {
            "id": 2,
            "message_type": "operation",
            "market": "crypto",
            "symbol": "HYPE",
            "side": "buy",
            "agent_name": "CopyBotA",
            "quality_score": 2.1,
            "content": "[Copied from byonce_aiai] [BUY] HYPE signal",
        },
        {
            "id": 3,
            "message_type": "operation",
            "market": "crypto",
            "symbol": "HYPE",
            "side": "buy",
            "agent_name": "CopyBotB",
            "quality_score": 2.2,
            "content": "[Copied from byonce_aiai] [BUY] HYPE signal",
        },
    ]

    result = analyze_signal_intelligence(signals)

    assert result["summary"]["total_signals"] == 3
    assert result["summary"]["operation_signals"] == 3
    assert result["summary"]["original_operation_signals"] == 1
    assert result["summary"]["copied_operation_signals"] == 2

    top_agent = result["source_agent_rankings"][0]

    assert top_agent["agent_name"] == "byonce_aiai"
    assert top_agent["symbol"] == "HYPE"
    assert top_agent["original_signal_count"] == 1
    assert top_agent["copy_count"] == 2
    assert top_agent["total_influence"] == 3
    assert top_agent["copy_multiplier"] == 2