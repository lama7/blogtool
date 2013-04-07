import sys

################################################################################
"""getProxy

    Returns an instance of the appropriate proxy object based on the blog type.
"""
def getProxy(blogtype, url, user, password):
    module_name = "%s_proxy" % blogtype
    try:
        module = __import__(module_name, globals(), locals(), [], 1)
    except ImportError:
        print "Blogtype '%s' not supported." % blogtype
        sys.exit()

    return module.getInst(url, user, password)
