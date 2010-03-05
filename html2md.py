#!/usr/bin/python

from StringIO import StringIO

try:
    from lxml import etree
    LXML_PRESENT = True

except ImportError:
    LXML_PRESENT = False

#################################################################################
class html2md:
    def __init__(self):

        self.out = ''
        self._tags = []  # holds nested tags- not the same as the last
                         # processed tag since tags are removed from the list
                         # when the end of the tag is reached
        self._start_tags = [] # tracks all opened tags
        self._last_processed = None  # last tag that was close- basically the
                                     # previous top of _tags stack
        self.bq = ''
        self.ol_tag = 1
        self.reflinks = 0
        self.links = []
        self.start_handlers = dict(
                                   [
                                    ('a', self.a_start),
                                    ('p', self.p_start),
                                    ('blockquote', self.bq_start),
                                    ('code', self.code_start),
                                    ('em', self.em_start),
                                    ('strong', self.strong_start),
                                    ('li', self.li_start),
                                    ('ul', self.ul_start),
                                    ('ol', self.ol_start)
                                   ]
                                  )
        self.end_handlers = dict (
                                  [
                                   ('a', self.a_end),
                                   ('p', self.p_end),
                                   ('blockquote', self.bq_end),
                                   ('li', self.li_end),
                                   ('ul', self.ul_end),
                                   ('ol', self.ol_end)
                                  ] 
                                 )

    def convert(self, html):
        events = ('start', 'end')
        for action, e in etree.iterparse(StringIO("<post>%s</post>" % html),
                                         events = events):
            if action == 'start':
                self._tag_enter(e.tag)
                if e.tag in self.start_handlers.keys():
                    self.start_handlers[e.tag](e)
                else:
                    self.generic_start_handler(e)
            
            if action == 'end':
                if e.tag in self.end_handlers.keys():
                    self.end_handlers[e.tag](e)
                else:
                    self.generic_end_handler(e)

                self._tag_exit(e.tag)

        return self.out
 
    def _outAppend(self, s):
        # if we're in a blockquote, then prepend the '> '
        if 'blockquote' in self._tags:
            self.out += self.bq

        # make sure that there is text- if the tag starts with, say, a link
        # then text will be None
        if s:
            self.out += s

    def generic_start_handler(self, e):
        if e.text:
            self.out += (e.text.lstrip()).rstrip('\n')

    def generic_end_handler(self, e):
        pass

    def p_start(self, p):
        # if the p-tag occurs within a list, then remove the 
        # trailing '\n' because it will get added on by the p-tag
        # processing
        if self._last_tag() == 'li':
            if self._start_tags[-2] == 'p':
                self.out += '    '
            else:
                self.out = self.out[:-1]

        self._outAppend(p.text)

    def p_end(self, p):
        if len(self.links) != 0:
            self._outAppend("\n\n%s" % self.reflinkText())
        
        self.out += '\n'
        self._outAppend('\n')

    def bq_start(self, bqe):
        self.bq += '> '

    def bq_end(self, bqe):
        self.bq = self.bq[2:]
        self.out = self.out[:-4]
        
        self.out += '\n'
        if not self.bq:
            self.out += '\n'

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
        last_tag = self._last_tag()
        if last_tag == 'ul':
            self._outAppend('* %s' % li.text)
        elif last_tag == 'ol':
            self._outAppend('%s.  %s' % (self.ol_tag, li.text))
            self.ol_tag += 1

    def li_end(self, li):
        # we don't need to advance the line if we are in a list and 
        # processing a p-tag- the p-tag processing will add linefeeds
        if (self._start_tags[-2] not in [ 'ul', 'ol' ] and
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
        if self._start_tags[-1] != 'p':
            self._outAppend('\n')
        self.ol_tag = 1

    def ul_start(self, ul):
        pass

    def ul_end(self, ul):
        if ul.tail and not ul.tail.isspace():
            self._outAppend(ul.tail)
        self._outAppend('\n')

    def convert_inline(self, e, c):
        addspace = False
        if e.text.endswith(' '):
            addspace = True

        text = "%s%s%s" % (c, e.text.rstrip(), c)
        if addspace:
            text += ' '

        text += self._checktail(e)

        return text

    def _checktail(self, element):
        if element.tail and not element.tail.isspace():
            return element.tail
        else:
            return ''

    def reflinkText(self):
        text = ''
        for ref in self.links:
            text += "[%s]: %s" % (ref[0], ref[1])
            if ref[2]:
                text += ''' "%s"''' % (ref[2])
            text += '\n'

        del self.links[:]

        return text.rstrip()

    def _tag_enter(self, t):
        self._tags.append(t)
        self._start_tags.append(t)

    def _tag_exit(self, t):
        if self._current_tag() != t:
            print "Stack Error: %s versus current %s" % (self._current_tag, t)
            print self._tags
            sys.exit()
        else:
            self._last_processed = self._tags.pop()  # remove current tag

    def _current_tag(self):
        ntags = len(self._tags)
        if ntags > 0:
            return self._tags[ntags - 1]
        else:
            return None

    def _last_tag(self):
        ntags = len(self._tags)
        if ntags > 1:
            return self._tags[ntags - 2]
        else:
            return None

    def _last_opened(self):
        return self._start_tags[-2]

################################################################################
#
#
def convert(html):
    md = html2md()
 
    return md.convert(html)
