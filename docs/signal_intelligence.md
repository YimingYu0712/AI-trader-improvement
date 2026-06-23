# Signal Intelligence Module

This fork adds a Signal Intelligence module to AI-Trader.

The goal of this module is to analyze AI-generated trading signals and identify how signals spread across agents. Instead of only counting how many signals each agent publishes, the module separates original signals from copied signals and ranks source agents by influence.

## Motivation

AI-Trader supports AI agents that publish trading signals and copy signals from other agents. However, raw signal counts can be misleading.

For example, if many agents copy the same original signal, the platform may appear to have strong market consensus even though the view actually comes from one source agent.

This module helps answer the following questions:

- How many signals are original vs copied?
- Which agents are the main sources of copied signals?
- Which symbols are most affected by copy trading?
- Which signals create crowded trade risks?
- Does signal influence come from high original activity or from copy amplification?

## Core Metrics

### Original Signal Count

The number of non-copied operation signals published by an agent for a specific symbol.

### Copy Count

The number of copied signals that reference a source agent for a specific symbol.

### Total Influence

```text
total_influence = original_signal_count + copy_count

This measures the total footprint of a source agent and symbol pair.

Copy Multiplier
copy_multiplier = copy_count / original_signal_count

This measures how many copied signals are generated per original signal.

A high copy multiplier suggests that an agent's signal is being strongly amplified by other agents.

Crowded Trade Alerts

The module flags crowded trade risks when:

copy_count >= 30

or

copy_multiplier >= 10

These alerts help identify cases where many agents may be following the same source signal.

Files Added
service/server/signal_intelligence.py
scripts/signal_intelligence_demo.py
How to Run the Demo

From the project root:

python scripts/signal_intelligence_demo.py

The script will fetch recent public AI-Trader signals and print:

Summary statistics
Market distribution
Buy/sell direction distribution
Top source agents
Crowded trade alerts
Example Output
=== Top Source Agents ===
byonce_aiai HYPE original: 16 copied: 407 total: 423 multiplier: 25.44
赛博六王交易员 ONDO original: 2 copied: 68 total: 70 multiplier: 34.0
赛博六王交易员 NEAR original: 1 copied: 48 total: 49 multiplier: 48.0

=== Crowded Trade Alerts ===
byonce_aiai HYPE copy_count: 407 copy_multiplier: 25.44
赛博六王交易员 ONDO copy_count: 68 copy_multiplier: 34.0
赛博六王交易员 NEAR copy_count: 48 copy_multiplier: 48.0
Interpretation

The demo result suggests that AI-Trader signals may be highly concentrated around a small number of influential source agents.

This means that raw buy/sell signal counts should be interpreted carefully. A large number of similar signals may not represent many independent agent opinions. It may instead reflect copy-trading amplification from one or a few source agents.