import proxybase
import xmlrpclib
import mimetypes
import os

def getInst(url, user, password):
   wp = wpproxy(url, user, password)
   return wp

################################################################################
# the following defines a blogproxy class that inherits methods from the 
# xmlrpclib.  To make this work, the __init__ method of the ancestor
# class(xmlrpclib.ServerProxy in this case) must be called explicitly as 
# part of the initialization.  From that point, the various server methods
# are "directly" accessible through my blogproxy class
#
class wpproxy(proxybase.blogproxy):
    ############################################################################ 
    def getCategories(self, blogname):
        blogid = self._getBlogID(blogname)

        if self.categories == None:
            try:
                self.categories = self.metaWeblog.getCategories(blogid,
                                                                self.username,
                                                                self.password)

            except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
                raise proxybase.proxyError("wp.getCategories", error)

        return self.categories

    ############################################################################ 
    def newCategory(self, blogname, newcat, parent, slug='', desc=''):
        blogid = self._getBlogID(blogname)
 
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

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.newCategory", error)

        return id

    ############################################################################ 
    def getRecentTitles(self, blogname, number):
        blogid = self._getBlogID(blogname)
        try:
            recent = self.mt.getRecentPostTitles(blogid,
                                                 self.username,
                                                 self.password,
                                                 number)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.getRecentTitles", error)

        return recent

    ############################################################################ 
    def publishPost(self, blogname, post):
        # this code is based on the similar blogtk2.0 code that performs 
        # a similar task
        blogid = self._getBlogID(blogname)

        try:
            postid = self.metaWeblog.newPost(blogid,
                                             self.username,
                                             self.password,
                                             post,
                                             post['publish'])

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.publishPost", error)

        return postid

    ############################################################################ 
    def editPost(self, postid, post):
        try:
            self.metaWeblog.editPost(postid,
                                     self.username,
                                     self.password,
                                     post,
                                     post['publish'] )

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.editPost", error)

        return postid

    ############################################################################ 
    def getPost(self, postid):
        try:
            post = self.metaWeblog.getPost(postid, self.username, self.password)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.getPost", error)

        return post

    ############################################################################ 
    def deletePost(self, postid):
        try:
            postdelete = self.blogger.deletePost('',
                                                 postid,
                                                 self.username,
                                                 self.password,
                                                 True)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.deletePost", error)

        return postdelete

    ############################################################################ 
    def upload(self, blogname, filename):
        mediaStruct = {}

        blogid = self._getBlogID(blogname)

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

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.upload", error)

        return res

    ############################################################################ 
    ### START PRIVATE METHODS 

    ############################################################################ 
    def _getBlogID(self, blogname):
        # retrieves blogid given blogname from the blogs array
        # make sure it's been initialized
        self._getUsersBlogs()

        for blog in self.blogs:
            if blogname == blog['blogName']:
                return blog['blogid']

        # blog name not found
        return None

    ############################################################################ 
    def _getUsersBlogs(self):
        # a little trick to avoid repeatedly calling the xmlrpc method
        # it may not be necessary, we'll figure that out later
        if self.blogs == None:
            try:
                self.blogs = self.wp.getUsersBlogs(self.username, self.password)
            except (xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
                return None

        return self.blogs


