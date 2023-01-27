from setuptools import setup, find_packages


# grab packages from requirements files
with open('requirements311.txt') as f:
    rr = f.readlines()



setup(
    name='fleak',
    version='0.8.413',
    description='Web App for Lowell Instruments BLE loggers',
    url='https://github.com/LowellInstruments/fleak',
    author='Lowell Instruments',
    author_email='joaquim@lowellinstruments.com',
    entry_points={
        'console_scripts': [
            # exe_name=package.pyfilename:functionname
            'fleak=fleak.main:main',
        ],
    },
    packages=find_packages(),
    # defined at top of this file
    install_requires=rr
)
