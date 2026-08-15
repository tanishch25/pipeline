import httpx
import json

response = httpx.post(
    "http://localhost:8000/api/prompts/test-pitch",
    json={
        "lead_id": 1,
        "system_prompt": "hello",
        "user_template": "world",
        "temperature": 0.7
    },
    timeout=30.0
)
print(response.status_code)
print(response.text)
