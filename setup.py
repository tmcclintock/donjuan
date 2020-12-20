import os

PATH_ROOT = os.path.dirname(__file__)
from setuptools import setup

import donjuan  # noqa: E402

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="donjuan",
    author="Tom McClintock",
    author_email="thmsmcclintock@gmail.com",
    version=donjuan.__version__,
    description=donjuan.__docs__,
    long_description=long_description,
    url="https://github.com/tmcclintock/PyDonJuan",
    packages=["donjuan"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
