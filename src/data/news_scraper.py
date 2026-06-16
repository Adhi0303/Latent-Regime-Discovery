import requests
import xml.etree.ElementTree as ET

# Ticker mapping: some tickers need aliases for better news coverage
TICKER_ALIAS = {
    "^GSPC": "SPY",  # S&P 500 ETF has better RSS coverage than the index
}

# Headers to mimic a real browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://finance.yahoo.com/',
    'DNT': '1',
}


def fetch_recent_news(ticker: str, limit: int = 5) -> list:
    """
    Fetches the latest news headlines for a given ticker using Yahoo Finance's
    public RSS feed endpoint. This bypasses the yfinance API which is blocked
    on cloud/datacenter IP ranges like Hugging Face Spaces.

    Returns a list of dicts with keys: title, summary, publisher, published_at.
    """
    query_ticker = TICKER_ALIAS.get(ticker, ticker)

    # Yahoo Finance RSS feed — public, no auth, not blocked on cloud servers
    rss_url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline"
        f"?s={query_ticker}&region=US&lang=en-US"
    )

    try:
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"RSS request failed for {ticker}: {e}")
        return _fallback_google_news(query_ticker, limit)
    except ET.ParseError as e:
        print(f"RSS parse error for {ticker}: {e}")
        return _fallback_google_news(query_ticker, limit)

    results = []
    channel = root.find('channel')
    if channel is None:
        return _fallback_google_news(query_ticker, limit)

    items = channel.findall('item')
    for item in items[:limit]:
        title = item.findtext('title', '').strip()
        summary = item.findtext('description', '').strip()
        publisher = item.findtext('source', 'Yahoo Finance').strip()
        pub_date = item.findtext('pubDate', '').strip()
        link = item.findtext('link', '').strip()

        if not title:
            continue

        results.append({
            "title": title,
            "summary": summary,
            "publisher": publisher,
            "published_at": pub_date,
            "url": link,
        })

    if not results:
        return _fallback_google_news(query_ticker, limit)

    return results


def _fallback_google_news(ticker: str, limit: int = 5) -> list:
    """
    Secondary fallback: Google News RSS feed for the ticker.
    Even less likely to be blocked since it's a Google domain.
    """
    try:
        rss_url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(rss_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as e:
        print(f"Google News fallback also failed for {ticker}: {e}")
        return []

    results = []
    channel = root.find('channel')
    if channel is None:
        return []

    items = channel.findall('item')
    for item in items[:limit]:
        title = item.findtext('title', '').strip()
        summary = item.findtext('description', title).strip()
        publisher = item.findtext('source', 'Google News').strip()
        pub_date = item.findtext('pubDate', '').strip()
        link = item.findtext('link', '').strip()

        if not title:
            continue

        results.append({
            "title": title,
            "summary": summary,
            "publisher": publisher,
            "published_at": pub_date,
            "url": link,
        })

    return results


if __name__ == "__main__":
    import json
    for t in ["^GSPC", "TSLA", "NVDA", "BTC-USD", "BRK-B"]:
        print(f"\n--- {t} ---")
        news = fetch_recent_news(t, limit=3)
        print(json.dumps(news, indent=2))
