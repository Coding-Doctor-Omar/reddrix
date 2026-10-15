<p align="center">
    <img src="./images/reddrix.png" width="350" alt="reddrix logo">
</p>

# Reddrix &mdash; An open-source, blazing-fast Reddit Scraper for Python (No API Key)

<p align="center"><h3>A powerful, async-first Reddit scraper (with built-in proxy support) for posts and comments with detailed metrics. No API key required. Scrape subreddits, profiles, and specific posts, or search Reddit site-wide by keywords or domains. Collect rich, structured data including authors, scores, timestamps, flairs, comment threads, and more (30+ fields).</h3></p>

<p align="center" class="badges">
    <a href="https://pypi.org/project/reddrix/">
        <img src="https://img.shields.io/badge/pypi-v0.2.4-orange.svg" alt="pypi package logo">
    </a>
    <a href="https://pypi.org/project/reddrix/">
        <img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="python versions badge">
    </a>
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="license">
    <a href="https://github.com/Coding-Doctor-Omar/reddrix/stargazers">
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

> If this repo is useful to you or saved your time, consider starring ⭐ it to support me and help others find it and have an easier time scraping Reddit ❤️.

> Need a hosted version? Check [Reddit Scraper Pro](https://apify.com/coding-doctor-omar/Reddit-Scraper-Pro) on Apify.

<p align="center">
    <a href="#installation">Installation</a> • <a href="#quickstart">Quickstart</a> • <a href="#features">Features</a> • 
    <a href="#output-dataset">Output Dataset</a> • <a href="#reddrix-arguments-options">Reddrix Arguments Options</a>
</p>

## Installation

```bash
pip install -U reddrix

reddrix install # Mandatory for installing the Camoufox dependency.
```

## Quickstart

**Using Async Context Manager:**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        mode="standard",
        subreddit_urls=[
            "https://www.reddit.com/r/webscraping",
            # URLs of specific subreddits to include when scraping posts and comments
            # Add as many as you want
        ],
        profile_urls=[], # URLs of specific profiles to include when scraping posts and comments; add as many as you want. Only public data is scraped
        post_urls=[], # URLs of specific posts to include in the scraping; add as many as you like
        sort="new",
        include_comments=True,
        max_results=500,
        max_posts_per_collection=500,
        verbose=True
    ) as reddrix:
        async for item in reddrix.get_items():
            # item is a Python dictionary with more than 30 keys.
            print(item["submissionType"], item["submissionUrl"])

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
        # item is a Python dictionary with more than 30 keys.
        print(item["submissionType"], item["submissionUrl"])
    
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
            # item is a Python dictionary with more than 30 keys.
            print(item["submissionType"], item["submissionUrl"])

if __name__ == "__main__":
    asyncio.run(main())
```

**Scraping Posts and Comments Based on Domains:**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        mode="domain_search",
        sort="new",
        domains=["github.com", "apify.com"],
        include_comments=True,
        max_results=500,
        max_posts_per_collection=500,
        verbose=True
    ) as reddrix:
        async for item in reddrix.get_items():
            # item is a Python dictionary with more than 30 keys.
            print(item["submissionType"], item["submissionUrl"])

if __name__ == "__main__":
    asyncio.run(main())
```



**Using Reddrix as a standalone Reddit http client for your custom scraping setup (random jitter between requests does not apply when using the get method directly, so you'll need to use your own logic here, or use the preset scraping setup shown above):**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix() as reddrix:
        json_data = await reddrix.get("https://www.reddit.com/r/webscraping.json")
        html_content = await reddrix.get(
            url="https://www.reddit.com/search?q=how+to+scrape+reddit",
            expected_data_type="HTML/XML" # You must specify the data type if you want to fetch html or xml.
        )

if __name__ == "__main__":
    asyncio.run(main())
```

**Using Reddrix with Proxies:**

```python
from reddrix import Reddrix
import asyncio

async def main():
    async with Reddrix(
        # Your normal arguments above ...,
        proxies=[
            "scheme://user:pass@hostname:port",
            "scheme://user2:pass2@hostname2:port2",
            # Add as many as you want, and Reddrix automatically rotates between them...
        ]
    ) as reddrix:
        async for item in reddrix.get_items():
            # item is a Python dictionary with more than 30 keys.
            print(item["submissionType"], item["submissionUrl"])

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- 🚀 **Async-First:** High-performance asynchronous scraping with `asyncio` and an async iterator for streaming results.
- 🔑 **No API Key Required:** Scrape Reddit without requiring an API key.
- 🔍 **Multiple Search Modes:** Scrape subreddits, user profiles, and specific posts, or search Reddit by keywords and domains.
- 💬 **Comprehensive Data Extraction:** Collect posts and comments with 30+ structured fields, including authors, scores, timestamps, flairs, media URLs, and comment thread metadata.
- 🌐 **Intelligent Scraping:** Even though Reddrix uses the Camoufox browser under the hood, it uses intelligent fetching via `page.evaluate()` with JS fetch to preserve the scraping speed (no navigation, no DOM parsing, no JS rendering, except for the occasional cookie refreshes). 
- 🛡️ **Resilient Scraping:** Built-in retries, cookie renewal, and configurable proxies.
- ⚙️ **Fine-Grained Control:** Configure sorting, time frames, result limits, comment depth, and comment counts.
- 🧩 **Standalone HTTP Client:** Use Reddrix's asynchronous `get()` method in your own custom scraping workflows.
- 🐍 **Pythonic API:** Manage scraper resources with an async context manager or explicit `start()` and `stop()` methods.

## Output Dataset

If you use the preset scraping setup from `async for item reddrix.get_items()`, each `item` is a Python dictionary with more than 30 keys.

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
  "isCrosspost": False,
  "crosspostParentId": None,
  "crosspostParentUrl": None,
  "title": "Is this good improvement for 10 hours of dedicated study + need help for rw section",
  "bodyText": "math significantly improved but reading writing is too tough for me (international student)\n\nplease help, i have to give the sat in two months, will reading novels improve my rw score?",
  "isEdited": False,
  "author": "stcer",
  "authorFlairText": None,
  "authorFlairImageUrl": None,
  "depth": None,
  "postFlair": None,
  "isNSFW": False,
  "subreddit": "r/Sat",
  "score": 32,
  "upvoteRatio": 0.98,
  "numComments": 29,
  "numCrossposts": 0,
  "externalUrl": "https://i.redd.it/cjhezz5bs9mh1.jpeg",
  "thumbnailUrl": None,
  "videoUrl": None,
  "imageUrl": "https://i.redd.it/cjhezz5bs9mh1.jpeg",
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
  "isCrosspost": False,
  "crosspostParentId": None,
  "crosspostParentUrl": None,
  "title": None,
  "bodyText": "How did you do that in 10 hours? Can you please give me the sources that you used? I also need help in rw section and I’ll take the sat in 2 weeks",
  "isEdited": False,
  "author": "AnalysisStill4932",
  "authorFlairText": None,
  "authorFlairImageUrl": None,
  "depth": 0,
  "postFlair": None,
  "isNSFW": False,
  "subreddit": "r/Sat",
  "score": 9,
  "upvoteRatio": None,
  "numComments": None,
  "numCrossposts": None,
  "externalUrl": None,
  "thumbnailUrl": None,
  "videoUrl": None,
  "imageUrl": None,
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
9. `postType` &mdash; [`string`, `None`] The post type. Can be any of `text`, `poll`, `link`, `image`, `gallery`, or `video`. For comments, this field will always be `None`.
10. `isCrosspost` &mdash; [`boolean`] Whether the post is a crosspost.
11. `crosspostParentId` &mdash; [`string`, `None`] The ID of the parent of the crosspost (for posts that are not crossposts, will be `None`).
12. `crosspostParentUrl` &mdash; [`string`, `None`] The URL of the parent of the crosspost (for posts that are not crossposts, will be `None`).
13. `title` &mdash; [`string`, `None`] The post title (will always be `None` for comments).
14. `bodyText` &mdash; [`string`, `None`] The main text content of a post or comment.
15. `isEdited` &mdash; [`boolean`] Whether the post or comment is edited.
16. `author` &mdash; [`string`] The author of the post or comment.
17. `authorFlairText` &mdash; [`string`, `None`] The text content of the author flair or a text version of it.
18. `authorFlairImageUrl` &mdash; [`string`, `None`] The URL for the image in an author flair.
19. `depth` &mdash; [`integer`, `None`] The comment depth (top-level comments have a depth of `0` and posts have a depth of `None`).
20. `postFlair` &mdash; [`string`, `None`] The post flair (will be `None` for comments).
21. `isNSFW` &mdash; [`boolean`] Whether the post or comment is NSFW.
22. `subreddit` &mdash; [`string`, `None`] The subreddit in which the post or comment was submitted.
23. `score` &mdash; [`integer`, `None`] The vote score of the post or comment.
24. `upvoteRatio` &mdash; [`float`, `None`] The ratio of upvotes to total number of votes of a post (always `None` for comments).
25. `numComments` &mdash; [`integer`, `None`] The number of comments in a post (always `None` for comments).
26. `numCrossposts` &mdash; [`integer`, `None`] The number of crossposts for a post (always `None` for comments).
27. `externalUrl` &mdash; [`string`, `None`] The external URL in a post. For comments, this field will be `None` because external URLs will be included in the `bodyText` anyway.
28. `thumbnailUrl` &mdash; [`string`, `None`] The thumbnail image URL for `video`, `image`, and `gallery` post types (always `None` for any other submission).
29. `videoUrl` &mdash; [`string`, `None`] The URL for the video in a post (always `None` for any submission other than `video` posts).
30. `imageUrl` &mdash; [`string`, `None`] The URL for the image in a post (always `None` for any submission other than `image` posts).
31. `galleryImagesUrls` &mdash; [`list`] A list of URLs for all images in a gallery (always empty for any submission other than `gallery` posts).

## Reddrix Arguments Options

1. `mode` (string) &mdash; One of `standard`, `keyword_search`, and `domain_search`. Default is `standard`.
2. `http_client` (string) &mdash; One of `curl_cffi` and `camoufox`. Default is `curl_cffi`.
3. `max_results` (integer) &mdash; The maximum total number of items (posts and comments combined) to return across all sources. Default is `999999`.
4. `max_posts_per_collection` (integer) &mdash; The maximum number of posts to scrape from each collection. A collection is a single subreddit, profile, keyword search, or domain. Default is `999999`.
5. `sort` (string) &mdash; One of `default`, `new`, and `hot`. Applies to subreddits, profiles, and `domain_search`. This option is ignored in `keyword_search` mode, which always uses Reddit's relevance sorting. Default is `default`.
6. `time_frame` (string) &mdash; One of `all_time`, `past_hour`, `today`, `past_week`, `past_month`, and `past_year`. Used in `standard` mode for subreddits and profiles, and ignored in `keyword_search` and `domain_search` modes. Default is `all_time`.
7. `subreddit_urls` (list of strings) &mdash; Subreddit URLs to scrape, e.g. `["https://www.reddit.com/r/webscraping"]`. Used in `standard` mode only. URLs that are not valid subreddit URLs are skipped. Default is `[]`.
8. `post_urls` (list of strings) &mdash; Specific post URLs to scrape, e.g. `["https://www.reddit.com/r/webscraping/comments/abc123/post_title/"]`. Used in `standard` mode only. URLs that are not valid post URLs are skipped. Default is `[]`.
9. `profile_urls` (list of strings) &mdash; User profile URLs to scrape the submitted posts of, e.g. `["https://www.reddit.com/user/username"]`. Both `/user/` and `/u/` URLs are supported. Used in `standard` mode only. URLs that are not valid profile URLs, or those of profiles that are deleted, banned, or hiding their content, are skipped. Default is `[]`.
10. `domains` (list of strings) &mdash; Domains to search for in Reddit posts that link to them, e.g. `["github.com", "apify.com"]`. Used in `domain_search` mode only. Default is `[]`.
11. `query` (string) &mdash; The search keywords to look up site-wide on Reddit. Used in `keyword_search` mode only. Default is `None`.
12. `include_comments` (boolean) &mdash; Whether to scrape the comments of each post in addition to the post itself. Comments are returned as separate items with `submissionType` set to `comment`. Default is `False`.
13. `max_comments_depth` (integer) &mdash; The maximum comment depth to scrape. Top-level comments have a depth of `0`, their replies have a depth of `1`, and so on. Only applies if `include_comments` is `True`. Default is `10`.
14. `max_comments_per_post` (integer) &mdash; The maximum total number of comments (top-level comments and replies) to scrape per post. Only applies if `include_comments` is `True`. Default is `999999`.
15. `max_top_comments_per_post` (integer) &mdash; The maximum number of top-level comments (depth `0`) to scrape per post. Only applies if `include_comments` is `True`. Default is `999999`.
16. `proxies` (list of strings) &mdash; A list of proxy URLs in the format `scheme://user:pass@hostname:port`. Reddrix rotates through them automatically, picking an unused proxy first and reusing proxies only after the whole list has been used. Default is `[]` (no proxy).
17. `verbose` (boolean) &mdash; Whether to print timestamped log messages (initialization, retries, etc.) to the console. Default is `False`.

## Star History

<a href="https://www.star-history.com/?repos=Coding-Doctor-Omar%2Freddrix&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=Coding-Doctor-Omar/reddrix&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=Coding-Doctor-Omar/reddrix&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=Coding-Doctor-Omar/reddrix&type=date&legend=top-left" />
 </picture>
</a>