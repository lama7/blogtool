from blogtool import __version__

from headerparse import HeaderError
from xmlproxy.proxybase import ProxyError
from fileprocessor import FileProcessor, FileProcessorError

import argparse

import html2md
import utils

import sys
import datetime
import os

################################################################################
"""_getProxy

   Wrapper function for getting a proxy object for a particular header.  Takes
   care of the "try-except" structure.
"""
def _getProxy(header):
    try:
        p = header.proxy()
    except HeaderError, err:
        print err
        sys.exit()

    return p

################################################################################
"""CommandLineOption

    Base Class for handling command line options

    Every option obect has an `args` attribute and a `kwargs` attribute that
    define the option for the argparse module.  Additionally, every option
    object has the `check` method and a `run` method.
"""
class CommandLineOption:
    args = ()  # to be overridden by the option
    kwargs = {}  # to be overriden by the option

    ############################################################################
    """check

        This method should check the relevant option and return True if the 
        option should be processed, False otherwise
        the 'opts' arg is the Values object returned by the OptParse parser.
        if the option is present and stores a value that is needed when the option
        is run, then the value should be squirreled away in an instance attribute
    """
    def check(self, opts):
        pass

    ############################################################################
    """run

        This method performs the actual option processing.  It does not return any
        error codes- any errors should raise the CommandLineOptionError exception
        the 'opts' arg will be the Values object returned by the OptParse parser.
        the 'proxy' arg will be a proxy object for communicating with the blog
        if necessary 
    """
    def run(self, header, opts):
        pass
        
################################################################################
"""DeletePost

    Define class to handle deleting posts from a blog.
"""
class DeletePost(CommandLineOption):
    args = ('-d', '--delete')
    kwargs = {
              'action' : 'store',
              'dest' : "del_postid", 
              'metavar' : 'POSTID',
              'help' : "Delete post POSTID from a blog." 
             }

    def check(self, opts):
        if opts.del_postid:
            self.postid = opts.del_postid
            return True

        return False

    def run(self, header, opts):
        print "Deleting post %s from %s" % (self.postid, header.name)

        proxy = _getProxy(header)
        try:
            postid = proxy.deletePost(self.postid)
        except ProxyError, err:
            print "Caught in options.DeletePost.run:"
            print err
            sys.exit()

        return None

################################################################################
"""DeleteComment

   Option for deleting a comment from a blog. 
"""
class DeleteComment(CommandLineOption):
    args = ('-D', '--deletecomment')
    kwargs = {
              'action' : 'store',
              'dest' : 'del_comment_id',
              'metavar' : 'COMMENTID',
              'help' : 'Delete comment COMMENTID from a blog.'
             }

    def check(self, opts):
        if opts.del_comment_id:
            self.comment_id = opts.del_comment_id
            return True
        return False
        
    def run(self, header, opts):
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
"""GetRecentTitles

    Define class to handle retrieving recent blog post info and displaying
    it to stdout.
"""
class GetRecentTitles(CommandLineOption):
    args = ('-t', '--recent-titles')
    kwargs = {
              'action' : 'store',
              'dest' : 'num_recent_t',
              'metavar' : 'NUMBER',
              'help' : "Retrieve NUMBER recent posts from a blog." 
             }

    def check(self, opts):
        if opts.num_recent_t:
            self.count = opts.num_recent_t
            return True

        return False

    def run(self, header, opts):
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
"""GetCategories

    Define class to handle retrieving category list from a blog and 
    displaying is to stdout.
"""
class GetCategories(CommandLineOption):
    args = ('-C', '--Categories')
    kwargs = {
              'action' : "store_true",
              'dest' : "getcats",
              'help' : "Get the list of catgories for a blog." 
             }

    def check(self, opts):
        return bool(opts.getcats)

    def run(self, header, opts):
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
"""AddCategory

    Define class to handle adding a category to a blog
"""
class AddCategory(CommandLineOption):
    args = ('-n', '--new-categories')
    kwargs = {
              'action' : 'store',
              'dest' : "newcat",
              'help' : '''
Add NEWCAT category to a blog.  NEWCAT can specifiy mutlitple levels of new
categories using a dot notation to separate subcategories, eg
"newcat1.subcata.subcatb".
'''
             }

    def check(self, opts):
        if opts.newcat:
            self.catname = opts.newcat
            return True

        return False

    def run(self, header, opts):
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
"""UploadMediaFile

    Implements option to upload a media file to a blog, such as a jpg file.
"""
class UploadMediaFile(CommandLineOption):
    args = ('-u', '--uploadmedia')
    kwargs = {
              'action' : 'store',
              'dest' : 'uploadfile',
              'metavar' : 'FILE',
              'help' : "Upload media file FILE to a blog."
             }

    def check(self, opts):
        if opts.uploadfile:
            self.uploadfile = opts.uploadfile
            return True

        return False

    def run(self, header, opts):
        try:
            proxy = _getProxy(header)
            uf = utils.chkFile(self.uploadfile)
            print "Attempting to upload '%s'..." % uf
            res = proxy.upload(uf)
        except utils.UtilsError, err:
            print "File not found: %s" % err
        except ProxyError, err:
            print "Caught in options.UploadMediaFile"
            print err

        return None

################################################################################
"""GetPost
       
    Define class to handle retrieving a post from a blog given the post's
    ID and printing the result to stdout.
"""
class GetPost(CommandLineOption):
    args = ('-g', '--getpost')
    kwargs = {
              'action' : 'store',
              'dest' : 'get_postid',
              'metavar' : 'POSTID',
              'help' : '''
Retrieves post POSTID from a blog and writes it to STDOUT using Markdown
formatting.  A header is also created, meaning a file capture could be used for
updating with blogtool.  
'''            
             }

    CATID = 0
    CATPARENTID = 1

    def check(self, opts):
        if opts.get_postid:
            self.postid = opts.get_postid
            return True

        return False

    def run(self, header, opts):
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
            more = "<!--%s-->" % (post['wp_more_text'] or "more")
            text = html2md.convert("%s%s%s" % (post['description'], 
                                               more,
                                               post['mt_text_more']))
        else:
            text = html2md.convert(post['description'])
        header_str = 'BLOG: %s\nPOSTID: %s\nTITLE: %s\n' % (header.name, 
                                                            self.postid, 
                                                            post['title'])
        header_str += 'CATEGORIES: %s\n' % self._buildCatStr(post['categories'])
        if post['mt_keywords']:
            header_str += 'TAGS: %s\n' % post['mt_keywords']
        if post['mt_excerpt']:
            if any([c in post['mt_excerpt'] for c in [',','\n','{','}']]):
                header_str += 'EXCERPT: """%s"""' % post['mt_excerpt']
            else:
                header_str += 'EXCERPT: %s' % post['mt_excerpt']
            header_str = header_str.rstrip() + '\n' # ensure header is terminated

        print (header_str + '\n' + text).encode("utf8")
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
               if blogcats_d[cat][self.CATPARENTID] == '0':
                   if cat_s == '':
                      cat_s += "%s" % cat
                   else:
                      cat_s += ", %s" % cat
               else:
                   cat_s += ".%s" % cat
        return cat_s

    ############################################################################
    """_sortCats
   
        Sorts catlist from category to lowest subcategory.  If multiple
        subcategories have a common parent, then the category hierarchy is
        duplicated and added to the list with the new subcategory.
    """
    def _sortCats(self, catlist, bcats_d):
        sortedcats = []
        while len(catlist) != 0:
            for cat in catlist[:]:
                cat_parent_id = bcats_d[cat][self.CATPARENTID]
                if cat_parent_id == '0':
                    sortedcats.append(cat)
                    catlist.remove(cat)
                else:
                    enumerated_seq = list(enumerate(sortedcats))
                    for i, s_cat in enumerated_seq:
                        if cat_parent_id == bcats_d[s_cat][self.CATID]:
                            # does this subcategory have the same parent as 
                            # another subcatgory?
                            if len(sortedcats) > i+1 and \
                               bcats_d[sortedcats[i+1]][self.CATPARENTID] == cat_parent_id:
                                # find the top of the category hierarchy
                                # i is the index of the parent of cat
                                while bcats_d[sortedcats[i]][self.CATPARENTID] != '0':
                                    i = i - 1
                                j = i # mark insertion point into sortedlist
                                # copy category hierarchy
                                hierarchycopy = []
                                while bcats_d[sortedcats[i]][self.CATPARENTID] != cat_parent_id:
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
                        elif bcats_d[cat][self.CATID] == bcats_d[s_cat][self.CATPARENTID]:
                            sortedcats.insert(i-1, cat)
                            catlist.remove(cat)
                            break
        return sortedcats
                    

################################################################################
"""GetComments

    Option to retrieve comments for blog post.
"""
class GetComments(CommandLineOption):
    args = ('-r', '--readcomments')
    kwargs = {
              'action' : 'store',
              'dest' : 'comments_postid',
              'metavar' : 'POSTID',
              'help' : '''
Retrieves the comments for post POSTID.
'''
             }

    def check(self, opts):
        if opts.comments_postid:
            self.postid = opts.comments_postid
            return True

        return False

    def run(self, header, opts):
        proxy = _getProxy(header)

        comments = proxy.getComments(self.postid)
        comments.reverse()
        for comment in comments:
            t_converted = datetime.datetime.strptime(comment['date_created_gmt'].value,
                                                     "%Y%m%dT%H:%M:%S")
            output = 'Comment ID: %s\n' % comment['comment_id']
            if comment['parent'] != '0':
                output += 'Parent ID:  %s\n' % comment['parent']
            output += 'Time:       %s\n' % t_converted
            output += 'Author:     %s\n' % comment['author']
            output += 'Email:      %s\n' % comment['author_email']
            if comment['author_url']:
                output += 'URL:        %s\n' % comment['author_url']

            content = html2md.convert(comment['content'])
            print output + '\n' + content

        return None

################################################################################
"""EditComment

    Class to handle editing of comments.
"""
class EditComment(CommandLineOption):
    args = ('--editcomment', )
    kwargs = {
              'action' : 'store',
              'dest' : 'commentid',
              'help' : '''
Edit comment COMMENTID already on the blog.  The comment will be downloaded and
an editor will be launched with the comment text formatted into Markdown syntax.
A header is also generated with the metadata from the blog in it so it can also
be edited, for instance to approve a comment held in moderation.
'''
             }

    def check(self, opts):
        if opts.commentid:
            self.commentid = opts.commentid
            return True
        return False

    def run(self, header, opts):
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
        fp = FileProcessor(**{'addpostcats' : False,
                              'publish' : True,
                              'posttime' : None,
                              'allblogs' : False,
                              'comment' : True,
                              'charset': opts.charset,
                              })
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
"""SetConfigFile

    Define class to handle parsing of a config file for blogtool.
"""
class SetConfigFile(CommandLineOption):
    args = ('-c', '--config')
    kwargs = { 
              'action' : 'store',
              'dest' : "configfile", 
              'metavar' : 'FILE',
              'help' : "Use FILE as the rc file when executing blogtool." 
             }

    def check(self, opts):
        if opts.configfile:
            self.configfile = opts.configfile

        # a hack- the run method here must always execute, so the check here 
        # should always return True
        return True

    def run(self, header, opts):
        if not hasattr(self, 'configfile'): 
            rcf = os.path.join(os.path.expanduser('~'), '.btrc')    
            if not os.path.isfile(rcf):
                return 
        else:
           try:
               rcf = utils.chkFile(self.configfile)
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
"""SetAddCategory

    Define class that sets flag indicating to add categories specified in
    blog post that are not on the blog.
"""
class SetAddCategory(CommandLineOption):
    args = ('-a', '--add-categories')
    kwargs = {
              'action' : 'store_true',
              'dest' : 'addpostcats',
              'default' : False,
              'help' : '''
A flag option that causes categories specified in a post file to be added to the
blog's category list if they do not already exist.  
'''
             }

    def check(self, opts):
        return opts.addpostcats

    def run(self, header, opts):
        return 'runeditor'

################################################################################
"""SetBlogname

    Define class for option that specfies blog to use if multiple blogs 
    setup in config file.
"""
class SetBlogname(CommandLineOption):
    args = ('-b','--blog')
    kwargs = {
              'action' : 'store',
              'dest' : 'blogname',
              'help' : '''
Specifies a blog to execute a command against for deleting posts or comments,
retrieving category lists or posts or comments, etc.  The name must correspond
to a name in ~/.btrc or a config file specified on the command line.
'''  
             }

    def check(self, opts):
        if opts.blogname:
            self.blogname = opts.blogname
            return True

        return False

    def run(self, header, opts):
        try:
            header.setBlogParmsByName(self.blogname)
        except HeaderError, err:
            print err
            sys.exit()
        return None

################################################################################
"""SetPosttime

    Define class for option to schedule when a post should be published.
"""
class SetPosttime(CommandLineOption):
    args = ('-s', '--schedule')
    kwargs = {
              'action' : 'store',
              'dest' : 'posttime',
              'metavar' : 'TIMESTR',
              'help' : '''
Sets the time to publish post.  TIMESTR supports a number of formats:  YYYYMMDDThh:mm, 
YYYYMMDDThh:mmAM/PM, YYYYMMDDThh:mm:ss, YYYYMMDDThh:mm:ssAM/PM,
Month Day, Year hour:min, Month Day, Year hour:min AM/PM, MM/DD/YYYY hh:mm,
MM/DD/YYYY hh:mmAM/PM, hh:mm MM/DD/YYYY, hh:mmAM/PM MM/DD/YYYY
''' 
             }

    def check(self, opts):
        if opts.posttime:
            return True
        else:
            return False

    def run(self, header, opts):
        return 'runeditor'

################################################################################
"""SetNoPublish

    Define class for option to write post to blog as a draft.
"""
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

    def run(self, header, opts):
        return 'runeditor'

################################################################################
"""SetAllBlogs

   Option to make blogtool execute a command on all blogs in a configuration
   file.
"""
class SetAllBlogs(CommandLineOption):
    args = ('-A', '--allblogs')
    kwargs = {
              'action' : "store_true",
              'dest' : "allblogs",
              'default' : False,
              'help' : '''
A flag option that will cause the post to be published to all blogs listed in
the rc file.
'''
             }

    def check(self, opts):
        if opts.allblogs:
            return True
        else:
            return False

    def run(self, header, opts):
        return 'runeditor'

################################################################################
"""SetPostComment

    Option to write a comment to a blog.
"""
class SetPostComment(CommandLineOption):
    args = ('--comment', )
    kwargs = {
              'action' : 'store',
              'dest' : 'comment',
              'default' : False,
              'metavar' : ('POSTID', 'COMMENTID'),
              'nargs' : 2,
              'help' : '''
Post text from file as a comment to post POSTID.  If the comment is in answer to
another comment, supply the COMMENTID, otherwise set it to 0.
'''
             }

    def check(self, opts):
        if opts.comment:
            self.postid = opts.comment[0]
            self.parentid = opts.comment[1]
            opts.comment = True  # used by the headerparse module
            return True
        else:
            return False

    def run(self, header, opts):
        header.postid = self.postid
        header.parentid = self.parentid
        return 'runeditor'

################################################################################
"""SetCharset

    Option to set the encoding for text in a blog post.
"""
class SetCharset(CommandLineOption):
    args = ('--charset', )
    kwargs = {
              'action' : 'store',
              'dest' : 'charset',
              'metavar' : 'CHARSET',
              'help' : '''
Set the CHARSET to use to decode the post text prior to running the text through
markdown.
'''
             }

    def check(self, opts):
        if opts.charset:
            self.charset = opts.charset
            return True
        else:
            return False

    def run(self, header, opts):
        header.charset = self.charset
        return 'runeditor' 

################################################################################
"""GetVersion

    Option to display version information.
"""
class GetVersion(CommandLineOption):
    args = ('--version',)
    kwargs = {
              'action' : 'store_true',
              'dest' : 'version',
             }

    def check(self, opts):
        return opts.version

    def run(self, header, opts):
        print "blogtool version  %s" % __version__
        return None


################################################################################
"""OptionProcessor
    
    Class that initializes the option parsing and coordinates executing the
    various options.
"""
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
        self.o_list.append(SetCharset())
        self.o_list.append(DeletePost())
        self.o_list.append(DeleteComment())
        self.o_list.append(GetRecentTitles())
        self.o_list.append(GetCategories())
        self.o_list.append(AddCategory())
        self.o_list.append(GetPost())
        self.o_list.append(UploadMediaFile())
        self.o_list.append(GetComments())
        self.o_list.append(EditComment())
        self.o_list.append(GetVersion())

        self.parser = argparse.ArgumentParser(description = "Command line based blog client")
        for option in self.o_list:
            self.parser.add_argument(*option.args, **option.kwargs)
        self.parser.add_argument('postfile', nargs='*', help= "File or files to post to a blog")

    def parse(self):
        self.opts = self.parser.parse_args()
        return self.opts.postfile

    def flags(self):
        return {
                'addpostcats' : self.opts.addpostcats,
                'publish'     : self.opts.publish,
                'posttime'    : self.opts.posttime,
                'allblogs'    : self.opts.allblogs,
                'comment'     : self.opts.comment,
                'charset'     : self.opts.charset,
               }

    def check(self, header):
        rval = False
        for option in self.o_list:
            if option.check(self.opts):
                if option.run(header, self.opts) == 'runeditor':
                     rval = True

        return rval
