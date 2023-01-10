from setuptools import setup, find_packages


# ugly but, meh
with open('requirements.txt', 'r') as f:
    my_reqs = [i for i in f.readlines() if '=' in i]
    my_reqs.append('lowell-mat@git+https://github.com/lowellinstruments/lowell-mat.git@v4')


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
    install_requires=my_reqs
)
