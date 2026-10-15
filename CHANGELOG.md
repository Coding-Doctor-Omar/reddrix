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