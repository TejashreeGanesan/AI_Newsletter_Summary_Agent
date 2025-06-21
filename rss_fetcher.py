import feedparser
from datetime import datetime, timezone
import logging
from config import RSS_FEEDS
from date_utils import parse_date_flexible, is_from_last_24_hours

logger = logging.getLogger(__name__)

def fetch_recent_articles():
    """Fetch articles from RSS feeds that were published in the last 24 hours"""
    all_articles = []
    reference_time = datetime.now(timezone.utc)

    logger.info(f"🔍 Fetching articles from {len(RSS_FEEDS)} RSS feeds...")
    logger.info(f"📅 Reference time (UTC): {reference_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            logger.info(f"📡 Parsing feed: {source_name}")

            # Parse the RSS feed
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning(f"⚠️ Feed parsing warning for {source_name}: {feed.bozo_exception}")

            feed_articles = []
            for entry in feed.entries:
                try:
                    # Extract publication date
                    published_date = None
                    if hasattr(entry, 'published'):
                        published_date = parse_date_flexible(entry.published)
                    elif hasattr(entry, 'updated'):
                        published_date = parse_date_flexible(entry.updated)

                    # Check if article is from last 24 hours
                    if published_date and is_from_last_24_hours(published_date, reference_time):
                        article = {
                            'title': entry.title if hasattr(entry, 'title') else 'No Title',
                            'url': entry.link if hasattr(entry, 'link') else '',
                            'summary': entry.summary if hasattr(entry, 'summary') else '',
                            'author': entry.author if hasattr(entry, 'author') else 'Unknown',
                            'published': published_date.isoformat() if published_date else '',
                            'source': source_name
                        }

                        feed_articles.append(article)
                        logger.info(f"✅ Found recent article: {article['title'][:50]}...")

                except Exception as e:
                    logger.error(f"Error processing entry from {source_name}: {e}")

            logger.info(f"📰 Found {len(feed_articles)} recent articles from {source_name}")
            all_articles.extend(feed_articles)

        except Exception as e:
            logger.error(f"❌ Error fetching from {source_name}: {e}")

    logger.info(f"🎉 Total recent articles found: {len(all_articles)}")
    return all_articles
