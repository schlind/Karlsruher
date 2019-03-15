from setuptools import setup, find_packages

import karlsruher

with open('README.setup.md', 'r', encoding='utf-8') as README:
    long_description = README.read()

setup(
    name='Karlsruher',
    version=karlsruher.__version__,
    description='Karlsruher Twitter Robot',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/schlind/Karlsruher',
    author='Karlsruher Twitter Robot Society',
    author_email='karlsruher-dev@schlind.org',
    maintainer='Sascha Schlindwein',
    maintainer_email='karlsruher-dev@schlind.org',
    classifiers=[  # Optional
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.7',
        'License :: Public Domain',
        'Topic :: Artistic Software',
        'Topic :: Internet',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
    ],
    zip_safe=True,
    keywords='twitter robot bot retweet cronjob',
    packages=find_packages(),
    python_requires='>=3.4, <4',
    install_requires=['pyaml', 'tweepy==3.7'],
    # setup_requires=['pytest-runner', 'pylint-runner'],
    # tests_require=['pytest','pytest-cov','pylint'],
    extras_require={
        'dev': ['check-manifest'],
        'test': ['pytest', 'pytest-cov', 'pylint'],
    },
    entry_points={
        'console_scripts': ['karlsruher=karlsruher.__main__:main']
    },
    project_urls={
        'Source': 'https://github.com/schlind/Karlsruher/',
    },
)
