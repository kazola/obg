from setuptools import setup

setup(
    name='fleak',
    entry_points={
        'console_scripts': [
            'fleak = fleak:main',
        ],
    }
)