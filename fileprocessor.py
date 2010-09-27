
from xmlproxy.proxybase import ProxyError
import utils
import re
import sys

try:
    from lxml import etree
except ImportError:
    print """
ATTENTION:
You need to install lxml to take full advantage of blogtool capabilities.
Without it, downloading posts is disallowed.  If all you need it to publish
posts to a blog, then this should be fine.

Unfortunately, this annoying warning message will pop-up everytime you run
blogtool.
"""
    raw_input('Press <ENTER> to continue...')
    import xml.etree.cElementTree as etree

try:
    import markdown
    MARKDOWN_PRESENT = True
except ImportError:
    print """
ATTENTION:
In order to publish posts with blogtool, python-markdown is required.  Without
it, all blogtool is capable of is some basic blog interaction for listing posts
or listing/ modifying categories.

Also, this annoying message will be displayed everytime you run blogtool.
"""
    raw_input('Press <ENTER> to continue...')
    MARKDOWN_PRESENT = False

################################################################################
'''   
    Error classes for blogtool
'''

################################################################################
'''   
    define base class for errors
'''
class FileProcessorError(Exception): 
    # to be overriden by the subclass
    def __init__(self, msg):
        self.message = 'blogtoolError: %s' % msg

    # this is typically all that's done with the __str__ method
    def __str__(self):
        return self.message

################################################################################
'''
'''
class FileProcessorRetry(Exception):
    pass

################################################################################
'''
    FileProcessor Class

    This class contains methods to process a file for posting to a blog.

'''
class FileProcessor():

    if MARKDOWN_PRESENT:
#        md = markdown.Markdown(extensions=['typed_list'])
        md = markdown.Markdown()


    EXTENDED_ENTRY_RE = re.compile(r'\n### MORE ###\s*\n')

    ############################################################################
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    ############################################################################
    def _getHeaderandPostText(self, linelist):
        # find first blank line so we can split the list
        for line in linelist:
            if line.isspace():
                i = linelist.index(line)
                break

        else:
            raise FileProcessorError("""
Post file must have a blank line separating header and post text.
""" )

        if len(linelist[0:i]) == 0:
            raise FileProcessorError('''
No header found, aborting.
''')
        elif len(linelist[i+1:]) == 0:
            raise FileProcessorError('''
No text for post, aborting.
''')

        return ''.join(linelist[0:i]), ''.join(linelist[i + 1:])

    ############################################################################ 
    def _procPost(self, posttext):
        if not MARKDOWN_PRESENT:
            print "Unable to publish post without python-markdown.  Sorry..."
            sys.exit()

        m = self.EXTENDED_ENTRY_RE.search(posttext)
        if m:
            description = posttext[:m.start()]
            extended = posttext[m.end():]
        else:
            description = posttext
            extended = ''

        html_desc = self._procText(description)
        if extended:
            html_ext = self._procText(extended)
        else:
            html_ext = ''

        return html_desc, html_ext

    ############################################################################ 
    '''
       Handles extra processing after markdown processing is complete.  For now,
       this consists of uploading image files and fixing up links to the
       uploaded image. 
    '''
    def _procText(self, text):
        tree = etree.XML('<post>%s</post>' % self.md.convert(text))
        for e in tree.getiterator():
            if e.text and e.tag not in ['pre', 'code', 'comment']:
                e.text = e.text.replace('\n', u' ')
            if e.tail:
                e.tail = e.tail.replace('\n', u' ')
            if e.tag == 'img':
                ifile = e.attrib['src']
                if ifile.find("http://") != -1:
                    # web resource defined, nothing to do
                    continue

                try:
                    ifile = utils.chkFile(ifile)
                    print "Attempting to upload '%s'..." % ifile
                    res = self._blogproxy.upload(ifile)
                except utils.UtilsError, err:
                    print "File not found: %s" % err
                    sys.exit(1)
                except ProxyError, err:
                    print "Caught in FileProcessor._procText:"
                    print err
                    sys.exit()

                # FIX ME- don't know if this is necessary
                if res == None:
                    print "Upload failed, proceeding...\n"
                    continue

                e.attrib['src'] = res['url']
                if 'alt' not in e.keys():
                    e.set('alt', res['file'])
                # the 'res' attr is bogus- I've added it so that I can specify the
                # appropriate resolution file I want in the url.  
                if 'res' in e.keys():
                    res_str = '-' + e.attrib['res'] + '.'
                    e.attrib['src'] = re.sub("\.(\w*)$", r'%s\1' % res_str, e.attrib['src'])
                    del(e.attrib['res'])

#        print etree.tostring(tree)
#        sys.exit()
    
        return (etree.tostring(tree).replace('<post>', '')).replace('</post>', '')

    ############################################################################ 
    def _procPostCategories(self, header):
        # first, build a list of catgories that aren't on the blog from the
        # post's category list
        nonCats = []
        for c in header.categories:
            try:
                cat_list = self._blogproxy.getCategories()
            except ProxyError, err:
                print "Caught in FileProcessor._procPostCategories:"
                print err
                sys.exit()

            t = utils.isBlogCategory(cat_list, c)
            if t != None:
                nonCats.append((c,) + t)

        # see if there were any unrecognized categories
        if len(nonCats) == 0:
            print "Post categories OK"
        elif self.addpostcats:
            [ utils.addCategory(self._blogproxy, *ct) for ct in nonCats ]
        else:
            rcats = [ ct[0] for ct in nonCats ]
            print "Category '%s' is not a valid category for %s so it is being\n\
                   \r removed from the category list for this post.\n\
                   \rUse the -a option if you wish to override this behavior or\n\
                   \rthe -n option to add it from the command line.\n" %\
                                                         (', '.join(rcats),
                                                          header.name)
            [ header.categories.remove(c) for c in rcats ]

        # last bit of category processing- if there are any categories 
        # with subcategories, like 'cat.subcat', they need to be split
        # up so that the post is categorized properly
        # the 'list(set(...)) removes all duplicates 
        if len(header.categories) == 0:
            print "This post has no valid categories, the default blog category\n\
                   \rwill be used.\n"
        else:
            header.categories =  list(set(reduce(lambda l1, l2: l1 + l2, 
                                      [c.split('.') for c in header.categories])))

    ############################################################################ 
    ''' parsePostFile

        Attempts to read a post file.  If successful, then a header and text
        portion are created.  The header portion can be parsed for so the
        text portion can be sent to the appropriate blogs.

    '''
    def parsePostFile(self, filename):
        try:
            f = open(filename, 'r')
            lines = f.readlines()
        except IOError:
            try:
                f = open(filename, 'w')
            except IOError, err:
                print err
                sys.exit()

            utils.edit(f, "TITLE: \nCATEGORIES: \n")
            raise FileProcessorRetry()
        else:
            f.close()

        return self._getHeaderandPostText(lines)

    ############################################################################ 
    '''
        pushPost

        Takes care of pushing a post up to a blog as defined by a header.
        Creates a blogproxy, processes the blog categories and builds a post
        object prior to determining if the post is just being updated or if it
        is a new post.  If the post is successfully sent, the post file is
        updated with the post ID assigned at the blog.
    '''
    def pushPost(self, post_text, header):
        self._blogproxy = header.proxy()
        self._blogname = header.name

        html_desc, html_ext = self._procPost(post_text)

        print "Checking post categories..."
        self._procPostCategories(header)

        rval = None
        try:
            post = utils.buildPost(header,
                                   html_desc,
                                   html_ext,
                                   timestamp = self.posttime,
                                   publish = self.publish )
            if header.postid:
                print "Updating '%s' on %s..." % (header.title, header.name)
                self._blogproxy.editPost(header.postid, post)
            else:
                if self.publish:
                    print "Publishing '%s' to '%s'" % (header.title, header.name) 
                else:
                    print "Publishing '%s' to '%s' as a draft" % (header.title,
                                                                  header.name)
                postid = self._blogproxy.publishPost(post)
                rval = postid
     
        except utils.UtilsError, timestr:
            print timestr
            sys.exit()
        except ProxyError, err:
            print "Caught in FileProcessor.pushPost:"
            print err
            sys.exit()

        return rval

    ############################################################################ 
    def updateFile(self, filename, hdr_text, post_text):
        # alter the file name so we don't overwrite
        filename += '.posted'
        try:
            f = open(filename, 'w')
            f.write(hdr_text)
            f.write('\n')
            f.write(post_text)
        except IOError:
            print "Error writing updated post file %s" % file
        else:
            f.close()


