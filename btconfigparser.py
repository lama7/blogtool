import re
import types
import sys

''' Start by defining a bunch of exception classes for various parse errors.
Admittedly, this is likely a naive implementaion, but I'm still learning about
this stuff so cut me some slack.
'''

################################################################################
#
#
class btParseError(Exception):
    pass

################################################################################
#
#
class btNoKeyword(btParseError):
    def __init__(self, string):
        self.message = "Expected keyword, found none: %s" % string
    def __str__(self):
        return self.message

################################################################################
#
#
class btKeywordError(btParseError):
    def __init__(self, keyword):
        self.message = "Invalid keyword: %s" % keyword
    def __str__(self):
        return self.message
    
################################################################################
#
#
class btValueError(btParseError):
    def __init__(self, string):
        self.message = "Could not parse keyword value: %s" % string
    def __str__(self):
        return self.message

################################################################################
#
#
class btInterpError(btParseError):
    def __init__(self, key, value):
        self.message = "Value '%s' not valid for key '%s'" % (key, value)
    def __str__(self):
        return self.message

################################################################################
#
#
class btPostSettings():
    def __init__(self):
        
        self.title = ''
        self.username = ''
        self.password = ''
        self.xmlrpc = ''
        self.categories = []
        self.tags = []
        self.name = ''
        self.postid = ''
        self.posttime = ''

    def set(self, attr, val):
        # this is bad form, but until we learn better we'll assume good
        # intentions by the caller
        setattr(self, attr, val)

    def get(self, attr):
        rval = getattr(self, attr)

        if attr == 'categories' or attr == 'tags':
            if len(rval) == 0:
                return None
        elif rval == '':
            return None
            
        return rval

    def debug(self):
        print self.title
        print self.username
        print self.password
        print self.xmlrpc
        print self.categories
        print self.tags
        print self.name
        print self.postid
        print self.posttime

################################################################################
#
#  define a config class- this will hide some ugliness
#
#  This version of the parser uses a different technique to make approach a
#  "truer" parser- that is, the ability to parse a series of lines according
#                  to a set of rules
#
#  The rules for this new version are as follows:
#  -  the largest element I'll call a ASSIGNMENT- consisting of a KEYWORD followed
#     ':', followed by an element
#  -  the parser starts by finding a KEYWORD, which is a capitalized word
#  -  the ':' can be followed by a single ELEMENT or a list of ',' separated
#     ELEMENTs
#  -  ASSIGNMENTs can span multiple lines if comprised of ',' separated
#     ELEMENTs
#  -  an ELEMENT can be a GROUP or a VALUE terminated by a newline or a ','
#  -  a GROUP is a series of SENTENCES related to the original KEYWORD
#     it starts with a '{' and is terminated by a '}'
#  -  a VALUE is a contiguous piece of text terminated by a ',' or a '\n'
#     or a '}'
#  -  multiple groups can be specified using a ',' to separate them
#
class bt_config():
    __hdr_value = re.compile('([^\n,]+)\s*(.*)', re.DOTALL)
    __hdr_group = re.compile('[{]\s*(.*)', re.DOTALL) 
    __hdr_group_term = re.compile('[}]\s*(.*)', re.DOTALL)
    __hdr_comma = re.compile(',\s*(.*)', re.DOTALL)
    __hdr_keyword = re.compile('([A-Z]+)\s*[:]\s*(.*)', re.DOTALL)
    __hdr_keywords = [ 'TITLE',
                       'BLOG',
                       'NAME',
                       'XMLRPC',
                       'CATEGORIES',
                       'POSTID', 
                       'USERNAME',
                       'PASSWORD',
                       'TAGS', 
                       'POSTTIME' ]

    def __init__(self):
        pass

    # the 'parsestring' should be the ENTIRE string to parse, not a piece-meal
    # version of it
    def parse(self, parsestring):
        ast = {}
        # turn the string into an abstract syntax tree which we will then
        # turn into a config object
        while parsestring:
            (keyword, val, parsestring) = self.__parseAssignment(parsestring)
            self.__addAST(ast, keyword, val)

        # determine how many configs we need by finding the length of the 
        # longest list in the AST
        numconfigs = max(map(lambda x: len(ast[x]), ast.keys()))
        postconfig = [ btPostSettings() for x in range(numconfigs) ]

        return self.__interpAST(ast, postconfig)


    # entry point to for parsing- basically, pass in any string to this
    def __parseAssignment(self, parsestring):
        m = self.__hdr_keyword.match(parsestring)
        if m == None:
            raise btNoKeyword(parsestring)

        keyword, parsestring = m.group(1,2)
        if keyword not in self.__hdr_keywords:
            raise btKeywordError(keyword)

        val, parsestring = self.__parseElement(parsestring)

        return keyword, val, parsestring

    # at this point, a 'KEYWORD:' has been parsed
    def __parseElement(self, parsestring):
        # if next character is a '{' then  parse a GROUP
        # otherwise, look for VALUE
        m = self.__hdr_group.match(parsestring)
        if m != None:
            return self.__parseGroup(m.group(1))
        else:
            return self.__parseValue(parsestring)

    # a VALUE is anything up to a newline or a ','
    def __parseValue(self, parsestring):
        m = self.__hdr_value.match(parsestring)
        if m == None:
            raise btValueError(parsestring)
        val, parsestring = m.group(1).rstrip(), m.group(2)

        # if next character is a comma, then we have a list otherwise
        # it's a single value assignment
        return self.__parseComma(val, parsestring)

    # a KEYWORD has been parse followed by a '{', so we need to start
    # parsing assignmens again.
    def __parseGroup(self, parsestring):
        sub_ast = {}

        # first process the group
        m = None
        while m == None:
            # continue processing within current group
            (keyword, val, parsestring) = self.__parseAssignment(parsestring)
            self.__addAST(sub_ast, keyword, val)
            
            # check for end of group
            m = self.__hdr_group_term.match(parsestring)

        # if next character is a comma, then we have a list
        return self.__parseComma(sub_ast, m.group(1))

    # common comma processing
    def __parseComma(self, obj, parsestring):
        m = self.__hdr_comma.match(parsestring)
        if m == None:
            return [obj], parsestring
        else:
            vallist, parsestring = self.__parseElement(m.group(1))
            vallist.insert(0, obj)
            return vallist, parsestring

    # adds a key value pair into the ast as appropriate
    def __addAST(self, ast, keyword, val):
        # build AST using keyword value pairs
        if keyword not in ast:
            ast[keyword] = []

        # determine how to add value into AST
        # in the case of CATEGORIES or TAGS, a list IS the object that
        # is needed, rather than a text string for other case so append
        # the list itself
        if keyword == 'CATEGORIES' or keyword == 'TAGS':
            ast[keyword].append(val)
        else:
            ast[keyword].extend(val)

    # takes an AST and creates config objects from it
    def __interpAST(self, ast, postconfig):
        # start by looking for the BLOG entry- process if it's a group
        # entries under the BLOG keyword define settings specific to 1 config
        # so process BLOG entries in order and build 1 config at a time
        if 'BLOG' in ast: 
            for blog, config in zip(ast['BLOG'], postconfig):
                # make sure it's a dict before proceeding
                if type(blog) != types.DictType:
                    config.set('name', blog)
                    continue

                # in a blog group, we'll assume there are no lists
                # anywhere we aren't expecting them
                for k, v in blog.iteritems():
                    k = k.lower()
                    # within a BLOG group, the only setting that can have more
                    # than 1 value are CATEGORIES and TAGS
                    if len(v) != 1:
                        raise btInterpError(k, v)

                    config.set(k, v.pop())
            del ast['BLOG']

        return self.__interpASTcommon(ast, postconfig)

    # this takes entries that are common to all configs- basically, for each
    # setting, look at each config and if a value isn't already set then set
    # it, otherwise leave it alone
    def __interpASTcommon(self, ast, postconfig):
        # processing is pretty straight forward now- iterate through the AST
        # and fill in the config objects.  
        for k, vallist in ast.iteritems():
            # helper function to assign a value to an attirbute of a config
            # object.  The actual loop is implemented as a list comprehension
            # Done this way for practice- the more verbose form of the 
            # comprehension is the commented out code immediately below the 
            # comprehension- for future reference I'm leaving it this way in
            # case something needs to change
            def assignConfigAttr(attr, val, cf):
                if attr == 'blog':
                    attr = 'name'
                elif type(val) != types.ListType and \
                     (attr == 'categories' or attr == 'tags'):
                    val = [val]
                elif attr == 'postid':
                    if vallist.index(val) == postconfig.index(cf):
                         cf.set(attr, val)
                    return
           
                if cf.get(attr) == None or \
                   vallist.index(val) == postconfig.index(cf):
                    cf.set(attr, val)
                    
            [ assignConfigAttr(k.lower(), x, config) for config in postconfig \
                                                     for x in vallist ]
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

        return postconfig


