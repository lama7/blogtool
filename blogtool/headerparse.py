from xmlproxy import getProxy

import sys
import re
import types
import copy

################################################################################
"""HeaderError

    Error class for header format errors.
"""
class HeaderError(Exception):
    NAMENOTFOUND = 0
    NOCONFIGFILE = 1

    ERR_STRINGS = [
                   '''
Blog name not found in config header or post header.''',
                   '''
A '~/.btrc' file was not found nor was a config file specified on the command
line.  Without a configuration file, the only operation possible is posting.

To perform any optional operations (deleting posts, retrieving recent titles,
etc.) please create a ~/.btrc file.''',
                  ]
    def __init__(self, err_code):
        self.message = "HeaderError: %s" % self.ERR_STRINGS[err_code]
        self.code = err_code

    def __str__(self):
        return self.message

################################################################################
"""HeaderParseError

    Error class for parsing errors.
"""
class HeaderParseError(Exception):
    def __init__(self, msg):
        self.message = "HeaderParseError: %s" % msg

    def __str__(self):
        return self.message

################################################################################
"""HeaderParms

    Essentially a data class for the various header settings.
"""    
class HeaderParms(object):

    _parms = {
                 'title'         : '',
                 'categories'    : [],
                 'tags'          : [],
                 'postid'        : '',
                 'posttime'      : '',
                 'name'          : '',
                 'blogtype'      : '',
                 'xmlrpc'        : '',
                 'username'      : '',
                 'password'      : '',
                 'commentstatus' : '',
                 'commentid'     : '',
                 'parentid'      : '',
                 'author'        : '',
                 'authorurl'     : '',
                 'authoremail'   : '',
                 'excerpt'       : '',
             }

    def __init__(self):
        for a,v in self._parms.iteritems():
            setattr(self, a, v)

    def __str__(self):
        l = ["%s:  %s" % (attr, getattr(self, attr)) for attr, val in self._parms.keys()]
        return '\n'.join(l) + '\n'

    def __contains__(self, item):
        if hasattr(self, item):
            return True
        else:
            return False

    def get(self, name):
        rval = getattr(self, name)
        if rval == '' or (type(rval) == types.ListType and len(rval) == 0):
            return None

        return rval

    @property
    def postMeta(self):
        return (self.title, 
                self.categories,
                self.tags,
                self.postid,
                self.posttime)

    @property
    def commentMeta(self):
        return (self.commentstatus,
                self.commentid,
                self.parentid,
                self.author,
                self.authorurl,
                self.authoremail)

    @property
    def XMLrpc(self):
        return (self.blogtype,
                self.xmlrpc,
                self.username,
                self.password)
    
    @property
    def parmDict(self):
        return { k: getattr(self, k) for k in self._parms.keys() }

################################################################################
"""Keyword
    
    A Container class for keywords useful for storing certain info about
    keyword types.
"""
class Keyword(object):
    def __init__(self, kwtype):
        self.kwtype = kwtype

################################################################################
"""HeaderParse

    Class for parsing header text and creating a HeaderParms object.

"""
class HeaderParse(object):
    __hdr_value = re.compile('([^\n,}]+)\s*(.*)', re.DOTALL)
    __hdr_group = re.compile('[{]\s*(.*)', re.DOTALL) 
    __hdr_group_term = re.compile('[}]\s*(.*)', re.DOTALL)
    __hdr_comma = re.compile(',\s*(.*)', re.DOTALL)
    __hdr_openingquote = re.compile(r'"{3}(.*)', re.DOTALL)
    __hdr_closingquote = re.compile(r'(.*?)"{3}\s+(.*)', re.DOTALL)
    __hdr_keyword = re.compile('([A-Z]+)\s*[:][ \t\f\v]*(.*)', re.DOTALL)

    KTYPE_SINGLEVAL = 0
    KTYPE_MULTIVAL = 1
    KTYPE_GROUP = 2

    def __init__(self):
        self.__kw_tbl = dict(
                             [
                              ( 'TITLE', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'BLOG', Keyword(self.KTYPE_GROUP) ),
                              ( 'NAME', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'XMLRPC', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'CATEGORIES', Keyword(self.KTYPE_MULTIVAL) ),
                              ( 'POSTID',  Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'USERNAME', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'PASSWORD', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'TAGS',  Keyword(self.KTYPE_MULTIVAL) ),
                              ( 'POSTTIME',  Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'BLOGTYPE', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'COMMENTID', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'PARENTID', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'AUTHOR', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'AUTHORURL', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'AUTHOREMAIL', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'COMMENTSTATUS', Keyword(self.KTYPE_SINGLEVAL) ),
                              ( 'EXCERPT', Keyword(self.KTYPE_SINGLEVAL) )
                             ]
                            )

    ############################################################################
    """parse

        The 'parsestring' should be the ENTIRE string to parse, not a piece-meal
        version of it.
    """
    def parse(self, parsestring):
        ast = {}

        # turn the string into an abstract syntax tree which we will then
        # turn into a config object
        while parsestring:
            (keyword, val, parsestring) = self.__parseAssignment(parsestring)
            self.__add2AST(ast, keyword, val)

        # determine how many configs we need by finding the length of the 
        # longest list in the AST
        numconfigs = max(map(lambda x: len(ast[x]), ast.keys()))
        postconfig = [ HeaderParms() for x in range(numconfigs) ]

        return self.__interpAST(ast, postconfig)

    ############################################################################
    """__parseAssignment
       
        Entry point to for parsing- basically, pass in any string to this.
    """
    def __parseAssignment(self, parsestring):
        m = self.__hdr_keyword.match(parsestring)
        if m == None:
            raise HeaderParseError("Expected keyword, found none: %s" %
                                   parsestring)

        keyword, parsestring = m.group(1,2)
        if keyword not in self.__kw_tbl:
            raise HeaderParseError("Invalid keyword: %s" % keyword)

        val, parsestring = self.__parseElement(parsestring)

        return keyword, val, parsestring

    ############################################################################
    """__parseElement

        At this point, a 'KEYWORD:' has been parsed, now continue to parse
        either a value or a group.
    """
    def __parseElement(self, parsestring):
        # if next character is a '{' then  parse a GROUP
        # otherwise, look for VALUE
        m = self.__hdr_group.match(parsestring)
        if m == None:
            # no bracket following keyword, so parse a normal value
            return self.__parseValue(parsestring)

        # an opening brackets starts a group
        return self.__parseGroup(m.group(1))

    ############################################################################
    """__parseValue

       A VALUE is anything up to a newline or a ',' or a string enclosed by
       pythonic triple double-quotes.
    """
    def __parseValue(self, parsestring):
        m = self.__hdr_openingquote.match(parsestring)
        if m != None:
            value, parsestring = self.__parseQuote(m.group(1))
        else:
            m = self.__hdr_value.match(parsestring)
            if m == None:
                raise HeaderParseError( "Could not parse keyword value: %s" %
                                        parsestring)
            value = m.group(1).rstrip()
            parsestring = m.group(2)

        # if next character is a comma, then we have a list otherwise
        # it's a single value assignment
        return self.__parseComma(value, parsestring)

    ############################################################################
    """__parseGroup

        A KEYWORD has been parse followed by a '{', so we need to start
        parsing assignmens again.
    """
    def __parseGroup(self, parsestring):
        sub_ast = {}

        # first process the group
        m = None
        while m == None:
            # continue processing within current group
            (keyword, val, parsestring) = self.__parseAssignment(parsestring)
            self.__add2AST(sub_ast, keyword, val)
            
            # check for end of group
            m = self.__hdr_group_term.match(parsestring)

        # if next character is a comma, then we have a list
        return self.__parseComma(sub_ast, m.group(1))

    ############################################################################
    """__parseQuote

        A '"""' has been parsed, so parse a string up to the closing '"""' and
        return the string and whatever is left of the parsestring.
    """
    def __parseQuote(self, parsestring):
        m = self.__hdr_closingquote.match(parsestring)
        if m == None:
            raise HeaderParseError( "Error in quoted string, no closing quotes: %s" %
                                    parsestring)
        return m.group(1), m.group(2)

    ############################################################################
    """__parseComma
        
        Actually, the name of this is a bit misleading as the comma has already
        been parsed.  The idea here is to build a list and continue parsing
        recursively.
    """
    def __parseComma(self, obj, parsestring):
        m = self.__hdr_comma.match(parsestring)
        if m == None:
            return [obj], parsestring
        else:
            vallist, parsestring = self.__parseElement(m.group(1))
            vallist.insert(0, obj)
            return vallist, parsestring

    ############################################################################
    """__add2AST

        Adds a key value pair into the AST as appropriate.
    """
    def __add2AST(self, ast, keyword, val):
        # first, make sure the value is agreeable with the keyword type
        kwtype = self.__kw_tbl[keyword].kwtype

        # single value keyword are just that- and no groups
        if (kwtype == self.KTYPE_SINGLEVAL and
            (len(val) > 1 or type(val[0]) == types.DictType)):
            raise HeaderParseError("Value '%s' not valid for key '%s'" % 
                                   (val, keyword) )
        # multival can't have any groups in the list
        elif (kwtype == self.KTYPE_MULTIVAL and
              len([ v for v in val if type(v) == types.DictType ]) != 0):
            raise HeaderParseError("Value '%s' not valid for key '%s'" % 
                                   (value, key) )

        # build AST using keyword value pairs
        if keyword not in ast:
            ast[keyword] = []

        # determine how to add value into AST
        # in the case of CATEGORIES or TAGS, a list IS the object that
        # is needed, rather than a text string for other case so append
        # the list itself
        if keyword in ['CATEGORIES', 'TAGS']:
            ast[keyword].append(val)
        else:
            ast[keyword].extend(val)

    ############################################################################
    """__interpAST

        Takes an AST and creates config objects from it.
    """
    def __interpAST(self, ast, postconfig):
        # start by looking for the BLOG entry- process if it's a group
        # entries under the BLOG keyword define settings specific to 1 config
        # so process BLOG entries in order and build 1 config at a time
        if 'BLOG' in ast: 
            for blog, config in zip(ast['BLOG'], postconfig):
                # make sure it's a dict before proceeding
                if type(blog) != types.DictType:
                    setattr(config, 'name', blog)
                    continue

                # in a blog group, we'll assume there are no lists
                # anywhere we aren't expecting them
                for k, v in blog.iteritems():
                    k = k.lower()
                    # within a BLOG group, the only setting that can have more
                    # than 1 value are CATEGORIES and TAGS
                    if len(v) != 1:
                        raise HeaderParseError("Value '%s' not valid for key '%s'" % (v, k) )

                    setattr(config, k, v.pop())
            del ast['BLOG']

        return self.__interpASTcommon(ast, postconfig)

    ############################################################################
    """__interpASTcommon

        This takes entries that are common to all configs- basically, for each
        setting, look at each config and if a value isn't already set then set
        it, otherwise leave it alone.
    """
    def __interpASTcommon(self, ast, postconfig):
        # processing is pretty straight forward now- iterate through the AST
        # and fill in the config objects.  
        for k, vallist in ast.iteritems():

            ###################################################################
            """_assignConfigAttr

                Helper function to assign a value to an attirbute of a config
                object.  The actual loop is implemented as a list comprehension
                Done this way for practice- the more verbose form of the 
                comprehension is the commented out code immediately below the 
                comprehension- for future reference I'm leaving it this way in
                case something needs to change
            """
            def __assignConfigAttr(attr, val, cf):
                if attr == 'blog':
                    attr = 'name'
                elif type(val) != types.ListType and \
                     (attr == 'categories' or attr == 'tags'):
                    val = [val]
                elif attr == 'postid':
                    if vallist.index(val) == postconfig.index(cf):
                        setattr(cf, attr, val)
                    return
           
                if cf.get(attr) == None or \
                   vallist.index(val) == postconfig.index(cf):
                    setattr(cf, attr, val)   
                    
            [ __assignConfigAttr(k.lower(), x, config) for config in postconfig \
                                                       for x in vallist ]
                                                     
#    The above list comprehension is equivalent to the following piece of code:
#
#            for o in v:
#                for config in postconfig:
#                    if k == 'blog':
#                        k = 'name'  # no blog attribute, substitute name for it
#                    elif (k == 'categories' or k == 'tags') and type(o) != types.ListType:
#                        o = [o]  # single value for tags and categories still
#                                 # need to go into a list
#
#                    # if no value is assigned, or if the config group index
#                    # matches the list index for the value, then assign
#                    if config.get(k) == None or v.index(o) == postconfig.index(config):
#                        config.set(k, o)


## For testing purposes:
#        for pc in postconfig:
#            print pc
#        sys.exit()


        return postconfig

################################################################################
"""
    reverseParse
    
    Reverse parses a HeaderParms object making into a parsable string.
"""
class reverseParser(object):
    def _getdefault(self, name):
        if self._default_parms:
            for df in self._default_parms:
                if name == df.name:
                    return df
        return None

    def _isdefault(self, default, k, v):
        if default and k in default and default.get(k) == v:
            return True
        else:
            return False

    def _add2dict(self, d, k, v):
        if k not in d:
            d[k] = list()

        d[k].append(v)

    def _valsequal(self, vallist, val):
        for item in vallist:
            if item != val:
                return False
        else:
            return True

    def _val2string(self, val):
        if isinstance(val, list):
            return ', '.join(val).strip("'")
        else:
            # look for characters special for header indicating need for triple
            # quoted string
            if re.search(r'[,\n{}]', val):
                return '"""%s"""' % val
            else:
                return val
    ###########################################################################
    """_clean
     
        Remove dict entries that have empty lists.
    """
    def _clean(self, d):
        cleaned_keys = []
        for k,v in d.iteritems():
            if self._valsequal(v, None):
                cleaned_keys.append(k)

        for k in cleaned_keys:
            del d[k]

        return d

    def _convertGlobals(self, d):
        removekeys = []
        text = ''
        for k,v in d.iteritems():
            if self._valsequal(v, v[0]): 
                removekeys.append(k)
                if k == 'name':
                    k = 'blog'
                text += "%s: %s\n" % (k.upper(), self._val2string(v[0]))

        for k in removekeys:
            del d[k]

        return text, d

    def _convertGroups(self, d):
        text = ''
        if 'name' in d:
            if len(d) == 1:
                # only blog name in dict, just list them
                text = 'BLOG: ' + ', '.join(d['name']) + '\n'
            else:
                text += 'BLOG:\t'
                blognames = d['name']
                del d['name']
                i = 0
                for name in blognames:
                    text += '{\n\t  NAME: %s\n' % name
                    for k,v in d.iteritems():
                        if v[i]:
                            text += "\t  %s: %s\n" % (k.upper(),
                                                      self._val2string(v[i])) 
                    text += '\t},\n\t'
                    i = i + 1   
        return text.strip(',\n\t')

    ############################################################################
    """toString

       This is the only public function for the reverse parser object.  It takes
       a parameter list dict and default parameter dict and then sets about
       turning them into a valid header string suitable for use in a post file
    """
    def toString(self, parms, defaultparms):
        self._default_parms = defaultparms
        d = {}
        for parml in parms:
            default = self._getdefault(parml.name)
            for k,v in parml.parmDict.iteritems():
                if k == 'name' or (not self._isdefault(default, k, v) and v):
                    val = v
                else:
                    val = None
                self._add2dict(d, k, val)

        hdrtext, d = self._convertGlobals(self._clean(d))
        hdrtext += self._convertGroups(d)
        return hdrtext + '\n'

################################################################################
"""Header

    Container class for dealing with headers.  
    
    This is the public class that a header is accessed through.
"""
class Header(object):
    _parser = HeaderParse()
    _revparser = reverseParser()

    def __init__(self):
        self._default_parms = None
        self._parm_index = None
        self._named_parmlist = None
        self._parms = None

    def __setattr__(self, name, value):
        if hasattr(self, '_parms') and (hasattr(self, '_parm_index') or
                                        hasattr(self, '_named_parmlist')):
            if self._parms:
                if len(self._parms) == 1:
                    pl = self._parms[0]
                elif self._named_parmlist:
                    pl = self._named_parmlist
                elif self._parm_index != None:
                    pl = self._parms[self._parm_index]
                else:
                    pl = self._parms[0]
                # now set the parameter in the parameter list's dict 
                if hasattr(pl, name):
                    setattr(pl, name, value)
                    return

        object.__setattr__(self, name, value)
                
    def __getattr__(self, name):
        if self._parms is None:
            raise HeaderError.NOCONFIGFILE
        elif len(self._parms) == 1:
            pl = self._parms[0]
        elif self._named_parmlist:
            pl = self._named_parmlist
        elif self._parm_index != None:
            pl = self._parms[self._parm_index]    
        else:
            raise AttributeError
        # if the parameter is in the parameter list, return it
        if hasattr(pl, name):
            return getattr(pl, name)
        else:
            raise AttributeError

    def __iter__(self):
        return self

    def __str__(self):
        return self._revparser.toString(self._parms, self._default_parms)

    def next(self):
        if self._parm_index == None:
            self._parm_index = 0
        elif self._parm_index + 1 < len(self._parms):
            self._parm_index += 1
        else:
            self._parm_index = None
            self._proxy = None
            raise StopIteration

        self._setProxy(self._parms[self._parm_index])
        return self

    def _reconcile(self, newparms):
        def _merge(default_parmlist, parmlist):
            for (k, v) in parmlist.parmDict.iteritems():
                if k in ['categories', 'tags']:
                    if len(v) != 0:
                        continue
                elif v:
                    continue

                default = default_parmlist.get(k)
                if default:
                    setattr(parmlist, k, default)

        if self._named_parmlist and len(newparms) == 1:
            _merge(self._named_parmlist, newparms[0])
        else:
            for parmlist in newparms:
                if parmlist.name:
                    for default_parmlist in self._default_parms:
                        if default_parmlist.name == parmlist.name:
                            break
                    else:
                        continue
                else:
                    i = newparms.index(parmlist)
                    if i >= len(self._default_parms):
                        continue
                    default_parmlist = self._default_parms[i]

                _merge(default_parmlist, parmlist)

        if hasattr(self, '_parms'):
            del self._parms[:]
        self._parms = newparms

    def _setProxy(self, pl):
        self._proxy = getProxy(*pl.XMLrpc)
        self._proxy.setBlogname(pl.name)

    @property
    def proxy(self):
        return self._proxy

    def debug(self):
        if self._named_parmlist:
            print "named_parm"
            print self._named_parmlist
        print "_parms:"
        for parm in self._parms:
            print parm

    def setBlogParmsByName(self, name = ''):
        if not self._parms:
            raise HeaderError(HeaderError.NOCONFIGFILE)

        for parm in self._parms:
            if parm.name == name:
                self._named_parmlist = parm
                self._setProxy(self._named_parmlist)
                break
        else:
            raise HeaderError(HeaderError.NAMENOTFOUND)

    def setDefaults(self, hdrstr):
        try:
            self._default_parms = self._parser.parse(hdrstr)
        except HeaderParseError, err:
            print err
            sys.exit()
        self._parms = copy.deepcopy(self._default_parms)

    def addParms(self, hdrstr, allblogs):
        try:
            newparms = self._parser.parse(hdrstr)
        except HeaderParseError, err:
            print err
            sys.exit()

        if self._default_parms:
            if allblogs:
                if len(self._default_parms) > len(newparms):
                    for p in newparms:
                        if p.name:
                            break
                    else:
                        while len(self._default_parms) > len(newparms):
                            newparms.append(copy.deepcopy(newparms[0]))
            self._reconcile(newparms)
        else:
            self._parms = newparms

    def buildPostHeader(self, options):
        def pl2text(pl):
            text = ': \n'.join([attrname.upper() for attrname in pl.parmDict \
                                                   if not pl.get(attrname) and \
                                                      attrname in req_parms])
            if text != '':
                text += ': \n'
            if flags['comment']:
                text += 'POSTID: %s\n' % pl.get('postid')
                parentid = pl.get('parentid')
                if parentid != '0':
                    text += 'PARENTID: %s\n' % parentid
            return text + 'BLOG: %s\n' % pl.get('name')
            

        REQUIRED = ['blog', 'blogtype', 'xmlrpc', 'username', 'password']
        REQUIRED_POST = REQUIRED + ['title', 'categories']
        REQUIRED_COMMENT = REQUIRED + ['postid', 'author']
        flags = options.flags()
        if flags['comment']:
            req_parms = REQUIRED_COMMENT
        else:
            req_parms = REQUIRED_POST

        if not self._parms:
            headertext = ': \n'.join([p.upper() for p in req_parms]) + ': \n'
        elif len(self._parms) == 1:
            headertext = pl2text(self._parms[0])
        elif self._named_parmlist is not None:
            headertext = pl2text(self._named_parmlist)
        #len(self._parms) > 1 and self._named_parmlist is None
        else:
            # mark any unfilled required parms with a known pattern 
            pattern = '!XxXx#'
            parmlist_copy = copy.deepcopy(self._parms)
            for rp in req_parms:
                for pl in parmlist_copy:
                    if rp == 'blog':
                        rp = 'name'
                    if not pl.get(rp):
                        setattr(pl, rp, pattern)
            # now build a header string and replace occurences of pattern
            # with blanks
            if flags['allblogs']:
                headertext = self._revparser.toString(parmlist_copy,
                                      self._default_parms).replace(pattern, '')
            else:
                headertext = self._revparser.toString(parmlist_copy, 
                                                     None).replace(pattern, '')
            del parmlist_copy

        return headertext
