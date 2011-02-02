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
class Html2Markdown:
    def __init__(self):

        # the blocklist is what will be returned as a joined string
        self._blocklist = []
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
                                     ('img', self._img),
                                    ]
                                   )

    def convert(self, html):
        events = ('start', 'end', 'comment')
        try:
            nhtml = str(unicodedata.normalize('NFKD', html))
        except TypeError:
            nhtml = html
#        print nhtml
        self._htmlIter = etree.iterparse(StringIO("<post>%s</post>" % nhtml),
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
            if event == 'end':
                self._tagstack.pop()
            if len(self._tagstack) != 0:
                continue

#            print "TAG: %s" % e.tag
#            print "TEXT: %s" % e.text
#            print "Attrib: %s" % e.attrib
#            print "TAIL: %s" % e.tail
#            print etree.tostring(e)

       
            # the 'page break' in a post is a comment- <!--more-->
            # catch that here if it exists
            if event == 'comment':
                self._blocklist.append('<!--more-->\n')
                # of course, comment's can have tails as well...
                tail = self._checktail(e)
                if tail:
                    self._blocklist.append(tail.lstrip().rstrip() + '\n')
            # back to the first level, start processing with the current 
            # block tag
            elif e.tag in self._blockHandlers:
                text = self._blockHandlers[e.tag](e, '')
                # text can possibly return with multiple appended '\n'
                # we can safely fix that here by stripping and appending a 
                # single '\n'- the join below will add the second one to the 
                # final text
                self._blocklist.append(text.rstrip() + '\n')
                e.clear() # don't need this anymore
            elif e.tag in self._inlineHandlers:
                text = self._inlineHandlers[e.tag](e)
                # what to do with text?  Since it's an inline, chances are it
                # needs to be appended to the text in the last entry in the
                # _blocklist...
                last = self._blocklist[-1]
                last = last.rstrip() + ' ' + text.rstrip() + '\n'
                self._blocklist[-1] = last

            # see if we created any links, if so add them now
            if len(self._links):
                self._blocklist.append(self._reflinkText())

        return '\n'.join(self._blocklist)

    def _p(self, p, text):
        # return all text contained in p-tag and it's subelements
        if p.text and not p.text.isspace():
            if text and not text.endswith('\n'):
                text += '\n'
            text += p.text

        # luckily, p-tags cannot be nested.  As a matter of fact, no other
        # block-tags can be nested in p-tags
        # now process subelements of p
        if len(p):
            # 'post' tags use the same handler and the CAN have block
            # elements...
            if p.tag == 'post':
                # this is all the text at the beginning of the post
                # we need to append a '\n' to make sure it is separated from
                # it's children.  Normally, the p tag processing would tak
                # care of this, but we can't rely on that here because all the
                # text that's normally in p tags is here in post.
                text = self._processChildren(p, text + '\n')
            else:
                for se in p:
                    if se.tag in self._inlineHandlers:
                        text += self._inlineHandlers[se.tag](se)
                    elif se.text.find('--more--') != -1:
                        if text: 
                            text = text.rstrip() + '\n\n'
                        text += "<!--more-->\n\n"
                    else:
                        print "Error:"
                        print etree.tostring(se)
                        print se.tag
                        sys.exit()

        # return text with any tail
        tail = self._checktail(p)
        if tail:
            return text.rstrip() + '\n\n' + tail.lstrip().rstrip() + '\n'
        else:
            return text.rstrip() + '\n'

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
        # if this blockquote is a child of the 'post' tag, then the only
        # way to pick up other text that belongs at the 'post' level is to
        # check this tags tail
        tail = self._checktail(bq)
        if tail:
            tail = '\n' + tail.lstrip()

        # return text with a '> ' prepended to each line
        # we only want to prepend to the text associated with this bq, text
        # passed in here from previous operations should not be prepended
        return text + self._prepend(bq_text, '> ') + tail

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

        # this loop handles 1 item in a list.  It will iterate multiple times
        # for linebreaks and multiple paragraphs
        for line in li_text.splitlines(1):
            if li_pre:
                text += "%s%s%s" % (' '*4*li_level, li_pre, line)
                li_pre = ''
            elif not line.isspace():
                text += "%s%s" % (' '*4*(li_level + 1), line)
            else:
                # most likely a linefeed...
                text += line

        return text

    def _pre(self, pre, text):
        return self._processChildren(pre, text)

    def _img(self, img):
        # processes img tag if it's on it's own
        attrib_str = ''
        for a in img.attrib.keys():
            if a not in ['alt', 'title', 'src']:
                attrib_str = "%s{@%s=%s}" % (attrib_str, a, img.attrib[a])
        if 'title' not in img.attrib.keys():
            img.set('title', '')
        img_text = "![%s%s](%s %s)" % (img.attrib['alt'], 
                                       attrib_str,
                                       img.attrib['src'],
                                       img.attrib['title'])
        return img_text
#        return "%s\n" % etree.tostring(img)
           
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
        return '  \n' + self._checktail(br)

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
            if child.tag in self._inlineHandlers and \
               child.getparent().tag != 'pre':
                text += self._inlineHandlers[child.tag](child)
            elif child.text and child.text.find('--more--') != -1:
                text = text.rstrip() + "\n\n<!--more-->\n\n"
            elif child.tag in self._blockHandlers:
                # when switching from inline tags to block tags, add
                # a linefeed
                if text and not text.endswith('\n'):
                    text += '\n'
                text = self._blockHandlers[child.tag](child, text)
                if child.tag == 'p':
                    text = text.rstrip() + '\n\n'
            else: # PITFALL!!! for now, catches a 'comment'
                text = text.rstrip() + "\n\n<!--more-->\n\n"
                tail = self._checktail(child)
                if tail:
                    text = text + tail.lstrip().rstrip() + '\n'

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
    md = Html2Markdown()
 
    return md.convert(html)
