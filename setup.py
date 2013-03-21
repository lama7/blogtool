import re
import os
from setuptools import setup

'''
Helper function to read a file since it's easier to add text to the README file
than to add it here.
'''
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def get_version():
    m = re.search("^__version__ = [\"](.*?)[\"]", open("blogtool/__version__.py").read())
    if m:
        return m.group(1)
    else:
        raise RuntimeError("Unable to find version string in blogtool/__version__.py")

setup(name = 'blogtool',
      version = get_version(),
      url = 'https://github.com/lama7/blogtool',
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: End Users/Desktop',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP :: Site Management',
          'Topic :: Text Processing',
          'Topic :: Utilities',
          ],
      long_description = read('README.md'),
      author = 'Gerry LaMontagne',
      author_email = 'gjlama94 [at] gmail [dot] com',
      license = 'MIT',
      description = 'A command line blog client',
      scripts = ['bin/bt'],
      packages = ['blogtool', 'blogtool.xmlproxy'],
      install_requires = ['markdown', 'lxml'],
      zip_safe = False)
