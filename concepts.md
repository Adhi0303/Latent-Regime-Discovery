# Latent Regime Discovery: Interview Study Guide

This document is designed to help you prepare for technical interviews. It breaks down every major mathematical, machine learning, and software engineering concept used in this project, explaining **what it is**, **why we used it**, and **how it works under the hood**.

---

## 1. Core Financial Concepts

### Latent Regimes
- **What it is:** "Latent" means hidden or unobservable. A "Regime" is a persistent state of the market (e.g., Bull, Bear, Sideways).
- **Why we used it:** You cannot calculate a "Bear Market" with a simple math formula; it is an invisible state inferred from other visible data (price, volume, volatility).
- **Interview Question:** *Why not just use a moving average crossover to detect a trend?* 
  - **Answer:** Moving averages are lagging indicators. By the time a 50-day moving average crosses a 200-day moving average, the crash has already happened. Regime modeling detects the mathematical *environment* shifting before the price fully collapses.

### Log Returns vs. Simple Returns
- **What it is:** Instead of calculating percentage change as `(New - Old) / Old`, we use `ln(New / Old)`.
- **Why we used it:** Log returns are "time additive." If a stock drops 50% and then gains 50%, a simple return calculation says you are even (wrong). Log returns mathematically account for compounding. Furthermore, log returns are usually normally distributed, which satisfies the mathematical assumptions required by our machine learning models.

### Max Drawdown & Alpha
- **Max Drawdown:** The maximum observed loss from a peak to a trough of a portfolio. It measures risk. Our AI strategy drastically reduced max drawdown by moving to cash during Bear regimes.
- **Alpha:** A measure of performance on a risk-adjusted basis. If the S&P 500 returned 10% (Beta) and our AI returned 15%, the AI generated 5% of Alpha (outperformance).

---

## 2. Machine Learning: Unsupervised Learning

### Hidden Markov Models (HMM)
- **What it is:** A statistical Markov model in which the system being modeled is assumed to be a Markov process with unobservable (latent) states.
- **How it works:** 
  1. **Transition Matrix:** The probability of moving from one state to another (e.g., 90% chance a Bull market stays a Bull market tomorrow; 10% chance it shifts to Sideways).
  2. **Emission Probabilities:** The probability of observing a certain volatility or momentum *given* that we are in a specific state. We used Gaussian Mixture Models (GMM) to model these emissions.
- **Why we used it:** To cluster chaotic daily financial data into 3 distinct, actionable states without explicitly telling the algorithm what a "Bull" or "Bear" market looks like (Unsupervised Learning).

### Principal Component Analysis (PCA)
- **What it is:** A dimensionality reduction technique.
- **How it works:** It takes highly correlated features (like Volatility and Drawdown) and projects them onto new, uncorrelated axes (Principal Components) while preserving as much variance (information) as possible.
- **Why we used it:** HMMs struggle with "Multicollinearity" (when input features are highly correlated). If we feed the HMM two features that basically mean the same thing, it overweighs them. PCA condenses our 6 features into 2 mathematically pure components.

### Robust Scaler
- **What it is:** A data normalization technique that removes the median and scales the data according to the Interquartile Range (IQR).
- **Why we used it:** Standard Scalers use the Mean and Standard Deviation. In finance, extreme outlier days (like the 2008 crash or 2020 COVID drop) heavily skew the mean. Robust Scaler ignores these extreme outliers, scaling the "normal" days perfectly.

---

## 3. Deep Learning: Supervised Learning

### Long Short-Term Memory Networks (LSTM)
- **What it is:** A specialized Recurrent Neural Network (RNN) designed to process sequences of data.
- **How it works:** Standard neural networks have no memory. RNNs have a looping mechanism to remember the last step. However, standard RNNs suffer from the "Vanishing Gradient Problem" (they forget things that happened 20 steps ago). LSTMs fix this by introducing a "Cell State" and three "Gates":
  1. **Forget Gate:** Decides what information from the past to throw away.
  2. **Input Gate:** Decides what new information to add to the cell state.
  3. **Output Gate:** Decides what the next hidden state should be based on the cell state.
- **Why we used it:** We feed it a "sequence" of the last 21 days of data. The LSTM remembers the trajectory of the past 3 weeks to predict exactly what the price will be on day 22.

### Backpropagation Through Time (BPTT)
- **What it is:** The algorithm used to train LSTMs. It unrolls the recurrent network through time and calculates the gradient of the loss function (Mean Absolute Error) with respect to the weights, updating the network to reduce prediction errors.
- **Context in Project:** Used in Module 11.6 (Auto-Retraining). When the scoreboard error gets too high, we run BPTT to adjust the LSTM's weights to the new market reality.

---

## 4. Natural Language Processing (NLP) & GenAI

### FinBERT (Transformers)
- **What it is:** A pre-trained Large Language Model based on Google's BERT architecture, specifically fine-tuned on millions of financial texts, corporate reports, and analyst transcripts.
- **How it works:** It uses the **Attention Mechanism**, allowing the model to weigh the importance of different words in a sentence regardless of their position. For example, it knows that the word "cut" in "interest rate cut" is positive for the stock market, whereas "cut" in "revenue cut" is negative.
- **Why we used it:** To act as our Fundamental Analyst, scoring the sentiment of live news headlines.

### RAG (Retrieval-Augmented Generation) & Vector Databases
- **What it is:** An architectural pattern that improves LLM responses by fetching factual data from an external database before generating an answer.
- **How it works:** We take PDFs (like SEC filings) and turn the text into arrays of numbers called **Embeddings**. We store these in a Vector Database. When FinBERT needs context, we use **Cosine Similarity** to find the math vectors that are closest to the current topic, retrieve the text, and feed it to the LLM.

---

## 5. Software Engineering & MLOps Architecture

### FastAPI
- **What it is:** A modern, high-performance web framework for building APIs with Python.
- **Why we used it:** It uses ASGI (Asynchronous Server Gateway Interface), allowing it to handle hundreds of concurrent requests simultaneously. We used it to wrap our heavy PyTorch models so they can serve predictions over HTTP to the frontend.

### Next.js & React
- **What it is:** A React framework for building fast, SEO-friendly web applications.
- **Why we used it:** It allows us to build isolated, reusable UI components (like the Scoreboard or the Ledger) that react instantly to state changes.

### Docker & Containerization
- **What it is:** A platform that packages an application and its dependencies into an isolated "container".
- **Why we used it:** "It works on my machine" syndrome. By writing Dockerfiles, we guarantee that our PyTorch version, Node.js version, and Python libraries are exactly the same whether we run it on a Windows laptop or an Ubuntu Azure server. 
- **Docker Compose:** Used to orchestrate multiple containers (Database + Backend + Frontend + Scheduler) on a shared internal network.

### CI/CD & Autonomous Pipelines (Cron)
- **What it is:** Continuous Integration / Continuous Deployment. In our context, continuous execution.
- **Why we used it:** We built a custom `scheduler.py` container. Because the AI is supposed to be an autonomous hedge fund, the scheduler acts as a heartbeat, pinging the `/api/bot/run` webhook every day at 4:15 PM without any human intervention.
