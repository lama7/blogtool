#!/usr/bin/python

import sys

from StringIO import StringIO

try:
    from lxml import etree
    LXML_PRESENT = True

except ImportError:
    LXML_PRESENT = False

#################################################################################
class html2md:
    def __init__(self):

        # the blocklist is what will be returned as a joined string
        self._blocklist = []
        # a block is a contiguous series of lines.  
        self._block = ''
        self._reflinks = 0
        self._links = []
        self._bq = ''
        self._li = []
        self._handlers = dict(
                              [
                               ('a', self._a),
                               ('p', self._p),
                               ('blockquote', self._bq),
                               ('code', self._code),
                               ('em', self._em),
                               ('strong', self._strong),
                               ('li', self._li),
                               ('ul', self._ul),
                               ('ol', self._ol),
                               ('img', self._img),
                               ('post', self._post)
                              ]
                             )

    def convert(self, html):
        events = ('start', 'end')
        self._htmlIter = etree.iterparse(StringIO("<post>%s</post>" % html),
                                         events = events)

        while 1:
            e = self._nextTag()
            if e is None:
                break
            elif e.tag == 'post':
                pass # we'll need to deal with this later.
                     # for now, this should work just fine
            else:
                self.blocklist.append(self._handlers[e.tag](e))
                self._block = ''

        print '\n'.join(self.blocklist)

        sys.exit()

    def _p(self, p):
        # we should only ever enter here on a start tag
        if p.text and not p.text.isspace():
            self._block += p.text

        # we need to worry about inline tags within 'p' tags
        p = self._nextTag()

        # if this is an end-tag, then we're done
        if p.tag == 'p':
            return self._block


            

        



    def bq_start(self, bqe):
        pass

    def bq_end(self, bqe):
        pass

    def a_start(self, a):
        pass

    def a_end(self, a):
        # first, put the text together
        self._outAppend("[%s][%s]" % (a.text, self.reflinks))
        self._outAppend(self._checktail(a))

        # now, save off reflink and link itself
        if 'title' not in a.attrib.keys():
            a.set('title', '')

        self.links.append((self.reflinks, a.attrib['href'], a.attrib['title']))
        self.reflinks += 1

    def code_start(self, code):
        last_tag = self._last_tag()
        if last_tag == 'p':
            self._outAppend(self.convert_inline(code, '`'))
        elif last_tag == 'pre':
            for line in code.text.split('\n'):
                self._outAppend('    %s\n' % line)

    def em_start(self, em):
        # if the text ends with a space, then add it after the *
        self._outAppend(self.convert_inline(em, '*'))

    def strong_start(self, strong):
        self._outAppend(self.convert_inline(strong, '**'))

    def li_start(self, li):
        # determine if this is an ordered or unordered list and prepend 
        # accordingly
        last_tag = self._last_tag()
        if last_tag == 'ul':
            self._outAppend('* %s' % li.text)
        elif last_tag == 'ol':
            self._outAppend('%s.  %s' % (self.ol_tag, li.text))
            self.ol_tag += 1

    def li_end(self, li):
        # we don't need to advance the line if we are in a list and 
        # processing a p-tag- the p-tag processing will add linefeeds
        if (self._start_tagstack[-2] not in [ 'ul', 'ol' ] and
            self._last_processed == 'p'):
            pass
        else:
            # advance line for next list item
            self.out += '\n'

    def ol_start(self, ol):
        pass

    def ol_end(self, ol):
        if ol.tail and not ol.tail.isspace():
            self._outAppend(ol.tail)
        if self._start_tagstack[-1] != 'p':
            self._outAppend('\n')
        self.ol_tag = 1

    def ul_start(self, ul):
        pass

    def ul_end(self, ul):
        if ul.tail and not ul.tail.isspace():
            self._outAppend(ul.tail)
        self._outAppend('\n')

    def img_start(self, img):
        self.out += '\n'
        self._outAppend(etree.tostring(img))

    def img_end(self, img):
        self.out += '\n' 

    def convert_inline(self, e, c):
        addspace = False
        if e.text.endswith(' '):
            addspace = True

        text = "%s%s%s" % (c, e.text.rstrip(), c)
        if addspace:
            text += ' '

        text += self._checktail(e)

        return text

    def reflinkText(self):
        text = ''
        for ref in self.links:
            text += "[%s]: %s" % (ref[0], ref[1])
            if ref[2]:
                text += ''' "%s"''' % (ref[2])
            text += '\n'

        del self.links[:]

        return text.rstrip()

    def _checktail(self, element):
        if element.tail and not element.tail.isspace():
            return element.tail
        else:
            return ''

    def _nextTag(self):
        try:
            (self._act, el) = self._htmlIter.next()
            return el

        except StopIteration:
            return None

################################################################################
#
#
def convert(html):
    md = html2md()
 
    return md.convert(html)
