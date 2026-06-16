import yfinance as yf
import requests

yf_session = requests.Session()
yf_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
})

def fetch_recent_news(ticker: str, limit: int = 5):
    """
    Fetches the latest news headlines for a given ticker from Yahoo Finance.
    Returns a list of dictionaries with 'title', 'summary', 'publisher', 'published_at'.
    """
    try:
        # S&P 500 ^GSPC doesn't always have great direct news, use SPY instead for news
        query_ticker = "SPY" if ticker == "^GSPC" else ticker
            
        ticker_obj = yf.Ticker(query_ticker, session=yf_session)
        news_items = ticker_obj.news
        results = []
        
        if not news_items:
            return results
            
        for item in news_items[:limit]:
            content = item.get('content', item) 
            title = content.get('title', '')
            summary = content.get('summary', '')
            
            provider = content.get('provider', {})
            # Provider might be a string in older yfinance, dict in newer
            if isinstance(provider, dict):
                publisher = provider.get('displayName', 'Yahoo Finance')
            else:
                publisher = str(provider)
                
            pub_date_str = content.get('pubDate', '')
            
            if not title:
                continue
                
            results.append({
                "title": title,
                "summary": summary,
                "publisher": publisher,
                "published_at": pub_date_str
            })
            
        return results
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

if __name__ == "__main__":
    news = fetch_recent_news("TSLA")
    for n in news:
        print(n)
