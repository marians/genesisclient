# encoding: utf-8

from setuptools import setup

setup(name='genesisclient',
      version='0.0.7',
      description='Genesis (DeStatis et. al.) client for Python',
      author='Marian Steinbach',
      author_email='marian@sendung.de',
      url='https://github.com/marians/genesisclient',
      license="MIT",
      packages=['genesisclient'],
      install_requires=[
        'lxml',
        'suds'],
      entry_points={
        'console_scripts': [
            'genesiscl = genesisclient:main'
        ]
      }
)
