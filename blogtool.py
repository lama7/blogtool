#!/usr/bin/env python

"""
    blogtool.py

    The entry module for the blogtool command line utility.

    Program initialization, option and file processing are all started from
    here.
"""

from headerparse import Header
from fileprocessor import FileProcessor, FileProcessorError, FileProcessorRetry
from options import OptionProcessor

import utils
import sys

################################################################################
def main():
    options = OptionProcessor()
    filelist = options.parse()
 
    ###########################################################################
    '''
    Make sure that this loop always executes, regardless of whether there 
    are actually options.  The config file is processed throught this loop
    and the program will break if that code does not run
    '''
    header = Header()
    runeditor = options.check(header)
    emptyheader_text = header.buildPostHeader(options)
    if len(sys.argv) == 1 or (len(filelist) == 0 and runeditor):
        fd = utils.edit(emptyheader_text)
        if fd == None:
            print "Nothing to do, exiting."
        filelist.append(fd.name)      

    ###########################################################################
    tmp_fn = None
    fp = FileProcessor(**options.flags())
    for filename in filelist:
        if tmp_fn != filename:
            tmp_fn = filename
            print "Processing post file %s..." % filename

        try:
            header_text, post_text = fp.parsePostFile(filename,
                                                      emptyheader_text)
        except FileProcessorRetry:
            filelist.insert(0, filename)
            continue
        except FileProcessorError, err_msg:
            print err_msg
            continue

        header.addParms(header_text, fp.allblogs)
        for hdr in header:
            rval = fp.pushContent(post_text, hdr)
            if rval and not fp.comment:
                header.postid = rval
                print 'Updating post file...'
                fp.updateFile(filename, '%s' % header, post_text) 

################################################################################
if __name__ == "__main__":
    main()
