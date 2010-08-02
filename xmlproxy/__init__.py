import os, sys
import re

#filepath = '/usr/local/share/blogtool/lib/xmlproxy'
filepath = os.path.expanduser('~/python/blogtool/xmlproxy')
sys.path.insert(1, filepath)

# a dict to hold imported modules
modules = {}

filefilter = re.compile("([a-zA-Z_]+)-proxy")

# the following dynamically imports modules from the current directory
cwd = os.path.abspath(os.curdir)
os.chdir(filepath)
for f in os.listdir(os.curdir):
    modulename, ext = os.path.splitext(f)
    if ext == ".py":
        m = filefilter.match(modulename)
        if m:
            modules[m.group(1)] = __import__(modulename)


os.chdir(cwd)

################################################################################
def getProxy(blogtype, url, user, password):
    if blogtype not in modules:
        print "Blogtype '%s' not supported." % blogtype
        sys.exit()

    return modules[blogtype].getInst(url, user, password)
