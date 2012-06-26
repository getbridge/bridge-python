from distutils.core import setup
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='BridgePython',
    version='0.2.2',
    author='',
    author_email='team@getbridge.com',
    packages=['BridgePython', 'BridgePython.data'],
    url='http://pypi.python.org/pypi/BridgePython/',
    license='LICENSE.txt',
    description='A Python API for the Bridge service.',
    long_description=read('README.md'),
    requires=[
        "tornado (>= 2.2)",
    ]
)
