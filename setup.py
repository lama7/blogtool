import os
from setuptools import setup

'''
Helper function to read a file since it's easier to add text to the README file
than to add it here.
'''
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name = 'blogtool',
      version = '1.0',
      classifiers = [
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP :: Site Management',
          'Topic :: Text Processing',
          ],
      long_description = read('README'),
      author = 'Gerry LaMontagne',
      author_email = 'gjlama94@gmail.com',
      license = 'MIT',
      description = 'A command line blog client',
      scripts = ['bin/bt'],
      packages = ['blogtool', 'blogtool.xmlproxy'],
      install_requires = ['markdown', 'lxml'],
      zip_safe = False)
