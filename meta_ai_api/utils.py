
import logging
import random
import time
from typing import Dict, Optional

import httpx
from bs4 import BeautifulSoup

from meta_ai_api.exceptions import FacebookInvalidCredentialsException

from meta_ai_api.extras import fake_agent
from meta_ai_api.extras import USER_AGENT, SEC_CH_UA, SEC_CH_UA_PLATFORM, SEC_CH_UA_MOBILE


def generate_offline_threading_id() -> str:
    """
    Generates an offline threading ID.

    Returns:
        str: The generated offline threading ID.
    """
    # Maximum value for a 64-bit integer in Python
    max_int = (1 << 64) - 1
    mask22_bits = (1 << 22) - 1

    # Function to get the current timestamp in milliseconds
    def get_current_timestamp():
        return int(time.time() * 1000)

    # Function to generate a random 64-bit integer
    def get_random_64bit_int():
        return random.getrandbits(64)

    # Combine timestamp and random value
    def combine_and_mask(timestamp, random_value):
        shifted_timestamp = timestamp << 22
        masked_random = random_value & mask22_bits
        return (shifted_timestamp | masked_random) & max_int

    timestamp = get_current_timestamp()
    random_value = get_random_64bit_int()
    threading_id = combine_and_mask(timestamp, random_value)

    return str(threading_id)


def extract_value(text: str, start_str: str, end_str: str) -> str:
    """
    Helper function to extract a specific value from the given text using a key.

    Args:
        text (str): The text from which to extract the value.
        start_str (str): The starting key.
        end_str (str): The ending key.

    Returns:
        str: The extracted value.
    """
    start = text.find(start_str) + len(start_str)
    end = text.find(end_str, start)
    return text[start:end]


def format_response(response: dict) -> str:
    """
    Formats the response from Meta AI to remove unnecessary characters.

    Args:
        response (dict): The dictionnary containing the response to format.

    Returns:
        str: The formatted response.
    """
    text = ""
    for content in (
        response.get("data", {})
        .get("node", {})
        .get("bot_response_message", {})
        .get("composed_text", {})
        .get("content", [])
    ):
        text += content["text"] + "\n"
    return text


# Function to perform the login
async def get_fb_session(email, password, proxy=None):
    login_url = "https://www.facebook.com/login/?next"
    headers = {
        "authority": "mbasic.facebook.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": SEC_CH_UA,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": SEC_CH_UA_PLATFORM,
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": fake_agent(),
    }
    
    client_kwargs = {"follow_redirects": True}
    if proxy:
        client_kwargs["proxy"] = proxy
    
    async with httpx.AsyncClient(**client_kwargs) as client:
        # Send the GET request
        response = await client.get(login_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        print(f" response {response}")

        # Parse necessary parameters from the login form
        lsd = soup.find("input", {"name": "lsd"})["value"]
        jazoest = soup.find("input", {"name": "jazoest"})["value"]

        # Define the URL and body for the POST request to submit the login form
        post_url = "https://www.facebook.com/login/?next"
        data = {
            "lsd": lsd,
            "jazoest": jazoest,
            "login_source": "comet_headerless_login",
            "email": email,
            "pass": password,
            "login": "1",
            "next": None,
        }

        headers = {
            "User-Agent": fake_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": None,
            "Referer": "https://www.facebook.com/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.facebook.com",
            "DNT": "1",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "cookie": f"datr={response.cookies.get('datr')};",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i",
        }

        # Send the POST request with a new client to preserve cookies
        client_kwargs = {"follow_redirects": True}
        if proxy:
            client_kwargs["proxy"] = proxy
            
        async with httpx.AsyncClient(**client_kwargs) as session:
            result = await session.post(post_url, headers=headers, data=data)
            
            jar = session.cookies
            
            if "sb" not in jar or "xs" not in jar:
                raise FacebookInvalidCredentialsException(
                    "Was not able to login to Facebook. Please check your credentials. "
                    "You may also have been rate limited. Try to connect to Facebook manually."
                )

            cookies = {
                **dict(result.cookies),
                "sb": jar["sb"],
                "xs": jar["xs"],
                "fr": jar["fr"],
                "c_user": jar["c_user"],
            }

            response_login = {
                "cookies": cookies,
                "headers": dict(result.headers),
                "response": response.text,
            }
            
            # Get meta AI cookies
            meta_ai_cookies = await get_cookies()

            url = "https://www.meta.ai/state/"

            payload = f'__a=1&lsd={meta_ai_cookies["lsd"]}'
            headers = {
                "authority": "www.meta.ai",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "content-type": "application/x-www-form-urlencoded",
                "cookie": f'ps_n=1; ps_l=1; dpr=2; _js_datr={meta_ai_cookies["_js_datr"]}; abra_csrf={meta_ai_cookies["abra_csrf"]}; datr={meta_ai_cookies["datr"]};; ps_l=1; ps_n=1',
                "origin": "https://www.meta.ai",
                "pragma": "no-cache",
                "referer": "https://www.meta.ai/",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": fake_agent(),
            }

            response = await session.post(url, headers=headers, content=payload)

            state = extract_value(response.text, start_str='"state":"', end_str='"')

            url = f"https://www.facebook.com/oidc/?app_id=1358015658191005&scope=openid%20linking&response_type=code&redirect_uri=https%3A%2F%2Fwww.meta.ai%2Fauth%2F&no_universal_links=1&deoia=1&state={state}"
            payload = {}
            headers = {
                "authority": "www.facebook.com",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
                "cookie": f"datr={response_login['cookies']['datr']}; sb={response_login['cookies']['sb']}; c_user={response_login['cookies']['c_user']}; xs={response_login['cookies']['xs']}; fr={response_login['cookies']['fr']}; abra_csrf={meta_ai_cookies['abra_csrf']};",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "cross-site",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": fake_agent(),
            }
            
            # Use a new session for this request
            client_kwargs = {"follow_redirects": False}
            if proxy:
                client_kwargs["proxy"] = proxy
                
            async with httpx.AsyncClient(**client_kwargs) as fb_session:
                response = await fb_session.get(url, headers=headers)

                next_url = response.headers.get("Location")

                url = next_url

                payload = {}
                headers = {
                    "User-Agent": fake_agent(),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://www.meta.ai/",
                    "Connection": "keep-alive",
                    "Cookie": f'dpr=2; abra_csrf={meta_ai_cookies["abra_csrf"]}; datr={meta_ai_cookies["_js_datr"]}',
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "cross-site",
                    "Sec-Fetch-User": "?1",
                    "TE": "trailers",
                }
                
                await fb_session.get(url, headers=headers)
                cookies = dict(fb_session.cookies)
                
                if "abra_sess" not in cookies:
                    raise FacebookInvalidCredentialsException(
                        "Was not able to login to Facebook. Please check your credentials. "
                        "You may also have been rate limited. Try to connect to Facebook manually."
                    )
                    
                logging.info("Successfully logged in to Facebook.")
                return cookies


async def get_cookies() -> dict:
    """
    Extracts necessary cookies from the Meta AI main page.

    Returns:
        dict: A dictionary containing essential cookies.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.meta.ai/")
        response_text = response.text
        
        return {
            "_js_datr": extract_value(
                response_text, start_str='_js_datr":{"value":"', end_str='",'
            ),
            "abra_csrf": extract_value(
                response_text, start_str='abra_csrf":{"value":"', end_str='",'
            ),
            "datr": extract_value(
                response_text, start_str='datr":{"value":"', end_str='",'
            ),
            "lsd": extract_value(
                response_text, start_str='"LSD",[],{"token":"', end_str='"}'
            ),
        }


async def get_session(
    proxy: Optional[Dict] = None, test_url: str = "https://api.ipify.org/?format=json"
) -> httpx.AsyncClient:
    """
    Get an async session with the proxy set.

    Args:
        proxy (Dict): The proxy to use (single proxy string, e.g., "http://proxy.com:8080")
        test_url (str): A test site from which we check that the proxy is installed correctly.

    Returns:
        httpx.AsyncClient: An async client with the proxy set.
    """
    if not proxy:
        return httpx.AsyncClient()
    
    client_kwargs = {"timeout": 10.0}
    if proxy:
        client_kwargs["proxy"] = proxy
    
    async with httpx.AsyncClient(**client_kwargs) as test_client:
        response = await test_client.get(test_url)
        if response.status_code == 200:
            # Return a new client with the proxy configured
            client_kwargs = {}
            if proxy:
                client_kwargs["proxy"] = proxy
            return httpx.AsyncClient(**client_kwargs)
        else:
            raise Exception("Proxy is not working.")