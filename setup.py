from setuptools import setup, find_packages

setup(
    name="dakota-content-generator",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "httpx>=0.24.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.0",
        "structlog>=23.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dakota-generate=scripts.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Dakota",
    description="AI-powered content generation system for institutional investors",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)