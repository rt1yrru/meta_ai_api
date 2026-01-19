# UG Image Generator - Async Version with httpx
import asyncio
from meta_ai_api import MetaAI

async def generate_images_anonymous():
    """Generate images using anonymous login (recommended)"""
    print("="*60)
    print("Method 1: Anonymous Login (No Session Required)")
    print("="*60)
    
    async with MetaAI() as ai:
        query = "a beautiful woman"
        print(f"Generating: {query}\n")
        
        # Generate images - use stream=False for complete response
        async for response in ai.prompt(message=query, stream=False):
            # Check if images were generated
            if response.get("media"):
                print(f"✅ Generated {len(response['media'])} images!\n")
                
                # Display each image
                for idx, img in enumerate(response["media"], 1):
                    print(f"Image {idx}:")
                    print(f"  URL: {img['url']}")
                    print(f"  Type: {img['type']}")
                    print(f"  Prompt: {img['prompt']}")
                    print("-" * 60)
                
                # Show metadata
                print(f"\nConversation ID: {response['uuid']}")
                print(f"Message: {response['message'].strip()}")
            else:
                print("❌ No images were generated")
                print(f"Message: {response['message']}")

async def generate_images_null_login():
    """
    Generate images using NULL login (requires valid session cookie)
    
    NOTE: You must update the session cookie in main.py first!
    Line to update: session_cookie = 'YOUR_ABRA_SESS_COOKIE_HERE'
    """
    print("\n" + "="*60)
    print("Method 2: NULL Login (Requires Session Cookie)")
    print("="*60)
    
    # Empty strings trigger NULL login mode
    async with MetaAI(fb_email="", fb_password="") as ai:
        query = "a cat wearing a hat"
        print(f"Generating: {query}\n")
        
        async for response in ai.prompt(message=query, stream=False):
            if response.get("media"):
                print(f"✅ Generated {len(response['media'])} images!\n")
                
                for idx, img in enumerate(response["media"], 1):
                    print(f"Image {idx}: {img['url'][:80]}...")
            else:
                print("❌ No images generated")
                print(f"Response: {response}")

async def download_images():
    """Generate and download images to disk"""
    import httpx
    
    print("\n" + "="*60)
    print("Method 3: Generate and Download Images")
    print("="*60)
    
    async with MetaAI() as ai:
        query = "a futuristic cityscape"
        print(f"Generating: {query}\n")
        
        async for response in ai.prompt(message=query, stream=False):
            if response.get("media"):
                print(f"Downloading {len(response['media'])} images...\n")
                
                # Download each image
                async with httpx.AsyncClient() as client:
                    for idx, img in enumerate(response["media"], 1):
                        img_url = img['url']
                        filename = f"generated_image_{idx}.jpg"
                        
                        # Download image
                        img_response = await client.get(img_url)
                        
                        # Save to file
                        with open(filename, "wb") as f:
                            f.write(img_response.content)
                        
                        print(f"✅ Saved: {filename}")
                
                print(f"\n✨ Downloaded {len(response['media'])} images successfully!")
            else:
                print("❌ No images to download")

async def multiple_image_requests():
    """Generate multiple sets of images in sequence"""
    print("\n" + "="*60)
    print("Method 4: Multiple Image Generations")
    print("="*60)
    
    prompts = [
        "a dragon in the sky",
        "a peaceful forest",
        "a robot playing guitar"
    ]
    
    async with MetaAI() as ai:
        for prompt in prompts:
            print(f"\nGenerating: {prompt}")
            
            async for response in ai.prompt(message=prompt, stream=False):
                if response.get("media"):
                    print(f"  ✅ Generated {len(response['media'])} images")
                else:
                    print(f"  ❌ No images")

async def concurrent_image_generation():
    """Generate multiple image sets concurrently (advanced)"""
    print("\n" + "="*60)
    print("Method 5: Concurrent Image Generation (Async Power!)")
    print("="*60)
    
    async def generate_one(prompt):
        """Helper to generate images for one prompt"""
        async with MetaAI() as ai:
            async for response in ai.prompt(message=prompt, stream=False):
                return {
                    "prompt": prompt,
                    "count": len(response.get("media", [])),
                    "images": response.get("media", [])
                }
    
    # Multiple prompts to generate simultaneously
    prompts = [
        "a sunset over mountains",
        "a cyber punk city",
        "a magical unicorn"
    ]
    
    print(f"Generating {len(prompts)} image sets concurrently...\n")
    
    # Run all generations concurrently!
    results = await asyncio.gather(
        *[generate_one(p) for p in prompts]
    )
    
    # Show results
    for result in results:
        print(f"Prompt: {result['prompt']}")
        print(f"  Generated: {result['count']} images")
        if result['images']:
            print(f"  First URL: {result['images'][0]['url'][:80]}...")
        print()

async def main():
    """Run all examples"""
    
    # Method 1: Anonymous (recommended - always works!)
    await generate_images_null_login()
    
    # Method 2: NULL login (requires session cookie update)
    # await generate_images_null_login()
    
    # Method 3: Download images
    # await download_images()
    
    # Method 4: Multiple sequential requests
    # await multiple_image_requests()
    
    # Method 5: Concurrent generation (async superpower!)
    # await concurrent_image_generation()

if __name__ == "__main__":
    asyncio.run(main())
