import httpx
import json

def test_mcp():
    base_url = "https://mcp.sellersprite.com/mcp"
    endpoints = ["", "/", "/sse", "/mcp", "/mcp/sse"]
    headers = {
        "secret-key": "953f8211226e4d31bcba3237ae18f21f",
        "Content-Type": "application/json"
    }
    
    for ep in endpoints:
        url = base_url + ep
        print(f"\n--- Testing {url} ---")
        try:
            # Try POST for listTools
            payload = {"jsonrpc": "2.0", "id": 1, "method": "listTools", "params": {}}
            resp = httpx.post(url, headers=headers, json=payload, timeout=5.0)
            print(f"POST Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"POST Success! Response: {resp.text[:200]}...")
            
            # Try GET (SSE)
            resp_get = httpx.get(url, headers=headers, timeout=5.0)
            print(f"GET Status: {resp_get.status_code}")
            if resp_get.status_code == 200:
                print(f"GET Success! Response: {resp_get.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_mcp()
