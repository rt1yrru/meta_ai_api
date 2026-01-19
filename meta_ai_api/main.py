import ujson as json
import logging
import asyncio
import urllib
import uuid
from typing import Dict, List, Optional
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from meta_ai_api.utils import (
    generate_offline_threading_id,
    extract_value,
    format_response,
)

from meta_ai_api.utils import get_fb_session, get_session

from meta_ai_api.exceptions import FacebookRegionBlocked
from meta_ai_api.extras import fake_agent

from meta_ai_api.session_meta import fb_session_cookie
MAX_RETRIES = 3

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MetaAI:
    """
    A class to interact with the Meta AI API to obtain and use access tokens for sending
    and receiving messages from the Meta AI Chat API.
    """

    def __init__(
        self, fb_email: str = None, fb_password: str = None, proxy: dict = None
    ):
        self.session = None  # Will be created in async context
        self.access_token = None
        self.fb_email = fb_email
        self.fb_password = fb_password
        self.proxy = proxy

        # Special handling for NULL login (empty strings)
        # NULL login should NOT be treated as authenticated
        if fb_email == "" and fb_password == "":
            self.is_authed = False  # Use anonymous mode with session cookie
            self.use_session_cookie = True
        else:
            self.is_authed = fb_password is not None and fb_email is not None
            self.use_session_cookie = False
            
        self.cookies = None  # Will be fetched async
        self.external_conversation_id = None
        self.offline_threading_id = None
        
        # Setup dump file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dump_file = f"meta_ai_dump_{timestamp}.txt"
        self.json_dump_file = f"meta_ai_dump_{timestamp}.json"
        
        # Initialize dump storage
        self.all_raw_responses = []
        self.all_extracted_data = []
        
        self._dump_log("=== Meta AI Session Started ===\n")
        self._dump_log(f"Timestamp: {datetime.now().isoformat()}\n")
        self._dump_log(f"Is Authenticated: {self.is_authed}\n\n")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize the async session and fetch cookies"""
        client_kwargs = {
            "timeout": 30.0,
            "follow_redirects": True,
        }
        if self.proxy:
            client_kwargs["proxy"] = self.proxy
        
        self.session = httpx.AsyncClient(**client_kwargs)
        # Don't override default headers - httpx defaults work fine!
        self.cookies = await self.get_cookies()

    async def close(self):
        """Close the async session"""
        if self.session:
            await self.session.aclose()

    def _dump_log(self, content: str, level: str = "INFO"):
        """Log to both file and console."""
        timestamp = datetime.now().isoformat()
        formatted = f"[{timestamp}] [{level}] {content}"
        
        print(formatted)
        
        with open(self.dump_file, 'a', encoding='utf-8') as f:
            f.write(formatted + "\n")

    def _dump_raw_response(self, raw_data, endpoint: str = ""):
        """Dump raw response data."""
        timestamp = datetime.now().isoformat()
        
        separator = "\n" + "="*80 + "\n"
        dump_content = f"{separator}[{timestamp}] RAW RESPONSE{f' - {endpoint}' if endpoint else ''}\n{separator}\n"
        
        if isinstance(raw_data, dict):
            dump_content += json.dumps(raw_data, indent=2, ensure_ascii=False)
        else:
            dump_content += str(raw_data)
        
        dump_content += "\n"
        
        with open(self.dump_file, 'a', encoding='utf-8') as f:
            f.write(dump_content)
        
        # Also store for JSON dump
        self.all_raw_responses.append({
            "timestamp": timestamp,
            "endpoint": endpoint,
            "data": raw_data
        })

    def _dump_extracted_data(self, data: dict):
        """Dump extracted and processed data."""
        timestamp = datetime.now().isoformat()
        
        dump_content = f"\n{'='*80}\n[{timestamp}] EXTRACTED DATA\n{'='*80}\n"
        dump_content += json.dumps(data, indent=2, ensure_ascii=False)
        dump_content += "\n"
        
        with open(self.dump_file, 'a', encoding='utf-8') as f:
            f.write(dump_content)
        
        # Store for JSON dump
        self.all_extracted_data.append({
            "timestamp": timestamp,
            "data": data
        })

    async def get_access_token(self) -> str:
        """
        Retrieves an access token using Meta's authentication API.

        Returns:
            str: A valid access token.
        """

        if self.access_token:
            return self.access_token

        url = "https://www.meta.ai/api/graphql/"
        payload = {
            "lsd": self.cookies["lsd"],
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraAcceptTOSForTempUserMutation",
            "variables": {
                "dob": "1999-01-01",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            },
            "doc_id": "7604648749596940",
        }
        payload = urllib.parse.urlencode(payload)
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f'_js_datr={self.cookies["_js_datr"]}; '
             f'abra_csrf={self.cookies.get("abra_csrf", "")}; '
             f'datr={self.cookies["datr"]}; '
             f'abra_sess={self.cookies.get("abra_sess", "")};', 
            "sec-fetch-site": "same-origin",
            "x-fb-friendly-name": "useAbraAcceptTOSForTempUserMutation",
            }
        self._dump_log(f"Requesting access token from {url}")

        response = await self.session.post(url, headers=headers, content=payload)

        # Dump raw response
        response_text = response.text
        self._dump_raw_response(response_text, endpoint="get_access_token (POST)")
        self._dump_log(f"Response Status: {response.status_code}")

        try:
            auth_json = response.json()
            self._dump_raw_response(auth_json, endpoint="get_access_token (PARSED JSON)")
        except json.JSONDecodeError:
            self._dump_log("ERROR: Unable to decode JSON response", level="ERROR")
            raise FacebookRegionBlocked(
                "Unable to receive a valid response from Meta AI. This is likely due to your region being blocked. "
                "Try manually accessing https://www.meta.ai/ to confirm."
            )

        access_token = auth_json["data"]["xab_abra_accept_terms_of_service"][
            "new_temp_user_auth"
        ]["access_token"]

        self._dump_log(f"Access token obtained: {access_token[:20]}...")

        await asyncio.sleep(1)

        return access_token

    async def prompt(self, message: str, stream: bool = False, attempts: int = 0, new_conversation: bool = False):
        """
        Sends a message to the Meta AI and returns/yields the response.
        Always returns an async generator for consistency.
        """
        self._dump_log(f"\n{'#'*80}")
        self._dump_log(f"NEW PROMPT REQUEST - Attempt {attempts + 1}")
        self._dump_log(f"Message: {message}")
        self._dump_log(f"Stream: {stream}")
        self._dump_log(f"New Conversation: {new_conversation}")
        self._dump_log(f"{'#'*80}\n")

        if not self.is_authed:
            self.access_token = await self.get_access_token()
            auth_payload = {"access_token": self.access_token}
            url = "https://graph.meta.ai/graphql?locale=user"
        else:
            auth_payload = {"fb_dtsg": self.cookies["fb_dtsg"]}
            url = "https://www.meta.ai/api/graphql/"

        if not self.external_conversation_id or new_conversation:
            external_id = str(uuid.uuid4())
            self._dump_log(f"Generated Conversation ID: {external_id}")
            self.external_conversation_id = external_id
            
        payload = {
            **auth_payload,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "useAbraSendMessageMutation",
            "variables": json.dumps({
                "message": {"sensitive_string_value": message},
                "externalConversationId": self.external_conversation_id,
                "offlineThreadingId": generate_offline_threading_id(),
                "suggestedPromptIndex": None,
                "flashVideoRecapInput": {"images": []},
                "flashPreviewInput": None,
                "promptPrefix": None,
                "entrypoint": "ABRA__CHAT__TEXT",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            }),
            "server_timestamps": "true",
            "doc_id": "7783822248314888",
        }
        payload = urllib.parse.urlencode(payload)
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "x-fb-friendly-name": "useAbraSendMessageMutation",
        }
        
        if self.is_authed:
            headers["cookie"] = f'abra_sess={self.cookies["abra_sess"]}'
            await self.session.aclose()
            client_kwargs = {"timeout": 30.0}
            if self.proxy:
                client_kwargs["proxy"] = self.proxy
            self.session = httpx.AsyncClient(**client_kwargs)

        self._dump_log(f"Sending POST request to: {url}")

        if not stream:
            # Non-streaming: get full response
            response = await self.session.post(url, headers=headers, content=payload)
            self._dump_log(f"Response Status Code: {response.status_code}")
            
            raw_response = response.text
            self._dump_raw_response(raw_response, endpoint="prompt (non-stream)")
            
            last_streamed_response = self.extract_last_response(raw_response)
            if not last_streamed_response:
                self._dump_log("No valid response found, retrying...", level="WARNING")
                if attempts < MAX_RETRIES:
                    await asyncio.sleep(3)
                    async for result in self.prompt(message, stream=stream, attempts=attempts + 1):
                        yield result
                else:
                    raise Exception("Unable to obtain a valid response from Meta AI. Try again later.")
            else:
                extracted_data = await self.extract_data(last_streamed_response)
                self._dump_extracted_data(extracted_data)
                yield extracted_data
        else:
            # Streaming: yield chunks as they arrive
            self._dump_log("Starting stream response processing...")
            async with self.session.stream('POST', url, headers=headers, content=payload) as response:
                self._dump_log(f"Response Status Code: {response.status_code}")
                
                lines_iter = response.aiter_lines()
                try:
                    first_line = await lines_iter.__anext__()
                    is_error = json.loads(first_line)
                    self._dump_raw_response(is_error, endpoint="prompt (stream - first line)")
                    
                    if len(is_error.get("errors", [])) > 0:
                        self._dump_log("Error detected in stream, retrying...", level="WARNING")
                        if attempts < MAX_RETRIES:
                            await asyncio.sleep(3)
                            async for result in self.prompt(message, stream=stream, attempts=attempts + 1):
                                yield result
                        else:
                            raise Exception("Unable to obtain a valid response from Meta AI. Try again later.")
                        return
                except StopAsyncIteration:
                    self._dump_log("Stream ended prematurely", level="ERROR")
                    if attempts < MAX_RETRIES:
                        await asyncio.sleep(3)
                        async for result in self.prompt(message, stream=stream, attempts=attempts + 1):
                            yield result
                    else:
                        raise Exception("Unable to obtain a valid response from Meta AI. Try again later.")
                    return
                
                # Stream the response
                async for chunk in self.stream_response(lines_iter):
                    yield chunk

    def extract_last_response(self, response: str) -> Optional[Dict]:
        """
        Extracts the last response from the Meta AI API.
        """
        self._dump_log("Extracting last response from stream...")
        last_streamed_response = None
        line_count = 0
        
        for line in response.split("\n"):
            try:
                json_line = json.loads(line)
                line_count += 1
            except json.JSONDecodeError:
                continue

            bot_response_message = (
                json_line.get("data", {})
                .get("node", {})
                .get("bot_response_message", {})
            )
            
            chat_id = bot_response_message.get("id")
            if chat_id:
                external_conversation_id, offline_threading_id, _ = chat_id.split("_")
                self.external_conversation_id = external_conversation_id
                self.offline_threading_id = offline_threading_id

            streaming_state = bot_response_message.get("streaming_state")
            if streaming_state == "OVERALL_DONE":
                last_streamed_response = json_line
                self._dump_log(f"Found OVERALL_DONE state at line {line_count}")
                self._dump_raw_response(json_line, endpoint="extract_last_response (FINAL)")

        self._dump_log(f"Processed {line_count} JSON lines from response")
        return last_streamed_response

    async def stream_response(self, lines):
        """
        Streams the response from the Meta AI API.
        """
        self._dump_log("Starting stream response iteration...")
        line_count = 0
        
        async for line in lines:
            if line:
                line_count += 1
                try:
                    json_line = json.loads(line)
                    self._dump_raw_response(json_line, endpoint=f"stream_response (line {line_count})")
                    
                    extracted_data = await self.extract_data(json_line)
                    if not extracted_data.get("message"):
                        continue
                    
                    self._dump_extracted_data(extracted_data)
                    yield extracted_data
                except json.JSONDecodeError as e:
                    self._dump_log(f"JSON decode error at line {line_count}: {e}", level="ERROR")
                    continue

        self._dump_log(f"Stream response complete. Processed {line_count} lines")

    async def extract_data(self, json_line: dict):
        """
        Extract data and sources from a parsed JSON line.
        """
        self._dump_log("Extracting data from JSON...")
        
        bot_response_message = (
            json_line.get("data", {}).get("node", {}).get("bot_response_message", {})
        )
        response = format_response(response=json_line)
        fetch_id = bot_response_message.get("fetch_id")
        sources = await self.fetch_sources(fetch_id) if fetch_id else []
        medias = self.extract_media(bot_response_message)
        
        result = {
            "message": response,
            "sources": sources,
            "media": medias,
            "uuid": self.external_conversation_id
        }
        
        self._dump_log(f"Extracted data: {len(response)} chars, {len(sources)} sources, {len(medias)} media items")
        
        return result

    @staticmethod
    def extract_media(json_line: dict) -> List[Dict]:
        """
        Extract media from a parsed JSON line.
        """
        medias = []
        imagine_card = json_line.get("imagine_card", {})
        session = imagine_card.get("session", {}) if imagine_card else {}
        media_sets = (
            (json_line.get("imagine_card", {}).get("session", {}).get("media_sets", []))
            if imagine_card and session
            else []
        )
        for media_set in media_sets:
            imagine_media = media_set.get("imagine_media", [])
            for media in imagine_media:
                medias.append({
                    "url": media.get("uri"),
                    "type": media.get("media_type"),
                    "prompt": media.get("prompt"),
                })
        return medias

    async def get_cookies(self) -> dict:
        """
        Extracts necessary cookies from the Meta AI main page.
        """
        headers = {}
        
        # NULL login with hardcoded session
        if self.use_session_cookie:
            # Use hardcoded session cookie (update this with your real cookie!)
            session_cookie = fb_session_cookie
            headers = {"cookie": f"abra_sess={session_cookie}"}
            self._dump_log(f"Using NULL login with session cookie")
        # Real Facebook authentication
        elif self.is_authed:
            if self.fb_email == "" and self.fb_password == "":
                # This shouldn't happen now, but keep as fallback
                session_cookie = fb_session
                headers = {"cookie": f"abra_sess={session_cookie}"}
                self._dump_log("Using NULL login (fallback)")
            else:
                # Real Facebook authentication
                fb_session = await get_fb_session(self.fb_email, self.fb_password, self.proxy)
                headers = {"cookie": f"abra_sess={fb_session['abra_sess']}"}
                self._dump_log("Using Facebook authentication")
        
        response = await self.session.get("https://www.meta.ai/", headers=headers)
        
        response_text = response.text
        
        self._dump_log(f"Response encoding: {response.encoding}")
        self._dump_log(f"Response length: {len(response_text)} chars")
        
        cookies = {
            "_js_datr": extract_value(
                response_text, start_str='_js_datr":{"value":"', end_str='",'
            ),
            "datr": extract_value(
                response_text, start_str='datr":{"value":"', end_str='",'
            ),
            "lsd": extract_value(
                response_text, start_str='"LSD",[],{"token":"', end_str='"}'
            ),
            "fb_dtsg": extract_value(
                response_text, start_str='DTSGInitData",[],{"token":"', end_str='"'
            ),
        }

        if len(headers) > 0 and self.is_authed:
            # For authenticated users, we need the session
            if self.use_session_cookie:
                cookies["abra_sess"] = session_cookie
            else:
                cookies["abra_sess"] = fb_session["abra_sess"]
        else:
            cookies["abra_csrf"] = extract_value(
                response_text, start_str='abra_csrf":{"value":"', end_str='",'
            )
        return cookies

    async def fetch_sources(self, fetch_id: str) -> List[Dict]:
        """
        Fetches sources from the Meta AI API based on the given query.
        """
        url = "https://graph.meta.ai/graphql?locale=user"
        payload = {
            "access_token": self.access_token,
            "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "AbraSearchPluginDialogQuery",
            "variables": json.dumps({"abraMessageFetchID": fetch_id}),
            "server_timestamps": "true",
            "doc_id": "6946734308765963",
        }

        payload = urllib.parse.urlencode(payload)

        headers = {
            "authority": "graph.meta.ai",
            "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f'dpr=2; abra_csrf={self.cookies.get("abra_csrf")}; datr={self.cookies.get("datr")}; ps_n=1; ps_l=1',
            "x-fb-friendly-name": "AbraSearchPluginDialogQuery",
        }

        self._dump_log(f"Fetching sources with fetch_id: {fetch_id}")

        response = await self.session.post(url, headers=headers, content=payload)
        response_text = response.text
        self._dump_raw_response(response_text, endpoint="fetch_sources")

        response_json = response.json()
        self._dump_raw_response(response_json, endpoint="fetch_sources (PARSED)")
        
        message = response_json.get("data", {}).get("message", {})
        search_results = (
            (response_json.get("data", {}).get("message", {}).get("searchResults"))
            if message
            else None
        )
        if search_results is None:
            self._dump_log("No search results found")
            return []

        references = search_results["references"]
        self._dump_log(f"Found {len(references)} references")
        return references

    def save_json_dump(self):
        """Save all data to JSON file."""
        dump_data = {
            "metadata": {
                "timestamp_start": self.all_raw_responses[0]["timestamp"] if self.all_raw_responses else None,
                "timestamp_end": datetime.now().isoformat(),
                "total_raw_responses": len(self.all_raw_responses),
                "total_extracted_data": len(self.all_extracted_data),
            },
            "raw_responses": self.all_raw_responses,
            "extracted_data": self.all_extracted_data,
        }
        
        with open(self.json_dump_file, 'w', encoding='utf-8') as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False)
        
        self._dump_log(f"\nJSON dump saved to: {self.json_dump_file}")
    
    def print_dump_locations(self):
        """Print where dumps are saved."""
        print(f"\n{'='*80}")
        print(f"DUMP FILES CREATED:")
        print(f"{'='*80}")
        print(f"Text Dump:  {self.dump_file}")
        print(f"JSON Dump:  {self.json_dump_file}")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    async def main():
        async with MetaAI() as meta:
            try:
                async for resp in meta.prompt("Hello!", stream=False):
                    print("\n" + "="*80)
                    print("RESPONSE:")
                    print("="*80)
                    print(resp)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                meta.save_json_dump()
                meta.print_dump_locations()
    
    asyncio.run(main())