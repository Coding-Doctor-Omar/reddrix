from setuptools import setup, find_packages

with open("PYPI_README.md", mode="r", encoding="utf-8") as f:
    description = f.read()

setup(
    name="reddrix",
    version="1.2.9",
    packages=find_packages(),
    install_requires=["camoufox[geoip]", "whiskeysour", "wreq"],
    entry_points={
        "console_scripts": ["reddrix=reddrix.cli:main"]
    },
    long_description=description,
    long_description_content_type="text/markdown",
    description="Reddrix is an open-source, blazing-fast Reddit Scraper for Python (No Login or API Key)"
)
