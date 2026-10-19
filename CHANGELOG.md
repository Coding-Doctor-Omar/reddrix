## v1.1.2 (Oct. 19, 2026)

1. Change the `depth` for comments to be an `integer` instead of a `string`.
2. Fix comment scraping bug that caused the scraper to not load "more comments".

## v1.1.1 (Oct. 19, 2026)

1. Fix edge case where post urls with special characters fail.

## v1.1.0 (Oct. 19, 2026)

1. Fix pagination bug that caused the scraper to keep stuck in the last page.

## v1.0.2 (Oct. 19, 2026)

1. CSS selector enhancement for post tags.

## v1.0.1 (Oct. 18, 2026)

1. Remove forgotten debug statement.

## v1.0.0 (Oct. 18, 2026)

1. Remove `http_client`, `domains`, and `time_frame` parameters from the `Reddrix` class.
2. Remove `isCrosspost`, `isEdited`, `authorFlairText`, `authorFlairImageUrl`, `isNSFW` (inside `tags`), `imageUrl` (will be the `externalUrl`), and `videoUrl` (will be the `externalUrl`) dataset fields.
3. Replace `curl-cffi` dependency with `wreq`.
4. Add `top_all_time`, `top_past_hour`, `top_today`, `top_past_week`, `top_past_month`, and `top_past_year` argument options to the `sort` parameter in the `Reddrix` class.
5. Add `tags` field to the dataset (includes tags such as `Spoiler`, `NSFW`, etc) and `crosspost` to the `postType` field.
6. Redesign Reddrix completely to make it no longer rely on JSON endpoints and to make it once again a no-login scraper.
7. The standalone `get` method no longer supports JSON. It only supports HTML or XML (no more `expected_data_type` parameter).

## v0.2.7 (Oct. 16, 2026)

1. Avoid using Camoufox fingerprint presets for more fingerprint variety.

## v0.2.6 (Oct. 16, 2026)

1. Allow users to supply custom Reddit credentials in env vars.
2. Bring back the `curl_cffi` argument for the `http_client` parameter.

## v0.2.5 (Oct. 16, 2026)

1. Fix pagination bug in `keyword_search` mode that caused the scraper to stop at 7 results.

## v0.2.4 (Oct. 15, 2026)

1. Fix typo in `Reddrix.refresh_cookies()`.

## v0.2.3 (Oct. 15, 2026)

1. Update cookie refresh intervals and selector timeouts.

## v0.2.2 (Oct. 15, 2026)

1. Prevent false errors from appearing at the end of runs.

## v0.2.1 (Oct. 15, 2026)

1. Fix minor bug that caused `AttributeError` in scraper initialization.

## v0.2.0 (Oct. 15, 2026)

1. `curl_cffi` http client is deprecated. Only `camoufox` will be used now.
2. Upgrade Reddrix in certain ways to circumvent the new anti-scraping measures.

## v0.1.7 (Oct. 14, 2026)

1. Allow CLI commands to be executed from outside a virtual environment and not just from inside via `python -m reddrix install` (Windows) or `python3 -m reddrix install` (Linux/MacOS).

## v0.1.6 (Oct. 12, 2026)

1. Change the `reddrix install` CLI command to only install Camoufox if the latest version is not already installed.

## v0.1.5 (Oct. 12, 2026)

1. Fix TypeError that occurred when using `camoufox` as the `http_client` argument for `Reddrix` without proxies.

## v0.1.3 (Oct. 12, 2026)

1. Fix cookie refresh bug from wrong attribute name in the `auto_retry` decorator.