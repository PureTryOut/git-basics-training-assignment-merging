import os

from setuptools import find_packages, setup

setup(
        name='aportsknife',
        version='0.0.1',
        license='GPL-3.0-or-later',
        author='Bart Ribbers',
        author_email='bribbers@disroot.org',
        description='A "swiss knife" tool for Alpine Linux aports',
        install_requires=['pyxdg', 'gitpython'],
        packages=find_packages(include=['aportsknife']),
        include_package_data=True,

        entry_points={
            'console_scripts': [
                'aportsknife=aportsknife.__main__:main'
            ]
        }
)
