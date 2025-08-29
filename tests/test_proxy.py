import httpx
import asyncio
import json

async def test_proxy():
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": "gpt-3.5-turbo",
        "max_tokens": 100,
        "messages": [
            {
                "role": "system",
                "content": "My name is Robert."
            },
            {
                "role": "user",
                "content": "как тебя зовут"
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(test_proxy())
