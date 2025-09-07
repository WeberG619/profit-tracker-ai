"""
Setup configuration for Profit Tracker AI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="profit-tracker-ai",
    version="1.0.0",
    author="Profit Tracker AI",
    author_email="support@profit-tracker-ai.com",
    description="AI-powered receipt processing and profit tracking for trade businesses",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WeberG619/profit-tracker-ai",
    packages=find_packages(exclude=["tests", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "isort>=5.13.2",
            "flake8>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "profit-tracker=app.create_app:create_app",
        ],
    },
)