#!/usr/bin/python

import sys
import re
import unicodedata

from StringIO import StringIO

try:
    from lxml import etree
    LXML_PRESENT = True

except ImportError:
    LXML_PRESENT = False

#################################################################################
"""Html2MdException

    Base exception class for module.
"""
class Html2MdException(Exception):

    pass

#################################################################################
"""TagHandler

    Base class for objects that convert a tag into text
"""
class TagHandler:

    def __init__(self, txtConverter):
        self._txtConverter = txtConverter

    def test(self, e):
        if e.tag == self.tag:
            return True
        return False

    def convert(self, e):
        '''
            To be over-ridden by subclasses.
        '''
        pass

    def getElementText(self, e):
        text = ''
        if e.text and not e.text.isspace():
            text = e.text
        return text + self._txtConverter.childHandler(e)

    def getElementAttributes(self, e):
        attr_str = ''
        for a in e.attrib.keys():
            attr_str += "{@%s=%s}" % (a, e.attrib[a])
        return attr_str


#################################################################################
"""InlineTagHandler

    Subclass of TagHandler- base class for inline tag objects like <em>, <code>,
    <strong>, etc. due to common conversion processing
"""
class InlineTagHandler(TagHandler):

    def convert(self, e):
        addspace = False
        '''
        EDGE CASE: it's possible to have nested inline elements, like ***strong
        and emphasis*** in which case, the outer element won't have any text.
        In this case, we'll assume that there must be a child element with text,
        so we'll parse that first to get some text, then place complete
        processing here.  
        '''
        if e.text is None:
            text = self._txtConverter.childHandler(e)
        else:
            if e.text.endswith(' '):
                addspace = True
            text = e.text
        text = "%s%s%s" % (self.inlinechars, text.rstrip(), self.inlinechars)
        if addspace:
            text += ' '

        return text

#################################################################################
"""FixedStringTagHandler

    subclass of TagHandler, baseclass for tag objects that process tags which
    return a fixed string, eg <br /> and <hr /> tags
"""
class FixedStringTagHandler(TagHandler):

    def convert(self, e):
        return self.conversion_str

#################################################################################
"""InlineCodeHandler

    Class for inline HTML elements like <em>text</em>
"""
class InlineCodeHandler(InlineTagHandler):

    tag = 'code'
    inlinechars = '`'

    def test(self, e):
        if e.tag == self.tag and e.getparent().tag != 'pre':
            return True
        return False

#################################################################################
"""EmHandler

    Specific class for ``em`` tags.
"""
class EmHandler(InlineTagHandler):
    
    tag = 'em'
    inlinechars = '*'

#################################################################################
"""StrongHandler

    Specific class for ``strong`` tags.
"""
class StrongHandler(InlineTagHandler):
    
    tag = 'strong'
    inlinechars = '**'

#################################################################################
"""StrikeHandler

    Specific class for ``strike`` tags- NOT IN MARKDOWN SPEC.
"""
class StrikeHandler(InlineTagHandler):

    tag = 'strike'
    inlinechars = '-'

#################################################################################
"""BrHandler

    Specific classs for ``br`` tags.
"""
class BrHandler(FixedStringTagHandler):
    
    tag = 'br'
    conversion_str = '  \n'

#################################################################################
"""HorizontalRuleHandler

    Specific class for ``hr`` tags.
"""
class HorizontalRuleHandler(FixedStringTagHandler):
    
    tag = 'hr'
    conversion_str = '* * *\n\n'
    
#################################################################################
"""AHandler

    Specific class for ``a`` tags.
"""
class AHandler(TagHandler):

    tag = 'a'

    def convert(self, a):
        if 'href' not in a.attrib.keys():
            raise Html2MdException

        # build return string based on anchor tag
        s = self.getElementText(a)

        # if the link is within the current document, use inline style
        if a.attrib['href'].startswith('#'):
            return "[%s](%s)" % (s, a.attrib['href'])

        reflink = self._searchlink(a.attrib['href'])
        if reflink is None:
            reflink = self._txtConverter._reflinks
            self._txtConverter._reflinks += 1
            # save the reflinks
            if 'title' not in a.attrib.keys():
                a.set('title', '')
            self._txtConverter._links.append((reflink, 
                                              a.attrib['href'],
                                              a.attrib['title']))

        # now that we have all the text, format it in markdown syntax
        return "[%s][%s]" % (s, reflink)
       
    def _searchlink(self, linktext):
        for t in self._txtConverter._links:
            if linktext == t[1]:
                return self._txtConverter._links.index(t)

        return None

#################################################################################
"""ImgHandler

    Specific class for ``img`` tags.
"""
class ImgHandler(TagHandler):

    tag = 'img'

    def convert(self, img):
        # processes img tag if it's on it's own
        attrib_str = self.getElementAttributes(img)
        if 'alt' not in img.attrib.keys() and 'src' not in img.attrib.keys():
            raise Html2MdException

        if 'title' not in img.attrib.keys():
            img.set('title', '')
        img_text = "![%s%s](%s %s)" % (img.attrib['alt'], 
                                       attrib_str,
                                       img.attrib['src'],
                                       img.attrib['title'])
        return img_text

    def getElementAttributes(self, img):
        attr_str = ''
        for a in img.attrib.keys():
            if a not in ['alt', 'title', 'src']:
                attr_str += "{@%s=%s}" % (a, img.attrib[a])
        return attr_str
 
#################################################################################
"""PHandler

    Specific class for ``p`` tags.
"""
class PHandler(TagHandler):
    
    tag = 'p'

    def convert(self, p):
        attrs = self.getElementAttributes(p)
        if attrs:
            attrs += '\n'
       
        return attrs + self.getElementText(p) + '\n\n'


#################################################################################
"""HeadingHandler

    Specific class for ``h1-6`` tags.
"""
class HeadingHandler(TagHandler):
    
    tag = re.compile('^h(\d)$')

    def test(self, e):
        if not isinstance(e.tag, str):
            return False
        m = self.tag.match(e.tag)
        if m:
            self._hlevel = m.group(1)
            return True

        return False

    def convert(self, h):
        h_text = self.getElementAttributes(h) + self.getElementText(h)
        if h.tag == 'h1':
            hdr_char = '='
        elif h.tag == 'h2':
            hdr_char = '-'
        else:
            return "#"*int(self._hlevel) + h_text + '\n\n'

        return h_text + '\n' + hdr_char*len(h_text) + '\n\n'
        
#################################################################################
"""BlockQuoteHandler

    Specific class for ``blockquote`` tags.
"""
class BlockQuoteHandler(TagHandler):

    tag = 'blockquote'
    prepend_char = '> '

    def __init__(self, txtConverter):
        self._txtConverter = txtConverter
        self._level = -1

    def convert(self, bq):
        self._level += 1

        text = self.getElementText(bq).rstrip() + '\n'
        text = self._txtConverter.prepend(text, self.prepend_char)
        if self._level > 0:
            text += '\n'

        self._level -= 1
        return text

#################################################################################
"""PreHandler

    Specific class for ``pre`` tags.
"""
class PreHandler(TagHandler):

    tag = 'pre'

    def convert(self, pre):
        return self._txtConverter.childHandler(pre)

#################################################################################
"""CodeBlockHandler
 
    Specfic class for ``code`` tags.
"""
class CodeBlockHandler(TagHandler):

    tag = 'code'
    prepend_char = '    '

    def test(self, e):
        if e.tag == self.tag and e.getparent().tag == 'pre':
            return True
        return False

    def convert(self, cb):
        return self._txtConverter.prepend(cb.text, self.prepend_char)

#################################################################################
"""OListHandler

    Object that converts ordered list tags to text- serves as a base class for
    the UListHandler as well
"""
class OListHandler(TagHandler):

    tag = 'ol'

    def convert(self, ol):
        # We'll handle this a little differently- we have to manually manage
        # each list item- if we just call 'getElementText' on the 'ol' tag, it
        # would process ALL the 'li' tags under here and we don't want that
        # because it would be too error prone untangling the mess to figure out
        # where to put the prepend char.  Since we're in a list related tag, I
        # think it's safe to assume it has children, so setup the loop and go.
        # NOTE: This approach also means there is not need for an 'li' tag
        #       handler
        self._txtConverter.listlevel += 1

        listitems = [ self.getElementText(li) for li in ol ]           
        text = self.listloop(listitems)

        # edge case- if a nested list and thies is a previous sibling that
        # isnt' a block tag, prepend a '\n'
        if self._txtConverter.listlevel > 0:
            previous_sibling = ol.getprevious()
            if previous_sibling is not None and \
               not self._txtConverter._isblock(previous_sibling):
                text = '\n' + text

        self._txtConverter.listlevel -= 1
        return text

    def listloop(self, listitems):
        item_number = 1 
        text = ''
        for listitem in listitems:
            # if a list without p-tags around the items, make sure the items are
            # separated with a '\n'
            if not listitem.endswith('\n'):
                listitem += '\n'
            listitem_pre = "%s." % item_number
            listitem_pre += ' '*(4 - len(listitem_pre))
            item_number += 1
            text += self.formatListItem(listitem, listitem_pre)

        return text

    def formatListItem(self, listitem, li_pre):
        text = ''
        li_pre = li_pre
        for line in listitem.splitlines(1):
            if li_pre:
                text += "%s" % (' '*(4*self._txtConverter.listlevel) + li_pre + 
                                                                   line.lstrip())
                li_pre = ''
            elif not line.isspace():
                text += "%s" % (' '*(4*(self._txtConverter.listlevel+1)) + 
                                                                   line.lstrip())
            else:
                # most likely a linefeed...
                text += line

        return text

    def getElementText(self, e):
        text = ''
        if e.text and not e.text.isspace():
            text = e.text
        # edge case- if an 'li' tag with text and the next element is another
        # list add a '\n'
        if text and e.tag == 'li' and len(e) != 0 and e[0].tag in ['ol', 'ul']:
            text += '\n'
        return text + self._txtConverter.childHandler(e)

#################################################################################
"""UListHandler

    Subclass of OListHandler, for ``ul`` tags.
"""
class UListHandler(OListHandler):

    tag = 'ul'

    def listloop(self, listitems):
        listitem_pre = '*   '
        text = ''
        for listitem in listitems:
            if not listitem.endswith('\n'):
                listitem += '\n'
            text += self.formatListItem(listitem, listitem_pre)

        return text

#################################################################################
"""Html2Morkdown

    Creates a converter object for turning HTML markup into markdown text.
"""
class Html2Markdown:

    _inlinetags = ['code', 'em', 'strong', 'br', 'strike', 'img', 'a']
    _blocktags = ['p', 'blockquote', 'li', 'ul', 'ol', 'pre', 'h1', 'h2', 'h3',
                  'h4', 'h5', 'h6', 'hr']

    def __init__(self):
        self._taghandlers = []
        self._taghandlers.append(PHandler(self))
        self._taghandlers.append(BlockQuoteHandler(self))
        self._taghandlers.append(UListHandler(self))
        self._taghandlers.append(OListHandler(self))
        self._taghandlers.append(HeadingHandler(self))
        self._taghandlers.append(PreHandler(self))
        self._taghandlers.append(CodeBlockHandler(self))
        self._taghandlers.append(AHandler(self))
        self._taghandlers.append(InlineCodeHandler(self))
        self._taghandlers.append(EmHandler(self))
        self._taghandlers.append(StrongHandler(self))
        self._taghandlers.append(BrHandler(self))
        self._taghandlers.append(StrikeHandler(self))
        self._taghandlers.append(ImgHandler(self))
        self._taghandlers.append(HorizontalRuleHandler(self))

        self.listlevel = -1
        self._blocklist = []
        self._reflinks = 0
        self._links = []

    def convert(self, html):
        try:
            nhtml = unicodedata.normalize('NFKD', html)
        except TypeError:
            nhtml = html
        except UnicodeEncodeError:
            print repr(html)
            sys.exit()

        # this is a negative-lookahead re- we're looking for '&' that are
        # unescaped in the data, the lxml parser chokes on those
        i = 0
        for m in re.finditer(u'&(?!amp;|gt;|lt;|quot;|#\d+;)', nhtml):
            if m:
                nhtml = nhtml[:m.start()+(i*4)] + u'&amp;' + nhtml[m.end()+(i*4):]
                i = i + 1
#        print nhtml
        root = etree.fromstring("<post>%s</post>" % nhtml)

        # if the 'post' tag has text, then grab it and add it as the first
        # block before proceeding to process the children
        if root.text and not root.text.isspace():
            self._blocklist.append(root.text.rstrip() + '\n')

        # process the children of root- we don't use `childhandler` because that
        # would return a large blob of text.  This way we can control the block
        # spacing
        for element in root:
            links_snapshot = len(self._links)
            try:
                text = self._tagHandler(element)
#                print text
                if text:
                    if self._isblock(element):
                        self._blocklist.append(text.rstrip() + '\n')
                    else:
                        # some kind of inline tag so we'll for now we'll just 
                        # append to the previous block
                        self._blocklist[-1] = self._blocklist[-1].rstrip() + \
                                             ' ' + text.rstrip() + '\n'
            except Html2MdException:
                while len(self._links) != links_snapshot:
                    self._links.pop()
                    self._reflinks -= 1

                self._blocklist.append(etree.tostring(element, pretty_print=True).rstrip() + '\n')
            # now add any referenced links as the final block
            if links_snapshot < len(self._links):
                self._blocklist.append(self._refLinkText(links_snapshot))

        return '\n'.join(self._blocklist)

    def childHandler(self, element):
        text = ''
        if len(element) != 0:
            for child in element:
                try:
#                    print "Child: %s" % child.tag
                    text += self._tagHandler(child)
                except Html2MdException:
                    raise
        return text

    def checkTail(self, element):
        if element.tail and not element.tail.isspace():
#            print "TAIL: %s" % element.tag
#            return element.tail.lstrip('\n')
            return element.tail
        else:
            return ''

    def prepend(self, text, pretext):
#        print text
        rtext = ''
        for line in text.splitlines():
            rtext += "%s%s\n" % (pretext, line)

        return rtext

    ############################################################################
    """_tagHandler

        Scans the `_taghandlers` list for a handler of the element type
        based on the element's tag.  Calls the `convert` method of the
        handler object.
        If no handler is found, then perform a simple check to see if the
        element is a 'comment'
        Otherwise return the tag as a string
    """
    def _tagHandler(self, element):
        for handler in self._taghandlers:
            if handler.test(element):
                text = handler.convert(element)
                break
        else:
            if element.tag is etree.Comment:
                text = "+ + +"
                if element.text != "more":
                    text +=  ' ' + element.text + " + + +"
                text += "\n\n"
            else:
                # certain elements are better printed using HTML method than XML
                # NOTE: Should use my own serializer rather than relying on
                # tostring
                if element.tag in ['iframe']:
                    text = etree.tostring(element, pretty_print=True, method="html")
                else:
                    text = etree.tostring(element, pretty_print=True)
                return text.replace(u'&amp;', u'&')

        return text + self.checkTail(element)

    def _refLinkText(self, first_link):
        text = ''
        for ref in self._links[first_link:]:
            text += "  [%s]: %s" % (ref[0], ref[1])
            if ref[2]:
                text += ''' "%s"''' % (ref[2])
            text += '\n'

        del self._links[:]

        return text

    def _isblock(self, e):
        if e.tag in self._blocktags:
            return True
        if e.tag == 'code' and e.getparent().tag == 'pre':
            return True
        # we need to pick up comments- but their tag is not a string, but a 
        # function so, until this stops working, we'll check the tag instance
        # for a string and return True if it isn't
        if not isinstance(e.tag, str):
            return True

        return False

################################################################################
"""convert

    Function that for instantiating an Html2Markdown object then converting the
    HTML.
"""
def convert(html):
    md = Html2Markdown()
 
    return md.convert(html)
