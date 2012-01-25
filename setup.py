try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import sys, os

version = '0.3.1'

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name = "ambhas",
    version = version,
    description = "A library devloped under the project AMBHAS",
    author = "Sat Kumar Tomer",
    author_email = "satkumartomer@gmail.com",
    url = "http://ambhas.com/",
    download_url = "http://pypi.python.org/pypi/ambhas/",
    keywords = ["ambhas", "hydrology", "statistics", "modelling"],
    packages = find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe = False,
    install_requires=["numpy"],
    classifiers = [
        "Programming Language :: Python :: 2.7",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        ],
    long_description = (
    "\n"+read('docs/index.txt')
    + '\n' + '\n'
    + read('CHANGELOG.txt')
    + '\n' + '\n'
    +'License\n'
    +'========\n'
    + 'Please read LICENSE.text available with the library.'
    + '\n'
    + 'Download\n'
    + '========\n'
    ),
)

