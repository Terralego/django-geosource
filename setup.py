#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


def read(fname):
    return open(fname).read()


setup(
    name="django_geosource",
    version="0.1",
    author="Makina Corpus",
    author_email="terralego-pypi@makina-corpus.com",
    description="Django GeoSource",
    url="https://github.com/Terralego/django-geosource",
    packages=find_packages(
        exclude=["*.tests", ]
    ),
    include_package_data=True,
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development",
        "OSI Approved :: MIT License",
    ],
    install_requires=[
        "Django>=2.1,<2.2",
        "djangorestframework>=3.8,<3.9",
        "django-polymorphic>=2.0,<2.1",
        "celery>=4.3,<4.4",
        "Fiona>=1.8,<1.9",
    ],
)
