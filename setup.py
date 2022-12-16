from setuptools import setup, find_packages


with open('requirements.txt', 'r') as f:
    my_reqs = [i for i in f.readlines() if '=' in i]
    my_reqs.append('lowell-mat@git+https://github.com/lowellinstruments/lowell-mat.git@poor')


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
    install_requires=my_reqs
)
