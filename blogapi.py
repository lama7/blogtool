import xmlrpclib
import mimetypes
import os
import time
import sys

class blogapiError(Exception):
    pass

class timeFormatError(blogapiError):
    def __init__(self, string):
        self.message = "Unrecognized time format: %s" % string

    def __str__(self):
        return self.message

################################################################################
# the following defines a blogproxy class that inherits methods from the 
# xmlrpclib.  To make this work, the __init__ method of the ancestor
# class(xmlrpclib.ServerProxy in this case) must be called explicitly as 
# part of the initialization.  From that point, the various server methods
# are "directly" accessible through my blogproxy class
#
class blogproxy(xmlrpclib.ServerProxy):
    def __init__(self, url, user, password):
        # for debugging info related to xmlrpc, add "verbose=True" to the 
        # __init__ argument list.
        xmlrpclib.ServerProxy.__init__(self, url)
        self.username = user
        self.password = password
        self.blogs = None
        self.categories = None
        self.postID = None
        return None

    def getBlogID(self, blogname):
        # retrieves blogid given blogname from the blogs array
        # make sure it's been initialized
        self.getUsersBlogs()

        for blog in self.blogs:
            if blogname == blog['blogName']:
                return blog['blogid']

        # blog name not found
        return None
        
    def getCategories(self, blogname):
        blogid = self.getBlogID(blogname)

        if self.categories == None:
            try:
                self.categories = self.metaWeblog.getCategories(blogid,
                                                                self.username,
                                                                self.password)
            except Exception, e:
                raise Exception, str(e)

        return self.categories

    def newCategory(self, blogname, newcat, parent, slug='', desc=''):
        blogid = self.getBlogID(blogname)
 
        newcStruct = {}

        newcStruct['name'] = newcat
        newcStruct['slug'] = slug
        newcStruct['description'] = desc
        newcStruct['parent_id'] = parent 

        try:
            id = self.wp.newCategory(blogid,
                                     self.username,
                                     self.password,
                                     newcStruct)
        except Exception, e:
            print 'newCategory error: %s\n' % e
            sys.exit(1)

        return id

    def help(self):
        try:
            methods = self.system.listMethods()
        except Exception, e:
            raise Exception, str(e)

        return methods

    def sayHello(self):
        try:
            hello = self.demo.sayHello()
        except Exception, e:
            raise Exception, str(e)

        return hello

    def getUsersBlogs(self):
        # a little trick to avoid repeatedly calling the xmlrpc method
        # it may not be necessary, we'll figure that out later
        if self.blogs == None:
            try:
                self.blogs = self.wp.getUsersBlogs(self.username, self.password)
            except Exception, e:
                print 'getUsersBlogs: %s\nUsername: %s\nPassword: %s\n' % (e,
                        self.username, self.password)
                sys.exit(1)

        return self.blogs

    def getRecent(self, blogname, number):
        blogid = self.getBlogID(blogname)
        try:
            recent = self.metaWeblog.getRecentPosts(blogid, 
                                                    self.username,
                                                    self.password,
                                                    number)
        except Exception, e:
            raise Exception, str(e)

        return recent 

    def getRecentTitles(self, blogname, number):
        blogid = self.getBlogID(blogname)
        try:
            recent = self.mt.getRecentPostTitles(blogid,
                                                 self.username,
                                                 self.password,
                                                 number)
        except Exception, e:
            print "Unable to retrieve posts from %s:\n" % blogname
            print "\t%s\n" % str(e)

        return recent

    def publishPost(self, blogname, post):
        # this code is based on the similar blogtk2.0 code that performs 
        # a similar task
        blogid = self.getBlogID(blogname)

        try:
            postid = self.metaWeblog.newPost(blogid,
                                             self.username,
                                             self.password,
                                             post,
                                             post['publish'])
        except Exception, e:
            print "Unable to publish to %s:\n\t%s\n" % (blogname, str(e))
            print "\t'%s'\n\t%s\n\t%s" % (blogname, self.username, self.password)
            postid = None

        return postid

    def editPost(self, postid, post):
        try:
            self.metaWeblog.editPost(postid,
                                     self.username,
                                     self.password,
                                     post,
                                     post['publish'] )
        except Exception, e:
            print "Unable to update post: %s\n\t%s" % (postid, str(e))
            print "\t%s\n\t%s)" % (self.username, self.password)
            postid = None

        return postid

    def getPost(self, postid):
        try:
            post = self.metaWeblog.getPost(postid, self.username, self.password)
        except Exception, e:
            print "Unable to retrieve postid: %s\n\t%s" % (postid, str(e))
            post = None

        return post

    def deletePost(self, postid):
        try:
            postdelete = self.blogger.deletePost('',
                                                 postid,
                                                 self.username,
                                                 self.password,
                                                 True)
        except Exception, e:
            print "Error deleting post: %s\n\t%s" % (postid, str(e))
            postdelete = None

        return postdelete

    def upload(self, blogname, filename):
        mediaStruct = {}

        blogid = self.getBlogID(blogname)

        # see if user supplied full path name
        if os.path.isfile(filename) != 1:
            # if not, anchor to user's home directory
            if not filename.startswith('/'):
                filename = '/' + filename
            filename = os.path.expanduser('~') + filename

        try:
            f = open(filename, 'rb')
            mediaData = f.read()
            f.close()

            mediaStruct['type'], encoding = mimetypes.guess_type(filename)
            if mediaStruct['type'] == None:
                print "Can't determine MIME type for %s" % filename
                sys.exit()

            mediaStruct['name'] = os.path.basename(filename)
            mediaStruct['bits'] = xmlrpclib.Binary(mediaData)
        
            res = self.metaWeblog.newMediaObject(blogid,
                                                 self.username,
                                                 self.password,
                                                 mediaStruct )
        except Exception, e:
            print "Error uploading file: %s\n\t%s" % (filename, str(e))
            res = None

        return res

################################################################################
#
# returns a post dictionary suitable for publishing
#
def buildPost(hdrobj, content, timestamp = None, publish = True):

    time_fmts = [
                  "%Y%m%dT%H:%M",        #YYYYMMDDThh:mm
                  "%Y%m%dT%I:%M%p",      #YYYYMMDDThh:mmAM/PM
                  "%Y%m%dT%H:%M:%S",     #YYYYMMDDThh:mm:ss
                  "%Y%m%dT%I:%M:%S%p",   #YYYYMMDDThh:mm:ssAM/PM
                  "%b %d, %Y %H:%M",     #Month Day, Year hour:min
                  "%b %d, %Y %I:%M%p",   #Month Day, Year hour:min AM/PM
                  "%m/%d/%Y %H:%M",      #MM/DD/YYYY hh:mm
                  "%m/%d/%Y %I:%M%p",    #MM/DD/YYYY hh:mmAM/PM
                  "%H:%M %m/%d/%Y",      #hh:mm MM/DD/YYYY
                  "%I:%M%p %m/%d/%Y",    #hh:mmAM/PM MM/DD/YYYY
                ]

    postStruct = {}

    postStruct['title'] = hdrobj.title
    postStruct['categories'] = hdrobj.categories
    postStruct['mt_keywords'] = hdrobj.tags
    postStruct['description'] = content
    postStruct['mt_excerpt'] = ''
    postStruct['mt_allow_commands'] = 1
    postStruct['mt_allow_pings'] = 1
    postStruct['mt_text_more'] = ''
    postStruct['mt_convert_breaks'] = 1

    if publish:
        postStruct['publish'] = 1
    else:
        postStruct['publish'] = 0

    # the post can be scheduled expicitly through the timestamp parm, or
    # via the hdrobj- precedence is given to the timestamp parm
    if timestamp == None and hdrobj.posttime:
        timestamp = hdrobj.posttime

    if timestamp != None:
        # the timestamp is provided as "local time" so we need to convert it to
        # UTC time- do this by converting timestamp to seconds from epoch, then
        # to UTC time.  Finally, pass it to xmlrpclib for formatting
        for tf in time_fmts:
            try:
                timeStruct = time.strptime(timestamp, tf)
                utctime = time.gmtime(time.mktime(timeStruct))
                # 
                posttime = time.strftime("%Y%m%dT%H:%M:%SZ", utctime)

                # the following merely makes the string into a xmlrpc datetime
                # object
                postStruct['dateCreated'] = xmlrpclib.DateTime(posttime)
#                postStruct['date_created_gmt'] = postStruct['dateCreated']

                break

            except ValueError:
                continue
        else:
            # if we get here, the time format could not be parsed properly
            # so we'll abort processing
            raise timeFormatError(timestamp)

    return postStruct

################################################################################
# 
# checks if a post category is a member of the blog's categories
#
def isBlogCategory(blogcats, postcat):
    # blogcats is a dictionary- the main thing we'll be interested in are the
    # categoryName, parentId, categoryId
    # postcat is a string representing the name of a category.  The string can
    # contain '.' separating parent categories from subcategories.  In this case
    # the individual entities will need to be checked against parentId's and
    # so forth
    pcatlist = postcat.split('.')

    # loop through category entries- we'll need to keep track of parent ID's 
    # along the way if subcategories are specified
    p_id = '0'   # initializer- this gives us top-level categories for the 
                 # first time through the loop
    for cat in pcatlist:
        # create a dict of tuples containing the category name, id and parentId
        catDict = dict([ (c['categoryName'], (c['categoryId'], c['parentId']))
                         for c in blogcats if p_id == c['parentId'] ])
        if cat in catDict:
            p_id = catDict[cat][0]
        else:
            return (cat, p_id)

    return None
