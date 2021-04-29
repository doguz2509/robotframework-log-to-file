import os
import re
import shutil
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

from robotbackground_custom_logger import __version__

NAME = 'robotbackground_custom_logger'
CLASSIFIERS = """
Development Status :: 5 - Production/Stable
License :: MIT
Operating System :: OS Independent
Programming Language :: Python :: 3
Topic :: Software Development :: Testing
Framework :: Robot Framework
""".strip().splitlines()
CURDIR = dirname(abspath(__file__))

print(f"Current dir: {CURDIR}")

VERSION = __version__
print(f"Version: {VERSION}")
with open(join(CURDIR, 'README.md')) as f:
    README = f.read()
with open(join(CURDIR, 'requirements.txt')) as f:
    REQUIRES = f.read().splitlines()

PACKAGES = find_packages('.', exclude=['venv'])
print(f"Packages: {PACKAGES}")

shutil.rmtree(os.path.join(CURDIR, 'dist'), True)

setup(
    name='robotbackground_custom_logger',
    version=VERSION,
    packages=PACKAGES,
    url='https://github.com/doguz2509/robotframework-log-to-file',
    download_url='https://pypi.org/project/robotbackground-custom-logger',
    package_data={'': ['*.robot', 'tests/*.robot']},
    license='MIT',
    author='Dmitry Oguz',
    author_email='doguz2509@gmail.com',
    description='RobotFramework extension for background logger',
    long_description=README,
    long_description_content_type='text/markdown',
    install_requires=REQUIRES
)
