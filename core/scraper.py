from typing import List, Optional
from playwright.sync_api import sync_playwright, Page
from models.schemas import LeadRecord, NicheType
import random
from urllib.parse import urlparse
import asyncio

class LeadScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]

    def _get_niche_from_query(self, query: str) -> NicheType:
        q_lower = query.lower()
        if "gym" in q_lower or "fitness" in q_lower:
            return NicheType.GYM
        elif "restaurant" in q_lower or "food" in q_lower or "cafe" in q_lower:
            return NicheType.RESTAURANT
        elif "plumb" in q_lower or "electric" in q_lower or "hvac" in q_lower:
            return NicheType.UTILITY
        return NicheType.OTHER

    def _clean_url(self, url: str) -> str:
        if not url:
            return ""
        if not url.startswith("http"):
            url = f"https://{url}"
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    def _handle_consent(self, page: Page):
        try:
            buttons = page.locator("button:has-text('Accept all'), button:has-text('I agree')")
            if buttons.count() > 0:
                buttons.first.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

    def _scrape_sync(self, query: str, limit: int) -> List[LeadRecord]:
        leads: List[LeadRecord] = []
        niche = self._get_niche_from_query(query)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={"width": 1280, "height": 720}
            )
            page = context.new_page()
            
            try:
                search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
                page.goto(search_url, wait_until="domcontentloaded")
                self._handle_consent(page)
                
                page.wait_for_selector("div[role='feed']", timeout=15000)
                page.wait_for_timeout(random.uniform(1500, 3500))

                feed_element = page.locator("div[role='feed']")
                cards = page.locator("div[role='feed'] > div > div > a")
                count = cards.count()
                
                attempts = 0
                while count < limit and attempts < 50:
                    feed_element.hover()
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(random.uniform(1000, 2000))
                    count = cards.count()
                    attempts += 1
                
                processed = 0
                for i in range(min(count, limit * 2)):
                    if processed >= limit:
                        break
                        
                    try:
                        card = cards.nth(i)
                        name = card.get_attribute("aria-label") or "Unknown"
                        
                        card.click()
                        page.wait_for_timeout(random.uniform(1500, 3000))
                        
                        website_locator = page.locator("a[data-item-id='authority']").first
                        website_url = ""
                        if website_locator.count() > 0:
                            website_url = website_locator.get_attribute("href")
                        
                        if not website_url:
                            continue
                            
                        clean_website = self._clean_url(website_url)
                        
                        # Extract phone number
                        phone_locator = page.locator("button[data-item-id^='phone:']").first
                        phone_number = None
                        if phone_locator.count() > 0:
                            phone_attr = phone_locator.get_attribute("data-item-id")
                            if phone_attr and "phone:" in phone_attr:
                                phone_number = phone_attr.split("phone:")[-1]
                        
                        lead = LeadRecord(
                            name=name,
                            niche=niche,
                            website_url=clean_website,
                            phone=phone_number,
                            city=query.split(" in ")[-1] if " in " in query else None
                        )
                        leads.append(lead)
                        processed += 1
                        
                    except Exception as e:
                        print(f"Warning: Failed to process a lead card: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error during Google Maps scraping: {e}")
            finally:
                browser.close()
                
        return leads

    async def scrape(self, query: str, limit: int = 5) -> List[LeadRecord]:
        print(f"Scraping for: {query} (Limit: {limit})")
        return await asyncio.to_thread(self._scrape_sync, query, limit)
