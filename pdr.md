# Product Design & Research Document (PDR)

## Project: Latent Regime Discovery System

**Version:** 1.0
**Project Type:** Machine Learning + Time Series Analysis + Financial Data Engineering
**Difficulty:** Intermediate → Advanced
**Portfolio Value:** High

---

# 1. Executive Summary

The Latent Regime Discovery System is an unsupervised machine learning platform that automatically identifies hidden market states (regimes) from historical financial data.

Unlike traditional prediction systems that attempt to forecast future prices directly, this system focuses on understanding the underlying environment in which markets operate.

The platform analyzes market behavior using statistical and machine learning techniques to discover latent regimes such as:

* Bull Markets
* Bear Markets
* High Volatility Periods
* Crisis Events
* Sideways Markets

The final output is a regime detection engine that continuously classifies market conditions and visualizes transitions between market states.

---

# 2. Problem Statement

Financial markets are non-stationary systems.

Most machine learning models assume:

```text
Past patterns continue indefinitely.
```

This assumption is often false because markets continuously shift between different behavioral states.

For example:

| Period | Market Condition  |
| ------ | ----------------- |
| 2017   | Bull Market       |
| 2020   | COVID Crash       |
| 2021   | Recovery Bull Run |
| 2022   | Bear Market       |
| 2023   | Mixed Volatility  |

A strategy that performs well during a bull market may fail during a crisis regime.

The challenge:

```text
Market regimes exist,
but they are not directly observable.
```

The goal is to infer these hidden states from observable market data.

---

# 3. Project Objectives

Primary Objectives:

* Discover hidden market regimes using unsupervised learning.
* Compare multiple regime discovery methods.
* Build a complete end-to-end ML pipeline.
* Visualize market regime transitions.
* Analyze characteristics of discovered regimes.

Secondary Objectives:

* Learn probabilistic machine learning.
* Understand temporal dependencies in time-series data.
* Build a production-quality portfolio project.
* Create an interactive analytics dashboard.

---

# 4. Business Value

Organizations that benefit from regime detection:

* Hedge Funds
* Asset Managers
* Quantitative Trading Firms
* Risk Management Teams
* Portfolio Managers
* Algorithmic Trading Systems

Potential applications:

### Strategy Selection

```text
If Bull Market:
    Trend Following

If Bear Market:
    Defensive Allocation

If High Volatility:
    Risk Reduction
```

### Risk Management

Detect increasing probability of crisis regimes.

### Portfolio Optimization

Allocate assets based on regime probabilities.

---

# 5. Machine Learning Concepts Covered

---

## Unsupervised Learning

No labels exist.

The model must discover structure from data.

Learn:

* Clustering
* Density Estimation
* Hidden Structure Discovery

---

## Time Series Analysis

Understand temporal behavior.

Learn:

* Lag Features
* Rolling Windows
* Volatility Modeling
* Trend Analysis

---

## Probabilistic Machine Learning

Outputs become probabilities.

Example:

```text
Bull = 68%

Bear = 12%

Volatility = 20%
```

Learn:

* Bayesian Thinking
* Probabilistic States
* Transition Probabilities

---

## Feature Engineering

Transform raw prices into meaningful signals.

Learn:

* Returns
* Volatility
* Momentum
* Drawdowns

---

## Model Evaluation Without Labels

One of the most important ML skills.

Learn:

* Cluster Validation
* Statistical Separation
* Temporal Stability Analysis

---

# 6. Dataset Selection

---

## Phase 1 Dataset

S&P 500 Historical Data

Source:

[Yahoo Finance](https://finance.yahoo.com/?utm_source=chatgpt.com)

Fields:

```text
Date
Open
High
Low
Close
Volume
```

Time Period:

```text
2005 → Present
```

Expected Records:

```text
~5000 Trading Days
```

---

## Phase 2 Expansion

Additional Assets:

* SPY
* Bitcoin
* GLD
* VIX

---

# 7. Data Pipeline Architecture

```text
Yahoo Finance API
          │
          ▼
Raw Market Data
          │
          ▼
Data Cleaning
          │
          ▼
Feature Engineering
          │
          ▼
Feature Store
          │
          ▼
Regime Discovery Models
          │
          ▼
Regime Analytics Engine
          │
          ▼
Visualization Dashboard
```

---

# 8. Feature Engineering

Raw prices are insufficient.

Features to create:

---

## Daily Returns

r_t=\frac{P_t-P_{t-1}}{P_{t-1}}

Purpose:

Measure daily market movement.

---

## Rolling Volatility

30-day rolling standard deviation.

Purpose:

Detect market uncertainty.

---

## Momentum

30-day return.

Purpose:

Identify market trends.

---

## Moving Average Distance

```text
Price - 50 Day MA
```

Purpose:

Measure trend strength.

---

## Volume Ratio

```text
Current Volume / Average Volume
```

Purpose:

Detect unusual market activity.

---

## Drawdown

Measures decline from recent peak.

Purpose:

Detect stress periods.

---

# 9. Machine Learning Models

---

# Model 1: K-Means Clustering

Purpose:

Baseline regime detector.

Characteristics:

* Fast
* Easy to understand
* Non-probabilistic

Input:

```text
Returns
Volatility
Momentum
```

Output:

```text
Cluster 1
Cluster 2
Cluster 3
```

Limitation:

Ignores temporal relationships.

---

# Model 2: Gaussian Mixture Model (GMM)

Purpose:

Probabilistic clustering.

Advantages:

* Soft cluster assignment
* Handles overlapping regimes

Output:

```text
Regime A: 70%

Regime B: 20%

Regime C: 10%
```

Skills Learned:

* Expectation Maximization
* Density Estimation

---

# Model 3: Hidden Markov Model (Core Model)

Purpose:

Discover hidden market states.

Core Idea:

```text
Hidden State
      ↓
Observed Features
```

Model learns:

* Hidden regimes
* Transition probabilities
* Regime persistence

Example:

```text
Bull → Bull → Bull

Bull → Bear

Bear → Bear
```

Why HMM?

Markets evolve over time.

HMM explicitly models temporal transitions.

---

# 10. Evaluation Strategy

Because labels do not exist:

Traditional accuracy metrics cannot be used.

---

## Statistical Separation

Each regime should exhibit:

Different:

* Mean Returns
* Volatility
* Drawdowns

---

## Regime Persistence

Good regimes should persist.

Bad output:

```text
Bull
Bear
Bull
Bear
Bull
```

every day.

Good output:

```text
Bull
Bull
Bull
Bull
Bull

Bear
Bear
Bear
```

---

## Historical Event Validation

Validate discovered regimes against known events.

Examples:

* Global Financial Crisis
* COVID-19 market crash
* 2022 stock market decline

---

# 11. Dashboard Features

Framework:

```text
Streamlit
```

---

## Market Overview

Display:

```text
Current Regime

Regime Probability

Volatility

Trend Strength
```

---

## Historical Visualization

Chart:

```text
Price History

Colored by Regime
```

Example:

```text
Green → Bull

Red → Bear

Yellow → Volatile
```

---

## Transition Matrix

Shows:

Probability of switching regimes.

Example:

| From | To       | Probability |
| ---- | -------- | ----------- |
| Bull | Bull     | 92%         |
| Bull | Bear     | 6%          |
| Bull | Volatile | 2%          |

---

## Regime Statistics

Display:

* Average Return
* Average Volatility
* Maximum Drawdown

per regime.

---

# 12. Tech Stack

### Programming

```text
Python
```

---

### Data Processing

```text
Pandas
NumPy
```

---

### Data Collection

```text
yfinance
```

---

### Machine Learning

```text
Scikit-Learn

hmmlearn

SciPy
```

---

### Visualization

```text
Plotly

Matplotlib
```

---

### Dashboard

```text
Streamlit
```

---

# 13. Expected Deliverables

---

## Deliverable 1

Research Report

Contents:

* Problem Statement
* Methodology
* Findings
* Conclusions

---

## Deliverable 2

Machine Learning Pipeline

Includes:

* Data ingestion
* Feature engineering
* Training
* Evaluation

---

## Deliverable 3

Interactive Dashboard

User can:

* Explore regimes
* View probabilities
* Analyze transitions

---

## Deliverable 4

GitHub Repository

Structure:

```text
latent-regime-discovery/

│
├── data/
├── notebooks/
├── src/
│   ├── data_pipeline.py
│   ├── feature_engineering.py
│   ├── clustering.py
│   ├── hmm_model.py
│   ├── evaluation.py
│
├── dashboard/
│   └── app.py
│
├── reports/
├── README.md
```

---

# 14. Future Enhancements

### Deep Learning Extension

LSTM Autoencoder

Purpose:

Learn latent market representations.

---

### Transformer-Based Regime Discovery

Use:

* Temporal Fusion Transformer
* Time Series Transformer

---

### Online Learning

Real-time regime updates.

---

### Multi-Asset Regime Analysis

Discover global market states using:

* Stocks
* Commodities
* Crypto
* Bonds

---

# Resume Impact

This project demonstrates:

* Unsupervised Learning
* Time Series Modeling
* Hidden Markov Models
* Probabilistic Machine Learning
* Financial Data Engineering
* Feature Engineering
* Dashboard Development
* End-to-End ML System Design

Among student ML portfolios, this is significantly more distinctive than typical classification or regression projects and tells a strong story about your ability to work with real-world, unlabeled, temporal data.
