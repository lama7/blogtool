from xmlproxy.proxybase import ProxyError

from tempfile import NamedTemporaryFile

import sys
import os
import subprocess

################################################################################
"""UtilsError

    Error class for utilities module.  Just accepts an error string explaining
    the exception.
"""
class UtilsError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message

################################################################################
"""dataStruct
    
    Empty container class for creating miscellaneous data structures.
"""
class dataStruct(object):
    pass

################################################################################
"""chkFile

    attempts to verify a file exists by checking the home directory as well as
    the absolute path to the file
"""
def chkFile(file):
    tmpfile = file
    if not os.path.isfile(tmpfile):
        tmpfile = os.path.join(os.path.expanduser('~'), tmpfile)
        if not os.path.isfile(tmpfile):
            raise UtilsError(file)

    return tmpfile

################################################################################
"""edit

    Launches an editor

    ``hdr_string``:  optional string to write to file 
    ``fh``:  filehandle of file to edit
"""
def edit(hdr_string = '', fh = None):
    editor = os.getenv('EDITOR', 'editor')
    if fh == None:
        fh = NamedTemporaryFile()

    try:
        fh.write(hdr_string) 
        fh.flush()
    except IOError, e:
        print "Could not write header text to file."

    try:
        rcode = subprocess.call([editor, fh.name])
    except OSError, e:
        print "Can't launch %s:  %s" % (editor, e)
        return None

    if rcode == 0:
        return fh
    else:
        return None

################################################################################
"""buildComment

    Returns a comment structure for use with the XMLRPC layer for posting a
    comment to the blog.
"""
def buildComment(header, comment_text):
    commentStruct = dataStruct()
    commentStruct.comment_parent = header.parentid or 0
    commentStruct.content = comment_text
    commentStruct.author = header.author
    commentStruct.author_url = header.authorurl
    commentStruct.author_email = header.authoremail
    if header.commentstatus:
        commentStruct.status = header.commentstatus
    return commentStruct

################################################################################
"""isBlogCategory

    Determines if a category is a valid category for the blog.  Validates a
    single category at a time, which includes the dotted subcategory notation.
    Returns ``None`` is the category is valid, returns a tuple of the category
    name and the category ID of the parent category.

    ``blogcats`` is a dictionary- the main thing we'll be interested in are the
    categoryName, parentId, categoryId

    ``postcat`` is a string representing the name of a category.  The string can
    contain '.' separating parent categories from subcategories.  In this case
    the individual entities will need to be checked against parentId's and
    so forth
"""
def isBlogCategory(blogcats, postcat):
    pcatlist = postcat.split('.')

    p_id = '0'
    for cat in pcatlist:
        catDict = dict([ (c['categoryName'], (c['categoryId'], c['parentId']))
                         for c in blogcats if p_id == c['parentId'] ])
        if cat in catDict:
            p_id = catDict[cat][0]
        else:
            return (cat, p_id)

    return None

###############################################################################
"""addCategory

    Adds a category to a blog.

    ``c`` is the full, dotted-notation category string that includes the parent
    categories.

    ``substart`` is the first potential subcategory that isn't on the blog.

    ``parentID`` is the parent ID of the subcategory to add.
"""
def addCategory(proxy, c, substart, parentId):
    # subcategories are demarked by '.'
    newcatlist = c.split('.')

    # isBlogCategory returns a tuple containing the first cat/
    # subcat that is not on the blog.  We cannot assume that the
    # first entry in the list matches the cat returned in the tuple
    # so we'll remove categories/subcats that already exist on
    # the blog
    while substart != newcatlist[0]:
        newcatlist.pop(0)
 
    for c in newcatlist:
        print "Adding %s with parent %s" % (c, parentId)
        try:
            parentId = proxy.newCategory(c, parentId)
        except ProxyError, err:
            print "Caught in utils.addCategory:"
            print err
            sys.exit()
