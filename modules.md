# Latent Regime Discovery System: Complete Project Architecture

This document outlines the step-by-step implementation plan for the Latent Regime Discovery System, structured in a logical, continuous flow.

---

## Phase 1: Research & Problem Definition
*Before writing code, we establish the business and mathematical logic.*

* **Module 1.1: Regime Definition Research**
  Define market regimes, state mathematical assumptions, and review how quantitative funds use regime modeling.
  *Output: `research/literature_review.md`, `research/assumptions.md`*

---

## Phase 2: Data Acquisition & Cleaning
*Building the foundation by extracting and cleaning raw financial data.*

* **Module 2.1: Data Ingestion**
  Fetch historical S&P 500 data programmatically via `yfinance`.
  *Code: `src/data/ingestion.py`*
* **Module 2.2: Data Cleaning**
  Handle missing values and enforce a continuous trading-day timeline.
  *Code: `src/data/cleaning.py`*

---

## Phase 3: Feature Engineering
*Transforming non-stationary raw prices into relative, stationary signals.*

* **Module 3.1: Price & Volatility Transformations**
  Calculate daily returns, log returns, and rolling standard deviations.
  *Code: `src/features/engineering.py`*
* **Module 3.2: Trend, Momentum & Stress Indicators**
  Calculate moving average distances, momentum, volume ratios, and maximum drawdowns.

---

## Phase 4: Exploratory Data Analysis (EDA)
*Understanding the mathematical distribution of our new features before modeling.*

* **Module 4.1: Feature Distribution Analysis**
  Study returns/volatility distributions, evaluating skewness and kurtosis.
* **Module 4.2: Correlation Analysis**
  Build correlation matrices to find relationships between features.
  *Code: `notebooks/EDA.ipynb`*

---

## Phase 5: Preprocessing & Dimensionality Reduction
*Preparing the data specifically for distance-based clustering algorithms.*

* **Module 5.1: Feature Scaling**
  Apply and compare `StandardScaler` vs `RobustScaler`.
  *Code: `src/features/preprocessing.py`*
* **Module 5.2: Principal Component Analysis (PCA)**
  Reduce the 10+ features into 2 or 3 principal components to allow for visual cluster mapping.

---

## Phase 6: Baseline & Probabilistic Clustering
*Establishing simple, non-temporal regime discovery baselines.*

* **Module 6.1: K-Means Regime Detection**
  Cluster the scaled features into distinct groups (Hard clustering).
  *Code: `src/models/baseline_clustering.py`*
* **Module 6.2: Gaussian Mixture Models (GMM)**
  Upgrade to probabilistic clustering based on density distributions (Soft clustering).

---

## Phase 7: Core Temporal Modeling (Hidden Markov Models)
*The core of the project: discovering regimes that persist over time.*

* **Module 7.1: HMM Implementation**
  Train Hidden Markov Models to model time-dependent state transitions using `hmmlearn`.
  *Code: `src/models/hmm_regimes.py`*

---

## Phase 8: Model Selection & Validation
*Proving the models work without having supervised "ground truth" labels.*

* **Module 8.1: Optimal Number of Regimes**
  Test 2, 3, 4, and 5 regimes, evaluating via AIC/BIC to mathematically select the best fit.
* **Module 8.2: Statistical Separation & Persistence**
  Prove regimes are statistically distinct and transition matrices show temporal persistence.
  *Code: `src/models/evaluation.py`*

---

## Phase 9: Regime Interpretation & Production Pipeline
*Translating abstract math into a robust, deployable software engine.*

* **Module 9.1: Automatic Regime Labeling**
  Map internal cluster IDs to human-readable labels (e.g., High Return + Low Vol = "Bull Market").
* **Module 9.2: Model Persistence & Prediction Pipeline**
  Save trained models (`joblib`) and create a pipeline that accepts new daily data to output current regime probabilities.
  *Code: `src/models/predict.py`*

---

## Phase 10: Interactive Dashboard Development
*Visualizing the results for end-users.*

* **Module 10.1: Streamlit Interface**
  Build a dashboard to display current regime probabilities, transition matrices, and historical charts.
  *Code: `src/visualization/dashboard.py`*

---

## Phase 11: Advanced Enhancements (Optional)
*Taking the project to elite quantitative research levels.*

* **Module 11.1: Global Macro Regimes**
  Add multi-asset data (Bitcoin, Gold, VIX) to model cross-asset regimes.
* **Module 11.2: Deep Learning Regime Forecasting**
  Use LSTMs or Time Series Transformers to predict *future* regime transitions.
