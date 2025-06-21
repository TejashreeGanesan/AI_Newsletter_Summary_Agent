import re
import logging

logger = logging.getLogger(__name__)

def clean_text_for_speech(text):
    """Clean text to remove unwanted characters that cause issues with text-to-speech"""
    if not text:
        return ""

    # Remove common problematic characters
    unwanted_chars = ['*', '/', '\\', '`', '~', '^', '|', '<', '>', '{', '}', '[', ']',
                      '§', '¶', '†', '‡', '•', '◦', '▪', '▫', '–', '—', ''', ''', '"', '"',
                      '…', '¡', '¿', '«', '»', '‹', '›', '€', '£', '¥', '©', '®', '™']

    # Replace unwanted characters with spaces or appropriate alternatives
    cleaned_text = text
    for char in unwanted_chars:
        cleaned_text = cleaned_text.replace(char, ' ')

    # Replace multiple special characters and symbols
    cleaned_text = re.sub(r'[^\w\s\.,!?;:()\-\'\"&@#%]', ' ', cleaned_text)

    # Clean up extra whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    # Remove markdown-style formatting
    cleaned_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_text)  # Bold
    cleaned_text = re.sub(r'\*(.*?)\*', r'\1', cleaned_text)  # Italic
    cleaned_text = re.sub(r'__(.*?)__', r'\1', cleaned_text)  # Bold
    cleaned_text = re.sub(r'_(.*?)_', r'\1', cleaned_text)  # Italic
    cleaned_text = re.sub(r'`(.*?)`', r'\1', cleaned_text)  # Code

    # Remove any remaining problematic patterns
    cleaned_text = re.sub(r'\\[a-zA-Z]', '', cleaned_text)  # Remove backslash commands
    cleaned_text = re.sub(r'\\\w+', '', cleaned_text)  # Remove other backslash patterns

    return cleaned_text.strip()


def clean_perplexity_summary(text):
    """Remove citations and references from Perplexity API responses"""
    if not text:
        return ""

    # Remove citation numbers in square brackets like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)

    # Remove citation numbers in parentheses like (1), (2), etc.
    text = re.sub(r'\(\d+\)', '', text)

    # Remove reference patterns like "References:" or "Sources:" at the end
    text = re.sub(r'\n*(?:References?|Sources?):.*$', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove any numbered list items that might be references
    text = re.sub(r'\n\d+\.\s+.*$', '', text, flags=re.MULTILINE)

    # Remove standalone numbers that might be citations
    text = re.sub(r'\s+\d+\s*$', '', text)
    text = re.sub(r'^\s*\d+\s+', '', text)

    # Clean up multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', ' ', text)

    # Apply general text cleaning for TTS
    text = clean_text_for_speech(text)

    return text.strip()


def clean_url(url):
    if not url:
        return ""
    url = url.strip()
    # Remove only whitespace and control characters
    url = ''.join(char for char in url if ord(char) >= 32 and char not in [' ', '\t', '\n', '\r'])
    return url

def clean_string_for_metadata(s, max_len, preserve_url=False):
    """Clean string for metadata storage with option to preserve URLs"""
    if not s:
        return ""

    if preserve_url:
        cleaned = clean_url(str(s))
    else:
        cleaned = clean_text_for_speech(str(s))
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 and ord(char) < 127)
    return cleaned[:max_len]

def ensure_complete_sentences(text):
    """Ensure the text ends with complete sentences"""
    if not text:
        return text

    # Split into sentences
    sentences = re.split(r'[.!?]+', text)

    # Remove empty strings and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    # If the last part doesn't seem complete (too short or doesn't make sense)
    if sentences and len(sentences[-1]) < 10:
        # Remove the incomplete last sentence
        sentences = sentences[:-1]

    # Rejoin with periods and ensure proper spacing
    if sentences:
        result = '. '.join(sentences) + '.'
        # Clean up any double periods
        result = re.sub(r'\.+', '.', result)
        return result

    return text

