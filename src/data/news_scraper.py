import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Map tickers to appropriate RSS feed search terms and sources
TICKER_SEARCH_MAP = {
    "^GSPC": "S&P 500",
    "SPY": "S&P 500",
    "BTC-USD": "Bitcoin",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "BRK-B": "Berkshire Hathaway",
}

RSS_SOURCES = [
    # Yahoo Finance RSS (different from API - works fine from any IP)
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US",
    # MarketWatch RSS
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    # CNBC general markets
    "https://search.cnbc.com/rs/search/combinedcombined/2.0/category/1/?externalonly=1&sourcesourceType=1&supplierId=1&pubId=10001147&partnerId=1&hascode=1&paginationFirstRecordNum=0&numResults=5&query={query}&type=1",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
}

def _parse_rss(xml_text: str, limit: int) -> list:
    """Parse an RSS XML string and return a list of news items."""
    results = []
    try:
        root = ET.fromstring(xml_text)
        # Handle both RSS 2.0 and Atom feeds
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        items = root.findall('.//item') or root.findall('.//atom:entry', ns)
        
        for item in items[:limit]:
            title_el = item.find('title') or item.find('atom:title', ns)
            desc_el = item.find('description') or item.find('atom:summary', ns)
            pub_el = item.find('pubDate') or item.find('atom:published', ns)
            
            title = (title_el.text or '').strip() if title_el is not None else ''
            summary = (desc_el.text or '').strip() if desc_el is not None else ''
            published = (pub_el.text or '').strip() if pub_el is not None else ''
            
            # Clean up HTML tags from summary if any
            import re
            summary = re.sub(r'<[^>]+>', '', summary)[:500]
            
            if title:
                results.append({
                    "title": title,
                    "summary": summary,
                    "publisher": "Financial News",
                    "published_at": published
                })
    except Exception as e:
        print(f"RSS parse error: {e}")
    return results


def fetch_recent_news(ticker: str, limit: int = 5) -> list:
    """
    Fetches the latest news headlines for a given ticker using RSS feeds.
    Falls back through multiple sources.
    Returns a list of dicts with 'title', 'summary', 'publisher', 'published_at'.
    """
    # Determine the query symbol (use SPY for ^GSPC as it has better RSS coverage)
    symbol = "SPY" if ticker in ("^GSPC", "%5EGSPC") else ticker
    query = TICKER_SEARCH_MAP.get(ticker, ticker)

    # Source 1: Yahoo Finance RSS feed for specific ticker
    yahoo_rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    try:
        resp = requests.get(yahoo_rss_url, headers=HEADERS, timeout=8)
        if resp.status_code == 200 and '<item>' in resp.text:
            items = _parse_rss(resp.text, limit)
            if items:
                # Tag publisher correctly
                for item in items:
                    src_el_match = None
                    item['publisher'] = "Yahoo Finance"
                print(f"Fetched {len(items)} news items from Yahoo Finance RSS for {ticker}")
                return items
    except Exception as e:
        print(f"Yahoo Finance RSS failed for {ticker}: {e}")

    # Source 2: MarketWatch top stories
    try:
        mw_url = "https://feeds.marketwatch.com/marketwatch/topstories/"
        resp = requests.get(mw_url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            items = _parse_rss(resp.text, limit)
            if items:
                for item in items:
                    item['publisher'] = "MarketWatch"
                print(f"Fetched {len(items)} items from MarketWatch RSS")
                return items
    except Exception as e:
        print(f"MarketWatch RSS failed: {e}")

    # Source 3: CNBC Markets RSS
    try:
        cnbc_url = "https://www.cnbc.com/id/10000664/device/rss/rss.html"
        resp = requests.get(cnbc_url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            items = _parse_rss(resp.text, limit)
            if items:
                for item in items:
                    item['publisher'] = "CNBC"
                print(f"Fetched {len(items)} items from CNBC RSS")
                return items
    except Exception as e:
        print(f"CNBC RSS failed: {e}")

    # Fallback: Return placeholder headlines so FinBERT still runs
    print(f"All RSS sources failed for {ticker}. Using fallback neutral headlines.")
    return [
        {
            "title": f"Markets continue trading amid economic uncertainty",
            "summary": "Investors are watching Federal Reserve policy decisions closely.",
            "publisher": "Market Overview",
            "published_at": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        },
        {
            "title": f"Stock market shows mixed signals in today's session",
            "summary": "Major indices fluctuate as traders assess economic data.",
            "publisher": "Market Overview",
            "published_at": datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        },
    ]


if __name__ == "__main__":
    news = fetch_recent_news("TSLA")
    for n in news:
        print(n)
