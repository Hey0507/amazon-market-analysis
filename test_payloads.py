import httpx
import asyncio
import json

async def test():
    base_url = "https://mcp.sellersprite.com/mcp"
    headers = {"Content-Type": "application/json", "secret-key": "953f8211226e4d31bcba3237ae18f21f"}

    payloads = [
        # 1. Wrapper
        {
            "jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {
                "name": "competitor_lookup",
                "arguments": {
                    "request": {
                        "marketplace": "DE", "month": "202604", "nodeIdPath": "340849031:412469031:5759565031", "size": 10, "variation": "Y"
                    }
                }
            }
        },
        # 2. Flat with nodeIdPaths array
        {
            "jsonrpc": "2.0", "method": "tools/call", "id": 2,
            "params": {
                "name": "competitor_lookup",
                "arguments": {
                    "marketplace": "DE", "month": "202604", "nodeIdPaths": ["340849031:412469031:5759565031"], "size": 10, "variation": "Y"
                }
            }
        },
        # 3. Flat with nodeIdPath string
        {
            "jsonrpc": "2.0", "method": "tools/call", "id": 3,
            "params": {
                "name": "competitor_lookup",
                "arguments": {
                    "marketplace": "DE", "month": "202604", "nodeIdPath": "340849031:412469031:5759565031", "size": 10, "variation": "Y"
                }
            }
        },
        # 4. request wrapper with nodeIdPaths array
        {
            "jsonrpc": "2.0", "method": "tools/call", "id": 4,
            "params": {
                "name": "competitor_lookup",
                "arguments": {
                    "request": {
                        "marketplace": "DE", "month": "202604", "nodeIdPaths": ["340849031:412469031:5759565031"], "size": 10, "variation": "Y"
                    }
                }
            }
        }
    ]

    async with httpx.AsyncClient() as client:
        for i, payload in enumerate(payloads, 1):
            print(f"Testing Payload {i}...")
            resp = await client.post(base_url, json=payload, headers=headers)
            print(f"  Status: {resp.status_code}")
            try:
                data = resp.json()
                print(f"  Response: {str(data)[:200]}")
            except:
                print(f"  Response: {resp.text[:200]}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test())
