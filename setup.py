import os

PATH_ROOT = os.path.dirname(__file__)
from setuptools import setup

import donjuan  # noqa: E402

setup(
    name="Donjuan",
    author="Tom McClintock",
    author_email="thmsmcclintock@gmail.com",
    version=donjuan.__version__,
    description=donjuan.__docs__,
    url="https://github.com/tmcclintock/PyDonJuan",
    packages=["donjuan"],
)
