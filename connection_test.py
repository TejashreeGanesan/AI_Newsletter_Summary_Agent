import logging
from config import pc, perplexity_client
import google.generativeai as genai
logger = logging.getLogger(__name__)
def test_connection():
    """Test all API connections"""
    logger.info("🔧 Testing API connections...")

    try:
        indexes = pc.list_indexes()
        logger.info(f"✅ Pinecone connected. Indexes: {[idx.name for idx in indexes]}")
    except Exception as e:
        logger.error(f"❌ Pinecone error: {e}")
        return False

    try:
        test_embedding = genai.embed_content(
            model='models/embedding-001',
            content="test",
            task_type="retrieval_document"
        )
        logger.info(f"✅ Google Gemini connected. Embedding dimension: {len(test_embedding['embedding'])}")
    except Exception as e:
        logger.error(f"❌ Google Gemini error: {e}")
        return False

    try:
        response = perplexity_client.chat.completions.create(
            model="llama-3.1-sonar-small-128k-online",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        logger.info("✅ Perplexity connected")
    except Exception as e:
        logger.error(f"❌ Perplexity error: {e}")
        return False

    return True
