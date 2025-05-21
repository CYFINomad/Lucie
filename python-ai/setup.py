from setuptools import setup, find_packages
import os

# Read requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Read the README for the long description
with open("../README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="lucie-ai",
    version="0.1.0",
    author="Lucie Team",
    author_email="your-email@example.com",
    description="Python AI services for Lucie personal assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Lucie",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "lucie-api=api.main:start_server",
            "lucie-grpc=grpc.server:start_server",
        ],
    },
)
