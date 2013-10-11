from distutils.core import setup

setup(name='genesisclient',
      version='0.0.4',
      description='Genesis (DeStatis et. al.) client for Python',
      author='Marian Steinbach',
      author_email='marian@sendung.de',
      url='https://github.com/marians/genesisclient',
      py_modules=['genesisclient'],
      install_requires=[
        'lxml',
        'suds']
)
