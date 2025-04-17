from setuptools import setup, find_packages

setup(
    name="neptune_gremlin_converter",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    author="Your Name",
    author_email="your.email@example.com",
    description="A utility to convert Neptune Gremlin results to OpenCypher format",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/neptune_gremlin_converter",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 