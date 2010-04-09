''' This file should be imported into any proxy implementations for blogs.  It
does not actually contain any functional code- well, other than the exception
class.'''

import xmlrpclib

################################################################################
#
# base class for api errors
#
class proxyError(Exception):
    def __init__(self, method, errmsg):
        self.message = "Exception in %s:\n\t%s" % (method, errmsg)

    def __str__(self):
        return self.message

################################################################################
#
# blogproxy
#
#   Defines a baseclass for blogproxy objects.  It, in turn, uses the
#   xmlrpclib.ServerProxy as a baseclass.
#
#   The actual objects should implement the following methods in order to work i
#   with blogtool.
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

    # The following methods should all be overridden by the blog specific
    # implementation of the api

    def getCategories(self, blogname):
        pass

    def newCategory(self, blogname, newcat, parent, slug='', desc=''):
        pass

    def getRecentTitles(self, blogname, number):
        pass

    def publishPost(self, blogname, post):
        pass

    def editPost(self, postid, post):
        pass

    def getPost(self, postid):
        pass

    def deletePost(self, postid):
        pass

    def upload(self, blogname, filename):
        pass

