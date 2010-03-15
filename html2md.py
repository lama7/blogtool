#!/usr/bin/python

import sys
import re

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
        self._block = ''    # for handling elements that can be nested
        self._reflinks = 0
        self._links = []
        self._tagstack = []
        self._listchars = []
        self._listblock= []
        self._blockHandlers = dict(
                                   [
                                    ('p', self._p),
                                    ('blockquote', self._blockquote),
                                    ('li', self._li),
                                    ('ul', self._listCommon),
                                    ('ol', self._listCommon),
                                    ('img', self._img),
                                    ('pre', self._pre),
                                    ('code', self. _codeBlock),
                                    ('post', self._p),
                                   ]
                                  )
        self._inlineHandlers = dict(
                                    [
                                     ('a', self._a),
                                     ('code', self._code),
                                     ('em', self._em),
                                     ('strong', self._strong),
                                     ('br', self._br),
                                    ]
                                   )


    def convert(self, html):
        events = ('start', 'end')
        self._htmlIter = etree.iterparse(StringIO("<post>%s</post>" % html),
                                         events = events)

        for event, e in self._htmlIter:
            if (e.tag == 'post' and 
                (not e.text or e.text.isspace())):
                continue
                
            # we don't need to process start events for everything,
            # just block elements that can nest
            if event == 'start':
                # build stack to track nesting
                self._tagstack.append(e.tag)
                if e.tag == 'ul':
                    self._listchars.insert(0, '*')
                elif e.tag == 'ol':
                    self._listchars.insert(0, 1)
                continue

            # process endtags because everything is available at that point
           
            # determine the nesting level, if we're back to the intial level
            # then we'll go ahead and process
            self._tagstack.pop()
            if len(self._tagstack) != 0:
                continue

            # back to the first level, start processing with the current 
            # block tag
            if e.tag in self._blockHandlers.keys():
                text = self._blockHandlers[e.tag](e, '')
                self._blocklist.append(text)
                e.clear() # don't need this anymore

                # see if we created any links, if so add them now
                if len(self._links):
                    self._blocklist.append(self._reflinkText())

        return '\n'.join(self._blocklist)

    def _p(self, p, text):
        # return all text contained in p-tag and it's subelements
        if p.text and not p.text.isspace():
            if text:
                text += '\n'
            text += p.text

        # luckily, p-tags cannot be nested.  As a matter of fact, no other
        # block-tags can be nested in p-tags
        # now process subelements of p
        if len(p):
            for se in p:
                text += self._inlineHandlers[se.tag](se)

        # if text already has a trailing '\n' then return it, otherwise
        # append a '\n'
        if text.endswith('\n'):
            return text
        else:
            return text + '\n'

    def _blockquote(self, bq, text):
        # we need to accomodate nesting here- but also the simplest case 
        # of just a single line of text
        # There are uses where text can be associated with the blockquotes
        # themselves, as opposed to buried in p-tags and what not
        bq_text = ''
        if bq.text and not bq.text.isspace():
            bq_text = bq.text 

        # now handle all child tags
        if len(bq):
            bq_text = self._processChildren(bq, bq_text)
        # make sure the text string is terminated with a newline
        if bq_text and not bq_text.isspace() and not bq_text.endswith('\n'):
            bq_text += '\n'

        bq_text = bq_text.rstrip() + '\n'
        # return text with a '> ' prepended to each line
        return text + self._prepend(bq_text, '> ')

    def _listCommon(self, listtypetag, text):
        # this is the entry function to process lists
        # the children will be the list items in li-tags
        # for now, we'll assume no text is associated with these tags
        # we'll have to see, but for now I'm assuming that the children
        # are li-tags
        text = self._processChildren(listtypetag, text)
        if not text.endswith('\n'):
            text += '\n'

        # for nested lists, the inner list will complete processing 
        # before outer lists, even though processing STARTS with outer
        # lists, therefore by the time we return to the outer most list
        # the _listchars should be empty but for the last list, so popping
        # should be ok
        self._listchars.pop(-1)

        return text

    def _li(self, li, text):
        # get list prepend character and nesting depth
        if self._listchars[-1] == '*':
            li_pre = '*   '
        else:
            li_pre = '%s.' % self._listchars[-1]
            li_pre += ' '*(4 - len(li_pre))
            self._listchars[-1] += 1
        li_level = self._getnestLevel(li.getparent())

        # be sure to separate list item from previous list item or text
        if text and not text.endswith('\n'):
            text += '\n'

        # now figure out the list text itself
        li_text = ''
        if li.text and not li.text.isspace():
            li_text = li.text

        # two possibilities- the li text has children that need processing
        # or the li is comprised of child elements (perhaps even starting with
        # an inline tag, in which case the text will likely be picked up
        # as a child of the inline tag)
        if len(li):
            li_text = self._processChildren(li, li_text)

        # li_text is set, now we need to 
        for line in li_text.splitlines():
            if li_pre:
                text += "%s%s%s" % (' '*4*li_level, li_pre, line)
                li_pre = ''
            elif not line.isspace():
                text += "%s%s\n" % (' '*4*(li_level + 1), line)

        return text

    def _pre(self, pre, text):
        return self._processChildren(pre, text)

    def _img(self, img, text):
        # processes img tag if it's on it's own
        return "%s\n" % etree.tostring(img)
           
    def _a(self, a):
        # build return string based on anchor tag
        s = ''
        if a.text and not a.text.isspace():
            s = a.text

        # see if there are any subelements
        if len(a):
            for se in a:
                s += self._inlineHandlers[se.tag](se)

        # now that we have all the text, format it in markdown syntax
        s = "[%s][%s]" % (s, self._reflinks)
        
        # save the reflinks
        if 'title' not in a.attrib.keys():
            a.set('title', '')
        self._links.append((self._reflinks, 
                            a.attrib['href'],
                            a.attrib['title']))
        self._reflinks += 1
            
        s += self._checktail(a)

        return s

    def _em(self, em):
        # return emphasis string- in markdown there are no sub elements of
        # em tags
        return self._convertInline(em, '*')

    def _br(self, br):
        return '  \n'

    def _strong(self, strong):
        return self._convertInline(strong, '**')

    def _code(self, code):
        # for handling code tags that occur in p-tags and the like
        return self._convertInline(code, '`')

    def _codeBlock(self, code, text):
        # for handling code tags that occur after pre-tags
        return self._prepend(code.text, '    ')

    def _processChildren(self, e, text):
        for child in e:
            if child in self._inlineHandlers.keys():
                text += self._inlineHandlers[child.tag](child)
            else:
                # when switching from inline tags to block tags, add
                # a linefeed
                if text and not text.endswith('\n'):
                    text += '\n'
                text = self._blockHandlers[child.tag](child, text)
                if child.tag == 'p':
                    text += '\n'

        return text

    def _prepend(self, text, pretext):
        rtext = ''
        for line in text.splitlines():
            rtext += "%s%s\n" % (pretext, line)

        return rtext

    def _convertInline(self, e, c):
        addspace = False
        if e.text.endswith(' '):
            addspace = True

        text = "%s%s%s" % (c, e.text.rstrip(), c)
        if addspace:
            text += ' '

        text += self._checktail(e)

        return text

    def _getnestLevel(self, e):
        # this function determines the amount of nesting for a tag
        nest = 0
        loop_e = e.getparent()
        while loop_e.tag != 'post':
            # naturally, lists are a little trickier
            if ((e.tag in ['ul', 'ol'] and loop_e.tag in ['ul', 'ol']) or
                loop_e.tag == e.tag):
                nest += 1
            loop_e = loop_e.getparent()

        return nest

    def _reflinkText(self):
        text = ''
        for ref in self._links:
            text += "[%s]: %s" % (ref[0], ref[1])
            if ref[2]:
                text += ''' "%s"''' % (ref[2])
            text += '\n'

        del self._links[:]

        return text

    def _checktail(self, element):
        if element.tail and not element.tail.isspace():
            return element.tail
        else:
            return ''

################################################################################
#
#
def convert(html):
    md = html2md()
 
    return md.convert(html)
