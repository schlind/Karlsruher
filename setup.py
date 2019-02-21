from setuptools import setup, find_packages
from os import path
#from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
#with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#    long_description = f.read()

setup(
    name='karlsruher',  # Required
    version='1.0.0',  # Required
    description='Karlsruher Retweet Robot',  # Optional
    #long_description=long_description,  # Optional
    #long_description_content_type='text/markdown',  # Optional (see note above)

    url='https://github.com/kartbot/karlsruher',  # Optional
    author='Karlsruher Retweet Robot Society',  # Optional
    author_email='',  # Optional

    # https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Twitter :: Robot',
        #'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='twitter retweet robot bot',  # Optional

    packages=find_packages(),  # Required

    python_requires='>=3.4, <4',

    install_requires=['tweepy==3.7'],  # Optional

    extras_require={  # Optional
        'dev': ['check-manifest'],
        'test': ['coverage', 'pylint', 'pytest', 'pytest-cov'],
    },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={  # Optional
#        'console_scripts': [ 'sample=sample:main',],
    },

    project_urls={  # Optional
        'Source': 'https://github.com/kartbot/karlsruher/',
    },
)
