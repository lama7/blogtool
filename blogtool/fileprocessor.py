
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

######################### Error classes for blogtool ###########################
################################################################################
"""FileProcessor

    Define base class for errors
"""
class FileProcessorError(Exception): 
    # to be overriden by the subclass
    def __init__(self, msg):
        self.message = 'Error in FileProcessor: %s' % msg

    # this is typically all that's done with the __str__ method
    def __str__(self):
        return self.message

################################################################################
"""FileProcessorRetry
  
    Simple exception to facilitate cross module looping based on success or
    failure of an action here in the fileprocessor module.
"""
class FileProcessorRetry(Exception):
    pass

################################################################################
"""FileProcessor

    This class contains methods to process a file for posting to a blog.

"""
class FileProcessor():

    if MARKDOWN_PRESENT:
        md = markdown.Markdown(extensions=['typed_list'])

    EXTENDED_ENTRY_RE = re.compile(r'\n\n(?:(?:### MORE ###\s*)|(?:(?:\+\ *){3,}(.*?)(?:\+\ *)*))\n\n')

    ############################################################################
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    ############################################################################
    """_getHeaderandContent

        Separates the text of a file into it's header section and content
        section.
    """
    def _getHeaderandContent(self, linelist):
        # find first blank line so we can split the list
        for line in linelist:
            if line.isspace():
                i = linelist.index(line)
                break
        else:
            raise FileProcessorError('''
FileProcessor._getHeaderandContent: Post file must have a blank line separating
header and post text.
''' )

        if len(linelist[0:i]) == 0:
            raise FileProcessorError('''
FileProcessor._getHeaderandContent: No header found, aborting.
''')
        elif len(linelist[i+1:]) == 0:
            raise FileProcessorError('''
FileProcessor._getHeaderandContent: No text for post, aborting.
''')

        return ''.join(linelist[0:i]), ''.join(linelist[i + 1:])

    ############################################################################ 
    """_procContent

        Processes the content portion of the file, running any plaintext markup
        converters.
    """
    def _procContent(self, posttext):
        if not MARKDOWN_PRESENT:
            print "Unable to publish post without python-markdown.  Sorry..."
            sys.exit()

        extended = ''
        more_text = ''
        m = self.EXTENDED_ENTRY_RE.search(posttext)
        if m:
            description = posttext[:m.start() + 1]
            extended = posttext[m.end() - 1:]
            # If present, this is the text that will appear in the "MORE" link 
            # on the blog
            if m.group(1):
                more_text = m.group(1)
            else:
                more_text = ''
        else:
            description = posttext

        html_desc = self._procHTML(description)
        if extended:
            html_ext = self._procHTML(extended)
        else:
            html_ext = ''

        return html_desc, html_ext, more_text

    ############################################################################ 
    """_procHTML

       Handles extra processing after markdown processing is complete.  For now,
       this consists of uploading image files and fixing up links to the
       uploaded image. 
    """
    def _procHTML(self, text):

        ######################################################################## 
        """_ptFixElement

            Fixes some whitespace issues and also takes care of uploading
            JPG files and then setting the link based on the result of the
            upload.
        """
        def _ptFixElement(e):
            if e.text and e.tag not in ['pre', 'code', 'comment']:
                e.text = e.text.replace('\n', u' ')
            if e.tail:
                e.tail = e.tail.replace('\n', u' ')
            if e.tag == 'img':
                ifile = e.attrib['src']
                if ifile.find("http://") != -1:
                    # web resource defined, nothing to do
                    return

                try:
                    ifile = utils.chkFile(ifile)
                    print "Attempting to upload '%s'..." % ifile
                    res = self._blogproxy.upload(ifile)
                except utils.UtilsError, err:
                    raise FileProcessorError("File not found: %s\n" % err)
                except ProxyError, err:
                    raise FileProcessorError("In FileProcessor._procHTML: %s\n" % err)

                # FIX ME- don't know if this is necessary
                if res == None:
                    print "Upload failed, proceeding...\n"
                    return

                e.attrib['src'] = res['url']
                if 'alt' not in e.keys():
                    e.set('alt', res['file'])
                # the 'res' attr is bogus- I've added it so that I can 
                # specify the appropriate resolution file I want in the url.  
                if 'res' in e.keys():
                    res_str = '-' + e.attrib['res'] + '.'
                    e.attrib['src'] = re.sub("\.(\w*)$", 
                                             r'%s\1' % res_str,
                                             e.attrib['src'])
                    del(e.attrib['res'])
            return

        def _ptEscapeCData(text, attrib=False):
            c_replace = dict([( "&", "&amp;"),
                              ( "<", "&lt;"),
                              ( ">", "&gt;"),
                              ( u'\u2019', "&#8217;"), #apostrophe
                              ( u'\u201c', "&#8220;"), #left double quote
                              ( u'\u201d', "&#8221;"), #right double quote
                            ])
            for c in c_replace.keys():
                if c in text:
                    text = text.replace(c, c_replace[c])

            if attrib:
                attrib_replace = dict([("\"", "&quot;"),
                                       ("\n", "&#10;"),
                                     ])
                for c in attrib_replace.keys():
                    if c in text:
                        text = text.replace(c, attrib_replace[c])
            return text

        #######################################################################
        """_ptSerialize

            Serializes an individual element as well as its child elements.
        """
        def _ptSerialize(e):
            _ptFixElement(e)
            e_str = '<%s' % (e.tag)
            for a in e.attrib.keys():
                e_str += ' %s=\"%s\"' %(a, _ptEscapeCData(e.attrib[a], True))

            # There are 2 different paths here, self-closing tags or create
            # an end tag
            if e.tag in ("area", "base", "basefont", "br", "col", "frame", "hr",
                         "img", "input", "isindex", "link", "meta", "param",
                         "embed"):
                e_str += "/>"  # self-closing
            else:
                e_str += '>'
                if e.text:
                    e_str += _ptEscapeCData(e.text)
                if len(e) != 0:
                    for child in e:
                        e_str += _ptSerialize(child)
                e_str += "</%s>" % (e.tag)
                               
            # finally, check the tail
            if e.tail:
                e_str += _ptEscapeCData(e.tail)

            return e_str

        #######################################################################
        """_ptFixUp

            Facilitates adjustments to the markup.  Accepts a parsed tree
            which is then reserialized with all adjustments.  I tried to use
            the etree.tostring function, but there were certain tags that
            couldn't be rendered properly in xhtml, like the iframe tag.
            Thus, I have to serialize it myself.
        """ 
        def _ptFixUp(tree):
            xhtml = ''
            for element in tree:
                if element.tag != 'post':
                    xhtml += _ptSerialize(element)

#            teststr = etree.tostring(tree, pretty_print=True).replace('<post>', '').replace('</post>', '')
#            if teststr.rstrip().lstrip() == xhtml.rstrip():
#                print "Match!/n"
#            else:
#                print xhtml + '\n'
#                print teststr
#            sys.exit()

            return xhtml

        # _procHTML function code starts here- basically, decode the post text
        # then run it through Markdown, then parse it with lxml so we can
        # process certain tags(ptHelper above), finally return the final
        # product as a string
        # check if charset was defined on command line
        if self.charset:
            encodings = [ self.charset ]
        else:
            encodings = ['ascii', 'utf-8', 'utf-16', 'iso-8859-1']

        last_error = ''
        for encoding in encodings:
            try:
                xhtml = self.md.convert(text.decode(encoding))
            except (UnicodeError, UnicodeDecodeError), err:
                last_error = err
                continue
            except:
                raise FileProcessorError("In FileProcessor._procHTML: %s\n" %
                                                             sys.exc_info()[0])
            else:
                # The text is marked up at this stage, but we need to clean it
                # up prior to shipping it out, so we parse it using lxml and
                # then rebuild it as a string as we fix each tag
                # Start by escaping any stray '&' characters- just make sure
                # they aren't already part of an escape sequence
                i = 0
                for m in re.finditer(u'&(?!amp|gt|lt|#\d+;)', xhtml):
                    if m:
                        xhtml = xhtml[:m.start()+(i*4)] + u'&amp;' + xhtml[m.end()+(i*4):]
                        i = i + 1
                return _ptFixUp(etree.XML('<post>%s</post>' % xhtml))
        else:
            raise FileProcessorError("In FileProcessor._procHTML: %s\n" %
                                                                     last_error)

    ############################################################################ 
    """_procCategories

        Takes the categories specified in the post header and validates them
        against the actual categories on the blog.  Takes into accout
        subcategories, so potentially categories can be similarly named but
        still be distinct based on their parent category, i.e. category "code"
        could be duplicated because there is a "lua.code" category and a
        "python.code" category.

        If any categories are NOT on the blog, then checks to see if they should
        be added or not.  Basically, we're checking for typos.  A default
        category is used and a notification is output so the user can correct
        the issue if they so desire.

        This modifies the original header category string.  It's most noticable
        where subcategories are concerned, the dotted notation will be lost and
        duplicate names are lost.
    """
    def _procCategories(self, header):
        # first, build a list of catgories that aren't on the blog from the
        # post's category list
        nonCats = []
        for c in header.categories:
            try:
                cat_list = self._blogproxy.getCategories()
            except ProxyError, err:
                raise FileProcessorError("In FileProcessor._procCategories:  %s\n" % err)
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
#            header.categories = list(set(reduce(lambda l1, l2: l1 + l2, 
#                                      [c.split('.') for c in header.categories])))
            return list(set(reduce(lambda l1, l2: l1 + l2, 
                                      [c.split('.') for c in header.categories])))

    ############################################################################ 
    """parsePostFile

        Attempts to read a post file.  If successful, then a header and text
        portion are created.  The header portion can be parsed for so the
        text portion can be sent to the appropriate blogs.
    """
    def parsePostFile(self, filename, hdrtext):
        try:
            if filename == 'STDIN':
                f = sys.stdin
            else:
                f = open(filename, 'r')
            lines = f.readlines()
        except IOError:
            try:
                f = open(filename, 'w')
            except IOError, err:
                print err
                sys.exit()

            utils.edit(hdrtext, f)
            raise FileProcessorRetry()
        else:
            f.close()

        return self._getHeaderandContent(lines)

    ############################################################################ 
    """pushContent

        Takes care of pushing a post up to a blog as defined by a header.
        Creates a blogproxy, processes the blog categories and builds a post
        object prior to determining if the post is just being updated or if it
        is a new post.  If the post is successfully sent, the post file is
        updated with the post ID assigned at the blog.
        Added: Also can be used to write a comment for the blog- thus the name
               change from pushPost to pushContent
    """
    def pushContent(self, post_text, header):
        rval = None
        self._blogproxy = header.proxy()
        html_desc, html_ext, more_text = self._procContent(post_text)
        if self.comment:
            comment = utils.buildComment(header, html_desc)
            try:
                if header.commentid:
                    print "Updating comment %s on %s" % (header.commentid, 
                                                         header.name)
                    rval = self._blogproxy.editComment(header.commentid,
                                                       comment)
                else:
                    print "Publishing comment to post %s..." % header.postid
                    commentid = self._blogproxy.newComment(header.postid,
                                                           comment)
                    rval = commentid
            except ProxyError, err:
                raise FileProcessorError("In FileProcessor.pushContent: %s\n" % err)
        else:
            print "Checking post categories..."
            categories = self._procCategories(header)
            try:
                post = utils.buildPost(header,
                                       html_desc,
                                       html_ext,
                                       categories,
                                       more_text,
                                       timestamp = self.posttime,
                                       publish = self.publish )
                if header.postid:
                    print "Updating '%s' on %s..." % (header.title, header.name)
                    self._blogproxy.editPost(header.postid, post)
                else:
                    if self.publish:
                        msg_text = "Publishing '%s' to '%s'" 
                    else:
                        msg_text = "Publishing '%s' to '%s' as a draft" 
                    print msg_text % (header.title, header.name)
                    postid = self._blogproxy.publishPost(post)
                    rval = postid
            except utils.UtilsError, timestr:
                raise FileProcessorError("In FileProcessor.pushContent: %s\n" %
                                                                       timestr)
            except ProxyError, err:
                raise FileProcessorError("In FileProcessor.pushContent: %s\n" %
                                                                           err)

        return rval

    ############################################################################ 
    """updateFile

        If a post is successfully published on the blog, we update the file with
        POSTID information so the file can potentially be used for post updates
        later on.
    """
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
