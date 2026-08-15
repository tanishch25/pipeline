import asyncio
from litellm import acompletion
from config.settings import settings

async def test():
    try:
        print(f"Testing model: {settings.DEFAULT_LLM_MODEL}")
        res = await acompletion(
            model=settings.DEFAULT_LLM_MODEL, 
            messages=[{'role':'user', 'content':'hello'}], 
            api_key=settings.GEMINI_API_KEY
        )
        print("Success:", res.choices[0].message.content)
    except Exception as e:
        print("Error:", repr(e))

asyncio.run(test())
