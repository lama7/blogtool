from headerparse import headerError
from proxybase import proxyError

import sys
import html2md
import utils
import datetime
import os

################################################################################
#
def _getProxy(header):
    try:
        p = header.proxy()
    except headerError, err:
        print err
        sys.exit()

    return p

################################################################################
#
#  Base Class for handling command line options
#
class btOption:
    args = ()  # to be overridden by the option
    kwargs = {}  # to be overriden by the option

    # this method should check the relevant option and return True if the 
    # option should be processed, False otherwise
    # the 'opts' arg is the Values object returned by the OptParse parser.
    # if the option is present and stores a value that is needed when the option
    # is run, then the value should be squirreled away in an instance attribute
    def check(self, opts):
        pass

    # this method performs the actual option processing.  It does not return any
    # error codes- any errors should raise the btOptionError exception
    # the 'opts' arg will be the Values object returned by the OptParse parser.
    # the 'proxy' arg will be a proxy object for communicating with the blog
    # if necessary 
    def run(self, header):
        pass
        
################################################################################
'''
    DeletePost

        Define class to handle deleting posts from a blog.

'''
class DeletePost(btOption):
    args = ('-d', '--delete')
    kwargs = {
              'action' : 'store',
              'dest' : "del_postid", 
              'help' : "delete a post" 
             }

    ############################################################################ 
    def check(self, opts):
        if opts.del_postid:
            self.postid = opts.del_postid
            return True

        return False

    ############################################################################ 
    def run(self, header):
        print "Deleting post %s" % self.postid

        proxy = _getProxy(header)
        try:
            postid = proxy.deletePost(self.postid)
        except proxyError, err:
            print "Caught in options.DeletePost.run:"
            print err
            sys.exit()

################################################################################
'''
    GetRecentTitles

        Define class to handle retrieving recent blog post info and displaying
        it to stdout.
'''
class GetRecentTitles(btOption):
    args = ('-t', '--recent-titles')
    kwargs = {
              'action' : 'store',
              'dest' : "num_recent_t",
              'help' : "rettrieve recent posts from a blog" 
             }

    ############################################################################ 
    def check(self, opts):
        if opts.num_recent_t:
            self.count = opts.num_recent_t
            return True

        return False

    ############################################################################ 
    def run(self, header):
        try:
            self._getRecentTitles(header)
        except headerError, err:
            if err.code != headerError.MULTIPLEBLOGS:
                print err
                sys.exit()
            else:
                for hdr in header:
                    self._getRecentTitles(hdr)

    def _getRecentTitles(self, header):
        proxy = header.proxy()
        blogname = header.name
        print "\nRetrieving %s most recent posts from blog '%s'.\n" % (self.count,
                                                                     blogname)
        try:
            recent = proxy.getRecentTitles(self.count)
        except proxyError, err:
            print "Caught in options.GetRecentTitles.run:"
            print err
            sys.exit()

        print "POSTID\tTITLE                               \tDATE CREATED"
        print "%s\t%s\t%s" % ('='*6, '='*35, '='*21)
        for post in recent:
            t_converted = datetime.datetime.strptime(post['dateCreated'].value,
                                                     "%Y%m%dT%H:%M:%S")
            padding = ' '*(35 - len(post['title']))
            print "%s\t%s\t%s" % (post['postid'],
                                  post['title'] + padding,
                                  t_converted.strftime("%b %d, %Y at %H:%M"))


################################################################################
'''
    GetCategories

        Define class to handle retrieving category list from a blog and 
        displaying is to stdout.

'''
class GetCategories(btOption):
    args = ('-C', '--Categories')
    kwargs = {
              'action' : "store_true",
              'dest' : "getcats",
              'help' : "Get a list of catgories for a blog" 
             }

    ############################################################################ 
    def check(self, opts):
        return bool(opts.getcats)

    ############################################################################ 
    def run(self, header):
        proxy = _getProxy(header)
        print "Retrieving category list for '%s'." % header.name

        try:
            cat_list = proxy.getCategories()
        except proxyError, err:
            print "Caught in options.GetCategories.run:"
            print err
            sys.exit()

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

################################################################################
''' 
    AddCategory

        Define class to handle adding a category to a blog

'''
class AddCategory(btOption):
    args = ('-n', '--new-categories')
    kwargs = {
              'action' : 'store',
              'dest' : "newcat",
              'help' : "Add a new category to a blog" 
             }

    ############################################################################ 
    def check(self, opts):
        if opts.newcat:
            self.catname = opts.newcat
            return True

        return False

    ############################################################################ 
    def run(self, header):
        proxy = _getProxy(header)
        blogname = header.name
        print "Checking if category already exists on '%s'..." % (blogname)

        # this will check the category string to see if it is a valid blog
        # category, or partially valid if sub-categories are specified.
        # If the category exists on the blog, processing stops, otherwise
        # the first part that is not on the blog is returned
        try:
            blogcats = proxy.getCategories()
        except proxyError, err:
            print "Caught in options.AddCategory.run:"
            print err
            sys.exit()

        t = utils.isBlogCategory(blogcats, self.catname)
        if t == None:
            print "The category specified alread exists on the blog."
        else:
            # t is a tuple with the first NEW category from the category string
            # specified and it's parentId.  Start adding categories from here
            print "Attempting to add '%s' category to blog '%s'" % (self.catname,
                                                                   blogname)
            # the '*' is the unpacking operator
            utils.addCategory(proxy, self.catname, *t)

################################################################################
'''
    UploadMediaFile

'''
class UploadMediaFile(btOption):
    args = ('-u', '--uploadmedia')
    kwargs = {
              'action' : 'store',
              'dest' : 'uploadfile',
              'help' : "Upload a file to a blog"
             }

    ############################################################################ 
    def check(self, opts):
        if opts.uploadfile:
            self.uploafile = opts.uploadfile
            return True

        return False

    ############################################################################ 
    def run(self, header):
        try:
            proxy = _getProxy(header)
            uf = utils.chkFile(opts.uploadfile)
            print "Attempting to upload '%s'..." % uf
            res = proxy.upload(uf)
        except utils.utilsError, err:
            print "File not found: %s" % err
        except proxyError, err:
            print "Caught in options.UploadMediaFile"
            print err

################################################################################
'''
    GetPost
       
        Define class to handle retrieving a post from a blog given the post's
        ID and printing the result to stdout.
     
'''
class GetPost(btOption):
    args = ('-g', '--getpost')
    kwargs = {
              'action' : 'store',
              'dest' : 'get_postid',
              'help' : """
Retrieves a blog post and writes it to STDOUT.  Certain HTML tags are stripped
and an attempt is made to format the text.  A header is also created, meaning
a file capture could be used for updating with blogtool.  
"""            
             }

    
    ############################################################################ 
    def check(self, opts):
        if opts.get_postid:
            self.postid = opts.get_postid
            return True

        return False

    ############################################################################ 
    def run(self, header):
        if not html2md.LXML_PRESENT:
            print "Option not supported without python-lxml library."
            return

        proxy = _getProxy(header)
        try:
            post = proxy.getPost(self.postid)
        except proxyError, err:
            print "Caught in options.GetPost.run:"
            print err
            sys.exit()

        if post['mt_text_more']:
            text = html2md.convert("%s%s%s" % (post['description'], 
                                               "<!--more-->",
                                               post['mt_text_more']))
        else:
            text = html2md.convert(post['description'])

        print 'BLOG: %s\nPOSTID: %s\nTITLE: %s\nCATEGORIES: %s' % ( header.name, 
                                                                    self.postid, 
                                                                  post['title'], 
                                                  ', '.join(post['categories']))
        if post['mt_keywords']:
            print 'TAGS: %s' % post['mt_keywords']

        print '\n' + text

################################################################################
'''
    SetConfigFile

        Define class to handle parsing of a config file for blogtool.

'''
class SetConfigFile(btOption):
    args = ('-c', '--config')
    kwargs = { 
              'action' : 'store',
              'dest' : "configfile", 
              'help' : "specify a config file" 
             }

    ############################################################################ 
    def check(self, opts):
        if opts.configfile:
            self.configfile = opts.configfile

        # a hack- the run method here must always execute, so the check here 
        # should always return True
        return True

    ############################################################################ 
    def run(self, header):
        if not hasattr(self, 'configfile'): 
            rcf = os.path.join(os.path.expanduser('~'), '.btrc')    
            if not os.path.isfile(rcf):
                return 
        else:
           try:
               rcf = utils.chkFile(self.configfile)
           except utils.utilsError, err:
               print "Config file not found: %s" % self.configfile
               sys.exit(1)

        try:
            f = open(rcf, 'r')
            hdrstr = ''.join(f.readlines())
        except IOError:
            print "Unable to open config file: %s" % self.configfile
            sys.exit(1)
        else:
            f.close()

        if hdrstr:
            header.setDefaults(hdrstr)
   
################################################################################
'''
    SetAddCategory

        Define class that sets flag indicating to add categories specified in
        blog post that are not on the blog.

'''
class SetAddCategory(btOption):
    args = ('-a', '--add-categories')
    kwargs = {
              'action' : 'store_true',
              'dest' : 'addcats',
              'help' : """
Categories specified for the post will be added to the blog's category list if
they do not already exist.
"""
             }

    ############################################################################ 
    def check(self, opts):
        self.addpostcats = opts.addcats
        return opts.addcats

    ############################################################################ 
    def run(self, header):
        return 'runeditor'

################################################################################
'''
    SetBlogname

        Define class for option that specfies blog to use if multiple blogs 
        setup in config file.
'''
class SetBlogname(btOption):
    args = ('-b','--blog')
    kwargs = {
              'action' : 'store',
              'dest' : "blogname",
              'help' : """
Blog name in config file for operations on blog.  The name must correspond to a name
in ~/.btrc or a config file specified on the command line.
"""  
             }

    ############################################################################ 
    def check(self, opts):
        if opts.blogname:
            self.blogname = opts.blogname
            return True

        return False

    ############################################################################ 
    def run(self, header):
        try:
            header.setBlogParmsByName(self.blogname)
        except headerError, err:
            print err
            sys.exit()

################################################################################
'''
    SetPosttime

        Define class for option to schedule when a post should be published.
'''
class SetPosttime(btOption):
    args = ('-s', '--schedule')
    kwargs = {
              'action' : 'store',
              'dest' : "posttime",
              'help' : """
Time to publish post, a number of formats are supported:  YYYYMMDDThh:mm, 
YYYYMMDDThh:mmAM/PM, YYYYMMDDThh:mm:ss, YYYYMMDDThh:mm:ssAM/PM,
Month Day, Year hour:min, Month Day, Year hour:min AM/PM, MM/DD/YYYY hh:mm,
MM/DD/YYYY hh:mmAM/PM, hh:mm MM/DD/YYYY, hh:mmAM/PM MM/DD/YYYY
""" 
             }

    ############################################################################ 
    def check(self, opts):
        self.posttime = opts.posttime
        if opts.posttime:
            return True
        else:
            return False

    ############################################################################ 
    def run(self, header):
        return 'runeditor'

################################################################################
'''
    SetNoPublish

        Define class for option to write post to blog as a draft.
'''
class SetNoPublish(btOption):
    args = ('--draft', )
    kwargs = {
              'action' : "store_false",
              'dest' : "publish",
              'default' : True,
              'help' : "Do not publish post.  Hold it as a draft." 
             }

    ############################################################################ 
    def check(self, opts):
        self.publish = opts.publish
        if not opts.publish:
            return True
        else:
            return False

    ############################################################################ 
    def run(self, header):
        return 'runeditor'

################################################################################
class SetAllBlogs(btOption):
    args = ('-A', '--allblogs')
    kwargs = {
              'action' : "store_true",
              'dest' : "allblogs",
              'default' : False,
              'help' : """
Will cause post to be published to all blogs listed in the rc file.
"""
             }

    ############################################################################ 
    def check(self, opts):
        self.allblogs = opts.allblogs
        if opts.allblogs:
            return True
        else:
            return False

    ############################################################################ 
    def run(self, header):
        return 'runeditor'

################################################################################
#
#  function to return a list of option objects
#
#  For new options, simply append an instance to the list
def getOptions():
    o_list = []
    o_list.append(SetConfigFile())  # should always be first in list
    o_list.append(SetBlogname())    # should always be second in list
    o_list.append(SetAddCategory())
    o_list.append(SetNoPublish())
    o_list.append(SetPosttime())
    o_list.append(SetAllBlogs())
    o_list.append(DeletePost())
    o_list.append(GetRecentTitles())
    o_list.append(GetCategories())
    o_list.append(AddCategory())
    o_list.append(GetPost())
    o_list.append(UploadMediaFile())

    return o_list
