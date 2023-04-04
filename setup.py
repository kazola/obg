from setuptools import setup, find_packages


setup(
    name='obg',
    version='0.1',
    description='Web App to control MBL Optode BLE devices via GUI',
    url='https://github.com/kazola/obg',
    author='Joaquim Oller',
    author_email='joller@mbl.edu.com',
    entry_points={
        'console_scripts': [
            # exe_name=package.pyfilename:functionname
            'obg=obg.main:main',
        ],
    },
    packages=find_packages(),
    install_requires=[
        'flet',
        'bleak',
    ]
)
