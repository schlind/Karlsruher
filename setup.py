from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='karlsruher',
    version='2.0-beta',
    description='Karlsruher Retweet Robot',
    long_description=long_description,
    long_description_content_type='text/markdown',

    #url='https://github.com/kartbot/karlsruher',
    #author='Karlsruher Retweet Robot Society',
    #author_email='',

    # https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Twitter :: Robot',
        'License :: None :: No License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.7',
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
