import streamlit as st
import os
from pinecone import Pinecone
from dotenv import load_dotenv
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
import asyncio
import edge_tts
import io

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Newsletter Summary",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern black and purple theme
st.markdown(f"""
<style>
    /* Main app background */
    .stApp {{
        background-color: #000000 !important;
        color: white;
    }}

    /* Remove link symbols from headers */
    .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a {{
        display: none !important;
    }}

    /* Hide streamlit header link */
    .stMarkdown [data-testid="stHeaderActionElements"] {{
        display: none !important;
    }}

    /* Main content area */
    .main-content {{
        background: rgba(0, 0, 0, 0.9);
        border-radius: 10px;
        padding: 5px;
        margin: 1px;
    }}

    /* Article card styling */

    /* Article titles */
    .article-title {{
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 12px;
        line-height: 1.3;
    }}

    /* Article meta information */
    .article-meta {{
        color: #CCCCCC;
        font-size: 14px;
        margin-bottom: 20px;
        display: flex;
        gap: 15px;
        align-items: center;
        flex-wrap: wrap;
    }}

    .article-meta a {{
        color: #7D2AE8;
        text-decoration: none;
    }}

    .article-meta a:hover {{
        text-decoration: underline;
    }}

    /* Article summary text */
    .article-summary {{
        font-size: 16px;
        line-height: 1.6;
        color: #FFFFFF;
        margin-bottom: 25px;
        text-align: justify;
    }}

    /* Image container with proper spacing and centering */
    .image-container {{
        display: flex;
        justify-content: center;
        margin: 25px 0;
        position: relative;
    }}

    /* Style for streamlit images - FIXED VERSION */
    .stImage {{
        text-align: center !important;
        margin: 25px auto !important;
    }}

    .stImage > div {{
        display: flex !important;
        justify-content: center !important;
        overflow: hidden !important;
        border-radius: 20px !important;
    }}

    .stImage img {{
        border-radius: 20px !important;
        border: 3px solid #7D2AE8 !important;
        box-shadow: 0 4px 15px rgba(125, 42, 232, 0.3) !important;
        max-width: 100% !important;
        height: auto !important;
        object-fit: cover !important;
    }}

    /* Override any conflicting border-radius styles */
    div[data-testid="stImage"] img {{
        border-radius: 20px !important;
        border: 3px solid #7D2AE8 !important;
    }}

    /* Additional override for image elements */
    [data-testid="stImage"] > div > img,
    [data-testid="stImage"] img,
    .stImage img {{
        border-radius: 20px !important;
        border: 3px solid #7D2AE8 !important;
        box-shadow: 0 4px 15px rgba(125, 42, 232, 0.3) !important;
    }}

    /* Image expand button positioning */
    .stImage button {{
        position: absolute !important;
        top: 10px !important;
        right: 10px !important;
        background: rgba(0, 0, 0, 0.7) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        color: white !important;
        cursor: pointer !important;
        z-index: 10 !important;
    }}

    .stImage button:hover {{
        background: rgba(125, 42, 232, 0.8) !important;
    }}

    /* Style buttons */
    .stButton > button {{
        background-color: #7D2AE8 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        margin: 0 auto !important;
        display: block !important;
        transition: all 0.3s ease !important;
    }}

    .stButton > button:hover {{
        background-color: #6A1BB8 !important;
        transform: translateY(-2px) !important;
    }}

    /* Style selectbox */
    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(125, 42, 232, 0.5) !important;
        border-radius: 8px !important;
        color: white !important;
        margin: 0 auto !important;
        width: 250px !important;
    }}

    /* Title styling - reduced size */
    h1 {{
        color: white !important;
        text-align: center !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 10px !important;
        text-decoration: none !important;
    }}

    h1 a {{
        display: none !important;
    }}

    .purple {{
        color: #7D2AE8 !important;
    }}

    /* Centered elements */
    .centered {{
        text-align: center;
        margin: 0 auto;
    }}

    /* Audio player - FIXED TO CENTER */
    .stAudio {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 20px auto !important;
        width: 100% !important;
    }}

    .stAudio > div {{
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        max-width: 600px !important;
        margin: 0 auto !important;
    }}

    audio {{
        border-radius: 8px !important;
        width: 100% !important;
        max-width: 600px !important;
        margin: 0 auto !important;
        border: none !important;
        outline: none !important;
    }}

    /* Remove link icons from all headers */
    .stMarkdown h1::after,
    .stMarkdown h2::after,
    .stMarkdown h3::after {{
        display: none !important;
    }}

    /* Hide anchor links */
    .stMarkdown a[href^="#"] {{
        display: none !important;
    }}

    /* Responsive design */
    @media (max-width: 768px) {{
        .article-meta {{
            flex-direction: column;
            gap: 8px;
            align-items: flex-start;
        }}

        .article-card {{
            padding: 15px;
        }}

        .article-title {{
            font-size: 20px;
        }}

        h1 {{
            font-size: 2rem !important;
        }}

        .stImage img {{
            max-width: 95% !important;
        }}

        .stAudio {{
            margin: 20px 0 !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_pinecone():
    """Initialize Pinecone connection"""
    try:
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME")

        if not api_key or not index_name:
            return None

        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        return index

    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None


def load_image_from_url(url):
    """Load and resize image from URL"""
    try:
        if not url or url == "":
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        # Smaller image size for better proportion with summary
        image.thumbnail((280, 200), Image.Resampling.LANCZOS)
        return image
    except Exception:
        return None


async def create_audio_from_all_articles(articles, voice="en-US-AriaNeural"):
    """Convert all articles to speech using edge-tts with high-quality voice"""
    try:
        # Combine all articles into one text
        full_text = "Welcome to your AI Newsletter Summary. Here are today's top stories.\n\n"

        for i, article in enumerate(articles, 1):
            # Add article number and title
            full_text += f"Article {i}: {article['title']}\n"

            # Add author and source
            if article['author'] and article['author'] != 'Unknown Author':
                full_text += f"By {article['author']} from {article['source']}.\n"
            else:
                full_text += f"From {article['source']}.\n"

            # Add summary
            full_text += f"{article['ai_summary']}\n\n"

            # Add a pause between articles
            if i < len(articles):
                full_text += "Next article.\n\n"

        full_text += "That concludes your newsletter summary. Have a great day!"

        # Create TTS using edge-tts
        communicate = edge_tts.Communicate(full_text, voice)

        # Generate audio to bytes
        audio_bytes = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.write(chunk["data"])

        audio_bytes.seek(0)
        return audio_bytes.getvalue()

    except Exception as e:
        st.error(f"Error creating audio: {e}")
        return None


def get_articles_from_pinecone(index, limit=7):
    """Retrieve articles from Pinecone"""
    try:
        query_response = index.query(
            vector=[0.1] * 768,
            top_k=limit,
            include_metadata=True
        )

        articles = []
        for match in query_response.matches:
            metadata = match.metadata
            articles.append({
                'id': match.id,
                'title': metadata.get('title', 'No Title'),
                'author': metadata.get('author', 'Unknown Author'),
                'source': metadata.get('source', 'Unknown Source'),
                'ai_summary': metadata.get('ai_summary', metadata.get('summary', 'No summary available')),
                'original_summary': metadata.get('original_summary', ''),
                'image': metadata.get('image', ''),
                'url': metadata.get('url', ''),
                'published': metadata.get('published', ''),
                'score': match.score
            })

        return articles

    except Exception as e:
        st.error(f"Error retrieving articles: {str(e)}")
        return []


def render_article_card(article, index):
    """Render individual article card"""
    st.markdown('<div class="article-card">', unsafe_allow_html=True)

    # Title
    st.markdown(f'<div class="article-title">{article["title"]}</div>', unsafe_allow_html=True)

    # Meta information
    published_date = ""
    if article["published"]:
        try:
            dt = datetime.fromisoformat(article["published"].replace('Z', '+00:00'))
            published_date = dt.strftime("%b %d, %Y")
        except:
            published_date = ""

    meta_html = f'''
    <div class="article-meta">
        <span>👤 <strong>{article["author"]}</strong></span>
        <span>📰 {article["source"]}</span>
        {f'<span>📅 {published_date}</span>' if published_date else ''}
        <span>🔗 <a href="{article["url"]}" target="_blank">Read Full Article</a></span>
    </div>
    '''
    st.markdown(meta_html, unsafe_allow_html=True)

    # AI Summary
    st.markdown(f'<div class="article-summary">{article["ai_summary"]}</div>', unsafe_allow_html=True)

    # Image with proper centering and spacing
    if article["image"]:
        image = load_image_from_url(article["image"])
        if image:
            # Create centered image container with better proportions
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            with col2:
                st.image(image, caption="Article Image", use_column_width=True)
        else:
            # Fallback placeholder centered
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            with col2:
                st.image("https://via.placeholder.com/280x200?text=No+Image+Available",
                         caption="Image not available", use_column_width=True)
    else:
        # No image placeholder centered
        col1, col2, col3 = st.columns([1.5, 1, 1.5])
        with col2:
            st.image("https://via.placeholder.com/280x200?text=No+Image+Available",
                     caption="No image available", use_column_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


def get_available_voices():
    """Get list of available high-quality voices"""
    return {
        "Aria (Female, US)": "en-US-AriaNeural",
        "Guy (Male, US)": "en-US-GuyNeural",
        "Jenny (Female, US)": "en-US-JennyNeural",
    }


def main():
    """Main Streamlit app"""

    # Header
    st.markdown('<div class="main-content">', unsafe_allow_html=True)

    # Title and description - using HTML to avoid link symbols
    st.markdown("""
    <div style="text-align: center;">
        <h1 style="color: white; font-size: 3.5rem; font-weight: 800; margin-bottom: 5px;">
            AI NEWSLETTER SUMMARY
        </h1>
    </div>
    """, unsafe_allow_html=True)

    # Initialize Pinecone
    index = init_pinecone()

    if index is None:
        st.error("Could not connect to the database. Please check your configuration.")
        st.stop()

    # Load articles
    with st.spinner("Loading articles..."):
        all_articles = get_articles_from_pinecone(index)

    if not all_articles:
        st.warning("No articles found.")
        st.stop()

    # Count sources
    sources = {}
    for article in all_articles:
        source = article['source']
        sources[source] = sources.get(source, 0) + 1

    source_text = ", ".join([f"{k}: {v}" for k, v in sources.items()])

    # Display article count and sources using HTML to avoid link symbols
    st.markdown(f"""
    <div class="centered">
        <h2 style="color: #7D2AE8; font-size: 1.8rem; margin-bottom: 15px;">
            Latest articles: Found {len(all_articles)}
        </h2>
        <p style="font-size: 16px; margin-bottom: 10px;">Sources: {source_text}</p>
        <p style="font-size: 16px; margin-bottom: 10px;">Stay updated with the latest AI and tech news with AI-powered summaries.</p>
        <p style="font-size: 16px; margin-bottom: 20px;">Select Voice and Click the below button to generate audio summary.</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice selection centered - FIXED EMPTY LABEL
    st.markdown('<div class="centered">', unsafe_allow_html=True)
    voices = get_available_voices()
    selected_voice_name = st.selectbox(
        "Select Voice",  # Added proper label
        list(voices.keys()),
        index=0,
        label_visibility="hidden"  # Hide the label for visual purposes
    )
    selected_voice = voices[selected_voice_name]

    # Generate button centered
    if st.button("Generate Audio Summary", type="primary"):
        with st.spinner(f"Generating audio for {len(all_articles)} articles..."):
            try:
                audio_data = asyncio.run(create_audio_from_all_articles(all_articles, selected_voice))

                if audio_data:
                    # Center the audio player using columns
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.audio(audio_data, format='audio/mp3')
                else:
                    st.error("Failed to generate audio. Please try again.")

            except Exception as e:
                st.error(f"Error generating audio: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Add some spacing before articles
    st.markdown("<br>", unsafe_allow_html=True)

    # Display articles
    for i, article in enumerate(all_articles):
        render_article_card(article, i)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()