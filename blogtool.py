#!/usr/bin/python

from options import OptionProcessor
from tempfile import NamedTemporaryFile
from headerparse import Header
import fileprocessor
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
    if len(sys.argv) == 1 or (len(filelist) == 0 and runeditor):
        fd = NamedTemporaryFile()
        if utils.edit(fd, "TITLE: \nCATEGORIES: \n") == None:
            print "Nothing to do, exiting."
        filelist.append(fd.name)      

    ###########################################################################
    tmp_fn = None
    fp = fileprocessor.FileProcessor(**options.flags())
    for filename in filelist:
        if tmp_fn != filename:
            tmp_fn = filename
            print "Processing post file %s..." % filename

        try:
            header_text, post_text = fp.parsePostFile(filename)
        except fileprocessor.FileProcessorRetry:
            filelist.insert(0, filename)
            continue
        except fileprocessor.FileProcessorError, err_msg:
            print err_msg
            continue

        header.addParms(header_text, fp.allblogs)
        print header
        sys.exit()
        for hdr in header:
            try:
                postid = fp.pushPost(post_text, hdr)
            except fileprocessor.FileProcessorError, err_msg:
                print err_msg
                sys.exit()

            if postid:
                print 'Updating post file...'
                fp.updateFile(filename, header_text, post_text, postid) 

################################################################################
if __name__ == "__main__":
    main()
