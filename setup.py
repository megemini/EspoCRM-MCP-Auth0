from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="espocrm-mcp-auth0",
    version="0.1.0",
    author="megemini",
    author_email="megemini@outlook.com",
    description="EspoCRM MCP Server with Auth0 authentication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/megemini/EspoCRM-MCP-Auth0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
