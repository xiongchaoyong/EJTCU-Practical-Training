import logging
from datetime import datetime, timezone
from typing import List

import feedparser
import httpx
from sqlalchemy.orm import Session

from models import RSSSource, Article

logger = logging.getLogger(__name__)

FEED_TIMEOUT = 15.0  # seconds


def fetch_articles_for_source(db: Session, source: RSSSource, limit: int = 10) -> List[Article]:
    """Fetch latest articles from a single RSS source and save to DB."""
    try:
        # Fetch feed content with timeout, then parse
        resp = httpx.get(source.url, timeout=FEED_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching RSS source '{source.name}' ({source.url})")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch RSS source '{source.name}' ({source.url}): {e}")
        return []

    if feed.bozo and not feed.entries:
        logger.warning(f"RSS source '{source.name}' returned bozo feed with no entries: {feed.bozo_exception}")
        return []

    entries = feed.entries

    # Sort by published time descending
    entries_with_date = []
    for entry in entries:
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
        entries_with_date.append((entry, published_at))

    entries_with_date.sort(key=lambda x: x[1] or datetime.min, reverse=True)
    entries_with_date = entries_with_date[:limit]

    new_articles = []
    existing_links = {
        a.link
        for a in db.query(Article).filter(Article.source_id == source.id).all()
    }

    for entry, published_at in entries_with_date:
        link = entry.get("link", "")
        title = entry.get("title", "Untitled")
        content_summary = entry.get("summary", entry.get("description", ""))

        if link in existing_links:
            continue

        article = Article(
            source_id=source.id,
            title=title,
            link=link,
            published_at=published_at,
            content_summary=content_summary,
        )
        db.add(article)
        new_articles.append(article)
        existing_links.add(link)

    if new_articles:
        db.commit()

    logger.info(f"Fetched {len(new_articles)} new articles from '{source.name}'")
    return new_articles


def fetch_all_sources(db: Session) -> dict:
    """Fetch articles from all active RSS sources."""
    sources = db.query(RSSSource).filter(RSSSource.is_active == True).all()
    total_new = 0

    for source in sources:
        articles = fetch_articles_for_source(db, source)
        total_new += len(articles)

    return {"new_articles": total_new, "sources_checked": len(sources)}
