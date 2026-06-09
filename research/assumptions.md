# Core Assumptions for Regime Modeling

Before training any models, it is critical to state the mathematical and conceptual assumptions our system relies on. If these assumptions are violated, the model's output cannot be trusted.

---

## 1. Non-Stationarity Assumption
**Assumption:** Financial markets are non-stationary. The probability distribution of returns, volatility, and correlations changes over time.
**Implication:** We cannot fit a single linear model or a single normal distribution to the entire history of the S&P 500. The data must be modeled as a mixture of multiple distinct environments.

## 2. Latency Assumption
**Assumption:** Market regimes exist, but they are **strictly unobservable (latent)**. 
**Implication:** There is no "ground truth" label for what regime the market was in on a specific day. We cannot use supervised learning (like Random Forests or XGBoost) to classify regimes directly. We must use unsupervised learning to infer them.

## 3. Finite State Assumption
**Assumption:** The market operates in a finite, relatively small number of distinct states (usually between 2 and 5). 
**Implication:** We aren't looking for 50 different micro-regimes. We are looking for broad, macroeconomic and behavioral states (e.g., Bull, Bear, Sideways, Crisis). Determining exactly *how many* states exist is a key hyperparameter we must optimize.

## 4. The Markov Property
**Assumption:** The future state of the market depends *only* on the current state of the market, and not on the sequence of events that preceded it.
**Mathematical Definition:** `P(State_t+1 | State_t, State_t-1, ..., State_0) = P(State_t+1 | State_t)`
**Implication:** This is the core assumption of the **Hidden Markov Model (HMM)**. While this is a simplification (real markets often have long-term memory), it is mathematically necessary to make the transition probability matrix computable.

## 5. Emission Independence
**Assumption:** Given a specific hidden regime, the observed features (e.g., today's returns and volatility) are independent of previous observations.
**Implication:** The only thing connecting yesterday's returns to today's returns is the hidden state transition. Again, this is a mathematical simplification required by standard HMMs, which is why we must carefully engineer our features (like taking rolling averages) to capture short-term memory before feeding it into the model.

## 6. Regime Persistence
**Assumption:** Regimes are "sticky." Once the market enters a regime, it is highly likely to stay in that regime the next day.
**Implication:** The diagonal of our transition matrix (probability of transitioning from Bull -> Bull) should be much closer to 1.0 than the off-diagonals (probability of Bull -> Crisis). If our model outputs a regime that flickers back and forth every single day, the model has failed to capture true regimes.
