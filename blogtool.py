#!/usr/bin/python

from xmlproxy import getProxy
from xmlproxy.proxybase import proxyError
import utils
import headerparse
from options import getOptions

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
    def __init__(self):
        self.message = ''

    # this is typically all that's done with the __str__ method
    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolNoBlogName(blogtoolError):
    def __init__(self):
        self.message = """
There are multple blogs in the config file.  Use the '-b' option to specify
which to use.
"""

################################################################################
#   
#
class blogtoolBadName(blogtoolError):
    def __init__(self):
        self.message = """
The blog name provided does not match anything in the configuration file.
"""

################################################################################
#   
#
class blogtoolNoConfig(blogtoolError):
    def __init__(self):
        self.message = """
A '~/.btconfig' file was not found nor was a config file specified on the command
line.  Without a configuration file, the only operation possible is posting.

To perform any optional operations (deleting posts, retrieving recent titles,
etc.) please create a ~/.btconfig file.
"""

################################################################################
#   
#
class blogtoolPostFileError(blogtoolError):
    def __init__(self):
        self.message = """
Post file must have a blank line separating header and post text.
"""

################################################################################
#   
#
class blogtoolDeletePostError(blogtoolError):
    def __init__(self, postid, blogname):
        self.message = "Unable to delete post %s from %s" % (postid, blogname)
    

################################################################################
#   
#
class blogtoolFNFError(blogtoolError):
    def __init__(self, filename):
        self.message = "File not found: %s" % filename

################################################################################
#   
#
class blogtoolHeaderError(blogtoolError):
    def __init__(self):
        self.message = """
The post file has an invalid header.
"""
        
################################################################################
#   
#
class blogtoolRetry(blogtoolError):
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
    def __init__(self):
                      
        # create a header parsing object
        self.hdr = headerparse.headerParse()

#self.options = getOptions()

    ############################################################################ 
    def setBlogProxy(self, xmlrpc, username, password):
        if self.blogproxy:
            del self.blogproxy

        self.blogproxy = blogapi.blogproxy(xmlrpc, username, password)

    ############################################################################ 
    def setBlogConfig(self, config):
        # this function sets the working blog config
        if cf_config == None:
           raise blogtoolNoConfig() 

        if len(cf_config) == 1:
            self.bc = cf_config[0]
        else:
            if not self.blogname:
                raise blogtoolNoBlogName()
            for bc in cf_config:
                if bc.name == self.blogname:
                    self.bc = bc
                    break
            else:
                # the name provided does not match anything in the config file
                raise blogtoolBadName()

        try:
            self.blogproxy = getProxy(self.bc.blogtype,
                                      self.bc.xmlrpc, 
                                      self.bc.username,
                                      self.bc.password)

        except ValueError:
            print "Invalid blogtype specified: %s" % self.bc.blogtype
            sys.exit()

    ############################################################################ 
    ''' parsePostFile

        Attempts to read a post file.  If successful, then a header and text
        portion are created.  The header portion can be parsed for so that he
        text portion can be sent to the appropriate blogs.

    '''
    def parsePostFile(self):
        try:
            f = open(self.filename, 'r')
            lines = f.readlines()
        except IOError:
            try:
                f = open(self.filename, 'w')
            except IOError, err:
                print err
                sys.exit()

            edit(f, "TITLE: \nCATEGORIES: \n")
            raise blogtoolRetry()
        else:
            f.close()

        # min of 1 line for header, a blank separator and a line of text = 3
        if len(lines) < 3:
            raise blogtoolPostFileError()
        self.header, self.posttext = self._getHeaderandPostText(lines)

        del lines

        try:
            self.post_config = reconcile(self.hdr.parse(self.header),
                                         self.cf_config)
        except headerparse.headerParseError, err_str:
            print err_str
            raise blogtoolHeaderError()

    ############################################################################ 
    '''
        pushPost

        Takes care of pushing a post up to a blog as defined by a header.
        Creates a blogproxy, processes the blog categories and builds a post
        object prior to determining if the post is just being updated or if it
        is a new post.  If the post is successfully sent, the post file is
        updated with the post ID assigned at the blog.
    '''
    def pushPost(self):
        # this handles pushing a post up to a blog
        try:
            self.blogproxy = getProxy(self.bc.blogtype,
                                      self.bc.xmlrpc, 
                                      self.bc.username,
                                      self.bc.password)

        except ValueError:
            print "Invalid blogtype specified: %s" % self.bc.blogtype

        html_desc, html_ext = self._procPost()

        print "Checking post categories..."
        self.bc.categories = self._procPostCategories()

        try:
            post = utils.buildPost(self.bc,
                                       html_desc,
                                       html_ext,
                                       timestamp = self.opts.posttime,
                                       publish = self.opts.publish )
        except utilsError, timestr:
            print timestr
            sys.exit()

        if self.bc.postid:
            print "Updating '%s' on %s..." % (self.bc.title, self.bc.name)
            try:
                postid = self.blogproxy.editPost(self.bc.postid, post)

            except proxyError, err:
                print err
                sys.exit()

            return None

        if self.opts.publish:
            print "Publishing '%s' to '%s'" % (self.bc.title,  self.bc.name) 
        else:
            print "Publishing '%s' to '%s' as a draft" % (self.bc.title,
                                                          self.bc.name)

        try:
            postid = self.blogproxy.publishPost(self.bc.name, post)

        except proxyError, err:
            print err
            sys.exit()

        if postid != None:
            header = self._updateHeader(postid)
            return 1                

    ############################################################################ 
    def _procPost(self):
        if not MARKDOWN_PRESENT:
            print "Unable to publish post without python-markdown.  Sorry..."
            sys.exit()

        m = self.EXTENDED_ENTRY_RE.search(self.posttext)
        if m:
            description = self.posttext[:m.start()]
            extended = self.posttext[m.end():]
        else:
            description = self.posttext
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
                else:
                    if os.path.isfile(ifile) != 1:
                        ifile = os.path.join(os.path.expanduser('~'), ifile)
                        if os.path.isfile(ifile) != 1:
                            raise blogtoolFNFError(e.attrib['src'])

                # run it up the flagpole
                print "Attempting to upload '%s'..." % ifile
                try:
                    res = self.blogproxy.upload(self.bc.name, ifile)
                except proxyError, err:
                    print err
                    sys.exit()

                # FIX ME- don't know if this is necessary
                if res == None:
                    print "Upload failed, proceeding...\n"
                    continue
                print "Done"

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
    def _procPostCategories(self):
        # first, build a list of catgories that aren't on the blog from the
        # post's category list
        nonCats = []
        for c in self.bc.categories:
            try:
                cat_list = self.blogproxy.getCategories(self.bc.name)
            
            except proxyError, err:
                print err
                sys.exit()

            t = utils.isBlogCategory(cat_list, c)
            if t != None:
                nonCats.append((c,) + t)

        # see if there were any unrecognized categories
        if len(nonCats) == 0:
            print "Post categories OK"
        elif self.opts.addpostcats:
            # since the addcat option is processed prior to post processing,
            # we should be able to get away with coopting the opts.blogname
            # and setting it to the current bc.name value without any 
            # repercussions- but check here when some kind of potential funny
            # business starts
            self.opts.blogname = self.bc.name
            [ utils.addCategory(*ct) for ct in nonCats ]
        else:
            rcats = [ ct[0] for ct in nonCats ]
            print "Category '%s' is not a valid category for %s so it is being\n\
                   \r removed from the category list for this post.\n\
                   \rUse the -a option if you wish to override this behavior or\n\
                   \rthe -n option to add it from the command line.\n" %\
                                                         (', '.join(rcats),
                                                          self.bc.name)
            [ self.bc.categories.remove(c) for c in rcats ]

        # last bit of category processing- if there are any categories 
        # with subcategories, like 'cat.subcat', they need to be split
        # up so that the post is categorized properly
        # the 'list(set(...)) removes all duplicates 
        if len(self.bc.categories) == 0:
            print "This post has no valid categories, the default blog category\n\
                   \rwill be used.\n"
            return self.bc.categories
        else:
            return list(set(reduce(lambda l1, l2: l1 + l2, 
                                   [c.split('.') for c in self.bc.categories])))

    ############################################################################ 
    '''
        updateHeder

        This function consists of subfunctions that drill into the header 
        string to find where to insert the POSTID info.  Each function returns 
        a tuple consisting of the next state, the header string that has been
        processed and the header string yet to be processed

    '''
    def _updateHeader(self, postid):

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
        hdr_str = self.header
        self.header = ''
        while current_state != None:
            current_state, procd_hdr, hdr_str = states[current_state](hdr_str)
            self.header += procd_hdr

    ############################################################################ 
    def _updateFile(self):
        # alter the file name so we don't overwrite
        self.filename += '.posted'
        try:
            f = open(self.filename, 'w')
            f.write(self.header)
            f.write('\n')
            f.write(self.posttext)
        except IOError:
            print "Error writing updated post file %s" % file
        else:
            f.close()

    ############################################################################
    def _getHeaderandPostText(self, linelist):
        # find first blank line so we can split the list
        for line in linelist:
            if line.isspace():
                i = linelist.index(line)
                break

        return ''.join(linelist[0:i]), ''.join(linelist[i + 1:])


################################################################################
# 
# Checks for and processes a config file for blogtool 
#  Info in config file: anything that can appear in the header of a postfile
#  Most likely for storing static blog related stuff like username, password,
#  xmlrpc, and blog name- essentially it sets defaults that can be overridden
#  by the postfile
#
#  12/4/09:  Now returns config_str which can be passed to a parser object.
#            Previous had returned a config object.  This was eliminated so
#            that the parser object did not need to be global
#
def getConfigFileStr(cfile):
    # cfile will be a filename or None
    if cfile == None:
        cfile = os.path.join(os.path.expanduser('~'), '.btconfig')    
        if os.path.isfile(cfile) != 1:
            return None
    else:
       # it's possible the user supplied a fully qualified path, so check if
       # the file exists
       if os.path.isfile(cfile) != 1:
           # try anchoring file to the user's home directory       
           cfile = os.path.join(os.path.expanduser('~'), cfile)
           if os.path.isfile(cfile) != 1:
               print "Unable to open config file: %s"
               sys.exit(1)

    # open the file
    try:
        f = open(cfile, 'r')
        # config file format is identical to header, so convert file lines
        # to a string and then return a config objct
        config_str = ''.join(f.readlines())
    except IOError:
        print "Unable to open config file: %s" % cfile
        sys.exit(1)
    else:
        f.close()

    return config_str 

##############################################################################
#
# reconcile- reconciles configuration info between config file and post 
#            Roughly speaking, the post config contained in the header trumps
#            any setting in the config file.
#
# This is not as difficult as it might at first seem.  
# If there is a NAME in the post config, find the equivalent blog entry in the
# config file and complete the config as required.
# If no name, then blog entries are processed in order- that is, entry 1 in
# post config is completed using entry 1 in config file, and so forth.
# Any conflicts are resolved in favor of leaving post config- we assume the user
# wanted to do something so we let them
#
def reconcile(pcl, cfcl):

    if cfcl == None:
        return pcl
    
    for pc in pcl:
        cf = None
        if pc.name != '':
            for cfc in cfcl:
                if cfc.name == pc.name:
                    cf = cfc
                    break
            else:
                continue  
        else:
            # without a name, we can only do take one other approach-
            # match the indexes of configs and go from there.
            i = pcl.index(pc)
            if not i < len(cfcl):
                continue
            cf = cfcl[pcl.index(pc)]

        # loop through the object attributes and plug in anything supplied
        # by config that isn't alread set
        for (k, v) in pc.__dict__.iteritems():
            # if any values are already assigned, then skip them- config file
            # values do NOT override post config values
            if k == 'categories' or k == 'tags':
                if len(v) != 0:
                   continue
            elif v != '':
                continue

            # value is not assigned already, see if config file assigns a value
            newv = cf.get(k)
            if newv != None:
                pc.set(k, newv)

    return pcl

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

    if len(sys.argv) == 1:
        fd = NamedTemporaryFile()
        if edit(fd, "TITLE: \nCATEGORIES: \n") == None:
            print "Nothing to do, exiting."
    else:
        parser = OptionParser("Usage: %prog [option] postfile1 postfile2 ...")
        for option in bt.options:
            parser.add_option(*option.args, **option.kwargs)
        (opts, filelist) = parser.parse_args(sys.argv[1:])

    ###########################################################################
    # process any configuration files 
    # do this NOW because option processing requires blog related info
    # like xmlrpc, passwords, etc.
    cf_str = getConfigFileStr(opts.configfile)
    if cf_str == None:
        cf_config = None
    else:
        try:
            cf_config = bt.hdr.parse(cf_str)
        except headerparse.headerParseError, err_str:
            print err_str
            sys.exit()

    bt.setBlogConfig(cf_config)

    ###########################################################################
    for filename in filelist:
        if self.filename != filename:
            self.filename = filename
            print "Processing post file %s..." % self.filename

        try:
            bt.parsePostFile()
        except blogtoolRetry:
            filelist.insert(0, self.filename)
            continue
        except (blogtoolPostFileError, blogtoolHeaderError), err_msg:
            print err_msg
            print "The post in %s cannot be sent to blog." % self.filename
            continue

        for bpc in self.post_config:
            if bt.pushPost(bpc):
                print 'Update post file...'
                self._updateFile()


    sys.exit()

################################################################################
if __name__ == "__main__":
    main()
