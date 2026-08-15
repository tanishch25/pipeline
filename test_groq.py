import asyncio
import os
from litellm import acompletion

os.environ["GROQ_API_KEY"] = "your_groq_api_key_here"

async def test():
    try:
        response = await acompletion(
            model="openai/llama-3.1-8b-instant",
            api_base="https://api.groq.com/openai/v1",
            api_key=os.environ["GROQ_API_KEY"],
            messages=[{"role": "user", "content": "hi"}],
            max_retries=1
        )
        print("Success!")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
