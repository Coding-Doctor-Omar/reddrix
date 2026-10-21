from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error, Browser, BrowserContext, Page
from .exceptions import AntiBotBlockError, FatalAntiBotBlockError, NotInitializedError, InvalidRequestError
from wreq.exceptions import StatusError, TimeoutError as wTimeoutError, BuilderError
from wreq import Cookie, Jar, Client, Proxy, SameSite, redirect
from urllib.parse import urlencode, urlparse, quote, unquote
from wreq.emulation import Emulation, Profile, Platform
from playwright._impl._errors import TargetClosedError
from datetime import datetime, timezone, timedelta
from camoufox.exceptions import UnknownIPLocation
from camoufox.async_api import AsyncCamoufox
from collections.abc import AsyncGenerator
from whiskeysour import WhiskeySour, Tag
from functools import wraps
from platform import system
from typing import Literal
from html import unescape
from asyncio import Task
import asyncio
import random
import json
import time


COOKIE_URL = "https://www.reddit.com/r/kasralainy" # Empty sub page for low bandwidth when obtaining cookies.

MAX_COOKIE_RETRIES = 5
CAMOUFOX_PLATFORMS = {
    "windows": "windows",
    "linux": "linux",
    "darwin": "macos"
}
WREQ_PLATFORMS = {
    "windows": Platform.Windows,
    "linux": Platform.Linux,
    "darwin": Platform.MacOS
}
TIME_FRAMES = {
    "top_all_time": "all",
    "top_past_hour": "hour",
    "top_today": "day",
    "top_past_week": "week",
    "top_past_month": "month",
    "top_past_year": "year"
}
COOKIE_LOCK = asyncio.Lock()

def auto_retry(max_attempts: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            url = kwargs.get("url") or args[1]
            scraper: Reddrix = args[0]
            
            if not scraper.started and scraper.is_running:
                raise NotInitializedError("Scraper is not initialized. Initialize the scraper with the context manager or the start() and stop() methods first.")

            for attempt in range(1, max_attempts + 1):
                current_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                except (AntiBotBlockError, TargetClosedError, asyncio.CancelledError):
                    if scraper.is_running:
                        if attempt == max_attempts:
                            raise FatalAntiBotBlockError(f"Error fetching URL: {url}\n\nError Message: Cookies expired, and attempts have been exhausted.")

                        async with COOKIE_LOCK:
                            if current_time - scraper.cookies_last_accessed_at >= 15:
                                await scraper.refresh_cookies()

                        await asyncio.sleep(min(2 ** attempt + random.uniform(0, 5), 60))
                    else:
                        return
                else:
                    return result

        return wrapper

    return decorator

class Reddrix:
    def __init__(
        self,
        mode: Literal["standard", "keyword_search"]="standard",
        stealth: Literal["adaptive", True, False]=True,
        max_results: int=999999,
        max_posts_per_collection: int=999999,
        sort: Literal["default", "new", "hot", "top_all_time", "top_past_hour", "top_today", "top_past_week", "top_past_month", "top_past_year"]="default",
        subreddit_urls: list[str]=[],
        post_urls: list[str]=[],
        profile_urls: list[str]=[],
        query: str=None,
        include_comments: bool=False,
        max_comments_depth: int=999999,
        max_comments_per_post: int=999999,
        max_top_comments_per_post: int=999999,
        proxies: list[str]=[],
        verbose: bool=False
    ):  
        if stealth == "adaptive":
            if include_comments:
                self.stealth = True
            else:
                self.stealth = False
        else:
            if stealth in [True, False]:
                self.stealth = stealth
            else:
                self.stealth = "adaptive"
        
        self.mode = mode
        self.max_results = max_results
        self.max_posts_per_collection = max_posts_per_collection
        self.sort = sort if "top" not in sort else "top"
        self.time_frame = TIME_FRAMES.get(sort) or ""
        self.subreddit_urls = subreddit_urls
        self.post_urls = post_urls
        self.profile_urls = profile_urls
        self.query = query
        self.include_comments = include_comments
        self.max_comments_depth = max_comments_depth
        self.max_comments_per_post = max_comments_per_post
        self.max_top_comments_per_post = max_top_comments_per_post
        self.seen_comment_ids = set()
        self.posts_comments_counts = {}
        
        self.cookies = []
        self.csrf_token: str | None = None
        self.cookie_jar = Jar()
        self.proxies = proxies
        self.is_verbose = verbose
        self.used_proxies = set()
        self.camoufox: AsyncCamoufox | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.client: Client | None = None
        self.started = False
        self.cookie_renewal_in_progress = False
        self.cookies_last_accessed_at = 0.0
        self.page_semaphore = asyncio.Semaphore(10)
        self.request_semaphore = asyncio.Semaphore(10)
        self.items_queue = asyncio.Queue(maxsize=1000)
        self.is_running = True
        self.interaction_task: Task | None = None
    
    async def start(self):
        return await self.__aenter__()
    
    async def stop(self):
        await self.__aexit__(None, None, None)
    
    def new_proxy_url(self) -> str:
        """Generates a new proxy url from the list (if provided)."""
        
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
    
    def fill_cookie_jar(self):
        """Fills the wreq client's cookie jar from the Camoufox browser context cookies."""
        
        for c in self.cookies:
            if c["name"] == "csrf_token":
                self.csrf_token = c["value"]
            
            if c["sameSite"] == "Lax":
                same_site = SameSite.Lax
            elif c["sameSite"] == "Strict":
                same_site = SameSite.Strict
            else:
                same_site = SameSite.Empty
            
            self.cookie_jar.add(
                Cookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c["domain"],
                    path=c["path"],
                    expires=datetime.fromtimestamp(c["expires"], tz=timezone.utc) if c["expires"] and c["expires"] > 0 else None,
                    http_only=c["httpOnly"],
                    secure=c["secure"],
                    same_site=same_site
                ),
                url="https://www.reddit.com/"
            )
    
    async def __aenter__(self):
        initialization_successful = False
        self.log("INITIALIZING SCRAPER")
        for attempt in range(1, MAX_COOKIE_RETRIES + 1):
            try:
                proxy_url = self.new_proxy_url()
                parsed_url = urlparse(proxy_url)
                self.camoufox = AsyncCamoufox(
                    os=CAMOUFOX_PLATFORMS[system().lower()],
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
                self.browser = await self.camoufox.__aenter__()
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                
                await self.page.goto(COOKIE_URL)
                login_btn = self.page.locator("#login-button")
                
                if self.stealth:
                    await login_btn.hover()
                    await asyncio.sleep(1.5)
                    self.cookies = await self.context.cookies()
                    
                    for c in self.cookies:
                        if c["name"] == "csrf_token":
                            self.csrf_token = c["value"]
                    
                    self.interaction_task = asyncio.create_task(self.interact_naturally_with_reddit())
                else:
                    await login_btn.hover(timeout=15000) # Ensure ALL cookies are harvested
                    self.cookies = await self.context.cookies()
                    self.fill_cookie_jar()
                    self.client = Client(
                        emulation=Emulation(profile=Profile.Firefox152, platform=WREQ_PLATFORMS[system().lower()]),
                        timeout=timedelta(seconds=7),
                        cookie_provider=self.cookie_jar,
                        proxies=[Proxy.all(proxy_url)] if proxy_url else [],
                        redirect=redirect.Policy.limited(5)
                    )
                    await self.camoufox.__aexit__(None, None, None)
                
                self.started = True
            except (ValueError, PlaywrightTimeoutError, TimeoutError, Error, UnknownIPLocation):
                self.log(f"INITIALIZATION ATTEMPT {attempt}/{MAX_COOKIE_RETRIES} FAILED. RETRYING...", level="error")
                try:
                    self.client.close()
                    await self.camoufox.__aexit__(None, None, None)
                    self.cookie_jar.clear()
                except AttributeError:
                    pass
                
            else:
                initialization_successful = True
                self.started = True
                self.cookies_last_accessed_at = time.time()
                break
        
        if not initialization_successful:
            raise FatalAntiBotBlockError(f"FAILED TO CONNECT TO REDDIT AFTER {MAX_COOKIE_RETRIES} ATTEMPTS.")
        else:
            self.log("BEGINNING SCRAPING")
        
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        try:
            self.client.close()
            await self.camoufox.__aexit__(None, None, None)
            self.cookie_jar.clear()
        except AttributeError:
            pass
        
        self.started = False
    
    async def refresh_cookies(self):
        if self.cookie_renewal_in_progress:
            return
        
        self.cookie_renewal_in_progress = True
        cookie_refresh_successful = False
        self.log("REFRESHING COOKIES...")
        
        try:
            self.client.close()
            await self.camoufox.__aexit__(None, None, None)
            self.cookie_jar.clear()
        except AttributeError:
            pass
        
        
        for attempt in range(1, MAX_COOKIE_RETRIES + 1):
            try:
                proxy_url = self.new_proxy_url()
                parsed_url = urlparse(proxy_url)
                
                self.camoufox = AsyncCamoufox(
                    os=CAMOUFOX_PLATFORMS[system().lower()],
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
                self.browser = await self.camoufox.__aenter__()
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                
                await self.page.goto(COOKIE_URL)
                login_btn = self.page.locator("#login-button")
                
                if self.stealth:
                    await login_btn.hover()
                    await asyncio.sleep(1.5)
                    self.cookies = await self.context.cookies()
                    
                    for c in self.cookies:
                        if c["name"] == "csrf_token":
                            self.csrf_token = c["value"]
                else:
                    await login_btn.hover(timeout=15000) # Ensure ALL cookies are harvested
                    self.cookies = await self.context.cookies()
                    self.fill_cookie_jar()
                    self.client = Client(
                        emulation=Emulation(profile=Profile.Firefox152, platform=WREQ_PLATFORMS[system().lower()]),
                        timeout=timedelta(seconds=7),
                        cookie_provider=self.cookie_jar,
                        proxies=[Proxy.all(proxy_url)] if proxy_url else [],
                        redirect=redirect.Policy.limited(5)
                    )
                    await self.camoufox.__aexit__(None, None, None)
            except (ValueError, PlaywrightTimeoutError, TimeoutError, Error, UnknownIPLocation):
                self.log(f"COOKIE REFRESH ATTEMPT {attempt}/{MAX_COOKIE_RETRIES} FAILED. RETRYING...", level="error")
                try:
                    self.client.close()
                    await self.camoufox.__aexit__(None, None, None)
                    self.cookie_jar.clear()
                except AttributeError:
                    pass
                
                self.cookies_last_accessed_at = time.time()
            else:
                cookie_refresh_successful = True
                self.log("COOKIE REFRESH SUCCESSFUL")
                self.cookies_last_accessed_at = time.time()
                break
        
        if not cookie_refresh_successful:
            raise FatalAntiBotBlockError(f"FAILED TO REFRESH COOKIES AFTER {MAX_COOKIE_RETRIES} ATTEMPTS.")
        
        self.cookie_renewal_in_progress = False
    
    async def interact_naturally_with_reddit(self):
        """Human-like behavior for long-lived sessions (for stealth mode only)."""
        
        buttons = [
            "#login-button",
            "#signup-button",
            'button[data-testid="create-post"]',
            ".join-btn",
            "#expand-user-drawer-button"
        ]
        while True:
            try:
                button_selector = random.choice(buttons)
                button = self.page.locator(button_selector)
                await button.hover()
                await asyncio.sleep(random.uniform(0.5, 5))
            except (TargetClosedError, PlaywrightTimeoutError, Error):
                await asyncio.sleep(0.3)
                continue
    
    def log(self, msg: str=None, level: Literal["info", "warning", "error"]="info"):
        if msg and self.is_verbose:
            now = datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat()
            print(f"{now} [reddrix] [{level.upper()}] {msg}", flush=True)
    
    def parse_item(self, raw: Tag) -> dict:
        """Parses each raw post or comment."""

        data: Tag = raw # Redundant statement kept in place to keep the new code compatible with the old code.
        
        if raw.name == "shreddit-post": # Posts
            submission_id = data["id"].split("_")[-1]
            submission_id_prefixed = data["id"]
            submission_type = "post"
            submission_url = "https://www.reddit.com" + data["permalink"]
            submitted_at = data["created-timestamp"]
            parent_id = None
            parent_post_id = None
            parent_post_url = None
            post_type = data["post-type"]
            
            if post_type == "crosspost":
                crosspost_parent_url: str = "https://www.reddit.com" + data.get("content-href")
                crosspost_parent_id = crosspost_parent_url.split("/comments/")[-1].split("/")[0]
            else:
                crosspost_parent_url = None
                crosspost_parent_id = None

            title = unescape(data["post-title"])
            text_el = data.select_one(f"#{submission_id_prefixed}-post-rtjson-content")
            
            if text_el:
                body_text = text_el.text.strip()
            else:
                body_text = None
            
            author = data["author"]
            depth = None
            
            post_flair = None
            post_flair_el = data.select_one("shreddit-post-flair")
            if post_flair_el:
                post_flair = post_flair_el.text.strip() or None
            
            tags_els = data.select('[slot="ssr-post-content-header"] > div')
            tags = []
            
            for el in tags_els:
                tag = el.text.strip()
                if tag not in tags:
                    tags.append(tag)
            
            subreddit = data.get("subreddit-prefixed-name") or None
            score = int(data["score"])
            upvote_ratio = float(data.get("upvote-ratio")) or None
            num_comments = int(data["comment-count"])
            
            if post_type == "crosspost":
                external_url = crosspost_parent_url
            else:
                external_url = data.get("content-href") if post_type in ["image", "video", "link", "gallery"] else None


            if post_type == "gallery":
                gallery_images_urls = []
                gallery_images_els = data.select('gallery-carousel li[slot] > img')
                for el in gallery_images_els:
                    img_id_slug = unescape((el.get("src") or el.get("data-lazy-src")).split("v0-")[-1].split("?")[0])
                    image_url = f"https://i.redd.it/{img_id_slug}"
                    gallery_images_urls.append(image_url)
            else:
                gallery_images_urls = []
                
            if post_type == "image":
                thumbnail_url = external_url
            elif post_type == "video":
                thumbnail_url = unescape(data.select_one('source').get("src"))
            elif post_type == "gallery":
                thumbnail_url = gallery_images_urls[0]
            else:
                thumbnail_url = None

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
                "crosspostParentId": crosspost_parent_id,
                "crosspostParentUrl": crosspost_parent_url,
                "title": title,
                "bodyText": body_text,
                "author": author,
                "depth": depth,
                "postFlair": post_flair,
                "tags": tags,
                "subreddit": subreddit,
                "score": score,
                "upvoteRatio": upvote_ratio,
                "numComments": num_comments,
                "externalUrl": external_url,
                "thumbnailUrl": thumbnail_url,
                "galleryImagesUrls": gallery_images_urls
            }
            
        else: # Comments
            submission_id = data["thingid"].split("_")[-1]
            submission_id_prefixed = data["thingid"]
            submission_type = "comment"
            submission_url: str = "https://www.reddit.com" + data["permalink"]
            submitted_at = data["created"]
            parent_id = data.get("parentid")
            parent_post_id = data.get("postid")
            parent_post_url = submission_url.split("/comments/")[0] + "/comments/"  + submission_url.split("/comments/")[-1].split("/")[0]
            post_type = None
            crosspost_parent_id = None
            crosspost_parent_url = None
            title = None
            
            try:
                body_text = data.select_one(f'#{submission_id_prefixed}-post-rtjson-content').text.strip()
            except AttributeError: # Happens with comments that are removed
                return {}
            
            comment_external_links_els = data.select(f"#{submission_id_prefixed}-post-rtjson-content a")
            for el in comment_external_links_els:
                body_text += f"\n{unescape(el['href'])}"
            
            author = data["author"]
            depth = int(data["depth"])
            post_flair = None
            tags = []
            
            if "/r/" in submission_url:
                subreddit = "r/" + submission_url.split("/r/")[-1].split("/")[0]
            else:
                subreddit = None
            
            score = int(data["score"])
            upvote_ratio = None
            num_comments = None
            external_url = None
            thumbnail_url = None
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
                "crosspostParentId": crosspost_parent_id,
                "crosspostParentUrl": crosspost_parent_url,
                "title": title,
                "bodyText": body_text,
                "author": author,
                "depth": depth,
                "postFlair": post_flair,
                "tags": tags,
                "subreddit": subreddit,
                "score": score,
                "upvoteRatio": upvote_ratio,
                "numComments": num_comments,
                "externalUrl": external_url,
                "thumbnailUrl": thumbnail_url,
                "galleryImagesUrls": gallery_images_urls
            }

    @auto_retry(max_attempts=5)
    async def post(self, url: str, params: dict={}, json_data: dict={}, form_data: dict={}) -> str | None:
        async with self.request_semaphore:
            if params:
                url += f"{'?' if '?' not in url else ''}{urlencode(params) if '?' not in url else f'&{urlencode(params)}'}"
            
            while self.cookie_renewal_in_progress:
                await asyncio.sleep(0.07)
            
            if not self.stealth:
                try:
                    if form_data:
                        res = await self.client.post(url, form=form_data)
                    elif json_data:
                        res = await self.client.post(url, json=json_data)
                    else:
                        raise InvalidRequestError("No JSON payload or form data provided in the POST request.")
                    
                    status_code = res.status.as_int()
                    res.raise_for_status()
                except StatusError:
                    if status_code == 404:
                        return None
                    else:
                        raise AntiBotBlockError
                except wTimeoutError:
                    raise AntiBotBlockError
                except BuilderError:
                    return None
                else:
                    data = await res.text()
                    return data  
            else:
                try:
                    if form_data:
                        js_expression = r'async (url) => {const formData = new URLSearchParams(FORM_DATA); const res = await fetch(url, {method: "POST", credentials: "include", body: formData}); return [await res.text(), res.status];}'
                        js_expression = js_expression.replace("FORM_DATA", json.dumps(form_data))
                    elif json_data:
                        js_expression = r'async (url) => {const res = await fetch(url, {method: "POST", credentials: "include", body: JSON.stringify(JSON_DATA)}); return [await res.text(), res.status];}'
                        js_expression = js_expression.replace("JSON_DATA", json.dumps(json_data))
                    else:
                        raise InvalidRequestError("No JSON payload or form data provided in the POST request.")
                    
                    data, status_code = await self.page.evaluate(js_expression, url)
                    if status_code >= 400:
                        if status_code == 404:
                            return None
                        else:
                            raise AntiBotBlockError
                except Exception:
                    raise AntiBotBlockError
                else:
                    return data
    
                
    
    @auto_retry(max_attempts=5)
    async def get(self, url: str, params: dict={}) -> str | None:
        async with self.request_semaphore:
            if params:
                url += f"{'?' if '?' not in url else ''}{urlencode(params) if '?' not in url else f'&{urlencode(params)}'}"
            
            while self.cookie_renewal_in_progress:
                await asyncio.sleep(0.07)
            
            if not self.stealth:
                try:
                    res = await self.client.get(url)
                    status_code = res.status.as_int()
                    res.raise_for_status()
                except StatusError:
                    if status_code == 404:
                        return None
                    else:
                        raise AntiBotBlockError
                except wTimeoutError:
                    raise AntiBotBlockError
                except BuilderError:
                    return None
                else:
                    data = await res.text()
                    return data
            else:
                try:
                    data, status_code = await self.page.evaluate(r'async (url) => {const res = await fetch(url, {credentials: "include"}); return [await res.text(), res.status];}', url)
                    if status_code >= 400:
                        if status_code == 404:
                            return None
                        else:
                            raise AntiBotBlockError
                except Exception:
                    raise AntiBotBlockError
                else:
                    return data
    
    async def fetch_post(self, url: str, cursor: str=None, initial_page: bool=False, depth_offset: int=0, post_id: str=None) -> None:
        """Fetches the post details (for the initial page) and comments."""
        
        if "/comments/" in url and initial_page:
            post_id = url.split("/comments/")[-1].split("/")[0]
            self.posts_comments_counts[post_id] = {"total": 0, "top": 0}
            url = url.split("/comments/")[0] + "/comments/" + "/".join(quote(unquote(item)) for item in url.split("/comments/")[-1].split("/"))
        
        if self.is_running:
            more = []
            
            async with self.page_semaphore:
                await asyncio.sleep(random.uniform(0.5, 2)) # Random jitter
                
                if initial_page or not cursor:
                    page_data = await self.get(url)
                else:
                    form = {"csrf_token": self.csrf_token, "cursor": cursor}
                    page_data = await self.post(url, form_data=form)

            if not page_data and self.is_running:
                self.log(f"SKIPPING URL: {url} (REASON: Invalid Url)", level="warning")
                return
            
            try:
                soup = WhiskeySour(page_data)
            except AttributeError: # When the scraper force shuts down after reaching max results or the like
                return
            
            if initial_page:
                post = soup.select_one("shreddit-post")
                if not post:
                    return
                
                await self.items_queue.put(post)
            
            comments = soup.select("shreddit-comment")
            
            if not self.include_comments:
                return
            
            for comment in comments:
                if self.posts_comments_counts[post_id]["total"] >= self.max_comments_per_post:
                    break
                
                if comment["thingid"] not in self.seen_comment_ids:
                    self.seen_comment_ids.add(comment["thingid"])
                    comment["depth"] = str(int(comment["depth"]) + depth_offset)
                else:
                    continue
                
                if int(comment["depth"]) > self.max_comments_depth:
                    self.max_comments_depth_reached = True
                    continue
                elif int(comment["depth"]) == self.max_comments_depth:
                    self.max_comments_depth_reached = True
                
                if int(comment["depth"]) <= self.max_comments_depth:
                    if int(comment["depth"]) == 0:
                        if self.posts_comments_counts[post_id]["total"] < self.max_comments_per_post and self.posts_comments_counts[post_id]["top"] < self.max_top_comments_per_post:
                            await self.items_queue.put(comment)
                            self.posts_comments_counts[post_id]["total"] += 1
                            self.posts_comments_counts[post_id]["top"] += 1
                    else:
                        if self.posts_comments_counts[post_id]["total"] < self.max_comments_per_post:
                            await self.items_queue.put(comment)
                            self.posts_comments_counts[post_id]["total"] += 1
            
            children_comments_elements = soup.select('#comment-children > faceplate-partial[slot="children"]')
            children_comments_urls_and_cursors: list[tuple[str]] = []
            
            for el in children_comments_elements:
                children_url = "https://www.reddit.com" + unescape(el.get("src"))
                children_cursor_el = el.select_one('input[name="cursor"]')
                children_cursor = children_cursor_el["value"]
                children_comments_urls_and_cursors.append((children_url, children_cursor))
            
            
            for item in children_comments_urls_and_cursors:
                more.append(asyncio.create_task(self.fetch_post(url=item[0], cursor=item[1], post_id=post_id)))
            
            # Simulating single-thread comment pages visits
            single_thread_children_els = soup.select('div.fold-more:not(.hidden) a.more-comments-link')
            for el in single_thread_children_els:
                parent_comment = el.find_parent("shreddit-comment")
                depth_offset_ = int(parent_comment["depth"])
                children_url = "https://www.reddit.com" + unescape(el.get("href"))
                more.append(asyncio.create_task(self.fetch_post(children_url, depth_offset=depth_offset_, post_id=post_id)))
            
            
            # Simulating the automatic scroll more comments loading
            automatic_more_comments_element = soup.select_one("#top-level-more-comments-partial")  
            if automatic_more_comments_element:
                cursor_el = automatic_more_comments_element.select_one('input[name="cursor"]')
                cursor_val = cursor_el["value"]
                automatic_more_comments_url = "https://www.reddit.com" + unescape(automatic_more_comments_element.get("src"))
                more.append(asyncio.create_task(self.fetch_post(automatic_more_comments_url, cursor=cursor_val, post_id=post_id)))
            
            # Simulating the manual more comments button if needed
            faceplate_partials_elements = soup.select('faceplate-partial.more-comments-partial[loading="action"]')
            if faceplate_partials_elements:
                manual_more_comments_element = faceplate_partials_elements[-1]
            else:
                manual_more_comments_element = None
            
            if manual_more_comments_element:
                manual_more_comments_url = "https://www.reddit.com" + unescape(manual_more_comments_element.get("src"))
                cursor_el = manual_more_comments_element.select_one('input[name="cursor"]')
                cursor_val = cursor_el["value"]
                more.append(asyncio.create_task(self.fetch_post(manual_more_comments_url, cursor=cursor_val, post_id=post_id)))
            
            # Waiting for all comments to finish for the post
            if more:
                await asyncio.gather(*more)

    async def fetch_collection(self, url: str) -> None:
        """Fetches an entire collection (e.g. a sub, a profile, or a keyword_search page)."""
        if self.is_running:
            next_page_url = None
            fetched_posts_count = 0
            post_tasks = []
            if self.mode != "keyword_search":
                while True:
                    async with self.page_semaphore:
                        await asyncio.sleep(random.uniform(0.5, 2)) # Random jitter
                        page_data = await self.get(url if not next_page_url else next_page_url)

                    if not page_data and self.is_running:
                        self.log(f"SKIPPING URL: {url} (REASON: Invalid Url)", level="warning")
                        return
                    
                    try:
                        soup = WhiskeySour(page_data)
                    except AttributeError: # When the scraper force shuts down after reaching max results or the like
                        return
                    
                    profile_not_found_or_banned_el = soup.select("#shreddit-forbidden-title")
                    if profile_not_found_or_banned_el:
                        return
                    
                    posts = soup.select("shreddit-post")
                    next_page_el = soup.select_one('faceplate-partial[slot="load-after"]')
                    
                    if next_page_el:
                        next_page_url = "https://www.reddit.com" + unescape(next_page_el["src"])
                    else:
                        next_page_url = None

                    for post in posts:
                        if fetched_posts_count >= self.max_posts_per_collection:
                            break

                        if fetched_posts_count < self.max_posts_per_collection:
                            post_url = "https://www.reddit.com" + post["permalink"]
                            post_tasks.append(asyncio.create_task(self.fetch_post(post_url, initial_page=True)))
                            fetched_posts_count += 1

                    if not next_page_url or fetched_posts_count >= self.max_posts_per_collection:
                        break

                if post_tasks:
                    await asyncio.gather(*post_tasks)
            else:
                while True:
                    async with self.page_semaphore:
                        await asyncio.sleep(random.uniform(0.5, 2)) # Random jitter
                        page_html: str = await self.get(url if not next_page_url else next_page_url)

                    if not page_html:
                        break

                    try:
                        soup = WhiskeySour(page_html)
                    except AttributeError: # When the scraper force shuts down after reaching max results or the like
                        return
                    
                    faceplate_partials = soup.select("faceplate-partial[loading=lazy][src]")
                    next_page_el = None
                    
                    for el in faceplate_partials:
                        if "cursor=e" in el.get("src"):
                            next_page_el = el
                    
                    if next_page_el and "cursor=e" in page_html:
                        next_page_url = "https://www.reddit.com" + unescape(next_page_el.get("src")) if next_page_el else ""
                    else:
                        next_page_url = None

                    posts = soup.select('a[data-testid="post-title"]')
                    for post in posts:
                        if fetched_posts_count >= self.max_posts_per_collection:
                            break

                        if fetched_posts_count < self.max_posts_per_collection:
                            post_url = "https://www.reddit.com" + post.get("href")
                            post_tasks.append(asyncio.create_task(self.fetch_post(post_url, initial_page=True)))

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

                params = {"t": self.time_frame}

                raw_sub_name = initial_url.split("/r/")[-1].split("/")[0]
                final_url = f"https://www.reddit.com/r/{raw_sub_name}"

                if self.sort != "default":
                    final_url += f"/{self.sort}/"

                final_url += f"?{urlencode(params)}"

                tasks.append(self.fetch_collection(final_url))

            # Posts
            for url in self.post_urls:
                initial_url = url
                if "reddit.com" not in initial_url or "/comments/" not in initial_url:
                    continue

                final_url = initial_url.split("/comments/")[0] + "/comments/" + initial_url.split("/comments/")[-1].split("/")[0] + "/"
                final_url = final_url + initial_url.split(final_url)[-1].split("/")[0]
                tasks.append(self.fetch_post(final_url, initial_page=True))

            # Profiles
            for url in self.profile_urls:
                initial_url = url
                if "reddit.com" not in initial_url or ("/u/" not in initial_url and "/user/" not in initial_url):
                    continue

                params = {
                    "sort": self.sort if self.sort != "default" else "",
                    "t": self.time_frame
                }

                if "/u/" in initial_url:
                    final_url = initial_url.split("/u/")[0] + "/user/" + initial_url.split("/u/")[-1].split("/")[0] + f"/submitted/?{urlencode(params)}"
                elif "/user/" in initial_url:
                    final_url = initial_url.split("/user/")[0] + "/user/" + initial_url.split("/user/")[-1].split("/")[0] + f"/submitted/?{urlencode(params)}"

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


        
        runner = asyncio.create_task(run_all_tasks())
        results_count = 0

        try:
            while True:
                item: Tag = await self.items_queue.get()

                if isinstance(item, Exception):
                    raise item

                if item != "done":
                    if item["author"] in ["deleted", "[deleted]"]:
                        continue
                    
                    parsed_item = self.parse_item(item)
                    
                    if not parsed_item:
                        continue
                    
                    results_count += 1

                    if results_count > self.max_results:
                        break
                    else:
                        yield parsed_item
                else:
                    break
        finally:
            self.is_running = False
            
            try:
                await self.camoufox.__aexit__(None, None, None)
                self.interaction_task.cancel()
                runner.cancel()
            except (AttributeError, ValueError):
                pass
