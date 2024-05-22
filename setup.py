# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='punctual',
    version='0.1.0',
    description='Make love and don\' worry about being punctual',
    long_description=readme,
    author='Luca Iacomino',
    author_email='lucaiacomino1999@gmail.com',
    url='https://github.com/JustNello/punctual',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)