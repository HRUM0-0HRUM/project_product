from setuptools import setup, find_packages

setup(
    name="grocery-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.7",
        "aiohttp==3.9.1",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "sphinx==7.4.6",
    ],
    python_requires=">=3.10",
)