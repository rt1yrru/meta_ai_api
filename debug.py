import asyncio
import httpx
from meta_ai_api.extras import fake_agent

async def test_meta_ai_connection():
    """Test if we can access Meta AI website"""
    
    print("Testing connection to Meta AI...")
    print(f"User-Agent: {fake_agent()}\n")
    
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
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            response = await client.get("https://www.meta.ai/", headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}\n")
            
            if response.status_code == 200:
                print("✅ Successfully connected to Meta AI!")
                print(f"Response length: {len(response.text)} characters\n")
                
                # Try to extract cookies
                cookies_found = []
                if '_js_datr' in response.text:
                    print("✅ Found _js_datr cookie in response")
                    cookies_found.append('_js_datr')
                else:
                    print("❌ Missing _js_datr cookie")
                    
                if 'abra_csrf' in response.text:
                    print("✅ Found abra_csrf cookie in response")
                    cookies_found.append('abra_csrf')
                else:
                    print("❌ Missing abra_csrf cookie")
                    
                if 'LSD' in response.text:
                    print("✅ Found LSD token in response")
                    cookies_found.append('LSD')
                else:
                    print("❌ Missing LSD token")
                
                if 'DTSGInitData' in response.text:
                    print("✅ Found DTSGInitData token in response")
                    cookies_found.append('DTSGInitData')
                else:
                    print("❌ Missing DTSGInitData token")
                
                print(f"\n📊 Found {len(cookies_found)}/4 required tokens")
                
                if len(cookies_found) == 4:
                    print("\n🎉 All required tokens found! You're ready to use the API!")
                else:
                    print("\n⚠️ Some tokens missing. The API might not work properly.")
                    
            elif response.status_code == 400:
                print("❌ 400 Bad Request - Meta AI rejected the request")
                print("This could be due to:")
                print("  1. Blocked region/IP")
                print("  2. Missing or incorrect headers")
                print("  3. Rate limiting")
                print("\nTry accessing https://www.meta.ai/ in your browser to verify it's accessible")
                
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error connecting: {e}")

if __name__ == "__main__":
    asyncio.run(test_meta_ai_connection())