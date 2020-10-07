#!/usr/bin/env python

import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(HERE, "README.md")).read()
CHANGES = open(os.path.join(HERE, "CHANGES.md")).read()

test_require = [
    "django-filter",
    "factory-boy",
    "flake8",
    "coverage",
    "django-geostore",
]

setup(
    name="django-geosource",
    version=open(os.path.join(HERE, "django_geosource", "VERSION.md")).read().strip(),
    include_package_data=True,
    author="Makina Corpus",
    author_email="terralego-pypi@makina-corpus.com",
    description="Django geographic asynchrone data sources loading",
    long_description=README + "\n\n" + CHANGES,
    description_content_type="text/markdown",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/Terralego/django-geosource.git",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
        "Django>=2.2",
        "djangorestframework",
        "django-polymorphic",
        "celery",
        "psycopg2",
        "Fiona",
        "pyexcel",
    ],
    tests_require=test_require,
    extras_require={
        "dev": test_require,
    },
)
