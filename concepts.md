# Latent Regime Discovery: Architecture & Technical Study Guide

This document breaks down the entire technical architecture of the **Latent Regime Discovery** project. It explains every major software engineering, artificial intelligence, and machine learning concept used, how they work mathematically, and exactly where they are implemented in the codebase.

---

## 1. Machine Learning: Unsupervised Learning

### Gaussian Mixture Models (GMM) / Regime Detection
- **What it is:** A probabilistic model that assumes all the data points are generated from a mixture of a finite number of Gaussian distributions with unknown parameters.
- **How it works:** Instead of hard-clustering (like K-Means), GMM assigns probabilities to each data point belonging to a cluster (e.g., 90% Bull, 10% Sideways). It calculates the means and variances of these clusters using the Expectation-Maximization (EM) algorithm.
- **Where it's implemented:** 
  - `src/ml/models.py` (`MarketRegimeModel` class).
- **Project Logic:** We feed historical price returns, volatility (standard deviation), and momentum indicators into the GMM. It clusters the chaotic financial data into 3 distinct, hidden market states (Bull, Sideways/Correction, Bear) without us ever explicitly defining the rules of those states.

### Principal Component Analysis (PCA)
- **What it is:** A dimensionality reduction technique.
- **How it works:** It takes highly correlated features and projects them onto new, uncorrelated orthogonal axes (Principal Components) while preserving maximum variance.
- **Where it's implemented:** 
  - Combined with the standard scaler before passing data into the GMM in `src/ml/models.py`.
- **Project Logic:** Financial indicators (like moving averages and momentum) are often highly collinear (they measure the same thing). PCA condenses our features into mathematically pure, independent signals so the GMM doesn't overweigh redundant data.

---

## 2. Deep Learning: Supervised Learning

### Long Short-Term Memory Networks (LSTM)
- **What it is:** A specialized form of Recurrent Neural Network (RNN) designed to process sequences of data over time without suffering from the vanishing gradient problem.
- **How it works:** LSTMs use a "Cell State" running through the network to remember long-term context, controlled by three gates:
  1. **Forget Gate:** Decides what past information to discard.
  2. **Input Gate:** Decides what new data to add.
  3. **Output Gate:** Calculates the prediction based on the cell state.
- **Where it's implemented:**
  - `src/ml/lstm_model.py` (`LSTMPredictor` class).
- **Project Logic:** We slice historical price data into sequences of length `N` (e.g., the last 14 days). The LSTM learns the exact temporal patterns of these sequences to predict the price for day `N+1`. 

### Continuous Learning Pipeline (Auto-Retraining)
- **What it is:** The process of dynamically updating a trained neural network as new data flows in, preventing "model drift."
- **Where it's implemented:**
  - `src/api/server.py` (`/api/bot/continuous_learn` endpoint).
- **Project Logic:** Markets are non-stationary (they change behavior). Our continuous learning pipeline takes the live prediction errors from the previous day, backpropagates them through the LSTM using the Adam optimizer, and updates the `.h5` weights so the bot is slightly smarter for tomorrow's prediction.

---

## 3. Natural Language Processing (NLP)

### FinBERT & Transformer Architectures
- **What it is:** A Large Language Model (LLM) based on Google's BERT architecture, specifically fine-tuned on financial texts, SEC filings, and analyst transcripts.
- **How it works:** It uses the **Self-Attention Mechanism**, allowing the model to weigh the contextual importance of different words in a sentence regardless of distance (e.g., understanding that "rate cut" is bullish for tech stocks, but "guidance cut" is bearish).
- **Where it's implemented:**
  - `src/bot/news_sentiment.py` (`NewsSentimentAnalyzer` class).
- **Project Logic:** We scrape live RSS news feeds for our specific tickers. The text is tokenized and passed through FinBERT, which returns a softmax probability distribution of Positive, Negative, or Neutral sentiment. We aggregate these into a single numerical "Macro Score."

---

## 4. Software Engineering & MLOps Architecture

### FastAPI & Python Backend
- **What it is:** A modern, incredibly fast Python web framework.
- **Where it's implemented:** `src/api/server.py`.
- **Project Logic:** Our Heavy ML models (PyTorch/Keras/Scikit-learn) live in the Python ecosystem. FastAPI wraps these models and the SQLite database, exposing them as RESTful HTTP endpoints (`GET`, `POST`) so the frontend and cron-jobs can trigger AI inferences on demand.

### SQLite Database & ORM
- **What it is:** A lightweight, serverless, file-based relational database.
- **Where it's implemented:** `src/bot/paper_trader.py` (via SQLAlchemy/SQLite).
- **Project Logic:** The paper-trading bot needs to remember its portfolio, cash balance, historical trades, and past AI predictions. SQLite stores this persistently in a `.db` file, ensuring our bot's ledger survives server restarts.

### Next.js & React (Frontend)
- **What it is:** A React framework for building blazing-fast, responsive web applications.
- **Where it's implemented:** The `frontend/` directory.
- **Project Logic:** React allows us to build isolated UI components (like the Scoreboard, Ledger, and LineChart). We fetch data from the FastAPI backend using `useEffect` and `fetch()`, updating the DOM asynchronously for a seamless user experience.

### Hugging Face Spaces & Vercel (Deployment)
- **What it is:** Cloud hosting platforms for ML backends and web frontends.
- **Where it's implemented:** The live URLs (`hf.space` and `vercel.app`).
- **Project Logic:** 
  - **Hugging Face:** Hosts our Python FastAPI server, running the heavy deep learning inferences and storing our SQLite database on a persistent virtual machine.
  - **Vercel:** Hosts our static Next.js frontend, utilizing edge-caching to deliver the UI globally in milliseconds.

### Cron-Jobs (Autonomous Scheduling)
- **What it is:** Time-based job schedulers that execute scripts automatically at specified intervals.
- **Where it's implemented:** Externally via `cron-job.org` pinging our `/api/bot/portfolio` endpoint.
- **Project Logic:** Because Hugging Face free-tier servers spin down when inactive, the Cron job acts as a continuous heartbeat. It pings the server every 3 hours, keeping the RAM active, ensuring the bot never misses a scheduled daily trade, and persisting the SQLite database permanently.
