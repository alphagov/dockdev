import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "dockdev",
    version = "0.1.0",
    author = "Ian Maddison",
    author_email = "ian.maddison@digital.cabinet-office.gov.uk",
    description = ("A simple development setup tool for docker containerised apps"),
    license = "MIT",
    keywords = "docker container development setup",
    url = "http://packages.python.org/dockdev",
    packages=['dockdev'],
    scripts=['bin/dockdev'],
    install_requires=['docker-py', 'GitPython'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
    ],
)