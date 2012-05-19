from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='prambanan',
      version=version,
      description="yet another python to javascript translator",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='python javascript',
      author='Gozali Kumara',
      author_email='ghk@gozalikumara.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "simplejson",
          "argparse",
          "chameleon",
          "logilab_astng",
      ],
      entry_points="""
      [console_scripts]
      prambanan = prambanan.cmd:main
      """
  )
