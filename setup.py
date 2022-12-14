from setuptools import setup, find_packages


setup(
    name='fleak',
    version='0.8.412',
    description='Web App to interact with Lowell Instruments loggers',
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
    install_requires=[
        'flet>=0.1.33',
        'bleak',
        'numpy',
        'pandas',
        'h5py',
        'humanize',
        'lowell-mat@git+https://github.com/lowellinstruments/lowell-mat.git@poor'
    ]
)
