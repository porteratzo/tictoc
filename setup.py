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
    install_requires=[
        "matplotlib",
        "numpy",
        "scipy",
        "psutil",
    ],
    extras_require={},
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ],
    options={"": {"editable_mode": "compat"}},
)
