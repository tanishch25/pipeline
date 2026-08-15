import asyncio
import os
from config.settings import settings
from core.pitcher import PitchGenerator
from models.schemas import LeadRecord, NicheType

async def test_pitch():
    lead_data = LeadRecord(
        name="Test Lead",
        niche=NicheType.GYM,
        city="Austin",
        website_url="https://test.com"
    )
    
    pitcher = PitchGenerator(engine="cloud") # Use Groq for fast testing
    
    print("Testing 3-draft generation and evaluation...")
    pitch = await pitcher.generate(lead_data, ["No SSL", "Slow load time"])
    
    print("\nFinal Result:")
    print(pitch.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(test_pitch())
