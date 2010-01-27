import re
import types

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
class btOperatorError(btParseError):
    def __init__(self, operator):
        self.message = "Invalid header operator: %s" % operator
    def __str__(self):
        return self.message

################################################################################
#
#
class btListError(btParseError):
    def __init__(self, string):
        self.message = "List error: %s" % string
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
class bt_config():
    __hdr_keyword = re.compile('([A-Z]+)\s*([:|{|\[])\s*(.*)', re.DOTALL)
    __hdr_value = re.compile('([^\n]+)\s*([A-Z]+.*|\}.*|$)', re.DOTALL)
    __hdr_list = re.compile('([^\]]+)\s*\]\s*(.*)', re.DOTALL)
    __hdr_group_term = re.compile('\s*[}]\s*(.*)', re.DOTALL)
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
        self.__hdr_operator = { '{' : self.__parseGroup,
                                '[' : self.__parseList,
                                ':' : self.__parseValue, }
#       self.__ast = {}

    def parse(self, parsestring):
        # turn the string into an astract syntax tree which we will then
        # turn into a config object
        ast = {}
        while parsestring:
            (keyword, val, parsestring) = self.__parseKeyword(parsestring)

            # build AST using keyword/ value pairs
            if keyword not in ast:
                ast[keyword] = []
            if keyword == 'CATEGORIES' or keyword == 'TAGS':
                ast[keyword].append(val)
            elif type(val) == types.ListType:
                ast[keyword].extend(val)
            else:
                ast[keyword].append(val)

        # determine how many configs we need by finding the length of the 
        # longest list in the AST
        numconfigs = max(map(lambda x: len(ast[x]), ast.keys()))
        postconfig = [ btPostSettings() for x in range(numconfigs) ]

        # now walk the tree to build the object
        # start by looking for the BLOG entry- process if it's a group
        if 'BLOG' in ast and \
           type(ast['BLOG'][0]) == types.DictType:
            for blog, config in zip(ast['BLOG'], postconfig):
                # in a blog group, we'll assume there are no lists
                # anywhere we aren't expecting them
                for k,v in blog.iteritems():
                    k = k.lower()
                    if k == 'categories' or k == 'tags':
                        if type(v) != types.ListType:
                            v = [v]
                    config.set(k, v)
            del ast['BLOG']

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

    def __parseKeyword(self, string):
        m = self.__hdr_keyword.match(string)
        if m == None:
            raise btNoKeyword(string)
        
        (keyword, operator, string) = m.group(1, 2, 3)
        if keyword not in self.__hdr_keywords:
            raise btKeywordError(keyword)

        if operator not in self.__hdr_operator:
            raise btOperatorError(operator)

        val, string = self.__hdr_operator[operator](string)

        return keyword, val, string

    def __parseGroup(self, string):
        d = {}

        while 1:
            # check if we've reached the end of the group
            m = self.__hdr_group_term.match(string)
            if m == None:
                # continue processing within current group
                (keyword, val, string) = self.__parseKeyword(string)
                d[keyword] = val
            else:
                break
        
        return (d, m.group(1))

    def __parseList(self, string):
        m = self.__hdr_list.match(string)
        if m == None:
            raise btListError(string)

        list = re.split('\s*,\s*', m.group(1).rstrip())
        return (list, m.group(2))

    def __parseValue(self, string):
        m = self.__hdr_value.match(string)
        if m == None:
            raise btValueError(string)
        
        return m.group(1).rstrip(), m.group(2)
 
