import httpx
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from models.schemas import TechnicalAuditMetrics
import asyncio

class WebsiteAuditor:
    def __init__(self, timeout_seconds: int = 15):
        self.timeout = timeout_seconds
        
    async def _fetch_html(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
            try:
                response = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                return response.text
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                return ""

    def _detect_stack(self, html: str, headers: dict = None) -> list:
        stack = []
        html_lower = html.lower()
        if "wp-content" in html_lower or "wordpress" in html_lower:
            stack.append("WordPress")
        if "wix.com" in html_lower or "x-wix" in html_lower:
            stack.append("Wix")
        if "weebly" in html_lower:
            stack.append("Weebly")
        if "joomla" in html_lower:
            stack.append("Joomla")
        if "cdn.shopify.com" in html_lower:
            stack.append("Shopify")
        if not stack:
            stack.append("Custom/Static")
        return stack

    def _analyze_with_playwright_sync(self, url: str) -> dict:
        result = {
            "load_time": 0.0,
            "is_mobile_responsive": True, # Assume true until proven false
        }
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # Mobile viewport (iPhone 12/13)
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
                )
                page = context.new_page()
                
                start_time = time.time()
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
                result["load_time"] = time.time() - start_time
                
                # Check for horizontal scroll (not mobile responsive)
                scroll_width = page.evaluate("document.documentElement.scrollWidth")
                viewport_width = page.viewport_size['width']
                if scroll_width > viewport_width:
                    result["is_mobile_responsive"] = False
                    
                browser.close()
        except Exception as e:
            print(f"Playwright analysis failed for {url}: {e}")
            # Fallback values if it fails
            result["load_time"] = self.timeout
            result["is_mobile_responsive"] = False
            
        return result

    async def audit(self, url: str) -> (TechnicalAuditMetrics, str):
        print(f"Auditing technical metrics for: {url}")
        
        has_ssl = url.startswith("https")
        
        html = await self._fetch_html(url)
        if not html:
            # Return failed audit
            return TechnicalAuditMetrics(
                has_ssl=has_ssl,
                load_time_seconds=float(self.timeout),
                is_mobile_responsive=False,
                detected_tech_stack=["Unknown"],
                meta_description_present=False,
                h1_count=0,
                has_broken_ctas=True
            ), "", None, {
                "facebook_url": None,
                "twitter_url": None,
                "instagram_url": None,
                "linkedin_url": None
            }

        soup = BeautifulSoup(html, "html.parser")
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        h1_count = len(soup.find_all("h1"))
        stack = self._detect_stack(html)
        
        # Run playwright in a separate thread to avoid event loop issues
        pw_results = await asyncio.to_thread(self._analyze_with_playwright_sync, url)
        
        metrics = TechnicalAuditMetrics(
            has_ssl=has_ssl,
            load_time_seconds=round(pw_results["load_time"], 2),
            is_mobile_responsive=pw_results["is_mobile_responsive"],
            detected_tech_stack=stack,
            meta_description_present=bool(meta_desc),
            h1_count=h1_count,
            has_broken_ctas=False # Simplified for now
        )
        
        # Clean text for LLM
        for script in soup(["script", "style", "noscript"]):
            script.extract()
        text_content = soup.get_text(separator=" ", strip=True)
        # truncate text to avoid token limits
        text_content = text_content[:5000]
        
        # Extract email using regex on raw html
        import re
        raw_emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", html)
        
        # Filter out obvious fake/system emails
        bad_domains = ['sentry', 'wix', 'example', 'domain', 'test']
        bad_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']
        
        valid_emails = []
        for e in raw_emails:
            e_lower = e.lower()
            if not any(b in e_lower for b in bad_domains) and not any(e_lower.endswith(ext) for ext in bad_extensions):
                valid_emails.append(e)
                
        found_email = valid_emails[0] if valid_emails else None
        # Extract social links
        social_links = {
            "facebook_url": None,
            "twitter_url": None,
            "instagram_url": None,
            "linkedin_url": None
        }
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].lower()
            if "facebook.com" in href and not social_links["facebook_url"]:
                social_links["facebook_url"] = a_tag["href"]
            elif ("twitter.com" in href or "x.com" in href) and not social_links["twitter_url"]:
                social_links["twitter_url"] = a_tag["href"]
            elif "instagram.com" in href and not social_links["instagram_url"]:
                social_links["instagram_url"] = a_tag["href"]
            elif "linkedin.com" in href and not social_links["linkedin_url"]:
                social_links["linkedin_url"] = a_tag["href"]
        
        return metrics, text_content, found_email, social_links
