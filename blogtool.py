#!/usr/bin/python

from xmlproxy.proxybase import proxyError
from options import getOptions

import utils
import headerparse

from optparse import OptionParser
from tempfile import NamedTemporaryFile

import time
import re
import sys
import os
import types
import subprocess

try:
    from lxml import etree
except ImportError:
    print """
ATTENTION:
You need to install lxml to take full advantage of blogtool capabilities.
Without it, downloading posts is disallowed.  If all you need it to publish
posts to a blog, then this should be fine.

Unfortunately, this annoying warning message will pop-up everytime you run
blogtool.
"""
    raw_input('Press <ENTER> to continue...')
    import xml.etree.cElementTree as etree

try:
    import markdown
    MARKDOWN_PRESENT = True
except ImportError:
    print """
ATTENTION:
In order to publish posts with blogtool, python-markdown is required.  Without
it, all blogtool is capable of is some basic blog interaction for listing posts
or listing/ modifying categories.

Also, this annoying message will be displayed everytime you run blogtool.
"""
    raw_input('Press <ENTER> to continue...')
    MARKDOWN_PRESENT = False

################################################################################
#   
#   Error classes for blogtool
#

################################################################################
#   
#  define base class for errors
class blogtoolError(Exception): 
    # to be overriden by the subclass
    def __init__(self, msg):
        self.message = 'blogtoolError: %s' % msg

    # this is typically all that's done with the __str__ method
    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolRetry(Exception):
    pass

################################################################################
#
# blogtool class
#
#    Define the blogtool class.  This pulls a bunch of related functions and
#    leverages some of the niceties of classes to streamline the code.  It is 
#    a fairly significant refactor of the original code which had function that
#    passed around blog information like the name or the class itself.
#
#    While the first refactor resulted in the creation of this class, this 
#    refactor is about cleaning it up.  The purpose here is to more clearly
#    define a 'blogtool' object.  This will entail removing the option
#    processing as well as the dependency on the config parser.  All of that
#    code will be moved to the 'main' function where it properly belongs.
#    The idea will be to whittle down the blogtool class to it's essence- a
#    wrapper around the xmlrpc function calls.
#
class blogtool():

    options = getOptions()

    EXTENDED_ENTRY_RE = re.compile(r'\n### MORE ###\s*\n')

    ############################################################################
    def _getHeaderandPostText(self, linelist):
        # find first blank line so we can split the list
        for line in linelist:
            if line.isspace():
                i = linelist.index(line)
                break

        else:
            raise blogtoolError("""
Post file must have a blank line separating header and post text.
""" )

        if len(linelist[0:i]) == 0:
            raise blogtoolError('''
No header found, aborting.
''')
        elif len(linelist[i+1:]) == 0:
            raise blogtoolError('''
No text for post, aborting.
''')

        return ''.join(linelist[0:i]), ''.join(linelist[i + 1:])

    ############################################################################ 
    def _procPost(self, posttext):
        if not MARKDOWN_PRESENT:
            print "Unable to publish post without python-markdown.  Sorry..."
            sys.exit()

        m = self.EXTENDED_ENTRY_RE.search(posttext)
        if m:
            description = posttext[:m.start()]
            extended = posttext[m.end():]
        else:
            description = posttext
            extended = ''

        self.md = markdown.Markdown()
        html_desc = self._procText(description)
        if extended:
            html_ext = self._procText(extended)
        else:
            html_ext = ''

        del self.md

        return html_desc, html_ext

    ############################################################################ 
    '''
       Handles extra processing after markdown processing is complete.  For now,
       this consists of uploading image files and fixing up links to the
       uploaded image. 
    '''
    def _procText(self, text):
        tree = etree.XML('<post>%s</post>' % self.md.convert(text))
        for e in tree.getiterator():
            if e.text and e.tag not in ['pre', 'code', 'comment']:
                e.text = e.text.replace('\n', u' ')
            if e.tail:
                e.tail = e.tail.replace('\n', u' ')
            if e.tag == 'img':
                ifile = e.attrib['src']
                if ifile.find("http://") != -1:
                    # web resource defined, nothing to do
                    continue

                try:
                    ifile = utils.chkFile(ifile)
                    print "Attempting to upload '%s'..." % ifile
                    res = self._blogproxy.upload(ifile)
                except utils.utilsError, err:
                    print "File not found: %s" % err
                    sys.exit(1)
                except proxyError, err:
                    print "Caught in blogtool.blogtool._procText:"
                    print err
                    sys.exit()

                # FIX ME- don't know if this is necessary
                if res == None:
                    print "Upload failed, proceeding...\n"
                    continue

                e.attrib['src'] = res['url']
                if 'alt' not in e.keys():
                    e.set('alt', res['file'])
                # the 'res' attr is bogus- I've added it so that I can specify the
                # appropriate resolution file I want in the url.  
                if 'res' in e.keys():
                    res_str = '-' + e.attrib['res'] + '.'
                    e.attrib['src'] = re.sub("\.(\w*)$", r'%s\1' % res_str, e.attrib['src'])
                    del(e.attrib['res'])

#        print etree.tostring(tree)
#        sys.exit()
    
        return (etree.tostring(tree).replace('<post>', '')).replace('</post>', '')

    ############################################################################ 
    def _procPostCategories(self, header):
        # first, build a list of catgories that aren't on the blog from the
        # post's category list
        nonCats = []
        for c in header.categories:
            try:
                cat_list = self._blogproxy.getCategories()
            except proxyError, err:
                print "Caught in blogtool.blogtool._procPostCategories:"
                print err
                sys.exit()

            t = utils.isBlogCategory(cat_list, c)
            if t != None:
                nonCats.append((c,) + t)

        # see if there were any unrecognized categories
        if len(nonCats) == 0:
            print "Post categories OK"
        elif self.options[2].addpostcats:
            [ utils.addCategory(self._blogproxy, *ct) for ct in nonCats ]
        else:
            rcats = [ ct[0] for ct in nonCats ]
            print "Category '%s' is not a valid category for %s so it is being\n\
                   \r removed from the category list for this post.\n\
                   \rUse the -a option if you wish to override this behavior or\n\
                   \rthe -n option to add it from the command line.\n" %\
                                                         (', '.join(rcats),
                                                          header.name)
            [ header.categories.remove(c) for c in rcats ]

        # last bit of category processing- if there are any categories 
        # with subcategories, like 'cat.subcat', they need to be split
        # up so that the post is categorized properly
        # the 'list(set(...)) removes all duplicates 
        if len(header.categories) == 0:
            print "This post has no valid categories, the default blog category\n\
                   \rwill be used.\n"
        else:
            header.categories =  list(set(reduce(lambda l1, l2: l1 + l2, 
                                      [c.split('.') for c in header.categories])))

    ############################################################################ 
    '''
        updateHeder

        This function consists of subfunctions that drill into the header 
        string to find where to insert the POSTID info.  Each function returns 
        a tuple consisting of the next state, the header string that has been
        processed and the header string yet to be processed

    '''
    def _updateHeader(self, hdr_text, postid):

        def findbloggroup(l):
            # it possible that BLOG will not appear in the header (blog info
            # can also be defined in an rc file or command line options)
            # if we reach the end of the header, just append the POSTID there
            m = re.match('(.*?BLOG\s*\{\s*)(.*)', l, re.DOTALL)
            if m == None:
                l += 'POSTID: %s\n' % postid
                return None, l, ''

            return states.index(findblogname), m.group(1), m.group(2)

        def findblogname(l):
            m = re.match('(.*?NAME\s*:\s*|NAME\s*:\s*)([^\n]+)(.*)', l, re.DOTALL)
            if m != None:
                hdr_ret = m.group(1) + m.group(2)
                if self.bc.name not in hdr_ret:
                    return states.index(findbloggroup), hdr_ret, m.group(3)

                return states.index(findendgroup), hdr_ret, m.group(3)

            # we've found the group where the POSTID is to be written
            return states.index(findendgroup), '', l

        def findendgroup(l):
            m = re.match('(.*?)([}])(.*)', l, re.DOTALL)
            hdr_ret = m.group(1)
            hdr_ret += '    POSTID: %s\n' % postid
            hdr_ret += m.group(2) + m.group(3)
            return None, hdr_ret, ''

        # actual _updateHeader function
        states = [
                  findbloggroup,
                  findblogname,
                  findendgroup ]

        current_state = states.index(findbloggroup)
        hdr_str = hdr_text
        hdr_text = ''
        while current_state != None:
            current_state, procd_hdr, hdr_str = states[current_state](hdr_str)
            hdr_text += procd_hdr

        return hdr_text

    ############################################################################ 
    ''' parsePostFile

        Attempts to read a post file.  If successful, then a header and text
        portion are created.  The header portion can be parsed for so the
        text portion can be sent to the appropriate blogs.

    '''
    def parsePostFile(self, filename):
        try:
            f = open(filename, 'r')
            lines = f.readlines()
        except IOError:
            try:
                f = open(filename, 'w')
            except IOError, err:
                print err
                sys.exit()

            edit(f, "TITLE: \nCATEGORIES: \n")
            raise blogtoolRetry()
        else:
            f.close()

        return self._getHeaderandPostText(lines)

    ############################################################################ 
    '''
        pushPost

        Takes care of pushing a post up to a blog as defined by a header.
        Creates a blogproxy, processes the blog categories and builds a post
        object prior to determining if the post is just being updated or if it
        is a new post.  If the post is successfully sent, the post file is
        updated with the post ID assigned at the blog.
    '''
    def pushPost(self, post_text, header):
        # this handles pushing a post up to a blog
        self._blogproxy = header.proxy()
        self._blogname = header.name

        html_desc, html_ext = self._procPost(post_text)

        print "Checking post categories..."
        self._procPostCategories(header)

        try:
            post = utils.buildPost(header,
                                   html_desc,
                                   html_ext,
                                   timestamp = self.options[4].posttime,
                                   publish = self.options[3].publish )
        except utils.utilsError, timestr:
            print timestr
            sys.exit()

        if header.postid:
            print "Updating '%s' on %s..." % (header.title, header.name)
            try:
                postid = self._blogproxy.editPost(header.postid, post)
            except proxyError, err:
                print "Caught in blogtool.blogtool.pushPost:"
                print err
                sys.exit()

            return None

        if self.options[3].publish:
            print "Publishing '%s' to '%s'" % (header.title,  header.name) 
        else:
            print "Publishing '%s' to '%s' as a draft" % (header.title,
                                                          header.name)

        try:
            postid = self._blogproxy.publishPost(post)
        except proxyError, err:
            print "Caught in blogtool.blogtool.pushPost:"
            print err
            sys.exit()

        return postid

    ############################################################################ 
    def updateFile(self, filename, hdr_text, post_text, postid):
        hdr_text = self._updateHeader(hdr_text, postid)
        # alter the file name so we don't overwrite
        filename += '.posted'
        try:
            f = open(filename, 'w')
            f.write(hdr_text)
            f.write('\n')
            f.write(post_text)
        except IOError:
            print "Error writing updated post file %s" % file
        else:
            f.close()

################################################################################
#
#
def edit(fh, hdr_string = ''):
    editor = os.getenv('EDITOR', 'editor')

    if hdr_string:
        try:
            fh.write("TITLE: \nCATEGORIES: \n")
            fh.flush()
        except IOError, e:
            print "Could not write header text to file."

    try:
        rcode = subprocess.call([editor, fh.name])
    except OSError, e:
        print "Can't launch %s:  %s" % (editor, e)
        return None

    if rcode == 0:
        return True
    else:
        return None

################################################################################
#
#
def main():
    bt = blogtool()
    header = headerparse.header()

    ###########################################################################
    parser = OptionParser("Usage: %prog [option] postfile1 postfile2 ...")
    for option in bt.options:
        parser.add_option(*option.args, **option.kwargs)
    (opts, filelist) = parser.parse_args()
 
    ###########################################################################
    # make sure that this loop always executes, regardless of whether there 
    # are actually options.  The config file is processed throught this loop
    # and the program will break if that code does not run
    runeditor = False
    for option in bt.options:
        if option.check(opts):
            if option.run(header) == 'runeditor':
                runeditor = True

    if len(sys.argv) == 1 or (len(filelist) == 0 and runeditor):
        fd = NamedTemporaryFile()
        if edit(fd, "TITLE: \nCATEGORIES: \n") == None:
            print "Nothing to do, exiting."
        filelist.append(fd.name)      

    ###########################################################################
    tmp_fn = None
    for filename in filelist:
        if tmp_fn != filename:
            tmp_fn = filename
            print "Processing post file %s..." % filename

        try:
            header_text, post_text = bt.parsePostFile(filename)
        except blogtoolRetry:
            filelist.insert(0, filename)
            continue
        except blogtoolError, err_msg:
            print err_msg
            continue

        header.addParms(header_text, bt.options[5].allblogs)
        for hdr in header:
            try:
                postid = bt.pushPost(post_text, hdr)
            except blogtoolError, err_msg:
                print err_msg
                sys.exit()

            if postid:
                print 'Updating post file...'
                bt.updateFile(filename, header_text, post_text, postid) 

    sys.exit()

################################################################################
if __name__ == "__main__":
    main()
