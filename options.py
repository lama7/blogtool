from headerparse import HeaderError
from proxybase import ProxyError
from fileprocessor import FileProcessor, FileProcessorError

from optparse import OptionParser

import html2md
import utils

import sys
import datetime
import os

################################################################################
#
def _getProxy(header):
    try:
        p = header.proxy()
    except HeaderError, err:
        print err
        sys.exit()

    return p

################################################################################
'''
    Base Class for handling command line options
'''
class CommandLineOption:
    args = ()  # to be overridden by the option
    kwargs = {}  # to be overriden by the option

    '''
    This method should check the relevant option and return True if the 
    option should be processed, False otherwise
    the 'opts' arg is the Values object returned by the OptParse parser.
    if the option is present and stores a value that is needed when the option
    is run, then the value should be squirreled away in an instance attribute
    '''
    def check(self, opts):
        pass

    '''
    This method performs the actual option processing.  It does not return any
    error codes- any errors should raise the CommandLineOptionError exception
    the 'opts' arg will be the Values object returned by the OptParse parser.
    the 'proxy' arg will be a proxy object for communicating with the blog
    if necessary 
    '''
    def run(self, header):
        pass
        
################################################################################
'''
    DeletePost

        Define class to handle deleting posts from a blog.

'''
class DeletePost(CommandLineOption):
    args = ('-d', '--delete')
    kwargs = {
              'action' : 'store',
              'dest' : "del_postid", 
              'help' : "delete a post" 
             }

    def check(self, opts):
        if opts.del_postid:
            self.postid = opts.del_postid
            return True

        return False

    def run(self, header):
        print "Deleting post %s" % self.postid

        proxy = _getProxy(header)
        try:
            postid = proxy.deletePost(self.postid)
        except ProxyError, err:
            print "Caught in options.DeletePost.run:"
            print err
            sys.exit()

        return None

################################################################################
'''
    DeleteComment
'''
class DeleteComment(CommandLineOption):
    args = ('-D', '--deletecomment')
    kwargs = {
              'action' : 'store',
              'dest' : 'del_comment_id',
              'help' : 'Delete a comment from a blog'
             }

    def check(self, opts):
        if opts.del_comment_id:
            self.comment_id = opts.del_comment_id
            return True
        return False
        
    def run(self, header):
        print "Deleting comment %s" % self.comment_id

        proxy = _getProxy(header)
        try:
            postid = proxy.deleteComment(self.comment_id)
        except ProxyError, err:
            print "Caught in options.DeleteComment.run:"
            print err
            sys.exit

        return None

################################################################################
'''
    GetRecentTitles

        Define class to handle retrieving recent blog post info and displaying
        it to stdout.
'''
class GetRecentTitles(CommandLineOption):
    args = ('-t', '--recent-titles')
    kwargs = {
              'action' : 'store',
              'dest' : "num_recent_t",
              'help' : "rettrieve recent posts from a blog" 
             }

    def check(self, opts):
        if opts.num_recent_t:
            self.count = opts.num_recent_t
            return True

        return False

    def run(self, header):
        try:
            self._getRecentTitles(header)
        except HeaderError, err:
            if err.code != HeaderError.MULTIPLEBLOGS:
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
        except ProxyError, err:
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

        return None


################################################################################
'''
    GetCategories

        Define class to handle retrieving category list from a blog and 
        displaying is to stdout.

'''
class GetCategories(CommandLineOption):
    args = ('-C', '--Categories')
    kwargs = {
              'action' : "store_true",
              'dest' : "getcats",
              'help' : "Get a list of catgories for a blog" 
             }

    def check(self, opts):
        return bool(opts.getcats)

    def run(self, header):
        proxy = _getProxy(header)
        print "Retrieving category list for '%s'." % header.name

        try:
            cat_list = proxy.getCategories()
        except ProxyError, err:
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

        return None

################################################################################
''' 
    AddCategory

        Define class to handle adding a category to a blog

'''
class AddCategory(CommandLineOption):
    args = ('-n', '--new-categories')
    kwargs = {
              'action' : 'store',
              'dest' : "newcat",
              'help' : "Add a new category to a blog" 
             }

    def check(self, opts):
        if opts.newcat:
            self.catname = opts.newcat
            return True

        return False

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
        except ProxyError, err:
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

        return None

################################################################################
'''
    UploadMediaFile

'''
class UploadMediaFile(CommandLineOption):
    args = ('-u', '--uploadmedia')
    kwargs = {
              'action' : 'store',
              'dest' : 'uploadfile',
              'help' : "Upload a file to a blog"
             }

    def check(self, opts):
        if opts.uploadfile:
            self.uploadfile = opts.uploadfile
            return True

        return False

    def run(self, header):
        try:
            proxy = _getProxy(header)
            uf = utils.chkfile(self.uploadfile)
            print "Attempting to upload '%s'..." % uf
            res = proxy.upload(uf)
        except utils.UtilsError, err:
            print "File not found: %s" % err
        except ProxyError, err:
            print "Caught in options.UploadMediaFile"
            print err

        return None

################################################################################
'''
    GetPost
       
        Define class to handle retrieving a post from a blog given the post's
        ID and printing the result to stdout.
     
'''
class GetPost(CommandLineOption):
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

    catID = 0
    parentID = 1

    def check(self, opts):
        if opts.get_postid:
            self.postid = opts.get_postid
            return True

        return False

    def run(self, header):
        if not html2md.LXML_PRESENT:
            print "Option not supported without python-lxml library."
            return

        proxy = _getProxy(header)
        try:
            post = proxy.getPost(self.postid)
            self.blogcats = proxy.getCategories()
        except ProxyError, err:
            print "Caught in options.GetPost.run:"
            print err
            sys.exit()

        if post['mt_text_more']:
            text = html2md.convert("%s%s%s" % (post['description'], 
                                               "<!--more-->",
                                               post['mt_text_more']))
        else:
            text = html2md.convert(post['description'])
        header_str = 'BLOG: %s\nPOSTID: %s\nTITLE: %s\n' % (header.name, 
                                                            self.postid, 
                                                            post['title'])
        header_str += 'CATEGORIES: %s\n' % self._buildCatStr(post['categories'])
        if post['mt_keywords']:
            header_str += 'TAGS: %s\n' % post['mt_keywords']
        print header_str + '\n' + text
        return None

    def _buildCatStr(self, catlist):
        blogcats_d = {cat['categoryName']:(cat['categoryId'], cat['parentId'])
                                                       for cat in self.blogcats}
        catlist = self._sortCats(catlist, blogcats_d)
        cat_s = ''
        # We need to convert the category list into a dot-delimited category
        # string if there are subcategories, or not depending on the categories
        # in the list- luckliy, the category list is sorted appropriately for us
        if len(catlist) == 1:
            cat_s = catlist[0]
        else:
            for cat in catlist:
               if blogcats_d[cat][self.parentID] == '0':
                   if cat_s == '':
                      cat_s += "%s" % cat
                   else:
                      cat_s += ", %s" % cat
               else:
                   cat_s += ".%s" % cat
        return cat_s

    def _sortCats(self, catlist, bcats_d):
        ''' Sorts catlist from category to lowest subcategory.  If multiple
            subcategories have a common parent, then the category hierarchy is
            duplicated and added to the list with the new subcategory.
        '''
        sortedcats = []
        while len(catlist) != 0:
            for cat in catlist[:]:
                cat_parent_id = bcats_d[cat][self.parentID]
                if cat_parent_id == '0':
                    sortedcats.append(cat)
                    catlist.remove(cat)
                else:
                    enumerated_seq = list(enumerate(sortedcats))
                    for i, s_cat in enumerated_seq:
                        if cat_parent_id == bcats_d[s_cat][self.catID]:
                            # does this subcategory have the same parent as 
                            # another subcatgory?
                            if len(sortedcats) > i+1 and \
                               bcats_d[sortedcats[i+1]][self.parentID] == \
                                                                  cat_parent_id:
                                # find the top of the category hierarchy
                                # i is the index of the parent of cat
                                while bcats_d[sortedcats[i]][self.parentID] != \
                                                                            '0':
                                    i = i - 1
                                j = i # mark insertion point into sortedlist
                                # copy category hierarchy
                                hierarchycopy = []
                                while bcats_d[sortedcats[i]][self.parentID] != \
                                      cat_parent_id:
                                    hierarchycopy.insert(0, sortedcats[i])
                                    i = i + 1
                                hierarchycopy.insert(0, cat) # add new cat
                                # insert copy into sorted list
                                for c in hierarchycopy:
                                    sortedcats.insert(j, c)
                                catlist.remove(cat)
                                break
                            else:
                                sortedcats.insert(i+1, cat)
                                catlist.remove(cat)
                                break
                        elif bcats_d[cat][self.catID] == \
                                                  bcats_d[s_cat][self.parentID]:
                            sortedcats.insert(i-1, cat)
                            catlist.remove(cat)
                            break
        return sortedcats
                    

################################################################################
'''
    GetComments
'''
class GetComments(CommandLineOption):
    args = ('-r', '--readcomments')
    kwargs = {
              'action' : 'store',
              'dest' : 'comments_postid',
              'help' : """
Retrieves the comments for a specific post.
"""
             }

    def check(self, opts):
        if opts.comments_postid:
            self.postid = opts.comments_postid
            return True

        return False

    def run(self, header):
        proxy = _getProxy(header)

        comments = proxy.getComments(self.postid)
        comments.reverse()
        for comment in comments:
            t_converted = datetime.datetime.strptime(comment['date_created_gmt'].value,
                                                     "%Y%m%dT%H:%M:%S")
            output = 'Comment ID: %s\n' % comment['comment_id']
            output += 'Parent ID:  %s\n' % comment['parent']
            output += 'Time:       %s\n' % t_converted
            output += 'Author:     %s\n' % comment['author']
            output += 'Email:      %s\n' % comment['author_email']
            output += 'URL:        %s\n' % comment['author_url']

            content = html2md.convert(comment['content'])
            print output + '\n' + content

        return None

################################################################################
'''
    EditComment

    Class to handle editing of comments.
'''
class EditComment(CommandLineOption):
    args = ('--editcomment', )
    kwargs = {
              'action' : 'store',
              'dest' : 'commentid',
              'help' : "Edit a comment already on the blog."
             }

    def check(self, opts):
        if opts.commentid:
            self.commentid = opts.commentid
            return True
        return False

    def run(self, header):
        proxy = _getProxy(header)
        comment = proxy.getComment(self.commentid)
        commenttext = "COMMENTID: %s\n" % (self.commentid)
        commenttext += "PARENTID: %s\n" % (comment['parent'])
        commenttext += "COMMENTSTATUS: %s\n" % (comment['status'])
        commenttext += "AUTHOR: %s\n" % (comment['author'])
        if comment['author_url']:
            commenttext += "AUTHORURL: %s\n" % (comment['author_url'])
        commenttext += "AUTHOREMAIL: %s\n" % (comment['author_email'])
        commenttext += "\n%s" % (html2md.convert(comment['content']))
        
        fd = utils.edit(commenttext)
        if fd == None:
            print "Nothing to do with comment."
        fp = FileProcessor(**{'comment' : True,
                              'allblogs' : False})
        try:
            header_text, commenttext = fp.parsePostFile(fd.name, '')
        except FileProcessorError, err_msg:
            print err_msg
            sys.exit()
        
        header.addParms(header_text, False)
        rval = fp.pushContent(commenttext, header)
        if rval:
            print "Comment %s updated." % self.commentid

        return None

################################################################################
'''
    SetConfigFile

        Define class to handle parsing of a config file for blogtool.

'''
class SetConfigFile(CommandLineOption):
    args = ('-c', '--config')
    kwargs = { 
              'action' : 'store',
              'dest' : "configfile", 
              'help' : "specify a config file" 
             }

    def check(self, opts):
        if opts.configfile:
            self.configfile = opts.configfile

        # a hack- the run method here must always execute, so the check here 
        # should always return True
        return True

    def run(self, header):
        if not hasattr(self, 'configfile'): 
            rcf = os.path.join(os.path.expanduser('~'), '.btrc')    
            if not os.path.isfile(rcf):
                return 
        else:
           try:
               rcf = utils.chkfile(self.configfile)
           except utils.UtilsError, err:
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
   
        return None

################################################################################
'''
    SetAddCategory

        Define class that sets flag indicating to add categories specified in
        blog post that are not on the blog.

'''
class SetAddCategory(CommandLineOption):
    args = ('-a', '--add-categories')
    kwargs = {
              'action' : 'store_true',
              'dest' : 'addpostcats',
              'help' : """
Categories specified for the post will be added to the blog's category list if
they do not already exist.
"""
             }

    def check(self, opts):
        return opts.addpostcats

    def run(self, header):
        return 'runeditor'

################################################################################
'''
    SetBlogname

        Define class for option that specfies blog to use if multiple blogs 
        setup in config file.
'''
class SetBlogname(CommandLineOption):
    args = ('-b','--blog')
    kwargs = {
              'action' : 'store',
              'dest' : "blogname",
              'help' : """
Blog name in config file for operations on blog.  The name must correspond to a name
in ~/.btrc or a config file specified on the command line.
"""  
             }

    def check(self, opts):
        if opts.blogname:
            self.blogname = opts.blogname
            return True

        return False

    def run(self, header):
        try:
            header.setBlogParmsByName(self.blogname)
        except HeaderError, err:
            print err
            sys.exit()
        return None

################################################################################
'''
    SetPosttime

        Define class for option to schedule when a post should be published.
'''
class SetPosttime(CommandLineOption):
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

    def check(self, opts):
        if opts.posttime:
            return True
        else:
            return False

    def run(self, header):
        return 'runeditor'

################################################################################
'''
    SetNoPublish

        Define class for option to write post to blog as a draft.
'''
class SetNoPublish(CommandLineOption):
    args = ('--draft', )
    kwargs = {
              'action' : "store_false",
              'dest' : "publish",
              'default' : True,
              'help' : "Do not publish post.  Hold it as a draft." 
             }

    def check(self, opts):
        if not opts.publish:
            return True
        else:
            return False

    def run(self, header):
        return 'runeditor'

################################################################################
'''
    SetAllBlogs
'''
class SetAllBlogs(CommandLineOption):
    args = ('-A', '--allblogs')
    kwargs = {
              'action' : "store_true",
              'dest' : "allblogs",
              'default' : False,
              'help' : """
Will cause post to be published to all blogs listed in the rc file.
"""
             }

    def check(self, opts):
        if opts.allblogs:
            return True
        else:
            return False

    def run(self, header):
        return 'runeditor'

################################################################################
'''
    SetPostComment
'''
class SetPostComment(CommandLineOption):
    args = ('--comment', )
    kwargs = {
              'action' : 'store_true',
              'dest' : 'comment',
              'default' : False,
              'help' : "Will cause text to be posted as a new comment."
             }

    def check(self, opts):
        if opts.comment:
            return True
        else:
            return False

    def run(self, header):
        return 'runeditor'

################################################################################
'''
    OptionProcessor
'''
class OptionProcessor:
    def __init__(self):
        self.o_list = []
        self.o_list.append(SetConfigFile())  # should always be first in list
        self.o_list.append(SetBlogname())    # should always be second in list
        self.o_list.append(SetAddCategory())
        self.o_list.append(SetNoPublish())
        self.o_list.append(SetPosttime())
        self.o_list.append(SetAllBlogs())
        self.o_list.append(SetPostComment())
        self.o_list.append(DeletePost())
        self.o_list.append(DeleteComment())
        self.o_list.append(GetRecentTitles())
        self.o_list.append(GetCategories())
        self.o_list.append(AddCategory())
        self.o_list.append(GetPost())
        self.o_list.append(UploadMediaFile())
        self.o_list.append(GetComments())
        self.o_list.append(EditComment())

        self.parser = OptionParser("Usage: %prog [option] postfile1 postfile2 ...")
        for option in self.o_list:
            self.parser.add_option(*option.args, **option.kwargs)

    def parse(self):
        self.opts, files = self.parser.parse_args()
        return files

    def flags(self):
        return {
                'addpostcats' : self.opts.addpostcats,
                'publish'     : self.opts.publish,
                'posttime'    : self.opts.posttime,
                'allblogs'    : self.opts.allblogs,
                'comment'     : self.opts.comment,
               }

    def check(self, header):
        rval = False
        for option in self.o_list:
            if option.check(self.opts):
                if option.run(header) == 'runeditor':
                     rval = True

        return rval

