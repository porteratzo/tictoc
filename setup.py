import setuptools
from setuptools import setup

setup(
    name="porter_bench",
    version="0.1.0",
    description="Scripts for benchmarking",
    url="https://github.com/porteratzo/porter_bench",
    author="Omar Montoya",
    author_email="omar.alfonso.montoya@hotmail.com",
    license="MIT License",
    packages=setuptools.find_packages(),
    python_requires=">=3.10,<3.13",
    install_requires=[
        "matplotlib>=3.8.0,<4.0.0",
        "numpy>=1.24.0,<3.0.0",
        "scipy>=1.10.0,<2.0.0",
        "psutil>=5.9.0,<6.0.0",
        "pandas>=2.0.0,<3.0.0",
    ],
    extras_require={
        "examples": [
            "torch>=2.0.0",
            "tqdm>=4.65.0",
        ],
        "dev": [
            "black>=24.1.1",
            "isort>=5.13.2",
            "flake8>=7.0.0",
            "flake8-docstrings>=1.7.0",
            "pylint>=3.0.0",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    options={"": {"editable_mode": "compat"}},
)
