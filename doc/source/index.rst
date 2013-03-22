.. blogtool documentation master file, created by
   sphinx-quickstart on Thu Mar 21 11:36:34 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to blogtool's documentation!
====================================

This is a python based, command-line blog client that supports Wordpress blogs.
It supports most of the common functions associated with blogging including:
posting to your blog, deleting posts, commenting to your blog, editting
comments, retrieving category lists and recent post activity, and even editting
posts.

To facilitate posting, blogtool reads files written using markdown_ text
markup.  These files can be pre-written and passed to blogtool on the command
line or blogtool can be run standalone, at which point it launches an editor for
entering a post into.

.. _markdown: http://daringfireball.net/projects/markdown/

Contents:

.. toctree::
    :maxdepth: 2

    configuration.rst
    commandline.rst
    usage.rst
    changelog.rst
