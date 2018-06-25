from glob import glob
import os

from setuptools import setup


setup(
    name='easl',
    version='0.2dev0',
    packages=['easl'],
    scripts=glob(os.path.join('scripts', '*.py')),
)
