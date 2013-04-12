#!/usr/bin/env python

from blogtool import header, options, filelist, emptyheader_text

from headerparse import Header
from fileprocessor import FileProcessor, FileProcessorError, FileProcessorRetry

################################################################################
"""run

    If importing ``blogtool``, this is the function that runs it.
"""
def run():
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
    run()
