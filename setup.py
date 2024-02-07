from setuptools import setup, find_packages

setup(
    name="ppe",
    version="0.0.1",
    author="Your Name",
    author_email="your_email@example.com",
    description="Description of your package",
    packages=find_packages(),
    install_requires=["pygame"],
    additional_requires={"dev": ["pytest", "black", "palettable"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
)
