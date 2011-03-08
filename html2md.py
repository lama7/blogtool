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
'''
    class TagHandler

    Base class for objects that convert a tag into text

'''
class TagHandler:

    def __init__(self, txtConverter):
        self._txtConverter = txtConverter

    def test(self, e):
        if e.tag == self.tag:
            return True
        return False

    def convert(self, e):
        addspace = False
        if e.text.endswith(' '):
            addspace = True
        text = "%s%s%s" % (self.inlinechars, e.text.rstrip(), self.inlinechars)
        if addspace:
            text += ' '

        return text

    def getElementText(self, e):
        text = ''
        if e.text and not e.text.isspace():
            text = e.text
        return text + self._txtConverter.childHandler(e)

    def getTagAttributes(self, e):
        attr_str = ''
        if e.tag == 'img':
            for a in e.attrib.keys():
                if a not in ['alt', 'title', 'src']:
                    attr_str += "{@%s=%s}" % (a, e.attrib[a])
        else:
            for a in e.attrib.keys():
                attr_str += "{@%s=%s}" % (a, e.attrib[a])
        return attr_str


#################################################################################
class InlineCodeHandler(TagHandler):

    tag = 'code'
    inlinechars = '`'

    def test(self, e):
        if e.tag == self.tag and e.getparent().tag != 'pre':
            return True
        return False

#################################################################################
class EmHandler(TagHandler):
    
    tag = 'em'
    inlinechars = '*'

#################################################################################
class StrongHandler(TagHandler):
    
    tag = 'strong'
    inlinechars = '**'

#################################################################################
class StrikeHandler(TagHandler):

    tag = 'strike'
    inlinechars = '-'

#################################################################################
class BrHandler(TagHandler):
    
    tag = 'br'

    def convert(self, e):
        return '  \n'

#################################################################################
class AHandler(TagHandler):

    tag = 'a'

    def convert(self, a):
        # build return string based on anchor tag
        s = self.getElementText(a)

        # now that we have all the text, format it in markdown syntax
        s = "[%s][%s]" % (s, self._txtConverter._reflinks)
        
        # save the reflinks
        if 'title' not in a.attrib.keys():
            a.set('title', '')
        self._txtConverter._links.append((self._txtConverter._reflinks, 
                                          a.attrib['href'],
                                          a.attrib['title']))
        self._txtConverter._reflinks += 1
            
        return s

#################################################################################
class ImgHandler(TagHandler):

    tag = 'img'

    def convert(self, img):
        # processes img tag if it's on it's own
        attrib_str = self.getTagAttributes(img)
        if 'title' not in img.attrib.keys():
            img.set('title', '')
        img_text = "![%s%s](%s %s)" % (img.attrib['alt'], 
                                       attrib_str,
                                       img.attrib['src'],
                                       img.attrib['title'])
        return img_text

#################################################################################
class PHandler(TagHandler):
    
    tag = 'p'

    def convert(self, p):
        return self.getElementText(p) + '\n\n'

#################################################################################
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
class PreHandler(TagHandler):

    tag = 'pre'

    def convert(self, pre):
        return self._txtConverter.childHandler(pre)

#################################################################################
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
'''
    class OListHandler

    Object that converts ordered list tags to text- serves as a base class for
    the UListHandler as well

'''
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

#################################################################################
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
class Html2Markdown:

    _inlinetags = ['code', 'em', 'strong', 'br', 'strike', 'img', 'a']
    _blocktags = ['p', 'blockquote', 'li', 'ul', 'ol', 'pre']

    def __init__(self):
        self._taghandlers = []
        self._taghandlers.append(PHandler(self))
        self._taghandlers.append(BlockQuoteHandler(self))
        self._taghandlers.append(UListHandler(self))
        self._taghandlers.append(OListHandler(self))
        self._taghandlers.append(PreHandler(self))
        self._taghandlers.append(CodeBlockHandler(self))
        self._taghandlers.append(AHandler(self))
        self._taghandlers.append(InlineCodeHandler(self))
        self._taghandlers.append(EmHandler(self))
        self._taghandlers.append(StrongHandler(self))
        self._taghandlers.append(BrHandler(self))
        self._taghandlers.append(StrikeHandler(self))
        self._taghandlers.append(ImgHandler(self))

        self.listlevel = -1
        self._blocklist = []
        self._reflinks = 0
        self._links = []

    def convert(self, html):
        try:
            nhtml = str(unicodedata.normalize('NFKD', html))
        except TypeError:
            nhtml = html
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
            text = self._tagHandler(element)
            if text:
                if self._isblock(element):
                    self._blocklist.append(text.rstrip() + '\n')
                else:
                    # some kind of inline tag so we'll for now we'll just append
                    # to the previous block
                    self._blocklist[-1] = self._blocklist[-1].rstrip() + \
                                         ' ' + text.rstrip() + '\n'

        # now add any referenced links as the final block
        if len(self._links):
            self._blocklist.append(self._refLinkText())
        return '\n'.join(self._blocklist)

    def childHandler(self, element):
        text = ''
        if len(element) != 0:
            for child in element:
#                print "Child: %s" % child.tag
                text += self._tagHandler(child)
        return text

    def checkTail(self, element):
        if element.tail and not element.tail.isspace():
#            print "TAIL: %s" % element.tag
            return element.tail.lstrip('\n')
        else:
            return ''

    def prepend(self, text, pretext):
#        print text
        rtext = ''
        for line in text.splitlines():
            rtext += "%s%s\n" % (pretext, line)

        return rtext

    def _tagHandler(self, element):
        ''' 
            Scans the `_taghandlers` list for a handler of the element type
            based on the element's tag.  Calls the `convert` method of the
            handler object.
            If no handler is found, then perform a simple check to see if the
            element is a 'comment'
            Otherwise return the tag as a string
        '''
        for handler in self._taghandlers:
            if handler.test(element):
                text = handler.convert(element)
                break
        else:
            if element.text and element.text.find('more') != -1:
                text = "### MORE ###\n\n"
            else:
                return etree.tostring(element)

        return text + self.checkTail(element)

    def _refLinkText(self):
        text = ''
        for ref in self._links:
            text += "[%s]: %s" % (ref[0], ref[1])
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
        # we need to pick up comments- they are to be treated as block tags
        if e.tag not in self._inlinetags:
            return True

        return False

################################################################################
def convert(html):
    md = Html2Markdown()
 
    return md.convert(html)
