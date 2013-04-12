import proxybase
import xmlrpclib
import mimetypes
import os

################################################################################
""" getInst

     returns an instance of a wpproxy object
"""
def getInst(url, user, password):
   wp = WordpressProxy(url, user, password)
   return wp

################################################################################
"""WordpressProxy

    The following defines a blogproxy class that inherits methods from the 
    xmlrpclib.  To make this work, the __init__ method of the ancestor
    class(xmlrpclib.ServerProxy in this case) must be called explicitly as 
    part of the initialization.  From that point, the various server methods
    are "directly" accessible through my blogproxy class
"""
class WordpressProxy(proxybase.BlogProxy):

    ############################################################################ 
    def getCategories(self):

        def _tryMethods(blogid):
            try:
                response = self.wp.getTerms(blogid, 
                                            self._username,
                                            self._password,
                                            'category',
                                            {})
            except xmlrpclib.Fault:
                pass
            except xmlrpclib.ProtocolError, error:
                raise proxybase.ProxyError("wp.getCategories", error)
            else:
                return [ { 'categoryName'        : cat['name'],
                           'parentId'            : cat['parent'],
                           'categoryId'          : cat['term_id'],
                           'categoryDescription' : cat['description'],} for cat in response ]

            # fallback to old method
            try:
                return self.metaWeblog.getCategories(blogid,
                                                     self._username,
                                                     self._password)
            except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
                raise proxybase.ProxyError("wp.getCategories", error)

        ########################################################################
        # getCategories starts here...
        if self._categories == None:
            self._categories = _tryMethods(self._getBlogID)

        return self._categories

    ############################################################################ 
    def newCategory(self, newcat, parent, slug='', desc=''):
        blogid = self._getBlogID()

        # start by trying newer Wordpress API call
        term = { 'name'        : newcat,
                 'taxonomy'    : 'category',
                 'slug'        : slug,
                 'description' : desc}
        # it appears that if parent is 0, the call won't work to add the
        # category, but will work if parent is not present.
        if int(parent) != 0:
            term['parent'] = int(parent)
        try:
           return self.wp.newTerm(blogid, 
                                   self._username,
                                   self._password,
                                   term)
        except xmlrpclib.Fault:
            pass
        except xmlrpclib.ProtocolError, error:
            raise proxybase.ProxyError("wp.newCategory", error)
 
        # fallback to old call
        try:
            return self.wp.newCategory(blogid,
                                       self._username,
                                       self._password,
                                       { 'name'        : newcat,
                                         'slug'        : slug,
                                         'description' : desc,
                                         'parent_id'   : parent})
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.newCategory", error)

    ############################################################################ 
    def getRecentTitles(self, number):
        blogid = self._getBlogID()

        # First, try the Wordpress XMLRPC API calls
        try:
            response = self.wp.getPosts(blogid,
                                        self._username,
                                        self._password,
                                        { # filter parameter
                                          'post_type'   : 'post',      # or 'page', 'attachment'
                                          'post_status' : 'publish',   # or 'draft', 'private, 'pending'
                                          'number'      : number,
                                          'offset'      : 0,           # offset by # posts
                                          'orderby'     : '',          # appears to have no effect
                                          'order'       : '',          # appears to have no effect
                                        },
                                        ['post_id', 'post_title', 'post_date'])
        except xmlrpclib.Fault:
            pass
        except xmlrpclib.ProtocolError, error:
            raise proxybase.ProxyError("wp.getRecentTitles", error)
        else:
            return [{'postid'      : postmeta['post_id'],
                     'title'       : postmeta['post_title'],
                     'dateCreated' : postmeta['post_date']} for postmeta in response ]

        # The Wordpress XMLRPC API is not available, try the old MT API
        try:
            return self.mt.getRecentPostTitles(blogid,
                                               self._username,
                                               self._password,
                                               number)
        except (xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.getRecentTitles", error)

    ############################################################################ 
    def publishPost(self, post):
        blogid = self._getBlogID()

        try:
            postid = self.metaWeblog.newPost(blogid,
                                             self._username,
                                             self._password,
                                             post,
                                             post.publish)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.publishPost", error)

        return postid

    ############################################################################ 
    def editPost(self, postid, post):
        try:
            self.metaWeblog.editPost(postid,
                                     self._username,
                                     self._password,
                                     post,
                                     post.publish)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.editPost", error)

        return postid

    ############################################################################ 
    def getPost(self, postid):
        blogid = self._getBlogID()
        try:
            response = self.wp.getPost(blogid, 
                                       self._username, 
                                       self._password,
                                       postid,
                                       ['postid', 'post_title', 'post_content', 'terms'])
        except xmlrpclib.Fault:
            pass
        except xmlrpclib.ProtocolError, error:
            raise proxybase.ProxyError("wp.getPost", error)
        else:
            # process response from server
            # to maintain compatiblity with existing code, massage response
            # into the expected form
            post = {
                    'description'  : response['post_content'],
                    'title'        : response['post_title'],
                    'mt_text_more' : '',
                    'mt_keywords'  : '',
                    'categories'   : []}
            for term in response['terms']:
                if term['taxonomy'] == 'category':
                    post['categories'].append(term['name'])
                elif term['taxonomy'] == 'post_tag':
                    if post['mt_keywords'] != '':
                        post['mt_keywords'] += ', '
                    post['mt_keywords'] += term['name']
            return post

        # fallback to older XMLRPC method
        try:
            return self.metaWeblog.getPost(postid, 
                                           self._username, 
                                           self._password)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.getPost", error)

    ############################################################################ 
    def deletePost(self, postid):
        blogid = self._getBlogID()
        # try the newer Wordpress XMLRPC API first...
        try:
            return self.wp.deletePost(blogid,
                                      self._username,
                                      self._password,
                                      postid)
        except xmlrpclib.Fault:
            pass
        except xmlrpclib.ProtocolError, error:
            raise proxybase.ProxyError("wp.deletePost", error)

        # if Wordpress API failed, try older XMLRPC API call
        try:
            return self.blogger.deletePost('',
                                           postid, 
                                           self._username,
                                           self._password,
                                           True)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.deletePost", error)

    ############################################################################ 
    def upload(self, filename):

        '''
            _tryMethods
            Helper function to maintain compatibility with older version of 
            Wordpress.  Tries the newest methods first and then older ones if
            the newer fail.
        '''
        def _tryMethods(blogid, mediaStruct):
            # try newer Wordpress API first...
            try:
                return self.wp.uploadFile(blogid,
                                          self._username,
                                          self._password,
                                          mediaStruct )
            except xmlrpclib.Fault:
                pass
            except xmlrpclib.ProtocolError, error:
                raise proxybase.ProxyError("wp.upload", error)

            # fall back to older XMLRPC API call
            try:
                return self.metaWeblog.newMediaObject(blogid,
                                                      self._username,
                                                      self._password,
                                                      mediaStruct )
            except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
                raise proxybase.ProxyError("wp.upload", error)

        #######################################################################
        # upload starts here...
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
        except IOError, error:
            raise proxybase.ProxyError("wp.upload", error)

        mediaStruct = {}
        mediaStruct['type'], encoding = mimetypes.guess_type(filename)
        if mediaStruct['type'] == None:
            print "Can't determine MIME type for %s" % filename
            sys.exit()
        mediaStruct['name'] = os.path.basename(filename)
        mediaStruct['bits'] = xmlrpclib.Binary(mediaData)
        return _tryMethods(self._getBlogID(), mediaStruct)

    ############################################################################ 
    def getComments(self, postid):
        blogid = self._getBlogID()
        count = self._getCommentCount(postid)
        comment_struct = {}
        comment_struct['post_id'] = postid
        comment_struct['status'] = ''
        comment_struct['offset'] = 0
        comment_struct['number'] = count['approved']

        try:
            comments = self.wp.getComments(blogid,
                                           self._username,
                                           self._password,
                                           comment_struct)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.getComments", error)

        return comments

    ############################################################################ 
    def newComment(self, postid, comment):
        blogid = self._getBlogID()
        try:
            commentid = self.wp.newComment(blogid,
                                           self._username,
                                           self._password,
                                           postid,
                                           comment)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.newComment", error)
       
        return commentid

    ############################################################################ 
    def deleteComment(self, commentid):
        blogid = self._getBlogID()
        try:
            status = self.wp.deleteComment(blogid,
                                           self._username,
                                           self._password,
                                           commentid)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.deleteComment", error)

        return status

    ############################################################################ 
    def editComment(self, commentid, comment):
        blogid = self._getBlogID()
        try:
            status = self.wp.editComment(blogid,
                                         self._username,
                                         self._password,
                                         commentid,
                                         comment)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.editComment", error)

        return status

    ############################################################################ 
    def getComment(self, commentid):
        blogid = self._getBlogID()
        try:
            status = self.wp.getComment(blogid,
                                        self._username,
                                        self._password,
                                        commentid)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.editComment", error)

        return status

    ##################### START PRIVATE METHODS ################################
    ############################################################################ 
    def _getBlogID(self):
        self._getUsersBlogs()

        for blog in self._blogs:
            if self._blogname == blog['blogName']:
                return blog['blogid']

        raise proxybase.ProxyError("wp._getBlogID", 
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
                raise proxybase.ProxyError('wp._getUsersBlogs', error)

    ############################################################################ 
    def _getCommentCount(self, postid):

        blogid = self._getBlogID()
        try:
            count = self.wp.getCommentCount(blogid,
                                            self._username,
                                            self._password,
                                            postid)
        except(xmlrpclib.Fault, xmlrpclib.ProtocolError), error:
            raise proxybase.ProxyError("wp.getCommentCount", error)

        return count
