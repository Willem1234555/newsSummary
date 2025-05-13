import requests
import urllib.parse
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
import feedparser

def scrape_google_news(search_term: str,
                       lang: str = "nl-NL",
                       country: str = "NL"):

    list_of_articles = []

    query = urllib.parse.quote(f"{search_term} when:1d")
    url = (
        f"https://news.google.com/rss/search"
        f"?q={query}&hl={lang}&gl={country}&ceid={country}:{lang.split('-')[0]}"
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GoogleNewsScraper/1.0)'
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    cutoff_time = datetime.now(timezone.utc) - timedelta(days=1)

    for entry in feed.entries:
        date_str = entry.get('published') or entry.get('updated')
        published_time = None
        if date_str:
            published_time = date_parser.parse(date_str)
            if not published_time.tzinfo:
                published_time = published_time.replace(tzinfo=timezone.utc)

        if published_time and published_time.astimezone(timezone.utc) >= cutoff_time:
            title = entry.title
            link = entry.link
            published = published_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            formatted = f"{title} ({published})"
            article = {'title': title, 'link': link, 'published': published}
            formatted += f"\n{link}"
            list_of_articles.append(article)

    return list_of_articles


if __name__ == "__main__":
    term = "luchtvaart OR vliegtuig OR schiphol"
    list_of_articles = scrape_google_news(term)
    if not list_of_articles:
        print("Geen artikelen.")
    else:
        print(list_of_articles)
