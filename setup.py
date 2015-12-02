from setuptools import setup

setup(
    name = "dockdev",
    version = "0.4.0",
    author = "Ian Maddison",
    author_email = "ian.maddison@digital.cabinet-office.gov.uk",
    description = ("A simple development setup tool for docker containerised apps"),
    license = "MIT",
    keywords = "docker container development setup",
    url = "https://github.com/alphagov/dockdev",
    packages=['dockdev'],
    scripts=['bin/dockdev'],
    install_requires=['docker-py>=1.3.1', 'GitPython>=1.0.1'],
    long_description='See https://github.com/alphagov/dockdev/README.md',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
    ],
)
