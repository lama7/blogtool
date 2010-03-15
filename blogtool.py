#!/usr/bin/python

from optparse import OptionParser
from tempfile import NamedTemporaryFile
from StringIO import StringIO

import xml.etree.cElementTree as etree
import unicodedata as ud

import blogapi

import btconfigparser

import time
import datetime
import re
import sys
import os
import types
import subprocess

try:
    import markdown
except ImportError:
    print """
You need to install python-markdown before you can use blogtool.
"""
    sys.exit()

#try:
#    import BeautifulSoup 
#except ImportError:
#    print """
#You need to install BeautifulSoup before you can use blogtool.
#"""
#    sys.exit()

#################################################################################
#
# bt_options- for processing command line arguments
#
options = [
            {    'optstr_short' : '-a',
                 'optstr_long'  : '--add-categories',
                 'action' : 'store_true',
                 'dest' : 'addcats',
                 'help' : """
Categories specified for the post will be added to the blog's category list if
they do not already exist.
"""
            },
            
            {    'optstr_short' : '-b',
                 'optstr_long'  : '--blog',
                 'action' : 'store',
                 'dest' : "blogname",
                 'help' : """
Blog name for operations on blog.  The name must correspond to a name in
~/.btconfig or a config file specified on the command line.
""" 
            },
             
            {    'optstr_short' : "-c", 
                 'optstr_long'  : "--config", 
                 'action' : 'store',
                 'dest' : "configfile", 
                 'help' : "specify a config file" 
            },
            
            {    'optstr_short' : "-d", 
                 'optstr_long' : '--delete',
                 'action' : 'store',
                 'dest' : "del_postid", 
                 'help' : "delete a post" 
            },
            
            {    'optstr_short' : "-C",
                 'optstr_long'  : "--Categories",
                 'action' : "store_true",
                 'dest' : "getcats",
                 'help' : "Get a list of catgories for a blog" 
            },

            {
                 'optstr_short' : '-g',
                 'optstr_long'  : '--getpost',
                 'action' : 'store',
                 'dest' : 'get_postid',
                 'help' : """
Retrieves a blog post and writes it to STDOUT.  Certain HTML tags are stripped
and an attempt is made to format the text.  A header is also created, meaning
a file capture could be used for updating with blogtool.  
"""                     
            },
            
            {    'optstr_short' : "-s",
                 'optstr_long'  : "--schedule",
                 'action' : 'store',
                 'dest' : "posttime",
                 'help' : "Time to publish post in YYYYmmddHHMMSS format" 
            },
            
            {    'optstr_short' : "-t",
                 'optstr_long'  : "--recent-titles",
                 'action' : 'store',
                 'dest' : "num_recent_t",
                 'help' : "rettrieve recent posts from a blog" 
            },
            
            {    'optstr_short' : "-n",
                 'optstr_long'  : "--new-categories",
                 'action' : 'store',
                 'dest' : "newcat",
                 'help' : "Add a new category to a blog" 
            },
            
            {    'optstr_long' : "--draft",
                 'action' : "store_false",
                 'dest' : "publish",
                 'default' : True,
                 'help' : "Do not publish post.  Hold it as a draft." 
            },
        ]

################################################################################
#   
#   Error classes for blogtool
#

################################################################################
#   
#  define base class for errors
class blogtoolError(Exception):
    pass

################################################################################
#   
#
class blogtoolNoBlogName(blogtoolError):
    def __init__(self):
        self.message = """
There are multple blogs in the config file.  Use the '-b' option to specify
which to use.
"""

    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolBadName(blogtoolError):
    def __init__(self):
        self.message = """
The blog name provided does not match anything in the configuration file.
"""

    def __str__(self):
        return self.message

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

    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolPostFileError(blogtoolError):
    def __init__(self):
        self.message = """
Post file must have a blank line separating header and post text.
"""

    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolDeletePostError(blogtoolError):
    def __init__(self, postid, blogname):
        self.message = "Unable to delete post %s from %s" % (postid, blogname)
    
    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolFNFError(blogtoolError):
    def __init__(self, filename):
        self.message = "File not found: %s" % filename

    def __str__(self):
        return self.message

################################################################################
#   
#
class blogtoolHeaderError(blogtoolError):
    def __init__(self):
        self.message = """
The post file has an invalid header.
"""

    def __str__(self):
        return self.message
        
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
class blogtool():

    ############################################################################ 
    def __init__(self, argv):
        # create config parser object
        self.btconfig = btconfigparser.bt_config()

        # create option parser object
        parser = OptionParser("Usage: %prog [option] postfile1 postfile2 ...")
        for o in options:
            # o is a dict
            if 'optstr_short' not in o.keys():
                parser.add_option(o['optstr_long'], 
                                  action = o['action'],
                                  dest = o['dest'],
                                  default = o['default'],
                                  help = o['help'])
            else:
                parser.add_option(o['optstr_short'],
                                  o['optstr_long'], 
                                  action = o['action'],
                                  dest = o['dest'],
                                  help = o['help'])
        (self.opts, self.filelist) = parser.parse_args(argv)

        # process any configuration files 
        # do this NOW because option processing requires blog related info
        # like xmlrpc, passwords, etc.
        cf_str = configfile(self.opts.configfile)
        if cf_str == None:
            self.cf_config = None
        else:
            try:
                self.cf_config = self.btconfig.parse(cf_str)
            except btconfigparser.btParseError, err_str:
                print err_str
                sys.exit()

    ############################################################################ 
    def doPreOptions(self):
        # option processing to be done independent of post files
        if not (self.opts.del_postid or 
                self.opts.num_recent_t or 
                self.opts.getcats or
                self.opts.newcat or
                self.opts.get_postid):
            return

        # setup bc and blogproxy for option processing
        self.setBlogConfig()

        # now actually check for options to process
        if self.opts.del_postid:
            try:
                self.doOptionDelPost()
            except blogtoolDeletePostError, err_str:
                print err_str

        if self.opts.num_recent_t:
            self.doOptionGetRecent()

        if self.opts.getcats:
            self.doOptionGetCategories()

        if self.opts.newcat:
            self.doOptionAddBlogCategory()

        if self.opts.get_postid:
            self.doOptionGetPost()

    ############################################################################ 
    def doFilelist(self):
        for self.filename in self.filelist:
            print "Processing post file %s..." % self.filename

            try:
                self.doPostFile()
            except blogtoolRetry:
                self.filelist.insert(0, self.filename)
                continue
            except (blogtoolPostFileError, blogtoolHeaderError), err_msg:
                print err_msg
                print "The post in %s will cannot be sent to blog." % \
                                                                   self.filename
                continue

            for bpc in self.post_config:
                self.bc = bpc
                if self.pushPost():
                    print 'Update post file...'
                    self.updateFile()

    ############################################################################ 
    def setBlogConfig(self):
        # this function sets the working blog config
        if self.cf_config == None:
           raise blogtoolNoConfig() 

        if len(self.cf_config) == 1:
            self.bc = self.cf_config[0]
        else:
            if not self.opts.blogname:
                raise blogtoolNoBlogName()
            for bc in self.cf_config:
                if bc.name == self.opts.blogname:
                    self.bc = bc
                    break
            else:
                # the name provided does not match anything in the config file
                raise blogtoolBadName()

        self.blogproxy = blogapi.blogproxy(self.bc.xmlrpc, 
                                           self.bc.username,
                                           self.bc.password)

    ############################################################################ 
    def addCategory(self, c, substart, parentId):
        # subcategories are demarked by '.'
        newcatlist = c.split('.')

        # the isBlogCategory returns a tuple containing the first cat/
        # subcat that is not on the blog.  We cannot assume that the
        # first entry in the list matches the cat returned in the tuple
        # so we'll remove categories/subcats that already exist on
        # the blog
        while substart != newcatlist[0]:
            newcatlist.pop(0)
     
        # now add the categories as needed- init the parent ID field
        # using the value from the tuple returned above
        for c in newcatlist:
            print "Adding %s with parent %s" % (c, parentId)
            parentId = self.blogproxy.newCategory(self.opts.blogname, c, parentId)

    ############################################################################ 
    def doOptionDelPost(self):
        # delete post option processing
    
        # We need a blog to delete from.  If there are multiple blogs specified
        # in the config file, then bail and instruct the user to use the -b
        # option.  If only 1, then use it regardless.  Oh- if multiples, then
        # check if a blog was specified.
        print "Deleting post %s" % self.opts.del_postid

        postid = self.blogproxy.deletePost(self.opts.del_postid)
        if postid == None:
            raise blogtoolDeletePostError(self.opts.del_postid, self.bc.name)


    ############################################################################ 
    def doOptionGetRecent(self):
        # recent post summary option processing
        print "Retrieving %s most recent posts from %s.\n" % (self.opts.num_recent_t,
                                                              self.bc.name)

        recent = self.blogproxy.getRecentTitles(self.bc.name, self.opts.num_recent_t)
        print "POSTID\tTITLE                               \tDATE CREATED"
        print "%s\t%s\t%s" % ('='*6, '='*35, '='*21)
        for post in recent:
            t_converted = datetime.datetime.strptime(post['dateCreated'].value,
                                                     "%Y%m%dT%H:%M:%S")
            padding = ' '*(35 - len(post['title']))
            print "%s\t%s\t%s" % (post['postid'],
                                  post['title'] + padding,
                                  t_converted.strftime("%b %d, %Y at %H:%M"))

        del recent

    ############################################################################ 
    def doOptionGetCategories(self):
        # list blog categories
        print "Retrieving category list for %s." % self.bc.name

        cat_list = self.blogproxy.getCategories(self.bc.name)
        
        print "Category       \tParent        \tDescription"
        print "%s\t%s\t%s" % ('='*14, '='*14, '='*35)
        for cat in cat_list:
           parent = [ c['categoryName'] for c in cat_list 
                                        if cat['parentId'] == c['categoryId'] ]
           str = cat['categoryName'] + ' '*(16 - len(cat['categoryName']))
           if len(parent) == 0:
               str += ' '*16
           else:
               str += parent[0] + ' '*(16 - len(parent[0]))

           str += cat['categoryDescription']
           print str

        del cat_list

    ############################################################################ 
    def doOptionAddBlogCategory(self):
        # add a new category
        print "Checking if category already exists on %s..." % (self.bc.name)

        # this will check the category string to see if it is a valid blog
        # category, or partially valid if sub-categories are specified.
        # If the category exists on the blog, processing stops, otherwise
        # the first part that is not on the blog is returned
        t = blogapi.isBlogCategory(self.blogproxy.getCategories(self.bc.name), 
                                   self.opts.newcat)
        if t == None:
            print "The category specified alread exists on the blog."
        else:
            # t is a tuple with the first NEW category from the category string
            # specified and it's parentId.  Start adding categories from here
            print "Attempting to add %s category to %s" % (self.opts.newcat,
                                                           self.bc.name)
            # the '*' is the unpacking operator
            self.addCategory(self.opts.newcat, *t)

    ############################################################################ 
    def doOptionGetPost(self):
        # retrieve a post from blog
        print "Retrieving post %s from blog %s..." % (self.opts.get_postid, 
                                                      self.bc.name)

        post = self.blogproxy.getPost(self.opts.get_postid)
#        for k,v in post.iteritems():
#            print "%s : %s" % (k, v)
        print repr(post['description'])
        print repr(post['mt_text_more'])

        md = html2md()
        text = md.convert(post['description'])
        if post['mt_text_more']:
            text += "<!--more-->\n\n"
            mdmore = html2md()
            text += mdmore.convert(post['mt_text_more'])

        print text

        sys.exit()

    ############################################################################ 
    def procPost(self):
        # when we run the text through markdown, it will preserve the linefeeds of 
        # the original text.  This is a problem when publishing because the blog
        # software turns the linefeeds within the 'p' tags to 'br' tags which
        # defeats the formatting powers of HTML.  So we'll remove all of the
        # linefeeds in the 'p' tags.  Towards this end, we'll use Beautiful Soup
        # because it streamlines what would otherwise be a tedious process
        tree = etree.XML('<post>%s</post>' % markdown.markdown(self.posttext))
        for e in tree.getiterator():
            if e.text and e.tag not in ['pre', 'code', 'comment']:
                e.text = e.text.replace('\n', u' ')
            if e.tail:
                e.tail = e.tail.replace('\n', u' ')
            if e.tag == 'img':
                ifile = e.attrib['src']
                if ifile.find("http://") == 1:
                    # web resource defined, nothing to do
                    continue
                else:
                    if os.path.isfile(ifile) != 1:
                        ifile = os.path.join(os.path.expanduser('~'), ifile)
                        if os.path.isfile(ifile) != 1:
                            raise blogtoolFNFError(e.attrib['src'])

                # run it up the flagpole
                print "Attempting to upload '%s'..." % ifile
                res = self.blogproxy.upload(self.bc.blogname, ifile)
                if res == None:
                    print "Upload failed, proceeding...\n"
                    continue
                print "Done"

                # replace the image file name in the 'img' tag with the url and also
                # add the 'alt' attribute, assuming it wasn't provided
                e.attrib['src'] = res['url']
                if 'alt' not in e.keys():
                    e.set('alt', res['file'])

                # check for an 'res' attribute and append this to the filename while
                # removing it from the attribute list
                if 'res' in e.keys():
                    res_str = '-' + e.attrib['res'] + '.'
                    e.attrib['src'] = re.sub("\.(\w*)$", r'%s\1' % res_str, e.attrib['src'])
                    
                    # the 'res' attr is bogus- I've added it so that I can specify the
                    # appropriate resolution file I want in the url.  
                    # remove it from the final post
                    del(e.attrib['res'])

#        print etree.tostring(tree)
#        sys.exit()
    
        return (etree.tostring(tree).replace('<post>', '')).replace('</post>', '')

    ############################################################################ 
    def procPostCategories(self):
        # first, build a list of catgories that aren't on the blog from the
        # post's category list
        nonCats = []
        for c in self.bc.categories:
            t = blogapi.isBlogCategory(self.blogproxy.getCategories(self.bc.name), 
                                       c)
            if t != None:
                nonCats.append((c,) + t)

        # see if there were any unrecognized categories
        if len(nonCats) == 0:
            print "Post categories OK"
        elif self.opts.addcats:
            # since the addcat option is processed prior to post processing,
            # we should be able to get away with coopting the opts.blogname
            # and setting it to the current bc.name value without any 
            # repercussions- but check here when some kind of potential funny
            # business starts
            self.opts.blogname = self.bc.name
            [ self.addCategory(*ct) for ct in nonCats ]
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
    def doPostFile(self):
        # since we'll be processing all of this from memory, just read everything
        # into a list.  We won't need it after we process it anyway
        try:
            f = open(self.filename, 'r')
            lines = f.readlines()

        # hopefully, this isn't too clever.  The assumption is that file
        # failed to opend because it doesn't exist.  In this case, open
        # it and launch and editor.  When the editor exits, insert the file
        # to argv list we are iterating over and go back to the top
        except IOError:
            try:
                f = open(self.filename, 'w')
            except IOError, err:
                print err
                sys.exit()

            edit(f)
            raise blogtoolRetry()

        # executed if no exceptions raised
        else:
            f.close()

        # technically, there needs to be at least 3 lines in the file- one for the
        # header, one blank line, one line for post text
        if len(lines) < 3:
            raise blogtoolPostFileError()

        self.header, self.posttext = getHeaderandPostText(lines)

        del lines  # no longer needed

        # now that we have the post header processed, we need to reconcile it
        # with anything from a config file
        try:
            self.post_config = reconcile(self.btconfig.parse(self.header),
                                         self.cf_config)
        except btconfigparser.btParseError, err_str:
            print err_str
            raise blogtoolHeaderError()

    ############################################################################ 
    def pushPost(self):
        # this handles pushing a post up to a blog
        self.blogproxy = blogapi.blogproxy(self.bc.xmlrpc, 
                                           self.bc.username,
                                           self.bc.password)

        posthtml = self.procPost()

        print "Checking post categories..."
        self.bc.categories = self.procPostCategories()

        # now build a post structure
        try:
            post = blogapi.buildPost(self.bc,
                                     posthtml,
                                     timestamp = self.opts.posttime,
                                     publish = self.opts.publish )
        except blogapi.timeFormatError, timestr:
            print timestr
            sys.exit()

        # time to publish, or update...
        if self.bc.postid:
            print "Updating '%s' on %s..." % (self.bc.title, self.bc.name)
            postid = self.blogproxy.editPost(self.bc.postid, post)
            return None

        # sending a new post
        if self.opts.publish:
            print "Publishing '%s' to '%s'" % (self.bc.title,  self.bc.name) 
        else:
            print "Publishing '%s' to '%s' as a draft" % (self.bc.title,
                                                          self.bc.name)

        postid = self.blogproxy.publishPost(self.bc.name, post)
        if postid != None:
            header = self.updateHeader(postid)
            return 1                

    ############################################################################ 
    def updateHeader(self, postid):
        # This function consists of subfunctions that drill into the header string
        # to find where to insert the POSTID info.  Each function returns a 
        # tuple consisting of the next state, the header string that has been
        # processed and the header string yet to be processed

        # state-function to find the BLOG keyword in the header
        def findbloggroup(l):
            # it possible that BLOG will not appear in the header (blog info
            # can also be defined in an rc file or command line options)
            # if we reach the end of the header, just append the POSTID there
            m = re.match('(.*?BLOG\s*\{\s*)(.*)', l, re.DOTALL)
            if m == None:
                # no BLOG groups, so just append the POSTID to the end of the 
                # line/header and we're done
                l += 'POSTID: %s\n' % postid
                return None, l, ''

            return states.index(findblogname), m.group(1), m.group(2)

        # find the NAME keyword in the BLOG group- also checks for the 
        # blogname itself since it's likely the two are on the same line
        def findblogname(l):
            m = re.match('(.*?NAME\s*:\s*|NAME\s*:\s*)([^\n]+)(.*)', l, re.DOTALL)
            if m != None:
                # found NAME keyword in the group
                hdr_ret = m.group(1) + m.group(2)
                if self.bc.name not in hdr_ret:
                    return states.index(findbloggroup), hdr_ret, m.group(3)

                # found the blogname, go to findendgroup
                return states.index(findendgroup), hdr_ret, m.group(3)

            # NAME keyword not in string, so go back to looking for another
            # BLOG group
            return states.index(findendgroup), '', l

        # we've found the group where the POSTID is going to be written,
        # now it's just a matter of finding the end of the group where we'll
        # add it
        def findendgroup(l):
            m = re.match('(.*?)([}])(.*)', l, re.DOTALL)
            hdr_ret = m.group(1)
            hdr_ret += '    POSTID: %s\n' % postid
            hdr_ret += m.group(2) + m.group(3)
            return None, hdr_ret, ''

        #
        # This is where the actual function is implemented- just a simple
        # FSM that processes the header string and inserts what is requied.
        #
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
    def updateFile(self):
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

#################################################################################
class html2md:
    def __init__(self):

        self.out = ''
        self._tags = []  # holds nested tags- not the same as the last
                         # processed tag since tags are removed from the list
                         # when the end of the tag is reached
        self._opened_tags = []
        self._last_processed = None  # last tag processed
        self.bq = ''
        self.ol_tag = 1
        self.reflinks = 0
        self.links = []
        self.start_handlers = dict(
                                   [
                                    ('a', self.a_start),
                                    ('p', self.p_start),
                                    ('blockquote', self.bq_start),
                                    ('code', self.code_start),
                                    ('em', self.em_start),
                                    ('strong', self.strong_start),
                                    ('li', self.li_start),
                                    ('ul', self.ul_start),
                                    ('ol', self.ol_start)
                                   ]
                                  )
        self.end_handlers = dict (
                                  [
                                   ('a', self.a_end),
                                   ('p', self.p_end),
                                   ('blockquote', self.bq_end),
                                   ('li', self.li_end),
                                   ('ul', self.ul_end),
                                   ('ol', self.ol_end)
                                  ] 
                                 )

    def convert(self, html):
        uhtml = ud.normalize('NFKD', unicode(html))

        events = ('start', 'end')
        for action, e in etree.iterparse(StringIO("<post>%s</post>" % uhtml),
                                         events = events):
            if action == 'start':
                self._tag_enter(e.tag)
                if e.tag in self.start_handlers.keys():
                    self.start_handlers[e.tag](e)
                else:
                    self.generic_start_handler(e)
            
            if action == 'end':
                if e.tag in self.end_handlers.keys():
                    self.end_handlers[e.tag](e)
                else:
                    self.generic_end_handler(e)

                self._tag_exit(e.tag)

        return self.out
 
    def _outAppend(self, s):
        # if we're in a blockquote, then prepend the '> '
        if 'blockquote' in self._tags:
            self.out += self.bq

        # make sure that there is text- if the tag starts with, say, a link
        # then text will be None
        if s:
            self.out += s

    def generic_start_handler(self, e):
        if e.text:
            self.out += (e.text.lstrip()).rstrip('\n')

    def generic_end_handler(self, e):
        pass

    def p_start(self, p):
        # if the p-tag occurs within a list, then remove the 
        # trailing '\n' because it will get added on by the p-tag
        # processing
        if self._last_tag() == 'li':
            if self._opened_tags[-2] == 'p':
                self.out += '    '
            else:
                self.out = self.out[:-1]

        self._outAppend(p.text)

    def p_end(self, p):
        if len(self.links) != 0:
            self._outAppend("\n\n%s" % self.reflinkText())
        
        self.out += '\n'
        self._outAppend('\n')

    def bq_start(self, bqe):
        self.bq += '> '

    def bq_end(self, bqe):
        self.bq = self.bq[2:]
        self.out = self.out[:-4]
        
        self.out += '\n'
        if not self.bq:
            self.out += '\n'

    def a_start(self, a):
        pass

    def a_end(self, a):
        # first, put the text together
        self._outAppend("[%s][%s]" % (a.text, self.reflinks))
        self._outAppend(self._checktail(a))

        # now, save off reflink and link itself
        if 'title' not in a.attrib.keys():
            a.set('title', None)

        self.links.append((self.reflinks, a.attrib['href'], a.attrib['title']))
        self.reflinks += 1

    def code_start(self, code):
        last_tag = self._last_tag()
        if last_tag == 'p':
            self._outAppend(self.convert_inline(code, '`'))
        elif last_tag == 'pre':
            for line in code.text.split('\n'):
                self._outAppend('    %s\n' % line)

    def em_start(self, em):
        # if the text ends with a space, then add it after the *
        self._outAppend(self.convert_inline(em, '*'))

    def strong_start(self, strong):
        self._outAppend(self.convert_inline(strong, '**'))

    def li_start(self, li):
        last_tag = self._last_tag()
        if last_tag == 'ul':
            self._outAppend('* %s' % li.text)
        elif last_tag == 'ol':
            self._outAppend('%s.  %s' % (self.ol_tag, li.text))
            self.ol_tag += 1

    def li_end(self, li):
        # we don't need to advance the line if we are in a list and 
        # processing a p-tag- the p-tag processing will add linefeeds
        if (self._opened_tags[-2] not in [ 'ul', 'ol' ] and
            self._last_processed == 'p'):
            pass
        else:
            # advance line for next list item
            self.out += '\n'

    def ol_start(self, ol):
        pass

    def ol_end(self, ol):
        if ol.tail and not ol.tail.isspace():
            self._outAppend(ol.tail)
        if self._opened_tags[-1] != 'p':
            self._outAppend('\n')
        self.ol_tag = 1

    def ul_start(self, ul):
        pass

    def ul_end(self, ul):
        if ul.tail and not ul.tail.isspace():
            self._outAppend(ul.tail)
        self._outAppend('\n')

    def convert_inline(self, e, c):
        addspace = False
        if e.text.endswith(' '):
            addspace = True

        text = "%s%s%s" % (c, e.text.rstrip(), c)
        if addspace:
            text += ' '

        text += self._checktail(e)

        return text

    def _checktail(self, element):
        if element.tail and not element.tail.isspace():
            return element.tail
        else:
            return ''

    def reflinkText(self):
        text = ''
        for ref in self.links:
            text += "[%s]: %s" % (ref[0], ref[1])
            if ref[2] != None:
                text += ''' "%s"''' % (ref[2])
            text += '\n'

        del self.links[:]

        return text.rstrip()

    def _tag_enter(self, t):
        self._tags.append(t)
        self._opened_tags.append(t)

    def _tag_exit(self, t):
        if self._current_tag() != t:
            print "Stack Error: %s versus current %s" % (self._current_tag, t)
            print self._tags
            sys.exit()
        else:
            self._last_processed = self._tags.pop()  # remove current tag

    def _current_tag(self):
        ntags = len(self._tags)
        if ntags > 0:
            return self._tags[ntags - 1]
        else:
            return None

    def _last_tag(self):
        ntags = len(self._tags)
        if ntags > 1:
            return self._tags[ntags - 2]
        else:
            return None

    def _last_opened(self):
        return self._opened_tags[-2]

#################################################################################
## entry function for processing post text- image links and what not are
## dealt with here
##
#def procPost(blog, blogname,  posttext):
#
#    # helper function for comprehension below
#    def skiptag(tag):
#        return (isinstance(tag, BeautifulSoup.Comment) or
#                tag.parent.name == 'pre' or
#                tag.parent.name == 'code')
#
#    # when we run the text through markdown, it will preserve the linefeeds of 
#    # the original text.  This is a problem when publishing because the blog
#    # software turns the linefeeds within the 'p' tags to 'br' tags which
#    # defeats the formatting powers of HTML.  So we'll remove all of the
#    # linefeeds in the 'p' tags.  Towards this end, we'll use Beautiful Soup
#    # because it streamlines what would otherwise be a tedious process
#    soup = BeautifulSoup.BeautifulSoup(markdown.markdown(posttext))
#
#    # remove extraneous newlines from the NavigableStrings (text)
#    # for better or worse, I'll leave extra space (i.e. multiple consecutive
#    # space characters) alone, for now.  Browser's get rid of the space so it 
#    # doesn't seem to hurt anyone if I leave it in place
#    # don't do this for 'pre' tags
#    souptext = soup.findAll(text = True) 
#    [ t.replaceWith(t.replace('\n', ' ')) for t in souptext if not skiptag(t) ]
#
#    # now deal with all the 'img' tags
#    for img in soup.findAll('img'):
#        # first, make sure this looks like a valid file
#        imgf = img['src']
#        if imgf.find("http://") == -1:
#            if os.path.isfile(imgf) != 1:
#                # try anchoring file to the user's home directory       
#                imgf = os.path.expanduser('~') + '/' + imgf
#                if os.path.isfile(imgf) != 1:
#                    error("Image file not found: %s\n" % img['src'])
#        else:
#            # this is a link so don't proceed any further, move on to the next
#            continue
#
#        # run it up the flagpole...
#        print "Attempting to upload '%s'..." % imgf
#        res = blog.upload(blogname, imgf)
#        if res == None:
#            print "Upload failed, proceeding...\n"
#            continue
#        print "Done"
#
#        # replace the image file name in the 'img' tag with the url and also
#        # add the 'alt' attribute, assuming it wasn't provided
#        # check for an 'res' attribute and append this to the filename while
#        # removing it from the attribute list
#        img['src'] = res['url']
#        if not img.has_key('alt'):
#            img['alt'] = res['file']
#
#        if img.has_key('res'):
#            res_str = '-' + img['res'] + '.'
#            img['src'] = re.sub("\.(\w*)$", r'%s\1' % res_str, img['src'])
#            
#            # the 'res' attr is bogus- I've added it so that I can specify the
#            # appropriate resolution file I want in the url.  
#            # remove it from the final post
#            del(img['res'])
#
#    return soup.renderContents()
#

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
def configfile(cfile):
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

    # if there is no config file, then we don't have to do anything
    if cfcl == None:
        return pc
    
    for pc in pcl:
        cf = None
        # first see if a name is supplied
        if pc.name != '':
            for cfc in cfcl:
                if cfc.name == pc.name:
                    cf = cfc
                    break
            # make sure we found a match
            if cf == None:
                continue  # nothing to do if we didn't find a match
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
# split the file into 2 sections- the header and the post
# divider is the first blank line encountered
#
def getHeaderandPostText(linelist):
    # find first blank line so we can split the list
    for line in linelist:
        if line.isspace():
            i = linelist.index(line)
            break

    return ''.join(linelist[0:i]), ''.join(linelist[i + 1:])


################################################################################
#
#
def edit(fh):
    editor = os.getenv('EDITOR', 'editor')

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
    # if there are no arguments, then launch an editor, then proceed with the
    # file generated by the editor, otherwise, proceed normally
    if len(sys.argv) == 1:
        fd = NamedTemporaryFile()
        if edit(fd) != None:
            bt = blogtool([fd.name])
        else:
            print "Nothing to do, exiting."
    else:
        bt = blogtool(sys.argv[1:])

    # process option that are independent of post files
    bt.doPreOptions()

    # now process the postfile, if any
    bt.doFilelist()

    print 'Done.'
    sys.exit()

################################################################################
#
# nothing special here...
if __name__ == "__main__":
    main()
