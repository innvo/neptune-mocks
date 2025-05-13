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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "neptune-mocks=neptune.cli:main",
        ],
    },
) 