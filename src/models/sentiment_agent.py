import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from transformers import pipeline
except ImportError:
    pipeline = None
    print("Warning: transformers library not found. Please pip install transformers torch")

class MacroSentimentAnalyst:
    def __init__(self):
        """
        Initializes the FinBERT LLM for financial sentiment analysis.
        """
        print("Initializing Macro Sentiment Analyst (FinBERT)...")
        if pipeline is None:
            self.analyzer = None
        else:
            # Load FinBERT from HuggingFace
            self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            
    def analyze_headlines(self, news_items):
        """
        Takes a list of news items (dicts with 'title' and 'summary')
        and calculates an aggregated Macro Sentiment Score (-1.0 to 1.0).
        """
        if not self.analyzer or not news_items:
            return 0.0, news_items
            
        scored_items = []
        total_score = 0.0
        
        for item in news_items:
            # Combine title and summary for better context
            text = f"{item['title']}. {item['summary']}"
            
            # FinBERT has a token limit, ensure we don't exceed it
            text = text[:1000] 
            
            try:
                result = self.analyzer(text)[0]
                label = result['label']  # 'positive', 'negative', 'neutral'
                confidence = result['score']
                
                # Convert to -1.0 to +1.0 scale
                if label == 'positive':
                    score = confidence
                elif label == 'negative':
                    score = -confidence
                else:
                    score = 0.0
                    
                total_score += score
                
                # Add score back to the item
                item['sentiment_label'] = label
                item['sentiment_score'] = score
                scored_items.append(item)
                
            except Exception as e:
                print(f"Error scoring text: {e}")
                
        if not scored_items:
            return 0.0, news_items
            
        # Average the score across all headlines
        macro_score = total_score / len(scored_items)
        
        return macro_score, scored_items

# Simple singleton instance for the API server
sentiment_analyst = None

def get_sentiment_analyst():
    global sentiment_analyst
    if sentiment_analyst is None:
        sentiment_analyst = MacroSentimentAnalyst()
    return sentiment_analyst

if __name__ == "__main__":
    from src.data.news_scraper import fetch_recent_news
    analyst = get_sentiment_analyst()
    news = fetch_recent_news("NVDA", limit=3)
    macro_score, scored_news = analyst.analyze_headlines(news)
    print(f"\nOverall Macro Sentiment Score: {macro_score:.3f}\n")
    for n in scored_news:
        print(f"[{n['sentiment_label'].upper()} ({n['sentiment_score']:.2f})] {n['title']}")
