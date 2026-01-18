import asyncio
import httpx
import re
from meta_ai_api.extras import fake_agent

async def advanced_meta_ai_test():
    """Advanced test to find where tokens are hiding"""
    
    print("🔍 Advanced Meta AI Token Search\n")
    
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
        response = await client.get("https://www.meta.ai/", headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Length: {len(response.text)} chars\n")
        
        html = response.text
        
        # Search for different token patterns
        patterns = {
            "_js_datr": [
                r'_js_datr["\']:\s*["\']([^"\']+)',
                r'"_js_datr":\s*{\s*"value":\s*"([^"]+)"',
                r'_js_datr":\{"value":"([^"]+)"',
            ],
            "abra_csrf": [
                r'abra_csrf["\']:\s*["\']([^"\']+)',
                r'"abra_csrf":\s*{\s*"value":\s*"([^"]+)"',
                r'abra_csrf":\{"value":"([^"]+)"',
            ],
            "lsd": [
                r'"LSD",\[\],\{"token":"([^"]+)"',
                r'"LSD":\s*"([^"]+)"',
                r'lsd["\']:\s*["\']([^"\']+)',
            ],
            "fb_dtsg": [
                r'"DTSGInitData",\[\],\{"token":"([^"]+)"',
                r'DTSGInitialData":\[\],\{"token":"([^"]+)"',
                r'"DTSGInitData":\s*"([^"]+)"',
            ],
        }
        
        found_tokens = {}
        
        for token_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, html)
                if match:
                    token_value = match.group(1)
                    found_tokens[token_name] = token_value
                    print(f"✅ Found {token_name}: {token_value[:30]}...")
                    break
            
            if token_name not in found_tokens:
                print(f"❌ Missing {token_name}")
        
        print(f"\n📊 Found {len(found_tokens)}/4 tokens")
        
        # Also check for script tags that might load tokens
        print("\n🔎 Checking for JavaScript initialization...")
        
        script_patterns = [
            r'<script[^>]*>(.*?)</script>',
        ]
        
        for pattern in script_patterns:
            scripts = re.findall(pattern, html, re.DOTALL)
            print(f"Found {len(scripts)} script tags")
            
            # Check if any contain our tokens
            for i, script in enumerate(scripts[:5]):  # Check first 5 scripts
                if any(keyword in script for keyword in ['_js_datr', 'abra_csrf', 'LSD', 'DTSG']):
                    print(f"\n📜 Script {i+1} contains token keywords:")
                    print(script[:500] + "..." if len(script) > 500 else script)
                    break
        
        # Save full HTML for manual inspection
        with open("meta_ai_response.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n💾 Full HTML saved to: meta_ai_response.html")
        
        # Try alternative: Look for any JSON-like structures
        print("\n🔍 Looking for embedded JSON data...")
        json_patterns = re.findall(r'\{[^{}]*"token"[^{}]*\}', html)
        if json_patterns:
            print(f"Found {len(json_patterns)} potential token objects:")
            for i, match in enumerate(json_patterns[:3]):
                print(f"  {i+1}. {match[:100]}...")
        
        return found_tokens

if __name__ == "__main__":
    tokens = asyncio.run(advanced_meta_ai_test())
    
    print("\n" + "="*60)
    if len(tokens) >= 3:  # We can work with at least 3 tokens
        print("✅ Should be able to proceed with API calls")
    else:
        print("⚠️ May need alternative authentication method")
    print("="*60)
