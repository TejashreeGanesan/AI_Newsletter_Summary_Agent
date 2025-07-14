import google.generativeai as genai
import time
import logging
import re

from config import perplexity_client
from text_utils import clean_perplexity_summary, ensure_complete_sentences

logger = logging.getLogger(__name__)


def preprocess_for_tts(text):
    """Preprocess text to make it more TTS-friendly"""
    # Handle version numbers (e.g., "2. 5" -> "2.5")
    text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)

    # Handle decimal numbers with spaces (e.g., "3. 14" -> "3.14")
    text = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', text)

    # Handle model names with spaces (e.g., "GPT 4" -> "GPT-4")
    text = re.sub(r'\b([A-Z]+)\s+(\d+(?:\.\d+)?)\b', r'\1-\2', text)

    # Handle common abbreviations that might have spaces
    text = re.sub(r'\bA\.\s*I\.\b', 'AI', text)
    text = re.sub(r'\bU\.\s*S\.\b', 'US', text)
    text = re.sub(r'\bU\.\s*K\.\b', 'UK', text)

    # Handle acronyms with periods and spaces (e.g., "N. A. S. A." -> "NASA")
    text = re.sub(r'\b([A-Z])\.\s*([A-Z])\.\s*([A-Z])\.\s*([A-Z])\.\b', r'\1\2\3\4', text)
    text = re.sub(r'\b([A-Z])\.\s*([A-Z])\.\s*([A-Z])\.\b', r'\1\2\3', text)

    # Handle company names with periods (e.g., "Inc." -> "Incorporated")
    text = re.sub(r'\bInc\.\b', 'Incorporated', text)
    text = re.sub(r'\bLtd\.\b', 'Limited', text)
    text = re.sub(r'\bCorp\.\b', 'Corporation', text)

    # Handle common technical terms
    text = re.sub(r'\bAPI\b', 'A-P-I', text)  # Some TTS engines pronounce this better
    text = re.sub(r'\bURL\b', 'U-R-L', text)
    text = re.sub(r'\bHTTP\b', 'H-T-T-P', text)

    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def generate_embedding(content):
    """Generate embedding using Google Gemini with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if len(content) > 10000:
                content = content[:10000]

            logger.debug(f"Generating embedding for content of length: {len(content)}")

            response = genai.embed_content(
                model='models/embedding-001',
                content=content,
                task_type="retrieval_document"
            )

            logger.debug(f"Embedding generated successfully. Dimension: {len(response['embedding'])}")
            return response['embedding']

        except Exception as e:
            logger.warning(f"Embedding attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to generate embedding after {max_retries} attempts")
                return None


def summarize_content(content):
    """Summarize content using Perplexity API with retry logic and clean output"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if len(content) > 12000:
                content = content[:12000]

            logger.debug("Calling Perplexity API for summarization...")

            chat = perplexity_client.chat.completions.create(
                model="sonar-pro",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert AI newsletter summarizer. Create a comprehensive yet concise summary that captures the essence of the article.

IMPORTANT: Your response must be clean text suitable for text-to-speech systems. Follow these rules:
- Do NOT use any markdown formatting (no *, **, _, __, `, etc.)
- Do NOT use special characters like backslashes, forward slashes, or symbols
- Use only plain text with proper punctuation
- Write in complete sentences with proper grammar
- Use simple quotation marks for quotes (not fancy quotes)
- Do NOT include any citations, reference numbers, or source attributions
- Do NOT add [1], [2], (1), (2) or any numbered references
- ALWAYS end with complete sentences - never cut off mid-sentence
- For version numbers, write them WITHOUT spaces (e.g., "Gemini 2.5" not "Gemini 2. 5")
- For model names, use hyphens instead of spaces with numbers (e.g., "GPT-4" not "GPT 4")
- Write out abbreviations when they might be unclear in speech

Your summary should:
- Be exactly 4-5 complete sentences (80-150 words)
- Start with the main news or development
- Include key details, numbers, or quotes when relevant
- Explain the significance or implications
- End with future outlook or impact with a proper conclusion
- Write for business professionals and tech enthusiasts
- Be engaging and informative
- Ensure all sentences are grammatically complete"""
                    },
                    {"role": "user",
                     "content": f"Please summarize this article in exactly 4-5 complete sentences with clean, plain text suitable for text-to-speech with no citations or references. Make sure version numbers have no spaces (like 2.5 not 2. 5) and end with a complete sentence:\n\n{content}"}
                ],
                max_tokens=250,  # Increased from 200 to ensure complete sentences
                temperature=0.2,  # Slightly lower for more consistent output

            )

            summary = chat.choices[0].message.content.strip()

            # Clean citations and references from Perplexity response
            clean_summary = clean_perplexity_summary(summary)

            # Additional check to ensure the summary ends properly
            clean_summary = ensure_complete_sentences(clean_summary)

            # Preprocess for TTS-friendly output
            clean_summary = preprocess_for_tts(clean_summary)

            logger.debug(f"Original summary: {summary}")
            logger.debug(f"Cleaned summary: {clean_summary}")
            logger.debug(f"Summary generated: {len(clean_summary)} characters")

            # Validate summary quality
            if len(clean_summary) < 50:
                logger.warning("Summary too short, retrying...")
                continue

            return clean_summary

        except Exception as e:
            logger.warning(f"Summarization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to generate summary after {max_retries} attempts")
                return "Summary not available"