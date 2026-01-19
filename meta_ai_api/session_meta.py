import os
from dotenv import load_dotenv

def get_fb_session(env_path=".env"):
    """
    Loads the environment variables and retrieves the FB session cookie.
    """
    load_dotenv(dotenv_path=env_path)
    session = os.getenv("FB_SESSION")
    
    if not session:
        # We use a default empty string or None so the import doesn't crash
        return None
        
    return session

# THIS IS THE MISSING PART:
# Call the function to create the variable that main.py is looking for
fb_session_cookie = get_fb_session()