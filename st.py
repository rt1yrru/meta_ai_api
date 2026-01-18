# starter script 
import asyncio
from meta_ai_api import MetaAI

async def main():
    # 1. Using 'async with' handles the setup and teardown of the connection
    async with MetaAI() as ai:
        
        # --- STREAMING ---
        print("--- Streaming Response ---")
        # prompt() is now always an async generator, so always use async for
        async for r in ai.prompt(message="what is value of pi?", stream=True):
            print(r["message"], end="", flush=True) 
        print("\n")
        
        # --- NORMAL QUERY ---
        print("--- Normal Query ---")
        query = "what is the value of pi?"
        # For non-streaming, we still use async for but it yields once
        async for response in ai.prompt(message=query, stream=False):
            print(response["message"])
        
        # --- FOLLOW-UP CONVERSATION ---
        print("\n--- Following Conversation ---")
        async for response in ai.prompt("what is 2 + 2?", stream=False):
            print(response["message"])
        
        async for response in ai.prompt("what was my previous question?", stream=False):
            print(response["message"])
    
    # --- NEW CONVERSATION ---
    print("\n--- New Conversation ---")
    async with MetaAI() as ai2:
        async for response in ai2.prompt("what is 2 + 2?", stream=False):
            print(response["message"])
        
        # Using the new_conversation=True flag
        async for response in ai2.prompt("what was my previous question?", new_conversation=True, stream=False):
            print(response["message"])

if __name__ == "__main__":
    # This is the "engine" that runs your async code
    asyncio.run(main())