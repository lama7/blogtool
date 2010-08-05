from xmlrpclib import DateTime
from proxybase import proxyError
import time
import sys

################################################################################
class utilsError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message

################################################################################
#
# returns a post dictionary suitable for publishing
#
def buildPost(hdrobj, desc, more, timestamp = None, publish = True):

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
    postStruct['description'] = desc
    postStruct['mt_excerpt'] = ''
    postStruct['mt_allow_commands'] = 1
    postStruct['mt_allow_pings'] = 1
    postStruct['mt_text_more'] = more
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
                posttime = time.strftime("%Y%m%dT%H:%M:%SZ", utctime)

                # the following merely makes the string into a xmlrpc datetime
                # object
                postStruct['dateCreated'] = DateTime(posttime)

                break

            except ValueError:
                continue
        else:
            # the time format could not be parsed properly
            raise utilsError("Unable to parse timestring: %s" % timestamp)
            

    return postStruct

################################################################################
'''
    isBlogCategory

    blogcats is a dictionary- the main thing we'll be interested in are the
    categoryName, parentId, categoryId
    postcat is a string representing the name of a category.  The string can
    contain '.' separating parent categories from subcategories.  In this case
    the individual entities will need to be checked against parentId's and
    so forth
'''
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
        except proxyError, err:
            print "Caught in utils.addCategory:"
            print err
            sys.exit()
