from setuptools import setup

setup(name='kagesenshi_org',
      version='1.0',
      description='KageSenshi website',
      author='Izhar Firdaus',
      author_email='izhar@kagesenshi.org',
      url='http://www.python.org/sigs/distutils-sig/',
      install_requires=[
          # needed by morepath
#        'venusian >= 1.0a8',
#        'reg >= 0.5',
        'werkzeug >= 0.9.4',
        'Chameleon >= 2.14',
        'morepath == 0.2',
      ]
     )
