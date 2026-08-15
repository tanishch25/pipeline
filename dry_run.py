import asyncio
from main import run_pipeline_async

if __name__ == "__main__":
    asyncio.run(run_pipeline_async("Test Gyms", 5, True))
