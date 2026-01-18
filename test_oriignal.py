"""
Test if we can replicate the original requests behavior with httpx
"""
import asyncio
import httpx
from bs4 import BeautifulSoup

def extract_value(text: str, start_str: str, end_str: str) -> str:
    """Extract value between start and end strings"""
    start = text.find(start_str)
    if start == -1:
        return ""
    start = start + len(start_str)
    end = text.find(end_str, start)
    if end == -1:
        return ""
    return text[start:end]

async def test_with_httpx():
    """Replicate the original requests_html approach with httpx"""
    
    print("Testing HTTPX with original pattern...\n")
    
    # Don't set any custom headers - let httpx use defaults
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.meta.ai/")
        
        print(f"Status: {response.status_code}")
        print(f"Headers sent by httpx:")
        print(f"  User-Agent: {client.headers.get('user-agent')}")
        print()
        
        if response.status_code != 200:
            print(f"❌ Got {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            return
        
        html_text = response.text
        print(f"Response length: {len(html_text)} chars\n")
        
        # Try to extract cookies using original patterns
        cookies = {}
        
        # Pattern 1: _js_datr
        val = extract_value(html_text, '_js_datr":{"value":"', '",')
        if val:
            cookies["_js_datr"] = val
            print(f"✅ Found _js_datr: {val[:30]}...")
        else:
            print(f"❌ Missing _js_datr")
        
        # Pattern 2: abra_csrf
        val = extract_value(html_text, 'abra_csrf":{"value":"', '",')
        if val:
            cookies["abra_csrf"] = val
            print(f"✅ Found abra_csrf: {val[:30]}...")
        else:
            print(f"❌ Missing abra_csrf")
        
        # Pattern 3: datr
        val = extract_value(html_text, 'datr":{"value":"', '",')
        if val:
            cookies["datr"] = val
            print(f"✅ Found datr: {val[:30]}...")
        else:
            print(f"❌ Missing datr")
        
        # Pattern 4: LSD
        val = extract_value(html_text, '"LSD",[],{"token":"', '"}')
        if val:
            cookies["lsd"] = val
            print(f"✅ Found LSD: {val[:30]}...")
        else:
            print(f"❌ Missing LSD")
        
        print(f"\n📊 Found {len(cookies)}/4 cookies")
        
        # Save for inspection
        with open("httpx_test_output.html", "w", encoding="utf-8") as f:
            f.write(html_text)
        print(f"💾 Saved to: httpx_test_output.html")
        
        return cookies

async def test_with_requests_html_pattern():
    """Test using the exact same pattern as requests_html"""
    
    print("\n" + "="*60)
    print("Testing with requests_html pattern (using httpx)")
    print("="*60 + "\n")
    
    # Mimic requests_html behavior - minimal headers
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get("https://www.meta.ai/")
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Check page structure
            scripts = soup.find_all("script")
            print(f"Found {len(scripts)} script tags")
            
            # Look for inline data
            for i, script in enumerate(scripts[:10]):
                script_text = script.string or ""
                if "_js_datr" in script_text or "abra_csrf" in script_text:
                    print(f"\n✅ Script {i} contains cookies:")
                    print(script_text[:500])
                    break

if __name__ == "__main__":
    asyncio.run(test_with_httpx())
    asyncio.run(test_with_requests_html_pattern())
