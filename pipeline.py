import asyncio
import logging
from datetime import datetime
import pytz
from rss_fetcher import fetch_recent_articles
from pinecone_manager import create_index, clear_old_articles, embed_and_store, verify_stored_data
from ai_services import summarize_content
from connection_test import test_connection
from scrape import ArticleScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set timezone
IST = pytz.timezone('Asia/Kolkata')

async def process_articles():
    """Main processing function"""
    logger.info("🚀 Starting newsletter processing for last 24 hours...")

    index = create_index()
    if not index:
        logger.error("Failed to create/access Pinecone index")
        return

    # Clear old articles first
    clear_old_articles(index)

    # Fetch articles from last 24 hours
    articles = fetch_recent_articles()

    if not articles:
        logger.warning(
            "⚠️ No recent articles found! This might be normal if no newsletters were published in the last 24 hours.")
        return

    logger.info(f"📰 Processing {len(articles)} articles...")

    # Initialize the scraper
    scraper = ArticleScraper()

    processed_count = 0
    failed_count = 0

    for i, article in enumerate(articles, 1):
        try:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Processing article {i}/{len(articles)}: {article['title']}")
            logger.info(f"Published: {article['published']}")
            logger.info(f"Source: {article['source']}")
            logger.info(f"Original URL: {article['url']}")
            logger.info(f"{'=' * 60}")

            # Use the scraper to get content and image
            content, image_url = await scraper.scrape_article(article['url'])

            if content:
                ai_summary = summarize_content(content)
                success = embed_and_store(index, article, content, image_url, ai_summary)

                if success:
                    processed_count += 1
                    logger.info(f"✅ Successfully processed: {article['title'][:50]}...")
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to store: {article['title'][:50]}...")
            else:
                failed_count += 1
                logger.warning(f"⚠️ No content scraped for: {article['title'][:50]}...")

            # Small delay between articles to be respectful
            await asyncio.sleep(2)

        except Exception as e:
            failed_count += 1
            logger.error(f"Error processing article {article['title']}: {e}")

    logger.info(f"\n🎉 Processing complete!")
    logger.info(f"✅ Successfully processed: {processed_count} articles")
    logger.info(f"❌ Failed: {failed_count} articles")
    if processed_count + failed_count > 0:
        logger.info(f"📊 Success rate: {(processed_count / (processed_count + failed_count) * 100):.1f}%")

    verify_stored_data(index)


def main():
    """Main entry point for the application - simplified for cron job execution"""
    logger.info("🚀 Starting Newsletter Pipeline with Perplexity API")
    logger.info(f"⏰ Current IST time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")

    if not test_connection():
        logger.error("❌ Some API connections failed. Please check your configuration.")
        return 1

    try:
        logger.info("🏃‍♂️ Running pipeline...")
        asyncio.run(process_articles())
        logger.info("✅ Pipeline execution completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())