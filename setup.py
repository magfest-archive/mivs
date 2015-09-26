from __future__ import unicode_literals

import os.path
from setuptools import setup, find_packages

pkg_name = 'mivs'
__here__ = os.path.abspath(os.path.dirname(__file__))
# Sideboard's implementation of http://stackoverflow.com/a/16084844/171094
# after this, __version__ should exist in the namespace
exec(open(os.path.join(__here__, pkg_name.replace('-', '_'), '_version.py')).read())
req_data = open(os.path.join(__here__, 'requirements.txt')).read()
requires = [r.strip() for r in req_data.split() if r.strip() != '']
requires = list(reversed(requires))

if __name__ == '__main__':
    setup(
        name=pkg_name,
        version=__version__,
        description='Sideboard ' + pkg_name + ' plugin',
        license='COMPANY-PROPRIETARY',
        scripts=[],
        setup_requires=['distribute'],
        install_requires=requires,
        packages=find_packages(),
        include_package_data=True,
        package_data={},
        zip_safe=False
    )
