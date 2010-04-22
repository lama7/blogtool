import proxybase
import xmlrpclib
import mimetypes
import os

################################################################################
# returns an instance of a wpproxy object
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
    def getCategories(self):
        blogid = self._getBlogID()

        if self._categories == None:
            try:
                self._categories = self.metaWeblog.getCategories(blogid,
                                                                self._username,
                                                                self._password)

            except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
                raise proxybase.proxyError("wp.getCategories", error)

        return self._categories

    ############################################################################ 
    def newCategory(self, newcat, parent, slug='', desc=''):
        blogid = self._getBlogID()
 
        newcStruct = {}

        newcStruct['name'] = newcat
        newcStruct['slug'] = slug
        newcStruct['description'] = desc
        newcStruct['parent_id'] = parent 

        try:
            id = self.wp.newCategory(blogid,
                                     self._username,
                                     self._password,
                                     newcStruct)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.newCategory", error)

        return id

    ############################################################################ 
    def getRecentTitles(self, number):
        blogid = self._getBlogID()
        try:
            recent = self.mt.getRecentPostTitles(blogid,
                                                 self._username,
                                                 self._password,
                                                 number)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.getRecentTitles", error)

        return recent

    ############################################################################ 
    def publishPost(self, post):
        # this code is based on the similar blogtk2.0 code that performs 
        # a similar task
        blogid = self._getBlogID()

        try:
            postid = self.metaWeblog.newPost(blogid,
                                             self._username,
                                             self._password,
                                             post,
                                             post['publish'])

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.publishPost", error)

        return postid

    ############################################################################ 
    def editPost(self, postid, post):
        try:
            self.metaWeblog.editPost(postid,
                                     self._username,
                                     self._password,
                                     post,
                                     post['publish'] )

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.editPost", error)

        return postid

    ############################################################################ 
    def getPost(self, postid):
        try:
            post = self.metaWeblog.getPost(postid, 
                                           self._username, 
                                           self._password)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.getPost", error)

        return post

    ############################################################################ 
    def deletePost(self, postid):
        try:
            postdelete = self.blogger.deletePost('',
                                                 postid,
                                                 self._username,
                                                 self._password,
                                                 True)

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.deletePost", error)

        return postdelete

    ############################################################################ 
    def upload(self, filename):
        mediaStruct = {}

        blogid = self._getBlogID()

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
                                                 self._username,
                                                 self._password,
                                                 mediaStruct )

        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.proxyError("wp.upload", error)

        return res

    ############################################################################ 
    ### START PRIVATE METHODS 

    ############################################################################ 
    def _getBlogID(self):
        # retrieves blogid given blogname from the blogs array
        # make sure it's been initialized
        self._getUsersBlogs()

        for blog in self._blogs:
            if self._blogname == blog['blogName']:
                return blog['blogid']

        raise proxybase.proxyError("wp._getBlogID", 
                                   'bad name: %s' % self._blogname)

    ############################################################################ 
    def _getUsersBlogs(self):
        # a little trick to avoid repeatedly calling the xmlrpc method
        # it may not be necessary, we'll figure that out later
        if self._blogs == None:
            try:
                self._blogs = self.wp.getUsersBlogs(self._username, 
                                                    self._password)
            except (xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
                raise proxybase.proxyError('wp._getUsersBlogs', error)
