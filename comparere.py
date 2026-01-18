import asyncio
import httpx
import requests
from meta_ai_api.extras import fake_agent

async def compare_requests_vs_httpx():
    """Compare what requests vs httpx returns"""
    
    headers = {
        "User-Agent": fake_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    print("="*60)
    print("TESTING WITH REQUESTS (sync)")
    print("="*60)
    
    # Test with requests
    response_requests = requests.get("https://www.meta.ai/", headers=headers)
    print(f"Status: {response_requests.status_code}")
    print(f"Encoding: {response_requests.encoding}")
    print(f"Content-Type: {response_requests.headers.get('content-type')}")
    print(f"Content-Encoding: {response_requests.headers.get('content-encoding')}")
    print(f"Length: {len(response_requests.text)} chars")
    
    # Check for tokens
    tokens_in_requests = {
        "_js_datr": "_js_datr" in response_requests.text,
        "abra_csrf": "abra_csrf" in response_requests.text,
        "LSD": "LSD" in response_requests.text,
        "DTSGInitData": "DTSGInitData" in response_requests.text,
    }
    
    print("\nTokens found in requests:")
    for token, found in tokens_in_requests.items():
        status = "✅" if found else "❌"
        print(f"  {status} {token}")
    
    # Save requests output
    with open("requests_output.html", "w", encoding="utf-8") as f:
        f.write(response_requests.text)
    print("\n💾 Saved to: requests_output.html")
    
    print("\n" + "="*60)
    print("TESTING WITH HTTPX (async)")
    print("="*60)
    
    # Test with httpx
    async with httpx.AsyncClient() as client:
        response_httpx = await client.get("https://www.meta.ai/", headers=headers)
        print(f"Status: {response_httpx.status_code}")
        print(f"Encoding: {response_httpx.encoding}")
        print(f"Content-Type: {response_httpx.headers.get('content-type')}")
        print(f"Content-Encoding: {response_httpx.headers.get('content-encoding')}")
        print(f"Length: {len(response_httpx.text)} chars")
        
        # Check for tokens
        tokens_in_httpx = {
            "_js_datr": "_js_datr" in response_httpx.text,
            "abra_csrf": "abra_csrf" in response_httpx.text,
            "LSD": "LSD" in response_httpx.text,
            "DTSGInitData": "DTSGInitData" in response_httpx.text,
        }
        
        print("\nTokens found in httpx:")
        for token, found in tokens_in_httpx.items():
            status = "✅" if found else "❌"
            print(f"  {status} {token}")
        
        # Save httpx output
        with open("httpx_output.html", "w", encoding="utf-8") as f:
            f.write(response_httpx.text)
        print("\n💾 Saved to: httpx_output.html")
    
    print("\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    
    print(f"Length difference: {len(response_requests.text) - len(response_httpx.text)} chars")
    
    # Compare first 1000 chars
    if response_requests.text[:1000] == response_httpx.text[:1000]:
        print("✅ First 1000 chars are identical")
    else:
        print("❌ First 1000 chars differ!")
        print("\nFirst difference at:")
        for i, (c1, c2) in enumerate(zip(response_requests.text, response_httpx.text)):
            if c1 != c2:
                print(f"  Position {i}")
                print(f"  Requests: {response_requests.text[max(0,i-50):i+50]}")
                print(f"  HTTPX:    {response_httpx.text[max(0,i-50):i+50]}")
                break
    
    # Check if both have same tokens
    print("\nToken comparison:")
    for token in tokens_in_requests.keys():
        req = "✅" if tokens_in_requests[token] else "❌"
        httpx_status = "✅" if tokens_in_httpx[token] else "❌"
        match = "✅ MATCH" if tokens_in_requests[token] == tokens_in_httpx[token] else "❌ DIFFERENT"
        print(f"  {token}: requests={req}, httpx={httpx_status} {match}")

if __name__ == "__main__":
    asyncio.run(compare_requests_vs_httpx())