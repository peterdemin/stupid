#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = "1.3.6"

if sys.argv[-1] == 'publish':
    try:
        import wheel  # noqa
    except ImportError:
        raise ImportError("Fix: pip install wheel")
    os.system('python setup.py sdist bdist_wheel upload')
    print("You probably want to also tag the version now:")
    print("  git tag -a {0} -m 'version {0}'".format(version))
    print("  git push --tags")
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a {0} -m 'version {0}'".format(version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


def get_requirements(filename):
    with open(filename) as fp:
        reqs = [x.strip() for x in fp.read().splitlines()
                if not x.strip().startswith('#')]
    return reqs


setup(
    name='stupid',
    version=version,
    description="""Slack super perfomance team collaboration bot""",
    long_description=readme + '\n\n' + history,
    author='Petr Demin',
    author_email='petr.demin@nih.gov',
    url='https://github.com/peterdemin/stupid',
    include_package_data=True,
    packages=['stupid'],
    install_requires=get_requirements('requirements.txt'),
    license="BSD",
    zip_safe=False,
    keywords='stupid',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'stupid = stupid.main:main',
        ]
    },
    setup_requires=['nose>=1.0', 'pytest-runner'],
    tests_require=get_requirements('requirements-dev.txt'),
)
