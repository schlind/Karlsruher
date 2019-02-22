'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher

Setup

'''

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Karlsruher',
    version='2.0b3',
    description='Karlsruher Retweet Robot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/schlind/Karlsruher',
    author='Karlsruher Retweet Robot Society',
    author_email='karlsruher-dev@schlind.org',
    maintainer='Sascha Schlindwein',
    maintainer_email='karlsruher-dev@schlind.org',
    classifiers=[  # Optional
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.7',
        #TODO 'License :: Public Domain',
        'Topic :: Artistic Software',
        'Topic :: Internet',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
    ],
    keywords='twitter retweet robot bot',
    packages=find_packages(),
    python_requires='>=3.4, <4',
    install_requires=['tweepy==3.7'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['pytest','pytest-cov','pylint'],
    },
    entry_points={
        'console_scripts': ['karlsruher=karlsruher.__main__:main']
    },
    project_urls={
        'Source': 'https://github.com/schlind/Karlsruher/',
    },
)
