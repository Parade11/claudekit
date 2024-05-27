from setuptools import setup, find_packages

setup(
    name="claudekit",
    version="0.1.0",
    description="Python toolkit for Claude API",
    author="chu2bard",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.18.0",
        "httpx>=0.25.0",
        "pydantic>=2.5.0",
    ],
)
