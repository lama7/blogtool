from xmlrpclib import DateTime
from xmlproxy.proxybase import ProxyError

from tempfile import NamedTemporaryFile

import time
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
class dataStruct:
    pass

################################################################################
""" _convertTime

    Function that attempts to convert a date time string to a datetime object
    in UTC time.  Defaults to assuming string is a local time representation.
"""
def _convertTime(timestr, local = True):
    # List of formats to attempt to match up.
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

    # the timestamp is provided as "local time" so we need to convert it to
    # UTC time- do this by converting timestamp to seconds from epoch, then
    # to UTC time.  Finally, pass it to xmlrpclib for formatting
    for tf in time_fmts:
        try:
            timeStruct = time.strptime(timestr, tf)
            if local:
                utctime = time.gmtime(time.mktime(timeStruct))
            else:
                utctime = timeStruct
            posttime = time.strftime("%Y%m%dT%H:%M:%SZ", utctime)

            # the following merely makes the string into a xmlrpc datetime
            # object
            return DateTime(posttime)

        except ValueError:
            continue
    else:
        # the time format could not be parsed properly
        raise UtilsError("Unable to parse timestring: %s" % timestamp)

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

    `fh`:  filehandle of file to edit
    `hdr_string`:  optional string to write to file 
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
"""buildPost

    Returns a post dictionary suitable for publishing
"""
def buildPost(hdrobj, desc, more, categories, more_text, timestamp = None, publish = True):

    postStruct = dataStruct()

    if more_text:
        postStruct.description = "%s<!--more %s-->%s" % (desc, more_text, more)
    else:
        postStruct.description = desc
        postStruct.mt_text_more = more

    postStruct.title = hdrobj.title
    postStruct.categories = categories
    postStruct.mt_keywords = hdrobj.tags
    postStruct.mt_excerpt = hdrobj.excerpt
    postStruct.mt_allow_comments = 1
    postStruct.mt_allow_pings = 1
    postStruct.mt_convert_breaks = 1

    if publish:
        postStruct.publish = 1
    else:
        postStruct.publish = 0

    # the post can be scheduled expicitly through the timestamp parm, or
    # via the hdrobj- precedence is given to the timestamp parm
    if timestamp == None and hdrobj.posttime:
        timestamp = hdrobj.posttime

    if timestamp != None:
        postStruct.dateCreated = _convertTime(timestamp)

    return postStruct

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
