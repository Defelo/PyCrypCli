from setuptools import setup, find_packages
from os import environ

setup(
    name="PyCrypCli",
    version=environ["VERSION"],
    url="https://github.com/Defelo/PyCrypCli",
    author="Defelo",
    author_email="elodef42@gmail.com",
    description="Python Cryptic Game Client",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        'console_scripts': ['pycrypcli=PyCrypCli.pycrypcli:main']
    }
)
