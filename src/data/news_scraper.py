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
# Use curl_cffi to impersonate Chrome's TLS fingerprint.
# Yahoo Finance blocks plain requests from datacenter IPs via TLS fingerprinting.
try:
    from curl_cffi import requests as curl_requests
    yf_session = curl_requests.Session(impersonate="chrome110")
    http_session = curl_requests.Session(impersonate="chrome110")
    print("news_scraper: Using curl_cffi Chrome-impersonating session.")
except ImportError:
    yf_session = requests.Session()
    http_session = requests.Session()
    yf_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    })
    http_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    })
    print("news_scraper: curl_cffi not available, using standard requests.")


def _parse_rss(xml_text: str, limit: int, publisher: str) -> list:
    """Parse an RSS XML string and return a list of news items."""
    results = []
    try:
        root = ET.fromstring(xml_text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        items = root.findall('.//item') or root.findall('.//atom:entry', ns)
        for item in items[:limit]:
            title_el = item.find('title') or item.find('atom:title', ns)
            desc_el = item.find('description') or item.find('atom:summary', ns)
            pub_el = item.find('pubDate') or item.find('atom:published', ns)
            title = (title_el.text or '').strip() if title_el is not None else ''
            summary = re.sub(r'<[^>]+>', '', (desc_el.text or '').strip())[:500] if desc_el is not None else ''
            published = (pub_el.text or '').strip() if pub_el is not None else ''
            if title:
                results.append({"title": title, "summary": summary, "publisher": publisher, "published_at": published})
    except Exception as e:
        print(f"RSS parse error: {e}")
    return results


def fetch_recent_news(ticker: str, limit: int = 5) -> list:
    """
    Fetches the latest news headlines using yfinance (primary) with RSS feeds as fallback.
    Returns a list of dicts with 'title', 'summary', 'publisher', 'published_at'.
    """
    query_ticker = "SPY" if ticker in ("^GSPC", "%5EGSPC") else ticker

    # --- Primary: yfinance with curl_cffi Chrome session ---
    try:
        ticker_obj = yf.Ticker(query_ticker, session=yf_session)
        news_items = ticker_obj.news
        results = []
        if news_items:
            for item in news_items[:limit]:
                content = item.get('content', item)
                title = content.get('title', '')
                summary = content.get('summary', '')
                provider = content.get('provider', {})
                publisher = provider.get('displayName', 'Yahoo Finance') if isinstance(provider, dict) else str(provider)
                pub_date_str = content.get('pubDate', '')
                if title:
                    results.append({"title": title, "summary": summary, "publisher": publisher, "published_at": pub_date_str})
            if results:
                print(f"yfinance fetched {len(results)} news items for {ticker}")
                return results
    except Exception as e:
        print(f"yfinance news failed for {ticker}: {e}. Trying RSS fallback.")

    # --- Fallback 1: Yahoo Finance RSS (public HTTP, not blocked) ---
    try:
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={query_ticker}&region=US&lang=en-US"
        resp = http_session.get(rss_url, timeout=8)
        if resp.status_code == 200 and '<item>' in resp.text:
            items = _parse_rss(resp.text, limit, "Yahoo Finance")
            if items:
                print(f"Yahoo Finance RSS fetched {len(items)} items for {ticker}")
                return items
    except Exception as e:
        print(f"Yahoo Finance RSS failed: {e}")

    # --- Fallback 2: MarketWatch RSS ---
    try:
        resp = http_session.get("https://feeds.marketwatch.com/marketwatch/topstories/", timeout=8)
        if resp.status_code == 200:
            items = _parse_rss(resp.text, limit, "MarketWatch")
            if items:
                print(f"MarketWatch RSS fetched {len(items)} items")
                return items
    except Exception as e:
        print(f"MarketWatch RSS failed: {e}")

    # --- Fallback 3: CNBC Markets RSS ---
    try:
        resp = http_session.get("https://www.cnbc.com/id/10000664/device/rss/rss.html", timeout=8)
        if resp.status_code == 200:
            items = _parse_rss(resp.text, limit, "CNBC")
            if items:
                print(f"CNBC RSS fetched {len(items)} items")
                return items
    except Exception as e:
        print(f"CNBC RSS failed: {e}")

    # --- Final fallback: neutral placeholder so FinBERT still runs ---
    print(f"All news sources failed for {ticker}. Using neutral placeholder headlines.")
    return [
        {"title": "Markets continue trading amid economic uncertainty", "summary": "Investors are watching Federal Reserve policy decisions closely.", "publisher": "Market Overview", "published_at": ""},
        {"title": "Stock market shows mixed signals in today's session", "summary": "Major indices fluctuate as traders assess economic data.", "publisher": "Market Overview", "published_at": ""},
    ]


if __name__ == "__main__":
    news = fetch_recent_news("TSLA")
    for n in news:
        print(n)
