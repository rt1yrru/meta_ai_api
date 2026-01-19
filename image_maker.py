# image generator 
import asyncio
from meta_ai_api import MetaAI

async def main():
    """
    Three ways to use MetaAI:
    1. Anonymous login (temporary token)
    2. NULL login (empty strings with hardcoded session) 
    3. Real Facebook login
    """
    
    # Method 1: Anonymous login (recommended for testing)
    print("Method 1: Anonymous Login")
    print("=" * 60)
    async with MetaAI() as ai:
        query = "can you draw me an image of a cat"
        print(f"Requesting: {query}\n")
        
        async for response in ai.prompt(message=query, stream=False):
            print(f"AI: {response['message']}\n")
            
            if response.get("media"):
                print("--- Generated Images ---")
                for idx, item in enumerate(response["media"], 1):
                    print(f"Image {idx}: {item['url']}")
                print(f"\nTotal: {len(response['media'])} images")
            else:
                print("ℹ️  No images generated")
    
    print("\n")

async def main_null_login():
    """
    Method 2: NULL login - Uses empty strings to trigger hardcoded session
    This replicates the original PG behavior
    """
    print("Method 2: NULL Login (Empty Strings)")
    print("=" * 60)
    
    # Empty strings trigger the NULL login path with hardcoded session
    async with MetaAI(fb_email="", fb_password="") as ai:
        query = "can you draw me an image of a cat"
        print(f"Requesting: {query}\n")
        
        async for response in ai.prompt(message=query, stream=False):
            print(f"AI: {response['message']}\n")
            
            if response.get("media"):
                print("--- Generated Images ---")
                for idx, item in enumerate(response["media"], 1):
                    print(f"\nImage {idx}:")
                    print(f"  URL: {item['url']}")
                    print(f"  Type: {item['type']}")
                    print(f"  Prompt: {item['prompt']}")
                    print("-" * 60)
                
                print(f"\nTotal images generated: {len(response['media'])}")
                
                # Show full response structure
                print("\n--- Full Response ---")
                print(f"Message: {response.get('message')}")
                print(f"Sources: {response.get('sources', [])}")
                print(f"UUID: {response.get('uuid')}")
            else:
                print("ℹ️  No images were generated")

async def main_facebook():
    """
    Method 3: Real Facebook authentication
    """
    print("Method 3: Facebook Login")
    print("=" * 60)
    
    async with MetaAI(fb_email="your@email.com", fb_password="your_password") as ai:
        query = "can you draw me an image of a cat"
        
        async for response in ai.prompt(message=query, stream=False):
            print(f"AI: {response['message']}")
            if response.get("media"):
                for idx, item in enumerate(response["media"], 1):
                    print(f"Image {idx}: {item['url']}")

if __name__ == "__main__":
    # Choose your method:
    
    # Method 1: Anonymous (no credentials needed)
    # asyncio.run(main())
    
    # Method 2: NULL login (empty strings - replicates original behavior)
    asyncio.run(main_null_login())
    
    # Method 3: Real Facebook login (uncomment and add real credentials)
    # asyncio.run(main_facebook())