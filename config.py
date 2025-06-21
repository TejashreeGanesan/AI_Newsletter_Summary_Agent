import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
import google.generativeai as genai
import pytz
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Load API keys
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
RSS_FEEDS = {
    "Lenny's Newsletter": "https://www.lennysnewsletter.com/feed",
    "Simon Willison's Weblog": "https://simonw.substack.com/feed",
    "ADPList Newsletter": "https://adplist.substack.com/feed",
    "Elvis Saravia NLP Newsletter": "https://nlp.elvissaravia.com/feed",
    "Sebastian Raschka Magazine": "https://magazine.sebastianraschka.com/feed",
    "Marvelous MLOps": "https://marvelousmlops.substack.com/feed",
    "Lewis Lin Newsletter": "https://lewislin.substack.com/feed",
    "Aishwarya Srinivasan Newsletter": "https://aishwaryasrinivasan.substack.com/feed",
    "Ask Gib Newsletter": "https://askgib.substack.com/feed",
    "Stratechery": "https://stratechery.passport.online/feed/rss/CLRbYxbmsr6HHbrioJtqt",
    "Corca Newsletter": "https://corca.substack.com",
    "Practical AI Podcast": "https://feeds.megaphone.fm/MLN2155636147"
}

# Configure APIs
genai.configure(api_key=GOOGLE_API_KEY)

# Configure Perplexity API client
perplexity_client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

pc = Pinecone(api_key=PINECONE_API_KEY)

# Set timezones
IST = pytz.timezone('Asia/Kolkata')
EST = pytz.timezone('US/Eastern')