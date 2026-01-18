# extras.py

# --- Traditional User-Agent ---
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'

# --- Low-Entropy User-Agent Client Hints (Sent by default) ---
SEC_CH_UA = '"Not A;Brand";v="99", "Chromium";v="144", "Google Chrome";v="144"'
SEC_CH_UA_PLATFORM = '"Linux"'
SEC_CH_UA_MOBILE = '?0' # ?0 means desktop (not mobile)

# --- High-Entropy User-Agent Client Hints (Only sent upon server request) ---
# To mimic a full browser, you include these in your request headers.
SEC_CH_UA_ARCH = '"x86"'  # The architecture from the UA string
SEC_CH_UA_PLATFORM_VERSION = '"6.1.0"' # Example Linux kernel version (varies, but 6.1 is common)
SEC_CH_UA_FULL_VERSION_LIST = '"Not A;Brand";v="99.0.0.0", "Chromium";v="144.0.0.0", "Google Chrome";v="144.0.0.0"'
# Note: x86_64 in the UA usually maps to "x86" in Sec-CH-UA-Arch

def fake_agent():
    """Returns the primary User-Agent string."""
    return USER_AGENT

def get_mimic_headers():
    """Returns a dictionary of all necessary headers for full mimicry."""
    return {
        # Traditional Headers
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',

        # Low-Entropy Client Hints
        'Sec-CH-UA': SEC_CH_UA,
        'Sec-CH-UA-Platform': SEC_CH_UA_PLATFORM,
        'Sec-CH-UA-Mobile': SEC_CH_UA_MOBILE,

        # High-Entropy Client Hints (Faking the server request)
        'Sec-CH-UA-Arch': SEC_CH_UA_ARCH,
        'Sec-CH-UA-Platform-Version': SEC_CH_UA_PLATFORM_VERSION,
        'Sec-CH-UA-Full-Version-List': SEC_CH_UA_FULL_VERSION_LIST,
        # Other useful security headers
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }