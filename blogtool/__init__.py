#!/usr/bin/env python

"""
    blogtool.py

    The entry module for the blogtool command line utility.

    Program initialization, option and file processing are all started from
    here.
"""

from __version__ import __version__

from options import OptionProcessor
from headerparse import Header

import sys
import utils

options = OptionProcessor()
filelist = options.parse()

'''
Make sure that this loop always executes, regardless of whether there 
are actually options.  The config file is processed through this loop
and the program will break if that code does not run
'''
header = Header()
runeditor = options.check(header)
emptyheader_text = header.buildPostHeader(options)
'''
Unfortunately, determining when to run the editor for creating a blogpost is
a bit tricky.  If `blogtool` is invoked by itself do so.  If no files are
supplied and certain options are specified that logically mean we want to 
create a post (see options.py for which ones return `runeditor`) BUT we
haven't editted a comment, then do so.  Finally, if only 3 arguments are
supplied on the command line and the blogname is set, meaning the following
command was run:

    > blogtool.py -b 'blogname'

then run the editor.
'''
if len(sys.argv) == 1 or \
   (len(filelist) == 0 and runeditor and not options.opts.commentid) or \
   (len(sys.argv) == 3 and options.opts.blogname is not None):
    fd = utils.edit(emptyheader_text)
    if fd == None:
        print "Nothing to do, exiting."
        sys.exit()
    filelist.append(fd.name)      


