from distutils.core import setup

setup(
    name='BridgePython',
    version='0.2.0',
    author='Flotype Inc.',
    author_email='team@getbridge.com',
    packages=['BridgePython', 'BridgePython.data'],
    url='http://pypi.python.org/pypi/BridgePython/',
    license='LICENSE.txt',
    description='A Python API for the Bridge service.',
    long_description=open('README.md').read(),
    requires=[
        "tornado (>= 2.2)",
    ]
)
