from datetime import datetime, timezone
import hashlib
import time
from ai_services import generate_embedding
from config import pc, PINECONE_INDEX_NAME
import logging

from text_utils import clean_string_for_metadata

logger = logging.getLogger(__name__)

def create_index():
    """Create Pinecone index if it doesn't exist"""
    try:
        existing_indexes = [index.name for index in pc.list_indexes()]
        logger.info(f"Existing indexes: {existing_indexes}")
        index = pc.Index(PINECONE_INDEX_NAME)
        stats = index.describe_index_stats()
        logger.info(f"Index ready. Stats: {stats}")
        return index
    except Exception as e:
        logger.error(f"Error creating/accessing index: {e}")
        return None

def clear_old_articles(index):
    """Delete all existing articles from Pinecone before adding new ones"""
    try:
        logger.info("Clearing old articles from Pinecone...")

        # Get all vector IDs by querying with a dummy vector
        query_response = index.query(
            vector=[0.0] * 768,
            top_k=10000,  # Get all vectors (adjust if you have more)
            include_metadata=False
        )

        if query_response.matches:
            vector_ids = [match.id for match in query_response.matches]
            logger.info(f"Found {len(vector_ids)} existing articles to delete")

            # Delete in batches of 100 (Pinecone limit)
            batch_size = 100
            for i in range(0, len(vector_ids), batch_size):
                batch_ids = vector_ids[i:i + batch_size]
                index.delete(ids=batch_ids)
                logger.info(f"Deleted batch {i // batch_size + 1}/{(len(vector_ids) + batch_size - 1) // batch_size}")
                time.sleep(1)  # Small delay between batches

            logger.info("Successfully cleared all old articles")
        else:
            logger.info("No existing articles found to delete")

    except Exception as e:
        logger.error(f"Error clearing old articles: {e}")


def embed_and_store(index, article, content, image_url="", ai_summary=""):
    """Store article with embedding in Pinecone"""
    try:
        logger.info(f"Starting embed_and_store for: {article['title'][:50]}...")

        embedding = generate_embedding(content[:5000])

        if embedding is None:
            logger.error(f"Failed to generate embedding for: {article['title']}")
            return False

        doc_id = hashlib.md5(article['url'].encode()).hexdigest()

        metadata = {
            "title": clean_string_for_metadata(article["title"], 500),
            "url": clean_string_for_metadata(article["url"], 500, preserve_url=True),  # Preserve URL structure
            "original_summary": clean_string_for_metadata(article["summary"], 1000),
            "ai_summary": clean_string_for_metadata(ai_summary if ai_summary else article["summary"], 2000),
            "author": clean_string_for_metadata(article["author"], 100),
            "source": clean_string_for_metadata(article["source"], 100),
            "published": article["published"],
            "content": clean_string_for_metadata(content, 2000),
            "image": clean_string_for_metadata(image_url, 500, preserve_url=True) if image_url else "",
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

        # Log the URL being stored for debugging
        logger.info(f"🔗 Storing URL: {metadata['url']}")

        upsert_response = index.upsert([{
            "id": doc_id,
            "values": embedding,
            "metadata": metadata
        }])

        logger.debug(f"Upsert response: {upsert_response}")

        time.sleep(1)
        query_response = index.fetch([doc_id])

        if doc_id in query_response.vectors:
            stored_url = query_response.vectors[doc_id].metadata.get('url', 'N/A')
            logger.info(f"✅ Successfully stored: {article['title'][:50]}...")
            logger.info(f"✅ Verified stored URL: {stored_url}")
            return True
        else:
            logger.error(f"❌ Failed to verify storage: {article['title'][:50]}...")
            return False

    except Exception as e:
        logger.error(f"Error storing article {article['title']}: {e}")
        return False

def verify_stored_data(index, limit=10):
    """Verify what data is actually stored in Pinecone"""
    try:
        logger.info("\n🔍 Verifying stored data in Pinecone...")

        stats = index.describe_index_stats()
        logger.info(f"📊 Pinecone index stats: {stats}")

        if stats.total_vector_count == 0:
            logger.warning("❌ No vectors found in Pinecone index!")
            return

        query_response = index.query(
            vector=[0.1] * 768,
            top_k=min(limit, stats.total_vector_count),
            include_metadata=True
        )

        if query_response.matches:
            logger.info(f"📚 Found {len(query_response.matches)} stored articles:")
            for i, match in enumerate(query_response.matches, 1):
                metadata = match.metadata
                logger.info(f"\n--- Article {i} ---")
                logger.info(f"📰 Title: {metadata.get('title', 'N/A')[:80]}...")
                logger.info(f"👤 Author: {metadata.get('author', 'N/A')}")
                logger.info(f"📰 Source: {metadata.get('source', 'N/A')}")
                logger.info(f"📅 Published: {metadata.get('published', 'N/A')}")
                logger.info(f"🔗 Stored URL: {metadata.get('url', 'N/A')}")
                logger.info(f"🤖 AI Summary: {metadata.get('ai_summary', 'N/A')[:100]}...")

        else:
            logger.warning("No articles found in query results")

    except Exception as e:
        logger.error(f"Error verifying stored data: {e}")

