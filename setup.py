from setuptools import setup, find_packages

with open("README.md", mode="r", encoding="utf-8") as f:
    description = f.read()

setup(
    name="reddrix",
    version="0.1.2",
    packages=find_packages(),
    install_requires=["camoufox[geoip]", "whiskeysour", "curl-cffi"],
    entry_points={
        "console_scripts": ["reddrix=reddrix.cli:main"]
    },
    long_description=description,
    long_description_content_type="text/markdown",
    description="Reddrix is an open-source, blazing fast Reddit Scraper for Python (No API Key)"
)
