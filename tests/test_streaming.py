import asyncio
import httpx
import json

async def test_streaming():
    """Тестирует streaming ответы"""
    url = "http://localhost:8000/v1/chat/completions"
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "Напиши короткое стихотворение про Python"
            }
        ],
        "stream": True,
        "max_tokens": 150
    }
    
    print("Sending streaming request...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}\n")
            
            if response.status_code == 200:
                print("Streaming response:")
                print("-" * 50)
                
                async for line in response.aiter_lines():
                    if line:
                        print(f"Received: {line}")
                        
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            
                            if data_str == "[DONE]":
                                print("\nStream completed!")
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    choice = data["choices"][0]
                                    if "delta" in choice and "content" in choice["delta"]:
                                        print(f"Content: {choice['delta']['content']}", end="")
                            except json.JSONDecodeError:
                                print(f"Could not parse: {data_str}")
            else:
                print(f"Error: {response.status_code}")
                print(await response.text())

async def test_non_streaming():
    """Тестирует обычные (не streaming) ответы"""
    url = "http://localhost:8000/v1/chat/completions"
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "Скажи 'Привет' на трех языках"
            }
        ],
        "stream": False,
        "max_tokens": 100
    }
    
    print("\n\nTesting non-streaming request...")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Error: {response.text}")

async def main():
    # Тест streaming
    await test_streaming()
    
    # Тест non-streaming
    await test_non_streaming()

if __name__ == "__main__":
    asyncio.run(main())
