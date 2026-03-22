#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from setuptools._distutils import setup


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit()

readme = open("README.md").read()
doclink = """
Documentation
-------------

Source and documentation at https://github.com/torial/PyTM."""
history = open("HISTORY.rst").read().replace(".. :changelog:", "")

setup(
    name="pytm-web",
    version="1.0.0",
    description="PyTM - CLI time tracker with web UI, project management, and invoice generation",
    long_description=readme + "\n\n" + doclink + "\n\n" + history,
    long_description_content_type="text/markdown",
    author="Sean (torial)",
    author_email="",
    url="https://github.com/torial/PyTM",
    packages=["PyTM", "PyTM.commands", "PyTM.core", "PyTM.web", "PyTM.web.routes"],
    package_dir={"pytm-web": "PyTM"},
    include_package_data=True,
    package_data={
        "PyTM.web": ["static/*", "templates/*.html", "templates/partials/*.html"],
    },
    install_requires=["click", "rich"],
    extras_require={
        "web": [
            "fastapi>=0.110",
            "uvicorn[standard]>=0.27",
            "python-multipart>=0.0.9",
            "jinja2>=3.1",
            "itsdangerous>=2.1",
        ],
    },
    license="MIT",
    zip_safe=False,
    keywords="PyTM time-tracker invoice web htmx fastapi",
    entry_points={
        "console_scripts": ["pytm=PyTM.cli:cli"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.12",
    ],
)
