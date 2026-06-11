import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.hmm_regimes import run_hmm_pipeline

def plot_hmm_regimes(df_results, output_path="notebooks/hmm_regimes.png"):
    """
    Plots the S&P 500 Close price with background shaded by HMM regimes.
    """
    plt.figure(figsize=(15, 8))
    
    # Plot price
    plt.plot(df_results.index, df_results['Close'], color='black', linewidth=1, label='S&P 500 Close')
    
    # Shade regimes
    # Green = Bull (0), Yellow = Sideways (1), Red = Bear/Crisis (2)
    colors = {0: 'lightgreen', 1: 'gold', 2: 'salmon'}
    labels = {0: 'Regime 0 (Low Vol / Bull)', 
              1: 'Regime 1 (Med Vol / Sideways)', 
              2: 'Regime 2 (High Vol / Bear)'}
              
    # Create proxy artists for legend
    import matplotlib.patches as mpatches
    patches = [mpatches.Patch(color=colors[i], alpha=0.3, label=labels[i]) for i in range(3)]
    
    # Shade background
    for r in range(3):
        mask = df_results['HMM_Regime'] == r
        plt.fill_between(df_results.index, 
                         df_results['Close'].min() * 0.9, 
                         df_results['Close'].max() * 1.1, 
                         where=mask, 
                         facecolor=colors[r], 
                         alpha=0.3)
                         
    plt.yscale('log')
    plt.title('S&P 500 Historical Price Colored by HMM Regimes (Log Scale)')
    plt.xlabel('Date')
    plt.ylabel('S&P 500 Price (Log Scale)')
    
    # Combine legends
    handles, plot_labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles + patches, plot_labels + [p.get_label() for p in patches], loc='upper left')
    
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved HMM regime plot to {output_path}")

def plot_hmm_probabilities(df_results, output_path="notebooks/hmm_probabilities.png"):
    """
    Plots the probabilities of each regime over time.
    """
    fig, axes = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    
    colors = {0: 'forestgreen', 1: 'orange', 2: 'red'}
    labels = {0: 'Regime 0 (Low Vol / Bull)', 
              1: 'Regime 1 (Med Vol / Sideways)', 
              2: 'Regime 2 (High Vol / Bear)'}
              
    for i in range(3):
        col = f'HMM_Prob_{i}'
        axes[i].plot(df_results.index, df_results[col], color=colors[i], label=labels[i])
        axes[i].fill_between(df_results.index, 0, df_results[col], color=colors[i], alpha=0.3)
        axes[i].set_ylabel('Probability')
        axes[i].set_ylim(-0.05, 1.05)
        axes[i].legend(loc='upper right')
        axes[i].grid(True, alpha=0.3, linestyle='--')
        
    axes[-1].set_xlabel('Date')
    plt.suptitle('HMM Regime Probabilities Over Time', fontsize=16, y=0.92)
    plt.savefig(output_path)
    print(f"Saved HMM probability plot to {output_path}")

def plot_transition_matrix(hmm_model, output_path="notebooks/hmm_transition_matrix.png"):
    """
    Plots a heatmap of the transition matrix.
    """
    plt.figure(figsize=(8, 6))
    
    labels = ['Bull (0)', 'Sideways (1)', 'Bear (2)']
    sns.heatmap(hmm_model.sorted_transmat_, annot=True, cmap='Blues', fmt='.3f', 
                xticklabels=labels, yticklabels=labels, vmin=0, vmax=1)
                
    plt.title('HMM Transition Probability Matrix')
    plt.ylabel('From Regime')
    plt.xlabel('To Regime')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved transition matrix plot to {output_path}")

if __name__ == "__main__":
    print("Running HMM Modeling Pipeline...")
    
    # Run the core pipeline (loads data, trains HMM, saves model, returns results)
    df_pca, df_orig, df_results, hmm_model = run_hmm_pipeline()
    
    print("\nGenerating Plots...")
    os.makedirs('notebooks', exist_ok=True)
    
    plot_hmm_regimes(df_results)
    plot_hmm_probabilities(df_results)
    plot_transition_matrix(hmm_model)
    
    print("\nHMM Pipeline Complete!")
