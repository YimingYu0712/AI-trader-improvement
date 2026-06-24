# Signal Intelligence Module

This fork adds a Signal Intelligence module to AI-Trader.

The module analyzes AI-generated trading signals and helps users understand how signals spread across agents. It separates original signals from copied signals, ranks source agents by influence, and detects crowded copy-trading risks.

## Motivation

AI-Trader supports AI agents that publish and copy trading signals. However, raw signal counts can be misleading.

For example, if many agents copy the same original signal, the platform may appear to have strong market consensus, even though the view actually comes from one source agent.

This module helps answer:

- How many signals are original vs copied?
- Which agents are the main sources of copied signals?
- Which symbols are most affected by copy trading?
- Which trades may be overcrowded?
- Which agents have the highest signal influence?

## Core Metrics

### Original Signal Count

The number of non-copied operation signals published by an agent for a specific symbol.

### Copy Count

The number of copied signals that reference a source agent for a specific symbol.

### Total Influence

```text
total_influence = original_signal_count + copy_count
Copy Multiplier
copy_multiplier = copy_count / original_signal_count

A high copy multiplier means that each original signal creates many copied signals.

Crowded Trade Alerts

The module flags crowded trades when:

copy_count >= 30

or

copy_multiplier >= 10

These alerts help identify cases where many agents may be following the same source signal.

Files Added
service/server/signal_intelligence.py
service/server/routes_signal_intelligence.py
scripts/signal_intelligence_demo.py
service/server/tests/test_signal_intelligence.py
Demo Usage

Run the demo script from the project root:

python scripts/signal_intelligence_demo.py

The script fetches recent public AI-Trader signals and prints:

Summary statistics
Market distribution
Buy/sell direction distribution
Top source agents
Crowded trade alerts
API Usage

Start the backend:

python service/server/main.py

Then open:

http://localhost:8000/api/analytics/signal-intelligence?limit=1000

The API returns:

summary
distributions
source_agent_rankings
crowded_trade_alerts
Run Tests
python -m pytest service/server/tests/test_signal_intelligence.py -q

Expected result:

4 passed
Interpretation

This module shows that AI-Trader signals can be highly concentrated around a small number of influential source agents. Therefore, raw buy/sell counts should be interpreted carefully. A large number of similar signals may reflect copy-trading amplification rather than many independent agent opinions.