from setuptools import setup, find_packages

setup(
    name="grocery-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot",
        "aiohttp",
        "beautifulsoup4",
        "lxml",
        "aiosqlite",
        "pydantic",
        "python-dotenv",
    ],
    python_requires=">=3.10",
)