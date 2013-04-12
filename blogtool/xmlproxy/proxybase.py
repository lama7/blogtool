''' This file should be imported into any proxy implementations for blogs.  It
does not actually contain any functional code- well, other than the exception
class.'''

import xmlrpclib

################################################################################
"""ProxyError

    Base class for api errors
"""
class ProxyError(Exception):
    def __init__(self, method, errmsg):
        self.message = "Exception in %s:\n\t%s" % (method, errmsg)

    def __str__(self):
        return self.message

################################################################################
"""BlogProxy

    Defines a baseclass for blogproxy objects.  It, in turn, uses the
    xmlrpclib.ServerProxy as a baseclass.
 
    The actual objects should implement the following methods in order to work i
    with blogtool.
"""
class BlogProxy(xmlrpclib.ServerProxy):
    def __init__(self, url, user, password):
        # for debugging info related to xmlrpc, add "verbose=True" to the 
        # __init__ argument list.
        xmlrpclib.ServerProxy.__init__(self, url)
        self._username = user
        self._password = password
        self._blogs = None
        self._categories = None

    # this is just the minimal implementation, it's would be better to check the
    # name for validity and raise an exception if it isn't a valid name for the
    # blog
    def setBlogname(self, blogname):
        self._blogname = blogname

    # The following methods should all be overridden by the blog specific
    # implementation of the api

    def getCategories(self):
        pass

    def newCategory(self, newcat, parent, slug='', desc=''):
        pass

    def getRecentTitles(self, number):
        pass

    def publishPost(self, post):
        pass

    def editPost(self, postid, post):
        pass

    def getPost(self, postid):
        pass

    def deletePost(self, postid):
        pass

    def upload(self, filename):
        pass

    def getComments(self, postid):
        pass

    def newComment(self, postid, comment):
        pass

    def deleteComment(self, commentid):
        pass

    def editComment(self, commentid, comment):
        pass

    def getComment(self, commentid):
        pass
