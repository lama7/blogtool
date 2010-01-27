#!/usr/bin/python

from optparse import OptionParser
from tempfile import NamedTemporaryFile
import blogapi

import btconfigparser

import time
import datetime
import re
import sys
import os
import types
import subprocess

try:
    import markdown
except ImportError:
    print "You need to install python-markdown before you can use blogtool."
    sys.exit()

try:
    import BeautifulSoup 
except ImportError:
    print "You need to install BeautifulSoup before you can use blogtool."
    sys.exit()

################################################################################
#
# error
#
def error(str):
    sys.stderr.write(str)
    sys.exit(1)

################################################################################
#
# split the file into 2 sections- the header and the post
# divider is the first blank line encountered
#
def getHeaderandPostText(linelist):
    # find first blank line so we can split the list
    for line in linelist:
        if line.isspace():
            i = linelist.index(line)
            break

    return ''.join(linelist[0:i]), ''.join(linelist[i + 1:])

#################################################################################
#
# bt_options- for processing command line arguments
#
def bt_options(argv):
    usage = "Usage: %prog [options] postfile1 postfile2 ,.."

    # create parser object
    global parser 
    parser = OptionParser(usage)

    parser.add_option("-a",
                      "--add-categories",
                      action = "store_true",
                      dest = "addcats",
                      help = "Categories specified for the post will be added\
                              to the blog's category list if they do not\
                              already exist.")

    parser.add_option("-b",
                      "--blog",
                      dest="blogname",
                      help="Blog name for operations on blog.  The name must\
                            correspond to a name in .btconfig or a config file\
                            specified on the command line.")
 
    parser.add_option("-c", 
                      "--config", 
                      dest="configfile", 
                      help="specify a config file")

    parser.add_option("-d", 
                      dest="del_postid", 
                      help="delete a post")

    parser.add_option("-C",
                      "--Categories",
                      action="store_true",
                      dest="getcats",
                      help="Get a list of catgories for a blog")

    parser.add_option("-s",
                      "--schedule",
                      dest = "posttime",
                      help = "Time to publish post in YYYYmmddHHMMSS format")

    parser.add_option("-t",
                      "--recent-titles",
                      dest="num_recent_t",
                      help="rettrieve recent posts from a blog")

    parser.add_option("-n",
                      "--new-categories",
                      dest="newcat",
                      help="Add a new category to a blog")

    parser.add_option("--draft",
                      action = "store_false",
                      dest = "publish",
                      default = True,
                      help = "Do not publish post.  Hold it as a draft.")

    # here we go...
    return parser.parse_args(argv)

#################################################################################
# 
# Checks for and processes a config file for blogtool 
#  Info in config file: anything that can appear in the header of a postfile
#  Most likely for storing static blog related stuff like username, password,
#  xmlrpc, and blog name- essentially it sets defaults that can be overridden
#  by the postfile
#
#  12/4/09:  Now returns config_str which can be passed to a parser object.
#            Previous had returned a config object.  This was eliminated so
#            that the parser object did not need to be global
#
def configfile(cfile):
    # cfile will be a filename or None
    if cfile == None:
        cfile = os.path.join(os.path.expanduser('~'), '.btconfig')    
        if os.path.isfile(cfile) != 1:
            return None
    else:
       # it's possible the user supplied a fully qualified path, so check if
       # the file exists
       if os.path.isfile(cfile) != 1:
           # try anchoring file to the user's home directory       
           cfile = os.path.join(os.path.expanduser('~'), cfile)
           if os.path.isfile(cfile) != 1:
               print "Unable to open config file: %s"
               sys.exit(1)

    # open the file
    try:
        f = open(cfile, 'r')
        # config file format is identical to header, so convert file lines
        # to a string and then return a config objct
        config_str = ''.join(f.readlines())
    except IOError:
        print "Unable to open config file: %s" % cfile
        sys.exit(1)
    finally:
        f.close()

    return config_str 

##############################################################################
#
# reconcile- reconciles configuration info between config file and post 
#            Roughly speaking, the post config contained in the header trumps
#            any setting in the config file.
#
# This is not as difficult as it might at first seem.  
# If there is a NAME in the post config, find the equivalent blog entry in the
# config file and complete the config as required.
# If no name, then blog entries are processed in order- that is, entry 1 in
# post config is completed using entry 1 in config file, and so forth.
# Any conflicts are resolved in favor of leaving post config- we assume the user
# wanted to do something so we let them
#
def reconcile(pcl, cfcl):

    # if there is no config file, then we don't have to do anything
    if cfcl == None:
        return pc
    
    for pc in pcl:
        cf = None
        # first see if a name is supplied
        if pc.name != '':
            for cfc in cfcl:
                if cfc.name == pc.name:
                    cf = cfc
                    break
            # make sure we found a match
            if cf == None:
                continue  # nothing to do if we didn't find a match
        else:
            # without a name, we can only do take one other approach-
            # match the indexes of configs and go from there.
            i = pcl.index(pc)
            if not i < len(cfcl):
                continue
            cf = cfcl[pcl.index(pc)]

        # loop through the object attributes and plug in anything supplied
        # by config that isn't alread set
        for (k, v) in pc.__dict__.iteritems():
            # if any values are already assigned, then skip them- config file
            # values do NOT override post config values
            if k == 'categories' or k == 'tags':
                if len(v) != 0:
                   continue
            elif v != '':
                continue

            # value is not assigned already, see if config file assigns a value
            newv = cf.get(k)
            if newv != None:
                pc.set(k, newv)

    return pcl

################################################################################
#
#
def addCategory(blog, blogname, c, substart, parentId):
    # subcategories are demarked by '.'
    newcatlist = c.split('.')

    # the isBlogCategory returns a tuple containing the first cat/
    # subcat that is not on the blog.  We cannot assume that the
    # first entry in the list matches the cat returned in the tuple
    # so we'll remove categories/subcats that already exist on
    # the blog
    while substart != newcatlist[0]:
        newcatlist.pop(0)
 
    # now add the categories as needed- init the parent ID field
    # using the value from the tuple returned above
    for c in newcatlist:
        print "Adding %s with parent %s" % (c, parentId)
        parentId = blog.newCategory(blogname, c, parentId)

#################################################################################
# entry function for processing post text- image links and what not are
# dealt with here
#
def procPost(blog, blogname,  posttext):

    # helper function for comprehension below
    def skiptag(tag):
        return (isinstance(tag, BeautifulSoup.Comment) or
                tag.parent.name == 'pre' or
                tag.parent.name == 'code')

    # when we run the text through markdown, it will preserve the linefeeds of 
    # the original text.  This is a problem when publishing because the blog
    # software turns the linefeeds within the 'p' tags to 'br' tags which
    # defeats the formatting powers of HTML.  So we'll remove all of the
    # linefeeds in the 'p' tags.  Towards this end, we'll use Beautiful Soup
    # because it streamlines what would otherwise be a tedious process
    soup = BeautifulSoup.BeautifulSoup(markdown.markdown(posttext))

    # remove extraneous newlines from the NavigableStrings (text)
    # for better or worse, I'll leave extra space (i.e. multiple consecutive
    # space characters) alone, for now.  Browser's get rid of the space so it 
    # doesn't seem to hurt anyone if I leave it in place
    # don't do this for 'pre' tags
    souptext = soup.findAll(text = True) 
    [ t.replaceWith(t.replace('\n', '')) for t in souptext if not skiptag(t) ]

    # now deal with all the 'img' tags
    for img in soup.findAll('img'):
        # first, make sure this looks like a valid file
        imgf = img['src']
        if imgf.find("http://") == -1:
            if os.path.isfile(imgf) != 1:
                # try anchoring file to the user's home directory       
                imgf = os.path.expanduser('~') + '/' + imgf
                if os.path.isfile(imgf) != 1:
                    error("Image file not found: %s\n" % img['src'])
        else:
            # this is a link so don't proceed any further, move on to the next
            continue

        # run it up the flagpole...
        print "Attempting to upload '%s'..." % imgf
        res = blog.upload(blogname, imgf)
        if res == None:
            print "Upload failed, proceeding...\n"
            continue
        print "Done"

        # replace the image file name in the 'img' tag with the url and also
        # add the 'alt' attribute, assuming it wasn't provided
        # check for an 'res' attribute and append this to the filename while
        # removing it from the attribute list
        img['src'] = res['url']
        if not img.has_key('alt'):
            img['alt'] = res['file']

        if img.has_key('res'):
            res_str = '-' + img['res'] + '.'
            img['src'] = re.sub("\.(\w*)$", r'%s\1' % res_str, img['src'])
            
            # the 'res' attr is bogus- I've added it so that I can specify the
            # appropriate resolution file I want in the url.  
            # remove it from the final post
            del(img['res'])

    return soup.renderContents()

################################################################################
#
# procPostCategories- basically a glorified check for typos in the catetories
#                     so the user will know and can act accordingly
#
def procPostCategories(pc, blog, addCatOption): 
    # first, build a list of catgories that aren't on the blog from the
    # post's category list
    nonCats = []
    for c in pc.categories:
        t = blogapi.isBlogCategory(blog.getCategories(pc.name), c)
        if t != None:
            nonCats.append((c,) + t)

    # see if there were any unrecognized categories
    if len(nonCats) == 0:
        print "Post categories OK"
    elif addCatOption:
        [ addCategory(blog, pc.name, *ct) for ct in nonCats ]
    else:
        rcats = [ ct[0] for ct in nonCats ]
        print "Category '%s' is not a valid category for %s so it is being\n\
               \r removed from the category list for this post.\n\
               \rUse the -a option if you wish to override this behavior or\n\
               \rthe -n option to add it from the command line.\n" %\
                                                     (', '.join(rcats), pc.name)
        [ pc.categories.remove(c) for c in rcats ]

    # last bit of category processing- if there are any categories 
    # with subcategories, like 'cat.subcat', they need to be split
    # up so that he post is categorized properly
    # the 'list(set(...)) removes all duplicates 
    if len(pc.categories) == 0:
        print "This post has no valid categories, the default blog category\n\
               \rwill be used.\n"
        return pc.categories
    else:
        return list(set(reduce(lambda l1, l2: l1 + l2, 
                           [c.split('.') for c in pc.categories])))

################################################################################
#
# updateHeader- when a post is successfully published, an ID number is
#                 returned. This function adds a POSTID field to the header. 
#
# One thing we can count on is that the header is properly formed here
#
def updateHeader(header, blogname, postid):
    
    # This function consists of subfunctions that drill into the header string
    # to find where to insert the POSTID info.  Each function returns a 
    # tuple consisting of the next state, the header string that has been
    # processed and the header string yet to be processed

    # state-function to find the BLOG keyword in the header
    def findbloggroup(l):
        # it possible that BLOG will not appear in the header (blog info
        # can also be defined in an rc file or command line options)
        # if we reach the end of the header, just append the POSTID there
        m = re.match('(.*?BLOG\s*\{\s*)(.*)', l, re.DOTALL)
        if m == None:
            # no BLOG groups, so just append the POSTID to the end of the 
            # line/header and we're done
            l += 'POSTID: %s\n' % postid
            return None, l, ''

        return states.index(findblogname), m.group(1), m.group(2)

    # find the NAME keyword in the BLOG group- also checks for the 
    # blogname itself since it's likely the two are on the same line
    def findblogname(l):
        m = re.match('(.*?NAME\s*:\s*|NAME\s*:\s*)([^\n]+)(.*)', l, re.DOTALL)
        if m != None:
            # found NAME keyword in the group
            hdr_ret = m.group(1) + m.group(2)
            if blogname not in hdr_ret:
                return states.index(findbloggroup), hdr_ret,  m.group(3)

            # found the blogname, go to findendgroup
            return states.index(findendgroup), hdr_ret, m.group(3)

        # NAME keyword not in string, so go back to looking for another
        # BLOG group
        return states.index(findendgroup), '', l

    # we've found the group where the POSTID is going to be written,
    # now it's just a matter of finding the end of the group where we'll
    # add it
    def findendgroup(l):
        m = re.match('(.*?)([}])(.*)', l, re.DOTALL)
        hdr_ret = m.group(1)
        hdr_ret += '    POSTID: %s\n' % postid
        hdr_ret += m.group(2) + m.group(3)
        return None, hdr_ret, ''

    #
    # This is where the actual function is implemented- just a simple
    # FSM that processes the header string and inserts what is requied.
    #
    states = [
              findbloggroup,
              findblogname,
              findendgroup ]

    current_state = states.index(findbloggroup)
    hdr_str = header
    header = ''
    while current_state != None:
        current_state, procd_hdr, hdr_str = states[current_state](hdr_str)
        header += procd_hdr

    return header
    
################################################################################
#
# writes an updated file- basically consists of an updated header with the
#                         POSTID field added
def updateFile(file, header, posttext):
    # alter the file name so we don't overwrite
    file += '.posted'
    try:
        f = open(file, 'w')
        f.write(header)
        f.write('\n')
        f.write(posttext)
    except IOError:
        print "Error writing updated post file %s" % file
    finally:
        f.close()

################################################################################
# 
# bt- this is the "main" function, as it were.  Program flow is controlled by 
#     this function.  Start here when if you dare...
#
def bt(argv):

    ############################################################################ 
    # helper function used when processing certain command line options
    def getpostconfig(cf):
        if cf == None:
            return None

        if len(cf) != 1:
            if not opts.blogname:
                error("There are multiple blogs in the config file.  Use the\n\
                       \r-b option to specify which to use.\n")
            for blog in cf:
                if blog.name == opts.blogname:
                    return blog
        else:
             return cf[0]

        return None  # name doesn't match anything in config file

    ############################################################################ 
    # create a parser object that we'll use in a bit to process the config file
    # and then later to process the post header
    btconfig = btconfigparser.bt_config()

    ############################################################################ 
    # command line option parser is initialized and then invoked in this
    # function- I can't really say this is THE way to do it, but it seems OK
    (opts, argv) = bt_options(argv)

    ############################################################################ 
    # handle any config files- we need to do this now because even for option 
    # processing we minimally need username, xmlrpc, and password info available
    cf_config = None
    cf_str = configfile(opts.configfile)
    if cf_str != None:
        try:
            cf_config = btconfig.parse(cf_str)
        except btconfigparser.btParseError, err_str:
            print err_str
            sys.exit()

    ############################################################################ 
    # delete post option processing
    atleastoneoptionfound = None
    if opts.del_postid:
        atleastoneoptionfound = 1
        # We need a blog to delete from.  If there are multiple blogs specified
        # in the config file, then bail and instruct the user to use the -b
        # option.  If only 1, then use it regardless.  Oh- if multiples, then
        # check if a blog was specified.
        pc = getpostconfig(cf_config)
        if pc == None:
            error("Cannot process 'delete' because there is no blog specified.\n")

        blog = blogapi.blogproxy(pc.xmlrpc, pc.username, pc.password)
        print "Deleting post %s" % opts.del_postid
        postid = blog.deletePost(opts.del_postid)
        if postid == None:
            error("Unable to delete post %s from %s" % (opts.del_postid, \
                                                        pc.name))
        print "Done\n"
        del pc, blog

    ############################################################################ 
    # recent post summary option processing
    if opts.num_recent_t:
        atleastoneoptionfound = 1
        pc = getpostconfig(cf_config)
        if pc == None:
            error("Cannot process 'recent' request because there is no blog\n\
                   \rspecified\n")

        blog = blogapi.blogproxy(pc.xmlrpc, pc.username, pc.password)
        print "Retrieving %s most recent posts from %s.\n" % (opts.num_recent_t,
                                                              pc.name)
        recent = blog.getRecentTitles(pc.name, opts.num_recent_t)
        print "POSTID\tTITLE                               \tDATE CREATED"
        print "%s\t%s\t%s" % ('='*6, '='*35, '='*21)
        for post in recent:
            t_converted = datetime.datetime.strptime(post['dateCreated'].value,
                                                     "%Y%m%dT%H:%M:%S")
            padding = ' '*(35 - len(post['title']))
            print "%s\t%s\t%s" % (post['postid'],
                                    post['title'] + padding,
                                    t_converted.strftime("%b %d, %Y at %H:%M"))
        del pc, blog, recent

    ############################################################################ 
    # list blog categories option
    if opts.getcats:
        atleastoneoptionfound = 1
        pc = getpostconfig(cf_config)
        if pc == None:
            error("Cannot process 'categories' request because there is no\n\
                   \rblog specified\n")

        blog = blogapi.blogproxy(pc.xmlrpc, pc.username, pc.password)
        print "Retrieving category list for %s." % pc.name
        cat_list = blog.getCategories(pc.name)
        
        print "Category       \tParent        \tDescription"
        print "%s\t%s\t%s" % ('='*14, '='*14, '='*35)
        for cat in cat_list:
           parent = [ c['categoryName'] for c in cat_list 
                                        if cat['parentId'] == c['categoryId'] ]
           str = cat['categoryName'] + ' '*(16 - len(cat['categoryName']))
           if len(parent) == 0:
               str += ' '*16
           else:
               str += parent[0] + ' '*(16 - len(parent[0]))

           str += cat['categoryDescription']
           print str

        del blog, cat_list, pc

    ############################################################################ 
    # add a new category
    if opts.newcat:
        atleastoneoptionfound = 1
        pc = getpostconfig(cf_config)
        if pc == None:
            error("Cannot process newcategory request because there is no\n\
                   \rblog specified\n")

        # first, make sure the category doesn't already exist
        print "Checking if category already exists on %s..." % (pc.name)
        blog = blogapi.blogproxy(pc.xmlrpc, pc.username, pc.password)

        # this will check the category string to see if it is a valid blog
        # category, or partially valid if sub-categories are specified.
        # If the category exists on the blog, processing stops, otherwise
        # the first part that is not on the blog is returned
        t = blogapi.isBlogCategory(blog.getCategories(pc.name), opts.newcat)
        if t == None:
            print "The category specified alread exists on the blog."
        else:
            # t is a tuple with the first NEW category from the category string
            # specified and it's parentId.  Start adding categories from here
            print "Attempting to add %s category to %s" % (opts.newcat,
                                                           pc.name)
            # the '*' is the unpacking operator
            addCategory(blog, pc.name, opts.newcat, *t)

        print "Done\n"
        del blog

    # Basically, blogtool is supposed to do SOMETHING.  Either delete a post, 
    # publish a post, get recent posts, whatever.  As implemented, publishing
    # posts are not implemented as an option- just supply the filename on the
    # command line.  Everything else is implemented as an option.  Further, 
    # if options are supplied in ADDITION to post files, blogtool will process
    # everything.  So either options are specified, or posts are specified,
    # or both are specified.
    if len(argv) == 0:
        if not atleastoneoptionfound:
            parser.error("Try specifying some arguments.  Really...")
        else:
            sys.exit()

    ############################################################################ 
    # fairly straightforward loop over the file in the arglist
    for file in argv:
        # since we'll be processing all of this from memory, just read everything
        # into a list.  We won't need it after we process it anyway
        try:
            f = open(file, 'r')
            lines = f.readlines()

        except IOError:
            print "Unable to open %s..." % f
            continue

        finally:
            f.close()

        # technically, there needs to be at least 3 lines in the file- one for the
        # header, one blank line, one line for post text
        if len(lines) < 3:
            error('Postfile must have a blank line separating header and post \
                   text')

        header, posttext = getHeaderandPostText(lines)

        del lines  # no longer needed

        # now that we have the post header processed, we need to reconcile it
        # with anything from a config file
        try:
            post_config = reconcile(btconfig.parse(header), cf_config)
        except btconfigparser.btParseError, err_str:
            print err_str
            sys.exit()

        # loop through the blogs that this post is being written to.
        updatepostfile = 0
        for pc in post_config:
            # setup proxy server with appropriate info
            blog = blogapi.blogproxy(pc.xmlrpc, pc.username, pc.password)

            # process post text
            posthtml = procPost(blog, pc.name, posttext)

            print "Checking post categories..."
            pc.categories = procPostCategories(pc, blog, opts.addcats)

            # we need a post structure, so get one
            try:
                post = blogapi.buildPost(pc, 
                                         posthtml,
                                         timestamp = opts.posttime,
                                         publish = opts.publish)
            except blogapi.timeFormatError, timestr:
                print timestr
                sys.exit()

            # time to publish, or update, the post
            if pc.postid:
                print "Updating '%s' on %s..." % (pc.title, pc.name)
                postid = blog.editPost(pc.postid, post)
            else:
                if opts.publish:
                    print "Publishing '%s' to '%s'" % (pc.title,  pc.name) 
                else:
                    print "Publishing '%s' to '%s' as a draft" % (pc.title,
                                                                  pc.name)

                postid = blog.publishPost(pc.name, post)
                if postid != None:
                    header = updateHeader(header, pc.name, postid)
                    updatepostfile = 1

        # check if we need to update the post file
        if updatepostfile:
            print 'Updating post file...'
            updateFile(file, header, posttext)

    print "Done."
    sys.exit()

################################################################################
#
#
def edit(fh):
    editor = os.getenv('EDITOR', 'vim')

    try:
        rcode = subprocess.call([editor, fh.name])
    except OSError, e:
        print "Can't launch %s:  %s" % (editor, e)
        return None

    if rcode == 0:
        return True
    else:
        return None

################################################################################
#
#
def main():
    if len(sys.argv) == 1:
        fd = NamedTemporaryFile()
        text = edit(fd)
        if text != None:
            bt([fd.name])
        else:
            print "Nothing to do, exiting."
    else:
        bt(sys.argv[1:])

################################################################################
#
# nothing special here...
if __name__ == "__main__":
    main()

''' TODO:
         - make sure updating the header is done properly.
         - add processing for scheduling for blog posting
'''
