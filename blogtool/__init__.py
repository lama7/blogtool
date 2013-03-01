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

    fp = FileProcessor(**options.flags())
    tmp_fn = None
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
            try:
                rval = fp.pushContent(post_text, hdr)
                if rval and not fp.comment:
                    header.postid = rval
                    print 'Updating post file...'
                    fp.updateFile(filename, '%s' % header, post_text) 
            except FileProcessorError, err:
                print err
                if filename.startswith("/tmp"):
                    if fp.comment:
                        filename += '.' + hdr.postid
                    else:
                        filename += '.' + hdr.title
                    print "Saving tmp content file %s" % filename
                    f = open(filename, 'w')
                    f.write('%s' % header + '\n' + post_text)
                    f.close()
                # It's possible there are other files to process so rather than 
                # bailing entirely we'll break out of this loop and move on to
                # the next file if there is one.  In most cases, this will be
                # like exitting the program since typical usage doesn't have
                # multiple files to process.
                break

################################################################################
if __name__ == "__main__":
    main()
