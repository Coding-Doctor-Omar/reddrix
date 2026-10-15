from playwright.async_api import Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, Error
from curl_cffi.requests.exceptions import SessionClosed, HTTPError, JSONDecodeError
from .exceptions import AntiBotBlockError, FatalAntiBotBlockError
from orjson import JSONDecodeError as orjsonJSONDecodeError
from playwright._impl._errors import TargetClosedError
from camoufox.exceptions import UnknownIPLocation
from camoufox.async_api import AsyncCamoufox
from urllib.parse import urlencode, urlparse
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from .iwswuf import iwsuff, happy, sad
from whiskeysour import WhiskeySour
from curl_cffi import AsyncSession
from functools import wraps
from platform import system
from typing import Literal
import asyncio
import random
import time


USERNAME = happy
PASSWORD = sad
MAX_RETRIES = 5
PLATFORMS = {
    "windows": "windows",
    "linux": "linux",
    "darwin": "macos"
}
TIME_FRAMES = {
    "all_time": "all",
    "past_hour": "hour",
    "today": "day",
    "past_week": "week",
    "past_month": "month",
    "past_year": "year"
}
COOKIE_LOCK = asyncio.Lock()

def auto_retry(max_attempts: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            url = kwargs.get("url") or args[1] if func.__name__ == "fetch_page_data" else None
            scraper: Reddrix = args[0]

            for attempt in range(max_attempts + 1):
                current_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                except (AntiBotBlockError, SessionClosed, TargetClosedError):
                    if attempt == max_attempts:
                        if url:
                            raise FatalAntiBotBlockError(f"Error fetching URL: {url}\n\nError Message: Cookies expired, and attempts have been exhausted.")
                        else:
                            raise FatalAntiBotBlockError(f"Error executing function: {func.__name__}\n\nError Message: Cookies expired, and attempts have been exhausted.")

                    async with COOKIE_LOCK:
                        if current_time - scraper.cookies_last_accessed_at >= 15: # Must match the wait selector timeout.
                            await scraper.refresh_cookies()

                    await asyncio.sleep(min(2 ** attempt + random.uniform(0, 5), 60))
                else:
                    return result

        return wrapper

    return decorator

class Reddrix:
    def __init__(
        self,
        mode: Literal["standard", "keyword_search", "domain_search"]="standard",
        http_client: Literal["curl_cffi", "camoufox"]="curl_cffi",
        max_results: int=999999,
        max_posts_per_collection: int=999999,
        sort: Literal["default", "new", "hot"]="default",
        time_frame: Literal["all_time", "past_hour", "today", "past_week", "past_month", "past_year"]="all_time",
        subreddit_urls: list[str]=[],
        post_urls: list[str]=[],
        profile_urls: list[str]=[],
        domains: list[str]=[],
        query: str=None,
        include_comments: bool=False,
        max_comments_depth: int=10,
        max_comments_per_post: int=999999,
        max_top_comments_per_post: int=999999,
        proxies: list[str]=[],
        verbose: bool=False
    ):
        if http_client == "curl_cffi":
            self.log("CURL_CFFI CLIENT IS DEPRECATED. SWITCHING TO CAMOUFOX...", level="warning")
        
        self.mode = mode
        self.max_results = max_results
        self.max_posts_per_collection = max_posts_per_collection
        self.sort = sort
        self.time_frame = TIME_FRAMES[time_frame]
        self.subreddit_urls = subreddit_urls
        self.post_urls = post_urls
        self.profile_urls = profile_urls
        self.domains = domains
        self.query = query
        self.include_comments = include_comments
        self.max_comments_depth = max_comments_depth
        self.max_comments_per_post = max_comments_per_post
        self.max_top_comments_per_post = max_top_comments_per_post
        self.proxies = proxies
        self.is_verbose = verbose
        self.used_proxies = set()
        
        self.http_client = "camoufox"
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.session: AsyncSession | None = None
        self.started = False
        self.cookie_renewal_in_progress = False
        self.cookies_last_accessed_at = 0.0
        self.page_semaphore = asyncio.Semaphore(10)
        self.request_semaphore = asyncio.Semaphore(10)
        self.items_queue = asyncio.Queue(maxsize=1000)
    
    async def start(self):
        return await self.__aenter__()
    
    async def stop(self):
        await self.__aexit__(None, None, None)
    
    def new_proxy_url(self) -> str:
        if not self.proxies:
            return ""
        
        proxy_to_be_used = ""
        for proxy in self.proxies:
            if proxy not in self.used_proxies:
                self.used_proxies.add(proxy)
                proxy_to_be_used = proxy
                break
        
        if not proxy_to_be_used:
            self.used_proxies.clear()
            proxy_to_be_used = random.choice(self.proxies)
            self.used_proxies.add(proxy_to_be_used)
        
        return proxy_to_be_used
    
    async def __aenter__(self):
        initialization_successful = False
        self.log("INITIALIZING SCRAPER")
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if self.http_client == "camoufox":
                    proxy_url = self.new_proxy_url()
                    parsed_url = urlparse(proxy_url)
                    self.camoufox = AsyncCamoufox(
                        os=PLATFORMS[system().lower()],
                        headless=True,
                        humanize=True,
                        fingerprint_preset=True,
                        proxy={
                            "server": f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}",
                            "username": parsed_url.username,
                            "password": parsed_url.password
                        } if proxy_url else None,
                        geoip=True if proxy_url else False
                    )
                    self.browser: Browser = await self.camoufox.start()
                    self.context = await self.browser.new_context()
                    self.page = await self.context.new_page()
                    n1 = iwsuff("ywivreqi")
                    n2 = iwsuff("tewwasvh")
                    nn = iwsuff("reqi")
                    ls = iwsuff("pskmr")
                    
                    await self.page.goto("https://old.reddit.com/login")
                    await self.page.wait_for_selector(f".{ls}")
                    h = await self.page.wait_for_selector(f'[{nn}="{n1}"]')
                    s = await self.page.wait_for_selector(f'[{nn}="{n2}"]')
                    await h.click()
                    
                    for char in iwsuff(USERNAME):
                        await self.page.keyboard.press(char)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    await s.click()
                    
                    for char in iwsuff(PASSWORD):
                        await self.page.keyboard.press(char)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    bgns = await self.page.wait_for_selector(f".{ls}")
                    await bgns.click()
                    await self.page.wait_for_selector('[alt="User Avatar"]')
                else: # Deprecated
                    self.session = AsyncSession(proxy=self.new_proxy_url(), allow_redirects=True)
                    self.session.headers["User-Agent"] = f"Reddrix{random.randint(0, 999999)}/v0.1.7"
                    res = await self.session.get("https://old.reddit.com/login")
                    res.raise_for_status()
                
                self.started = True
            except (ValueError, PlaywrightTimeoutError, TimeoutError, Error, HTTPError, UnknownIPLocation):
                self.log(f"INITIALIZATION ATTEMPT {attempt}/{MAX_RETRIES} FAILED. RETRYING...", level="error")
                if self.http_client == "camoufox":
                    try:
                        await self.context.close()
                        await self.browser.__aexit__(None, None, None)
                        await self.session.__aexit__(None, None, None)
                    except AttributeError:
                        pass
                else:
                    await self.session.close()
                
                self.started = False
            else:
                initialization_successful = True
                self.started = True
                self.cookies_last_accessed_at = time.time()
                break
        
        if not initialization_successful:
            raise FatalAntiBotBlockError(f"FAILED TO CONNECT TO REDDIT AFTER {MAX_RETRIES} ATTEMPTS.")
        
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        if self.http_client == "camoufox":
            try:
                await self.context.close()
                await self.browser.__aexit__(None, None, None)
                await self.camoufox.__aexit__(None, None, None)
            except AttributeError:
                pass
        else:
            await self.session.close()
        
        self.started = False
    
    async def refresh_cookies(self):
        if self.cookie_renewal_in_progress:
            return
        
        self.cookie_renewal_in_progress = True
        cookie_refresh_successful = False
        self.log("REFRESHING COOKIES...")
        
        if self.http_client == "camoufox":
            try:
                await self.context.close()
                await self.browser.__aexit__(None, None, None)
                await self.session.__aexit__(None, None, None)
            except AttributeError:
                pass
        else:
            await self.session.close()
        
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if self.http_client == "camoufox":
                    proxy_url = self.new_proxy_url()
                    parsed_url = urlparse(proxy_url)
                    self.camoufox = AsyncCamoufox(
                        os=PLATFORMS[system().lower()],
                        headless=True,
                        humanize=True,
                        fingerprint_preset=True,
                        proxy={
                            "server": f"{parsed_url.scheme}://{parsed_url.hostname}:{parsed_url.port}",
                            "username": parsed_url.username,
                            "password": parsed_url.password
                        } if proxy_url else None,
                        geoip=True if proxy_url else False
                    )
                    self.browser: Browser = await self.camoufox.start()
                    self.context = await self.browser.new_context()
                    self.page = await self.context.new_page()
                    n1 = iwsuff("ywivreqi")
                    n2 = iwsuff("twwasvh")
                    nn = iwsuff("reqi")
                    ls = iwsuff("pskmr")
                    
                    await self.page.goto("https://old.reddit.com/login")
                    await self.page.wait_for_selector(f".{ls}")
                    h = await self.page.wait_for_selector(f'[{nn}="{n1}"]')
                    s = await self.page.wait_for_selector(f'[{nn}="{n2}"]')
                    await h.click()
                    
                    for char in iwsuff(USERNAME):
                        await self.page.keyboard.press(char)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    await s.click()
                    
                    for char in iwsuff(PASSWORD):
                        await self.page.keyboard.press(char)
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                    bgns = await self.page.wait_for_selector(f".{ls}")
                    await bgns.click()
                    await self.page.wait_for_selector('[alt="User Avatar"]')
                else: # Deprecated
                    self.session = AsyncSession(proxy=self.new_proxy_url(), allow_redirects=True)
                    self.session.headers["User-Agent"] = f"Reddrix{random.randint(0, 999999)}/v0.1.7"
                    res = await self.session.get("https://old.reddit.com/login")
                    res.raise_for_status()
            except (ValueError, PlaywrightTimeoutError, TimeoutError, Error, HTTPError, UnknownIPLocation):
                self.log(f"COOKIE REFRESH ATTEMPT {attempt}/{MAX_RETRIES} FAILED. RETRYING...", level="error")
                
                if self.http_client == "camoufox":
                    try:
                        await self.context.close()
                        await self.browser.__aexit__(None, None, None)
                        await self.session.__aexit__(None, None, None)
                    except AttributeError:
                        pass
                else:
                    await self.session.close()
                
                self.cookies_last_accessed_at = time.time()
            else:
                cookie_refresh_successful = True
                self.cookies_last_accessed_at = time.time()
                break
        
        if not cookie_refresh_successful:
            raise FatalAntiBotBlockError(f"FAILED TO REFRESH COOKIES AFTER {MAX_RETRIES} ATTEMPTS.")
        
        self.cookie_renewal_in_progress = False
    
    def log(self, msg: str=None, level: Literal["info", "warning", "error"]="info"):
        if msg and self.is_verbose:
            now = datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat()
            print(f"{now} [reddrix] [{level.upper()}] {msg}", flush=True)
    
    def parse_item(self, raw: dict) -> dict:
        """Parses each raw post or comment."""

        data: dict = raw["data"]
        if raw["kind"] == "t3": # Posts
            submission_id = data["id"]
            submission_id_prefixed = f"t3_{submission_id}"
            submission_type = "post"
            submission_url = "https://www.reddit.com" + data["permalink"]
            submitted_at = datetime.fromtimestamp(data["created_utc"], tz=timezone.utc).isoformat()
            parent_id = None
            parent_post_id = None
            parent_post_url = None
            post_type = None
            is_crosspost = "crosspost_parent" in data
            crosspost_parent_id = data.get("crosspost_parent")
            
            if is_crosspost:
                crosspost_parent_url = "https://www.reddit.com" + data.get("url_overridden_by_dest")
            else:
                crosspost_parent_url = None

            if (data.get("is_self", False) or False) and "poll_data" in data:
                post_type = "poll"
            elif (data.get("is_self", False) or False) and "poll_data" not in data:
                post_type = "text"
            elif data.get("post_hint", "") == "link":
                post_type = "link"
            elif data["is_video"] or data.get("domain") == "v.redd.it" or ((data.get("media", {}) or {}).get("oembed", {}) or {}).get("type") == "video":
                post_type = "video"
            elif data.get("post_hint", "") == "image" or data.get("domain") == "i.redd.it":
                post_type = "image"
            elif data.get("is_gallery", False):
                post_type = "gallery"
            elif "self." not in (data.get("domain", "") or ""):
                post_type = "link"

            title = data["title"]
            body_text = data["selftext"]
            is_edited = False if not data["edited"] else True
            author = data["author"]
            author_flair_text = data.get("author_flair_text")
            author_flair_image_url = (data.get("author_flair_richtext", [{}]) or [{}])[0].get("u")
            depth = None
            post_flair = data.get("link_flair_text") or None
            is_nsfw = data.get("over_18", False) or False
            subreddit = data.get("subreddit_name_prefixed") or None
            score = data["score"]
            upvote_ratio = data.get("upvote_ratio") or None
            num_comments = data["num_comments"]
            num_crossposts = data.get("num_crossposts", 0) or 0
            
            if is_crosspost:
                external_url = "https://www.reddit.com" + data.get("url_overridden_by_dest")
            else:
                external_url = data.get("url_overridden_by_dest")

            if "preview.redd.it" in (data.get("thumbnail", "") or ""):
                if not ((data.get("secure_media", {}) or {}).get("oembed", {}) or {}).get("thumbnail_url"):
                    thumbnail_url = f'https://i.redd.it/{data.get("thumbnail").split(".it/")[-1].split("?")[0]}'
                else:
                    thumbnail_url = ((data.get("secure_media", {}) or {}).get("oembed", {}) or {}).get("thumbnail_url")
            else:
                thumbnail_url = None

            if post_type == "video":
                video_url = (((data.get("media", {}) or {}).get("reddit_video", {}) or {}).get("fallback_url", "") or "").split("?")[0]
                if not video_url:
                    video_url = external_url
            else:
                video_url = None

            if post_type == "image":
                image_url = thumbnail_url if isinstance(thumbnail_url, str) and "preview.reddit" in thumbnail_url else external_url
            else:
                image_url = None

            if post_type == "gallery":
                img_extension = data["thumbnail"].split("?")[0].split(".")[-1]
                gallery_images_urls = [f'https://i.redd.it/{id_}.{img_extension}' for id_ in [item["media_id"] for item in data["gallery_data"]["items"]]]

            else:
                gallery_images_urls = []

            return {
                "submissionId": submission_id,
                "submissionIdPrefixed": submission_id_prefixed,
                "submissionType": submission_type,
                "submissionUrl": submission_url,
                "submittedAt": submitted_at,
                "parentId": parent_id,
                "parentPostId": parent_post_id,
                "parentPostUrl": parent_post_url,
                "postType": post_type,
                "isCrosspost": is_crosspost,
                "crosspostParentId": crosspost_parent_id,
                "crosspostParentUrl": crosspost_parent_url,
                "title": title,
                "bodyText": body_text,
                "isEdited": is_edited,
                "author": author,
                "authorFlairText": author_flair_text,
                "authorFlairImageUrl": author_flair_image_url,
                "depth": depth,
                "postFlair": post_flair,
                "isNSFW": is_nsfw,
                "subreddit": subreddit,
                "score": score,
                "upvoteRatio": upvote_ratio,
                "numComments": num_comments,
                "numCrossposts": num_crossposts,
                "externalUrl": external_url,
                "thumbnailUrl": thumbnail_url,
                "videoUrl": video_url,
                "imageUrl": image_url,
                "galleryImagesUrls": gallery_images_urls
            }
            
        else: # Comments
            submission_id = data["id"]
            submission_id_prefixed = f"t1_{submission_id}"
            submission_type = "comment"
            submission_url: str = "https://www.reddit.com" + data["permalink"]
            submitted_at = datetime.fromtimestamp(data["created_utc"], tz=timezone.utc).isoformat()
            parent_id = data["parent_id"]
            parent_post_id = data["link_id"]
            parent_post_url = submission_url.split("/comments/")[0] + "/comments/"  + submission_url.split("/comments/")[-1].split("/")[0]
            post_type = None
            is_crosspost = False
            crosspost_parent_id = None
            crosspost_parent_url = None
            title = None
            body_text = data["body"]
            is_edited = False if not data["edited"] else True
            author = data["author"]
            author_flair_text = data.get("author_flair_text")
            author_flair_image_url = (data.get("author_flair_richtext", [{}]) or [{}])[0].get("u")
            depth = data["depth"]
            post_flair = None
            is_nsfw = False
            subreddit = data.get("subreddit_name_prefixed")
            score = data["score"]
            upvote_ratio = None
            num_comments = None
            num_crossposts = None
            external_url = None
            thumbnail_url = None
            image_url = None
            video_url = None
            gallery_images_urls = []

            return {
                "submissionId": submission_id,
                "submissionIdPrefixed": submission_id_prefixed,
                "submissionType": submission_type,
                "submissionUrl": submission_url,
                "submittedAt": submitted_at,
                "parentId": parent_id,
                "parentPostId": parent_post_id,
                "parentPostUrl": parent_post_url,
                "postType": post_type,
                "isCrosspost": is_crosspost,
                "crosspostParentId": crosspost_parent_id,
                "crosspostParentUrl": crosspost_parent_url,
                "title": title,
                "bodyText": body_text,
                "isEdited": is_edited,
                "author": author,
                "authorFlairText": author_flair_text,
                "authorFlairImageUrl": author_flair_image_url,
                "depth": depth,
                "postFlair": post_flair,
                "isNSFW": is_nsfw,
                "subreddit": subreddit,
                "score": score,
                "upvoteRatio": upvote_ratio,
                "numComments": num_comments,
                "numCrossposts": num_crossposts,
                "externalUrl": external_url,
                "thumbnailUrl": thumbnail_url,
                "videoUrl": video_url,
                "imageUrl": image_url,
                "galleryImagesUrls": gallery_images_urls
            }
    
    @auto_retry(max_attempts=3)
    async def get(self, url: str, params: dict={}, expected_data_type: Literal["JSON", "HTML/XML"]="JSON") -> dict | list | str:
        async with self.request_semaphore:
            if params:
                url += f"{'?' if '?' not in url else ''}{urlencode(params) if '?' not in url else f'&{urlencode(params)}'}"
            
            while self.cookie_renewal_in_progress:
                await asyncio.sleep(0.07)
            
            if self.http_client == "camoufox":
                try:
                    if expected_data_type == "JSON":
                        data: list | dict = await self.page.evaluate(r"async (url) => {const res = await fetch(url); return await res.json();}", url)
                    else:
                        data: str = await self.page.evaluate(r"async (url) => {const res = await fetch(url); return await res.text();}", url)
                    
                    if isinstance(data, dict) and data.get("error", 200) in [403, 404] and ("/user/" in url or "/u/" in url) and "/comments/" not in url:
                        return {} if expected_data_type == "JSON" else ""
                    elif isinstance(data, dict) and data.get("error", 200) >= 400:
                        raise AntiBotBlockError
                except Error:
                    raise AntiBotBlockError
                except AttributeError:
                    data = {} if expected_data_type == "JSON" else ""
                    pass
            else:
                try:
                    res = await self.session.get(url)
                    res.raise_for_status()
                    
                    if expected_data_type == "JSON":
                        data: list | dict = res.json()
                    else:
                        data: str = res.text       
                except HTTPError:
                    if "/user/" in url or "/u/" in url:
                        return {} if expected_data_type == "JSON" else ""
                    else:
                        raise AntiBotBlockError
                except (JSONDecodeError, orjsonJSONDecodeError):
                    raise AntiBotBlockError
        
        return data

    @auto_retry(max_attempts=3)
    async def fetch_children_batch(self, post_id: str, id_batch: list) -> tuple[list[dict]]:
        api_url = f"https://www.reddit.com/api/morechildren.json?api_type=json&link_id={post_id}&children={','.join(id_batch)}"
        async with self.page_semaphore:
            await asyncio.sleep(random.uniform(0.5, 4)) # Random jitter
            page_data = await self.get(api_url)
            if page_data["json"]["errors"]:
                raise AntiBotBlockError

        return [item for item in page_data["json"]["data"]["things"] if item["kind"] == "t1" and item["data"]["id"] != "_" and item["data"]["depth"] <= self.max_comments_depth], [item for item in page_data["json"]["data"]["things"] if item["kind"] == "more" and item["data"]["id"] != "_" and item["data"]["depth"] <= self.max_comments_depth]

    @auto_retry(max_attempts=3)
    async def fetch_more_comments(self, post_id: str, more_items: list, fetched_comments_count: int, fetched_top_comments_count: int) -> tuple[dict, int, int]:
        more_ids_batches = {}
        more = []

        for item in more_items:
            item_id = item["data"]["id"]
            more_ids_batches.update({item_id: [[]]})

            for child in item["data"]["children"]:
                more_ids_batches[item_id][-1].append(child)
                if len(more_ids_batches[item_id][-1]) % 100 == 0:
                    more_ids_batches[item_id].append([])

            if not more_ids_batches[item_id][-1]:
                more_ids_batches[item_id] = more_ids_batches[item_id][:-1]

        all_batches = [batch for batches in more_ids_batches.values() for batch in batches]
        batch_tasks = [self.fetch_children_batch(post_id, batch) for batch in all_batches]

        for future in asyncio.as_completed(batch_tasks):
            comments, new_more = await future

            if fetched_comments_count >= self.max_comments_per_post:
                break

            more.extend(new_more)

            for comment in comments:
                if fetched_comments_count >= self.max_comments_per_post:
                    break

                if comment["kind"] == "t1" and comment["data"]["depth"] <= self.max_comments_depth:
                    if comment["data"]["depth"] == 0:
                        if fetched_comments_count < self.max_comments_per_post and fetched_top_comments_count < self.max_top_comments_per_post:
                            await self.items_queue.put(comment)
                            fetched_comments_count += 1
                            fetched_top_comments_count += 1
                    else:
                        if fetched_comments_count < self.max_comments_per_post:
                            await self.items_queue.put(comment)
                            fetched_comments_count += 1

        return more, fetched_comments_count, fetched_top_comments_count

    async def fetch_post(self, url: str) -> None:
        fetched_comments_count = 0
        fetched_top_comments_count = 0
        more = []

        async with self.page_semaphore:
            await asyncio.sleep(random.uniform(0.5, 4)) # Random jitter
            page_data = await self.get(url)

        post = page_data[0]["data"]["children"][0]
        comments: list = page_data[1]["data"]["children"] or []

        await self.items_queue.put(post)

        if not self.include_comments:
            return

        for comment in comments:
            if fetched_comments_count >= self.max_comments_per_post:
                break

            if comment["kind"] == "t1" and comment["data"]["depth"] <= self.max_comments_depth:
                if comment["data"]["depth"] == 0:
                    if fetched_comments_count < self.max_comments_per_post and fetched_top_comments_count < self.max_top_comments_per_post:
                        await self.items_queue.put(comment)
                        fetched_comments_count += 1
                        fetched_top_comments_count += 1
                else:
                    if fetched_comments_count < self.max_comments_per_post:
                        await self.items_queue.put(comment)
                        fetched_comments_count += 1

            elif comment["kind"] == "more" and comment["data"]["id"] != "_":
                more.append(comment)

        while more and fetched_comments_count < self.max_comments_per_post:
            more, fetched_comments_count, fetched_top_comments_count = await self.fetch_more_comments(post_id=post["data"]["name"], more_items=more, fetched_comments_count=fetched_comments_count, fetched_top_comments_count=fetched_top_comments_count)

    async def fetch_collection(self, url: str) -> None:
        after = ""
        next_page_url = ""
        fetched_posts_count = 0
        post_tasks = []
        if self.mode != "keyword_search":
            while True:
                async with self.page_semaphore:
                    await asyncio.sleep(random.uniform(0.5, 4)) # Random jitter
                    page_data = await self.get(url, params={"after": after})

                if not page_data:
                    break

                after = page_data["data"]["after"] or ""
                posts = page_data["data"]["children"]

                for post in posts:
                    if fetched_posts_count >= self.max_posts_per_collection:
                        break

                    if post["kind"] == "t3" and fetched_posts_count < self.max_posts_per_collection:
                        post_url = "https://www.reddit.com" + post["data"]["permalink"] + ".json?threaded=false"

                        if self.include_comments and post["data"]["num_comments"] > 0:
                            post_tasks.append(asyncio.create_task(self.fetch_post(post_url)))
                        else:
                            await self.items_queue.put(post)

                        fetched_posts_count += 1

                if not after or fetched_posts_count >= self.max_posts_per_collection:
                    break

            if post_tasks:
                await asyncio.gather(*post_tasks)
        else:
            while True:
                async with self.page_semaphore:
                    await asyncio.sleep(random.uniform(0.5, 4)) # Random jitter
                    page_html: str = await self.get(url if not next_page_url else next_page_url, expected_data_type="HTML/XML")

                if not page_html:
                    break

                soup = WhiskeySour(page_html)
                next_page_el = soup.select_one("faceplate-partial[loading=lazy]")
                next_page_url = "https://www.reddit.com" + next_page_el.get("src") if next_page_el else ""

                posts = soup.select('a[data-testid="post-title"]')
                for post in posts:
                    if fetched_posts_count >= self.max_posts_per_collection:
                        break

                    if fetched_posts_count < self.max_posts_per_collection:
                        post_url = "https://www.reddit.com" + post.get("href") + ".json?threaded=false"
                        post_tasks.append(asyncio.create_task(self.fetch_post(post_url)))

                        fetched_posts_count += 1

                if not next_page_url or fetched_posts_count >= self.max_posts_per_collection:
                    break

            if post_tasks:
                await asyncio.gather(*post_tasks)
    
    async def get_items(self) -> AsyncGenerator[dict, None]:
        tasks = []

        async def run_all_tasks():
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                await self.items_queue.put(e)
            else:
                await self.items_queue.put("done")

        if self.mode == "standard":
            # Subreddits
            for url in self.subreddit_urls:
                initial_url = url
                if "reddit.com" not in initial_url or "/r/" not in initial_url:
                    continue

                params = {"limit": 100, "t": self.time_frame}

                raw_sub_name = initial_url.split("/r/")[-1].split("/")[0]
                final_url = f"https://www.reddit.com/r/{raw_sub_name}"

                if self.sort != "default":
                    final_url += f"/{self.sort}/"

                final_url += f".json?{urlencode(params)}"

                tasks.append(self.fetch_collection(final_url))

            # Posts
            for url in self.post_urls:
                initial_url = url
                if "reddit.com" not in initial_url or "/comments/" not in initial_url:
                    continue

                final_url = initial_url.split("/comments/")[0] + "/comments/" + initial_url.split("/comments/")[-1].split("/")[0] + ".json?threaded=false"
                tasks.append(self.fetch_post(final_url))

            # Profiles
            for url in self.profile_urls:
                initial_url = url
                if "reddit.com" not in initial_url or ("/u/" not in initial_url and "/user/" not in initial_url):
                    continue

                params = {
                    "limit": 100,
                    "sort": self.sort if self.sort != "default" else "",
                    "t": self.time_frame
                }

                if "/u/" in initial_url:
                    final_url = initial_url.split("/u/")[0] + "/u/" + initial_url.split("/u/")[-1].split("/")[0] + f"/submitted/.json?{urlencode(params)}"
                elif "/user/" in initial_url:
                    final_url = initial_url.split("/user/")[0] + "/user/" + initial_url.split("/user/")[-1].split("/")[0] + f"/submitted/.json?{urlencode(params)}"

                tasks.append(self.fetch_collection(final_url))
        elif self.mode == "keyword_search":
            final_url = ""

            if self.query:
                params = {
                    "q": self.query,
                    "type": "posts",
                    "sort": "relevance"
                }

                final_url = f"https://www.reddit.com/search/?{urlencode(params)}"
                tasks.append(self.fetch_collection(final_url))
        else: # domain_search
            for domain in self.domains:
                final_url = f"https://www.reddit.com/domain/{domain}/"
                if self.sort != "default":
                    final_url += f"{self.sort}/"

                final_url += ".json?limit=100"
                tasks.append(self.fetch_collection(final_url))


        
        runner = asyncio.create_task(run_all_tasks())
        results_count = 0

        try:
            while True:
                item = await self.items_queue.get()

                if isinstance(item, Exception):
                    raise item

                if item != "done":
                    results_count += 1

                    if results_count > self.max_results:
                        break
                    else:
                        yield self.parse_item(item)
                else:
                    break
        finally:
            runner.cancel()
