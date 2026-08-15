import asyncio
from core.scraper import LeadScraper
import traceback

async def test():
    try:
        scraper = LeadScraper(headless=True)
        print("Scraper initialized. Running...")
        leads = await scraper.scrape("Gyms in Austin TX", 2)
        print(f"Found {len(leads)} leads")
    except Exception as e:
        print("EXCEPTION CAUGHT!")
        print(f"Type: {type(e)}")
        print(f"Str: '{str(e)}'")
        print(traceback.format_exc())

asyncio.run(test())
