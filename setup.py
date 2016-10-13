#!/usr/bin/env python
import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))


setup(
    name='mock-services',
    version=open(os.path.join(here, 'VERSION')).read().strip(),
    description='Mock services.',
    long_description=open(os.path.join(here, 'README.rst')).read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords=[
        'http',
        'mock',
        'requests',
        'rest',
    ],
    author='Florent Pigout',
    author_email='florent.pigout@novapost.fr',
    url='https://github.com/novafloss/mock-services',
    license='MIT',
    install_requires=[
        'attrs',
        'funcsigs',
        'requests-mock',
    ],
    extras_require={
        'test': [
            'flake8'
        ],
        'release': [
            'wheel',
            'zest.releaser'
        ],
    },
    packages=[
        'mock_services'
    ],
)
