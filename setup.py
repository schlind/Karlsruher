# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""Setup"""

from os import path
from setuptools import setup, find_packages
from distutils.util import convert_path

VERSION_FILE='karlsruher/__version__.py'

def version():
    namespace = {}
    with open(convert_path(VERSION_FILE)) as version_file:
        for line in version_file.readlines():
            line = line.strip()
            if line.startswith('__version__'):
                exec(line, namespace)
    if namespace['__version__']:
        return namespace['__version__']
    raise RuntimeError('No __version__ in {}'.format(VERSION_FILE))


HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, 'README.setup.md'), encoding='utf-8') as README:
    long_description = README.read()


setup(
    name='Karlsruher',
    version=version(),
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
