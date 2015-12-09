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
    ],
    keywords=[
        'mock',
        'responses',
    ],
    author='Florent Pigout',
    author_email='florent.pigout@novapost.fr',
    url='https://github.com/novafloss/mock-services',
    license='MIT',
    install_requires=[
        'attrs',
        'funcsigs',
        'responses',
        'setuptools>=17.1',
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
