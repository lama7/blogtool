import re
import os
from setuptools import setup

m = re.search("^__version__ = [\"](.*?)[\"]", open("blogtool/__version__.py").read())
if m:
    version_str =  m.group(1)
else:
    raise RuntimeError("Unable to find version string in blogtool/__version__.py")

long_description = \
'''
This is an XMLRPC client for Wordpress blogs.  It is command-line, rather than
GUI, based and reads markdown_ formatted text files to post to a web log.  The
text files must also be formatted with a header, see the `usage documentation`_
for details.

In addition to support for posting, a number of blog related administrative
actions are supported like commenting, comment editting and moderation, post
deletion and so forth.  See the documentation_ for a full description.

The source for ``blogtool`` lives here_.

.. _markdown: http://daringfireball.net/projects/markdown/
.. _usage documentation: http://pythonhosted.org/blogtool/usage.html
.. _documentation: http://pythonhosted.org/blogtool/
.. _here: https://github.com/lama7/blogtool
'''

setup(name = 'blogtool',
      version = version_str,
      url = 'https://github.com/lama7/blogtool',
      download_url = "https://pypi.python.org/packages/source/b/blogtool/blogtool-%s.tar.gz" % version_str,
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
      long_description = long_description,
      author = 'Gerry LaMontagne',
      author_email = 'gjlama94 [at] gmail [dot] com',
      license = 'MIT',
      description = 'A command-line, XMLRPC based blog client',
      scripts = ['bin/bt'],
      packages = ['blogtool', 'blogtool.xmlproxy'],
      install_requires = ['markdown', 'lxml'],
      zip_safe = False)
