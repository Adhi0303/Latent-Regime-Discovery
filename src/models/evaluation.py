import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score
from sklearn.ensemble import RandomForestClassifier
import shap

def calculate_aic_bic(hmm_model, X):
    """
    Calculates AIC and BIC for a trained GaussianHMM model.
    AIC = 2k - 2 * ln(L)
    BIC = k * ln(n) - 2 * ln(L)
    where:
    k = number of free parameters
    L = maximum likelihood (hmm_model.score(X))
    n = number of observations
    """
    try:
        # Check if hmmlearn provides aic and bic directly (newer versions might)
        aic = hmm_model.aic(X)
        bic = hmm_model.bic(X)
        return aic, bic
    except AttributeError:
        # Manual calculation
        n_features = X.shape[1]
        n_components = hmm_model.n_components
        
        # Free parameters calculation for full covariance GaussianHMM
        # 1. Initial state probabilities: n_components - 1
        # 2. Transition matrix: n_components * (n_components - 1)
        # 3. Means: n_components * n_features
        # 4. Covariances (full): n_components * (n_features * (n_features + 1)) / 2
        
        n_params = (n_components - 1) + \
                   (n_components * (n_components - 1)) + \
                   (n_components * n_features) + \
                   (n_components * n_features * (n_features + 1) / 2)
                   
        log_likelihood = hmm_model.score(X)
        n_samples = X.shape[0]
        
        aic = 2 * n_params - 2 * log_likelihood
        bic = n_params * np.log(n_samples) - 2 * log_likelihood
        
        return aic, bic

def evaluate_clustering(X, labels):
    """
    Evaluates cluster separation using Silhouette Score.
    """
    if len(np.unique(labels)) > 1:
        score = silhouette_score(X, labels)
    else:
        score = -1
    return score

def get_surrogate_shap_values(X_orig, labels, random_state=42):
    """
    Trains a Random Forest classifier to map original (uncompressed) features 
    to the HMM-discovered regimes, then uses SHAP to calculate feature importance.
    
    Returns the trained surrogate model and the SHAP explainer object.
    """
    print("\nTraining SHAP Surrogate Model (Random Forest)...")
    
    # Train the surrogate model
    rf = RandomForestClassifier(n_estimators=100, random_state=random_state, max_depth=5)
    rf.fit(X_orig, labels)
    
    accuracy = rf.score(X_orig, labels)
    print(f"Surrogate Model Accuracy: {accuracy*100:.2f}% (High accuracy means SHAP will faithfully explain the HMM)")
    
    print("Calculating SHAP values...")
    explainer = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X_orig)
    
    return rf, explainer, shap_values
