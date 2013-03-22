.. contents::

Change Log
==========

Latest Version: 1.1.0 
---------------------

by Gerry LaMontagne

Minor rev change because of switch from ``optparse`` library to ``argparse``.
Also incorporated the ``STDIN`` file as a special file name case for reading
from the standard input.  Finally, the Comment_ option now requires 2
arguments, a ``POSTID`` and a ``COMMENTID`` which is the ID of the comment being
replied to.

.. _Comment: commandline.html#options

- Added *test/parserecent*
- Added *test/serializertest.sh*
- *.gitattributes*

  + Removed merge strategy, no longer needed

- *.gitignore*

  + Added *test/recent* file

- *MANIFEST.md*

  + Added *INSTALL.md* and *LICENSE.md*

- *README.md*

  + Minor documentation clarifications

- *blogtool/__version__.py*

  + Bumped version

- *blogtool/fileprocessor.py*

  + Added special filename ``STDIN`` to facilitate reading from the standard
    input.

- *blogtool/headerparse.py*

  + Generates ``PARENTID`` header field for comment entry if a ``PARENTID`` is
    supplied.

- *blogtool/options.py*

  + Now uses ``argparse`` module instead of ``optparse``
  + GetPost output now encoded in UTF-8
  + PostComment option now takes 2 arguments- ``POSTID`` and ``COMMENTID`` which
    is the ID of the comment being replied to.

- *doc/source/commandline.rst*

  + Documentation presentation improvement

- *doc/source/conf.py*

  + Now parses *blogtool/__version__.py* for version information.
  + HTML theme changed to haiku

- *doc/source/index.rst*

  + Added *doc/source/changelong.rst*
  + Minor documenation changes

- *doc/source/usage.rst*

  + Added contents
  + Documented addition of ``STDIN`` as special file name on command line

- *setup.py*

  + Changed Development Status::Beta classifier to Production/ Stable

Version 1.0.3
-------------

by Gerry LaMontagne

A maintenance revision.  No new functionality added.

- Added sphinx generated HTML based documentation

  + Added *doc/source/index.rst*
  + Added *doc/source/configuration.rst*
  + Added *doc/source/commandline.rst*
  + Added *doc/source/conf.py*
  + Added *doc/source/usage.rst*

- *blogtool/__version__.py*

  + Bumped version

- *setup.py*

  + Changed long_description to rely on doc string in *setup.py* rather than
    *README.md*
  + Version information now extracted as soon as *setup.py* is run, rather than
    from called function

Version 1.0.2
-------------

by Gerry LaMontagne

Basically a maintenance revision, although the ``--version`` options was added
in this version.

- Created *blogtool/__main__.py*
- Created *blogtool/__version__.py*
- *blogtool/__init__.py*

  + Moved main execution loop into *blogtool/__main__.py*
  + Imports version string

- *blogtool/options.py*

  + Added GetVersion option

- *setup.py*

  + Reads *blogtool/__version__.py* for project version info

Version 1.0.1
-------------

by Gerry LaMontagne

A bug fix revision.

- Added *INSTALL.md*
- Added *LICENSE.md*
- *MANIFEST.md*

  + Added include *README.md*

- *README.md*
  
  + Numerous presentation changes
  + Added Contents entry with internal links
  + Various additions to existing documentation
  + Added Basic Usage and Pictures sections

- *blogtool/fileprocessor.py*

  + Fixed bug when generating ``img`` tags
  + Escaping of various HTML entities like <,>, and &
  + Serialize the lxml parse tree without ``etree.tostring``

- *blogtool/html2md.py*

  + Bug fix- properly converts nested inline elements to markdown equivalents
  + Bug fix- check for escaping of & in XMLRPC string
  + Bug fix- now generates properly closed ``iframe`` tags.

- *setup.py*

  + Added Topic::Utilities and Intended Audience::End Users/ Desktop classifiers
  + Bumped version

Version 1.0
-----------

by Gerry LaMontagne

- First Public Release

