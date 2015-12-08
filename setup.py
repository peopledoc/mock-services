#!/usr/bin/env python
import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))


setup(
    name='responses-helpers',
    version='0.1.dev0',
    description='Responses helpers.',
    long_description=open(os.path.join(here, 'README.rst')).read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    keywords=[
        'mock',
        'responses',
    ],
    author='PeopleDoc',
    author_email='rd@novapost.fr',
    url='https://github.com/novafloss/responses-helpers',
    license='MIT',
    install_requires=[
        'funcsigs',
        'responses',
        'setuptools>=17.1',
    ],
    packages=[
        'responses_helpers'
    ],
)
