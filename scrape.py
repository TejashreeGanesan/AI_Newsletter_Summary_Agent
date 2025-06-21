import asyncio
import logging
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Configure logging
logger = logging.getLogger(__name__)

class ArticleScraper:
    """Main article scraper class with multiple scraping strategies"""

    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def scrape_with_crawl4ai(self, url):
        """Scrape full content from article URL using Crawl4AI with enhanced configuration"""
        try:
            logger.info(f"Scraping with Crawl4AI: {url}")

            # Configure crawler with optimized settings
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,  # Always get fresh content
                wait_for="css:body",  # Wait for body to load
                page_timeout=30000,  # 30 second timeout
                delay_before_return_html=2.0,  # Wait 2 seconds for JS to render
                remove_overlay_elements=True,  # Remove popups/overlays
                excluded_tags=['script', 'style', 'nav', 'footer', 'header', 'aside', 'advertisement', 'ads'],
                wait_for_images=False,  # Don't wait for images to speed up
            )

            async with AsyncWebCrawler(config=self.browser_config, verbose=True) as crawler:
                # First attempt with standard configuration
                result = await crawler.arun(url=url, config=config)

                if not result.success:
                    logger.warning(f"First attempt failed for {url}: {result.error_message}")

                    # Second attempt with different settings
                    fallback_config = CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        page_timeout=45000,  # Longer timeout
                        delay_before_return_html=3.0,  # Longer wait
                        remove_overlay_elements=True,
                        wait_for="networkidle",  # Wait for network to be idle
                    )

                    result = await crawler.arun(url=url, config=fallback_config)

                    if not result.success:
                        logger.error(f"Both attempts failed for {url}: {result.error_message}")
                        return "", ""

                # Extract content and image
                content, image_url = self._extract_content_from_result(result, url)

                if content and len(content) > 100:
                    logger.info(f"✅ Successfully scraped {url} with Crawl4AI - {len(content)} characters")
                    return content, image_url
                else:
                    logger.warning(f"⚠️ No meaningful content found for {url} with Crawl4AI")
                    return "", ""

        except Exception as e:
            logger.error(f"❌ Error scraping {url} with Crawl4AI: {e}")
            return "", ""

    def _extract_content_from_result(self, result, url):
        """Extract content and images from Crawl4AI result"""
        content = ""
        image_url = ""

        # Get cleaned text content
        if result.cleaned_html:
            content = self._extract_text_from_html(result.cleaned_html)

        # Fall back to markdown if cleaned_html doesn't work well
        if not content or len(content) < 100:
            if result.markdown:
                content = self._clean_markdown_content(result.markdown)

        # Extract images from the original HTML
        if result.html:
            image_url = self._extract_image_from_html(result.html, url)

        # Limit content size to prevent oversized embeddings
        if content and len(content) > 15000:
            content = content[:15000]

        # Log results
        content_length = len(content) if content else 0
        logger.info(f"Crawl4AI results for {url}:")
        logger.info(f"  Success: {result.success}")
        logger.info(f"  Content length: {content_length} characters")
        logger.info(f"  Image found: {'Yes' if image_url else 'No'}")

        return content, image_url

    def _extract_text_from_html(self, html_content):
        """Extract clean text from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Try to find main content area
            main_content = None
            content_selectors = [
                'article', '[role="main"]', 'main', '.post-content',
                '.entry-content', '.article-content', '.content', '.post-body'
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content and main_content.get_text().strip():
                    break

            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body') or soup

            if main_content:
                content = main_content.get_text()
                # Clean up the content
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)
                return content

        except Exception as e:
            logger.error(f"Error extracting text from HTML: {e}")

        return ""

    def _clean_markdown_content(self, markdown_content):
        """Clean and format markdown content"""
        try:
            content = markdown_content
            # Clean markdown formatting for better text extraction
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # Remove links
            content = re.sub(r'[#*_`]', '', content)  # Remove markdown symbols
            content = re.sub(r'\s+', ' ', content).strip()
            return content
        except Exception as e:
            logger.error(f"Error cleaning markdown content: {e}")
            return ""

    def _extract_image_from_html(self, html_content, base_url):
        """Extract the best image from HTML content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Try to find a good image
            img_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                'img[class*="featured"]',
                'img[class*="hero"]',
                'article img',
                '.content img',
                'img'
            ]

            for selector in img_selectors:
                img_element = soup.select_one(selector)
                if img_element:
                    src = img_element.get('content') or img_element.get('src', '')
                    if src:
                        # Make relative URLs absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = urljoin(base_url, src)

                        if src.startswith('http') and any(
                                ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                            return src

        except Exception as e:
            logger.error(f"Error extracting image from HTML: {e}")

        return ""

    async def scrape_with_requests(self, url):
        """Fallback scraping method using requests + BeautifulSoup"""
        try:
            logger.info(f"Scraping with requests fallback: {url}")

            response = requests.get(url, headers=self.headers, timeout=30, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Try to find main content area first
            main_content = None
            content_selectors = [
                'article', '[role="main"]', 'main', '.post-content',
                '.entry-content', '.article-content', '.content'
            ]

            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # If no main content found, use body
            if not main_content:
                main_content = soup.find('body')

            content = ""
            if main_content:
                content = main_content.get_text()
            else:
                content = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)

            # Try to find images
            image_url = self._extract_image_from_html(str(soup), url)

            if content and len(content) > 100:
                content = content[:15000] if len(content) > 15000 else content
                logger.info(f"✅ Fallback scraping successful for {url} - {len(content)} characters")
                return content, image_url
            else:
                logger.warning(f"⚠️ Fallback scraping found no meaningful content for {url}")
                return "", ""

        except Exception as e:
            logger.error(f"❌ Fallback scraping error for {url}: {e}")
            return "", ""

    async def scrape_article(self, url):
        """Main scraping function that tries Crawl4AI first, then falls back to requests"""
        try:
            # First try with Crawl4AI
            content, image_url = await self.scrape_with_crawl4ai(url)

            if content and len(content) > 100:
                return content, image_url

            # Fallback to requests if Crawl4AI doesn't work well
            logger.info(f"Falling back to requests for {url}")
            return await self.scrape_with_requests(url)

        except Exception as e:
            logger.error(f"Error in main scraping function for {url}: {e}")
            return "", ""

    async def scrape_multiple_articles(self, urls):
        """Scrape multiple articles concurrently"""
        try:
            logger.info(f"Scraping {len(urls)} articles concurrently...")

            # Create tasks for concurrent scraping
            tasks = [self.scrape_article(url) for url in urls]

            # Run with limited concurrency to avoid overwhelming servers
            semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests

            async def scrape_with_semaphore(url):
                async with semaphore:
                    return await self.scrape_article(url)

            # Execute all tasks
            results = await asyncio.gather(*[scrape_with_semaphore(url) for url in urls])

            logger.info(f"Completed scraping {len(results)} articles")
            return results

        except Exception as e:
            logger.error(f"Error in batch scraping: {e}")
            return [(None, None) for _ in urls]


# Convenience functions for easy importing
async def scrape_single_article(url):
    """Scrape a single article - convenience function"""
    scraper = ArticleScraper()
    return await scraper.scrape_article(url)


async def scrape_articles_batch(urls):
    """Scrape multiple articles - convenience function"""
    scraper = ArticleScraper()
    return await scraper.scrape_multiple_articles(urls)

'''
# For testing the scraper independently
if __name__ == "__main__":
    async def test_scraper():
        """Test the scraper with a sample URL"""
        test_url = "https://simonw.substack.com/p/trying-out-the-new-gemini-25-model"

        scraper = ArticleScraper()
        content, image_url = await scraper.scrape_article(test_url)

        print(f"Content length: {len(content) if content else 0}")
        print(f"Image URL: {image_url}")
        print(f"Content preview: {content[:200] if content else 'No content'}...")


    # Run the test
    asyncio.run(test_scraper())
'''