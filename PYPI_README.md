<p align="center">
    <img src="https://raw.githubusercontent.com/Coding-Doctor-Omar/reddrix/main/images/reddrix.png" width="350" alt="reddrix logo">
</p>

# Reddrix &mdash; An open-source, blazing-fast Reddit Scraper for Python (No Login or API Key)

<p align="center"><h3>A powerful, async-first Reddit scraper (with built-in proxy support) for posts and comments with detailed metrics (no login or API key). Scrape subreddits, profiles, and specific posts, or search Reddit site-wide by keywords. Collect rich, structured data including authors, scores, timestamps, post flairs, full comment threads, and more (24+ fields).</h3></p>

<p align="center" class="badges">
    <a href="https://pypi.org/project/reddrix/">
        <img src="https://img.shields.io/badge/pypi-v1.2.13-orange.svg" alt="pypi package logo">
    </a>
    <a href="https://pypi.org/project/reddrix/">
        <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="python versions badge">
    </a>
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
    <a href="https://img.shields.io/github/stars/Coding-Doctor-Omar/reddrix?style=flat">
        <img src="https://img.shields.io/github/stars/Coding-Doctor-Omar/reddrix?style=flat">
    </a>
    <a href="https://pypistats.org/packages/reddrix">
        <img src="https://img.shields.io/pypi/dw/reddrix">
    </a>
    <img src="https://img.shields.io/github/last-commit/Coding-Doctor-Omar/reddrix" alt="last commit badge">
    <a href="https://ko-fi.com/CodingDoctorOmar" target="_blank" rel="noopener noreferrer">
        <img src="https://img.shields.io/badge/Ko--fi-Support%20me-ff5e5b?style=flat&logo=ko-fi" alt="Ko-Fi" />
    </a>
</p>

> If this Python package is useful to you or saved you time, consider starring the [GitHub repository](https://github.com/Coding-Doctor-Omar/reddrix) ⭐ to support me and help other find it and have an easier time scraping Reddit ❤️.

<p align="center">
    <a href="#installation">Installation</a> • <a href="#quickstart">Quickstart</a> • <a href="#features">Features</a> • 
    <a href="#output-dataset">Output Dataset</a> • <a href="#reddrix-arguments-options">Reddrix Arguments Options</a>
</p>

> [!TIP]
> Reddrix works best with the `stealth=True` argument (see below). This argument is the default argument, unless you choose to switch it off.

## Installation

```bash
pip install -U reddrix
```
```bash
reddrix install # Mandatory for installing the Camoufox browser.
```

**For Docker, ensure you include the following in the Dockerfile:**

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      unzip ca-certificates fonts-liberation curl \
      libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
      libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
```

## Quickstart

**Using Async Context Manager:**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        mode="standard",
        subreddit_urls=["https://www.reddit.com/r/webscraping"],
        post_urls=[],
        profile_urls=[],
        include_comments=True,
        max_results=500,
        verbose=True
    ) as reddrix:
        async for item in reddrix.get_items():
            # item is a Python dictionary with 24 keys.
            print(reddrix.results_count, item["submissionType"], item["submissionUrl"])

if __name__ == "__main__":
    asyncio.run(main())
```

**Without the context manager:**

```python
from reddrix import Reddrix
import asyncio

async def main():
    reddrix = Reddrix(
        mode="standard",
        subreddit_urls=["https://www.reddit.com/r/webscraping"],
        sort="new",
        include_comments=True,
        max_results=500,
        max_posts_per_collection=500,
        verbose=True
    )
    await reddrix.start()
    
    async for item in reddrix.get_items():
        # item is a Python dictionary with 24 keys.
        print(reddrix.results_count, item["submissionType"], item["submissionUrl"])
    
    await reddrix.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

**Scraping Posts and Comments Based on Keywords (uses Reddit's current shreddit search engine):**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        mode="keyword_search",
        sort="new", # The sort option is ignored for this mode
        query="how to scrape reddit",
        include_comments=True,
        max_results=500,
        max_posts_per_collection=500,
        verbose=True
    ) as reddrix:
        async for item in reddrix.get_items():
            # item is a Python dictionary with 24 keys.
            print(reddrix.results_count, item["submissionType"], item["submissionUrl"])

if __name__ == "__main__":
    asyncio.run(main())
```

**Using Reddrix as a standalone Reddit http client for your custom scraping setup (has both GET and POST methods):**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix() as reddrix:
        html_content = await reddrix.get(
            url="https://www.reddit.com/search/",
            params={"q": "how to scrape reddit"}
        ) # Only HTML/XML is supported
        
        print(html_content)

if __name__ == "__main__":
    asyncio.run(main())
```

> [!TIP]
> Random request jittering does not apply when using the GET and POST methods directly, so use your own jittering in this case, or just use the preset scraping setup shown above.

**Using Reddrix with Proxies:**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        # Your normal arguments above ...,
        proxies=[
            "scheme://user:pass@hostname:port",
            "scheme2://user2:pass2@hostname2:port2",
            # Add as many as you want, and Reddrix automatically rotates between them...
        ]
    ) as reddrix:
        # Rest of the code as usual...

if __name__ == "__main__":
    asyncio.run(main())
```

## Stealth Mode

The stealth mode has 3 options: `True`, `False`, and `adaptive`.

**Why is it needed?**

Reddrix no longer relies on Reddit's legacy JSON endpoints, since these endpoints are now behind login walls. Instead, it scrapes New Reddit's HTML and internal API endpoints, and these are protected by Cloudflare and reCaptcha Enterprise.

**How It Works:**

When stealth is set to `True` (the default option), Reddrix will open Camoufox, navigate to an empty sub page to harvest cookies, then will start scraping by sending direct HTTP requests to Reddit's internal API endpoints from within the same Camoufox browser context using JavaScript fetch (no navigation, no clicking). While firing these requests, Reddrix will initialize randomized mouse movements with random delays and human-like patterns in the loaded page. This approach avoids the fingerprint drift between the browser and the wreq client by sending the HTTP requests from the same browser. Additionally, the random mouse movements constantly generate reCaptcha Enterprise clearances, ensuring the session remains trusted and lasts a long time while still preserving most of the scraping speed.

Without the stealth mode, Reddrix will still work, but there will be a slightly higher chance of getting detected.

**Disadvantage:**

The disadvantage is heavy resource usage.

*If this option is set to `adaptive`, it will only be activated when `include_comments` is set to `True`, since comments are often more protected by anti-bot measures.*

Example Code:

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        stealth=True, # Default is True, but can also be set to False or "adaptive"
        # Rest of the arguments as usual...
    ) as reddrix:
        # Rest of the code as usual

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- 🚀 **Async-First:** High-performance asynchronous scraping with `asyncio` and an async iterator for streaming results.
- 🥷 **Adaptive Stealth**: Optionally enable the `stealth` mode for intelligent, highly undetectable scraping.
- 🔑 **No Login or API Key**: Scrape Reddit seamlessly without logging in or providing an API key.
- 🔍 **Multiple Search Modes:** Scrape subreddits, user profiles, and specific posts, or search Reddit by keywords.
- 💬 **Comprehensive Data Extraction:** Collect posts and comments with 24+ structured fields, including authors, scores, timestamps, flairs, media URLs, and FULL comment threads (no depth limit).
- 🛡️ **Resilient Scraping:** Built-in retries, cookie renewal, request jittering, and configurable proxies.
- ⚙️ **Fine-Grained Control:** Configure sorting, time frames, result limits, comment depth, and comment counts.
- 🧩 **Standalone HTTP Client:** Use Reddrix's asynchronous `get()` or `post()` method in your own custom scraping workflows.
- 🐍 **Pythonic API:** Manage scraper resources with an async context manager or explicit `start()` and `stop()` methods.

## Output Dataset

If you use the preset scraping setup from `async for item reddrix.get_items()`, each `item` is a Python dictionary with 24 keys.

**Example Reddit Post Output:**

```python
{
  "submissionId": "1w1gc8p",
  "submissionIdPrefixed": "t3_1w1gc8p",
  "submissionType": "post",
  "submissionUrl": "https://www.reddit.com/r/Sat/comments/1w1gc8p/is_this_good_improvement_for_10_hours_of/",
  "submittedAt": "2026-08-29T07:53:42+00:00",
  "parentId": None,
  "parentPostId": None,
  "parentPostUrl": None,
  "postType": "image",
  "crosspostParentId": None,
  "crosspostParentUrl": None,
  "title": "Is this good improvement for 10 hours of dedicated study + need help for rw section",
  "bodyText": "math significantly improved but reading writing is too tough for me (international student)\n\nplease help, i have to give the sat in two months, will reading novels improve my rw score?",
  "author": "stcer",
  "depth": None,
  "postFlair": None,
  "tags": [],
  "subreddit": "r/Sat",
  "score": 32,
  "upvoteRatio": 0.98,
  "numComments": 29,
  "numCrossposts": 0,
  "externalUrl": "https://i.redd.it/cjhezz5bs9mh1.jpeg",
  "galleryImagesUrls": []
}
```

**Example Comment Output:**

```python
{
  "submissionId": "p6lwobb",
  "submissionIdPrefixed": "t1_p6lwobb",
  "submissionType": "comment",
  "submissionUrl": "https://www.reddit.com/r/Sat/comments/1w1gc8p/is_this_good_improvement_for_10_hours_of/p6lwobb/",
  "submittedAt": "2026-08-29T13:41:52+00:00",
  "parentId": "t3_1w1gc8p",
  "parentPostId": "t3_1w1gc8p",
  "parentPostUrl": "https://www.reddit.com/r/Sat/comments/1w1gc8p",
  "postType": None,
  "crosspostParentId": None,
  "crosspostParentUrl": None,
  "title": None,
  "bodyText": "How did you do that in 10 hours? Can you please give me the sources that you used? I also need help in rw section and I’ll take the sat in 2 weeks",
  "author": "AnalysisStill4932",
  "depth": 0,
  "postFlair": None,
  "tags": [],
  "subreddit": "r/Sat",
  "score": 9,
  "upvoteRatio": None,
  "numComments": None,
  "externalUrl": None,
  "thumbnailUrl": None,
  "galleryImagesUrls": []
}
```
**Output Fields Explanation:**

1. `submissionId` &mdash; [`string`] The ID of the post or comment.
2. `submissionIdPrefixed` &mdash; [`string`] The prefixed ID of the post or comment.
3. `submissionType` &mdash; [`string`] Whether the submission is a `post` or `comment`.
4. `submissionUrl` &mdash; [`string`] The URL for the submission.
5. `submittedAt` &mdash; [`string`] The date and time the post or comment was submitted in UTC timezone and ISO format.
6. `parentId` &mdash; [`string`, `None`] The ID of the direct parent post or comment.
7. `parentPostId` &mdash; [`string`, `None`] The ID of the parent post. For posts, this field will always be `None` since posts have no parent.
8. `parentPostUrl` &mdash; [`string`, `None`] The URL of the parent post. For posts, this field will always be `None` since posts have no parent.
9. `postType` &mdash; [`string`, `None`] The post type. Can be any of `text`, `poll`, `link`, `crosspost`, `image`, `gallery`, or `video`. For comments, this field will always be `None`.
10. `crosspostParentId` &mdash; [`string`, `None`] The ID of the parent of the crosspost (for posts that are not crossposts, will be `None`).
11. `crosspostParentUrl` &mdash; [`string`, `None`] The URL of the parent of the crosspost (for posts that are not crossposts, will be `None`).
12. `title` &mdash; [`string`, `None`] The post title (will always be `None` for comments).
13. `bodyText` &mdash; [`string`, `None`] The main text content of a post or comment.
14. `author` &mdash; [`string`] The author of the post or comment.
15. `depth` &mdash; [`integer`, `None`] The comment depth (top-level comments have a depth of `0` and posts have a depth of `None`).
16. `postFlair` &mdash; [`string`, `None`] The post flair (will be `None` for comments).
17. `tags` &mdash; [`list`]  A list of the tags for the post (always empty for comments).
18. `subreddit` &mdash; [`string`, `None`] The subreddit in which the post or comment was submitted.
19. `score` &mdash; [`integer`, `None`] The vote score of the post or comment.
20. `upvoteRatio` &mdash; [`float`, `None`] The ratio of upvotes to total number of votes of a post (always `None` for comments).
21. `numComments` &mdash; [`integer`, `None`] The number of comments in a post (always `None` for comments).
22. `externalUrl` &mdash; [`string`, `None`] The external URL in a post. For comments, this field will be `None` because external URLs will be included in the `bodyText` anyway.
23. `thumbnailUrl` &mdash; [`string`, `None`] The thumbnail image URL for `video`, `image`, and `gallery` post types (always `None` for any other submission).
24. `galleryImagesUrls` &mdash; [`list`] A list of URLs for all images in a gallery (always empty for any submission other than `gallery` posts).

## Reddrix Arguments

1. `mode` (string) &mdash; Either `standard` or `keyword_search`. Default is `standard`.
2. `stealth` (string or boolean) &mdash; Whether to use the stealth mode (explained above) in scraping. Default is `True`.
3. `max_results` (integer) &mdash; The maximum total number of items (posts and comments combined) to return across all sources. Default is `999999`.
4. `max_posts_per_collection` (integer) &mdash; The maximum number of posts to scrape from each collection. A collection is a single subreddit, profile, keyword search, or domain. Default is `999999`.
5. `sort` (string) &mdash; One of `default`, `new`, `hot`, `top_all_time`, `top_past_hour`, `top_today`, `top_past_week`, `top_past_month`, and `top_past_year`. Applies to subreddits and profiles. This option is ignored in `keyword_search` mode, which always uses Reddit's relevance sorting. Default is `default`.
6. `subreddit_urls` (list of strings) &mdash; Subreddit URLs to scrape, e.g. `["https://www.reddit.com/r/webscraping"]`. Used in `standard` mode only. URLs that are not valid subreddit URLs are skipped. Default is `[]`.
7. `post_urls` (list of strings) &mdash; Specific post URLs to scrape, e.g. `["https://www.reddit.com/r/webscraping/comments/abc123/post_title/"]`. Used in `standard` mode only. URLs that are not valid post URLs are skipped. Default is `[]`.
8. `profile_urls` (list of strings) &mdash; User profile URLs to scrape the submitted posts of, e.g. `["https://www.reddit.com/user/username"]`. Both `/user/` and `/u/` URLs are supported. Used in `standard` mode only. URLs that are not valid profile URLs, or those of profiles that are deleted, banned, or hiding their content, are skipped. Default is `[]`.
9.  `query` (string) &mdash; The search keywords to look up site-wide on Reddit. Used in `keyword_search` mode only. Default is `None`.
10. `include_comments` (boolean) &mdash; Whether to scrape the comments of each post in addition to the post itself. Comments are returned as separate items with `submissionType` set to `comment`. Default is `False`.
11. `max_comments_depth` (integer) &mdash; The maximum comment depth to scrape. Top-level comments have a depth of `0`, their replies have a depth of `1`, and so on. Only applies if `include_comments` is `True`. Default is `999999`.
12. `max_comments_per_post` (integer) &mdash; The maximum total number of comments (top-level comments and replies) to scrape per post. Only applies if `include_comments` is `True`. Default is `999999`.
13. `max_top_comments_per_post` (integer) &mdash; The maximum number of top-level comments (depth `0`) to scrape per post. Only applies if `include_comments` is `True`. Default is `999999`.
14. `proxies` (list of strings) &mdash; A list of proxy URLs in the format `scheme://user:pass@hostname:port`. Reddrix rotates through them automatically, picking an unused proxy first and reusing proxies only after the whole list has been used. Default is `[]` (no proxy).
15. `verbose` (boolean) &mdash; Whether to print timestamped log messages (initialization, retries, etc.) to the console. Default is `False`.

## Star History

<a href="https://www.star-history.com/?repos=Coding-Doctor-Omar%2Freddrix&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=Coding-Doctor-Omar/reddrix&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=Coding-Doctor-Omar/reddrix&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=Coding-Doctor-Omar/reddrix&type=date&legend=top-left" />
 </picture>
</a>