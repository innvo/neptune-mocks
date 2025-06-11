I'll help you create a proper Python package structure that can be imported and added to requirements.txt. First, let me check the current project structure.
Let me check the current requirements.txt to see what dependencies are already listed.
I'll help you create a proper Python package structure. Here's what we'll do:
Create a proper package structure with setup.py
Move the existing code into the package
Update requirements.txt
First, let's create a setup.py file:

from setuptools import setup, find_packages

setup(
    name="neptune-mocks",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.0.0",
        "tqdm>=4.65.0",
        "faker>=19.0.0",
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "boto3>=1.34.0",
        "requests>=2.31.0",
    ],
    python_requires=">=3.8",
    author="Eric Chasin",
    description="A package for generating mock data for Neptune",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
) 

Now, let's create an __init__.py file in the src directory to make it a proper Python package:

"""
Neptune Mocks - A package for generating mock data for Neptune
"""

__version__ = "0.1.0"

Now, let's update the requirements.txt to include the package in development mode:

```
pandas>=2.0.0
tqdm>=4.65.0
faker>=19.0.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
boto3>=1.34.0
requests>=2.31.0
-e . 
```
