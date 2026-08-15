import asyncio
from core.pitcher import PitchGenerator
from models.schemas import LeadRecord, NicheType

async def test():
    pitcher = PitchGenerator()
    lead = LeadRecord(name="Test", website_url="http://test.com", niche=NicheType.GYM)
    try:
        pitch = await pitcher.generate(lead, ["Bad design"])
        print("SUCCESS:", pitch)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
