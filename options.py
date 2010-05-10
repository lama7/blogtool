import html2md
import blogutils
import datetime

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
    def run(self, proxy, blogname):
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
    def run(self, proxy, blogname):
        print "Deleting post %s" % opts.del_postid

        # We need a blog to delete from.  If there are multiple blogs specified
        # in the config file, then bail and instruct the user to use the -b
        # option.  If only 1, then use it regardless.  Oh- if multiples, then
        # check if a blog was specified.
        postid = proxy.deletePost(opts.del_postid)

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
    def run(self, proxy, blogname):
        print "Retrieving %s most recent posts from %s.\n" % (self.count,
                                                              blogname)

        # this does the heavy lifting
        recent = proxy.getRecentTitles(blogname, self.count)

        # now do some formatting of the returned info prior to printing
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
    def run(self, proxy, blogname):
        # list blog categories
        print "Retrieving category list for %s." % blogname

        cat_list = proxy.getCategories(blogname)
        
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
    def run(self, proxy, blogame):
        # add a new category
        print "Checking if category already exists on %s..." % (blogname)

        # this will check the category string to see if it is a valid blog
        # category, or partially valid if sub-categories are specified.
        # If the category exists on the blog, processing stops, otherwise
        # the first part that is not on the blog is returned
        t = blogutils.isBlogCategory(proxy.getCategories(blogname), 
                                     self.catname)
        if t == None:
            print "The category specified alread exists on the blog."
        else:
            # t is a tuple with the first NEW category from the category string
            # specified and it's parentId.  Start adding categories from here
            print "Attempting to add %s category to %s" % (self.catname,
                                                           blogname)
            # the '*' is the unpacking operator
            blogutils.addCategory(proxy, blogname, self.catname, *t)

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
    def run(self, proxy, blogname):
        if not html2md.LXML_PRESENT:
            print "Option not supported without python-lxml library."
            return

        # retrieve a post from blog
        post = proxy.getPost(self.postid)
        if post['mt_text_more']:
            text = html2md.convert("%s%s%s" % (post['description'], 
                                               "<!--more-->",
                                               post['mt_text_more']))
        else:
            text = html2md.convert(post['description'])

        print 'BLOG: %s\nPOSTID: %s\nTITLE: %s\nCATEGORIES: %s' % (
               self.bc.name, 
               postid, 
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
            return True
 
        return False

    ############################################################################ 
    def run(self, proxy, blogname):
        # cfile will be a filename or None
        if not hasattr(self, 'configfile'): 
            cfile = os.path.join(os.path.expanduser('~'), '.btconfig')    
            if os.path.isfile(self.configfile) != 1:
                return None
        else:
           # it's possible the user supplied a fully qualified path, so check if
           # the file exists
           if os.path.isfile(self.configfile) != 1:
               # try anchoring file to the user's home directory       
               cfile = os.path.join(os.path.expanduser('~'), self.configfile)
               if os.path.isfile(self.configfile) != 1:
                   print "Unable to open config file: %s"
                   sys.exit(1)

        # open the file
        try:
            f = open(self.configfile, 'r')
            # config file format is identical to header, so convert file lines
            # to a string and then return a config objct
            config_str = ''.join(f.readlines())
        except IOError:
            print "Unable to open config file: %s" % self.configfile
            sys.exit(1)
        else:
            f.close()

        return config_str 

   
################################################################################
'''
    SetAddCatgory

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
        return bool(opts.addcats)
          

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
Blog namconfigfilee for operations on blog.  The name must correspond to a name in
~/.btconfig or a config file specified on the command line.
"""  
                 }

    ############################################################################ 
    def check(self, opts):
        if opts.blogname:
            self.blogname = opts.blogname
            return True

        return False

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
                  'help' : "Time to publish post in YYYYmmddHHMMSS format" 
                 }

    ############################################################################ 
    def check(self, opts):
        if opts.posttime:
            self.posttime = opts.posttime
            return True

        return False

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
        return bool(opts.publish)

################################################################################
#
#  function to return a list of option objects
#
#  For new options, simply append an instance to the list
def getOptions():
    o_list = []
    o_list.append(SetConfigFile())
    o_list.append(SetBlogname())
    o_list.append(SetAddCategory())
    o_list.append(SetNoPublish())
    o_list.append(SetPosttime())
    o_list.append(DeletePost())
    o_list.append(GetRecentTitles())
    o_list.append(GetCategories())
    o_list.append(AddCategory())
    o_list.append(GetPost())

    return o_list
