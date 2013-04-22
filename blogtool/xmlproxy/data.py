"""data.py

    Contains data structures to insulate the application code from the details
    of the various data structures used by the XMLRPC methods.
"""

################################################################################
"""DataErrorException

    Class for data exceptions
"""
class DataTypeError(Exception):
    
    def __init__(self, errmsg):
        self._message = "Post object type '%s' not supported" % errmsg

    def __str__(self):
        return self.message

################################################################################
"""post

    An kind of container class for post structures.  It serves to provide a
    consistent interface between the application and the actual data.

    Can be called with no initialization parms, in which case it returns an
    empty object, otherwise it contains the data structure which will be
    accessible through instance attributes.
"""
class Post(object):

    _supported_types = ('native', 'wp', 'metaweblog')
    _wp_map = { 'id'       : 'post_id',
                'title'    : 'post_title',
                'dategmt'  : 'post_date_gmt',
                'status'   : 'post_status',
                'posttype' : 'post_type',
                'author'   : 'post_author',
                'excerpt'  : 'post_excerpt',
                'comments' : 'comment_status',
                'ping'     : 'ping_status', }

    _metaweblog_map = { 'id'       : 'postid',
                        'title'    : 'title',
                        'dategmt'  : 'date_created_gmt',
                        'status'   : 'post_status',
                        'posttype' : 'post_type',
                        'author'   : 'wp_author_display_name',
                        'excerpt'  : 'mt_excerpt',
                        'comments' : 'mt_allow_comments',
                        'ping'     : 'mt_allow_pings', }

    def __init__(self, data=None, type = 'native'):

        if data != None:
            if type not in self._supported_types:
                raise DataTypeError(type)
            self._data = data
            self._type = type
        else:
            self._type = 'native'

    @staticmethod
    def _getter(attr):
        def _get(self):
            def native():
                return getattr(self, "_%s" % attr)
            def wp():
                return self._data[self._wp_map[attr]]
            def metaweblog():
                return self._data[self._metaweblog_map[attr]]

            _types = { 'native'     : native,
                       'wp'         : wp,
                       'metaweblog' : metaweblog, }
            return _types[self._type]()
        return _get
 
    @staticmethod
    def _setter(attr):
        def _set(self, value):
            def native(v):
                setattr(self, "_%s" % attr, v)
            def wp(v):
                self._data[self._wp_map[attr]] = v
            def metaweblog(v):
                self._data[self._metaweblog_map[attr]] = v
            _types = { 'native'     : native,
                       'wp'         : wp,
                       'metaweblog' : metaweblog, }
            _types[self._type](value)
        return _set

    @staticmethod
    def _nativeonlyset(attr):
        def _set(self, value):
            if self._type != 'native':
                raise ValueError
            setattr(self, "_%s" % attr, value)
        return _set

    @property
    def id(self):
        return self._getter('id')(self)

    @id.setter
    def id(self, value):
        self._setter('id')(self, value)
 
    @property
    def title(self):
        return self._getter('title')(self)

    @title.setter
    def title(self, value):
        self._setter('title')(self, value)
 
    @property
    def dategmt(self):
        return self._getter('dategmt')(self)

    @dategmt.setter
    def dategmt(self, value):
        self._setter('dategmt')(self, value)
 
    @property
    def status(self):
        return self._getter('status')(self)

    @status.setter
    def status(self, value):
        self._setter('status')(self, value)

    @property
    def posttype(self):
        return self._getter('posttype')(self)

    @posttype.setter
    def posttype(self, value):
        self._setter('posttype')(self, value)

    @property
    def author(self):
        return self._getter('author')(self)

    @author.setter
    def author(self, value):
        self._setter('author')(self, value)

    @property
    def excerpt(self):
        return self._getter('excerpt')(self)

    @excerpt.setter
    def excerpt(self, value):
        self._setter('excerpt')(self, value)

    @property
    def comments(self):
        return self._getter('comments')(self)

    @comments.setter
    def comments(self, value):
        self._setter('comments')(self, value)

    @property
    def ping(self):
        return self._getter('ping')(self)

    @ping.setter
    def ping(self, value):
        self._setter('ping')(self, value)

    @property
    def content(self):
        def native():
            return self._content

        def wp():
            return self._data['post_content']

        def metaweblog():
            if self._data['mt_text_more']:
                if self._data['wp_more_text']:
                    more = "more %s" % self._data['wp_more_text']
                else:
                    more = "more"
                return "%s<!--%s-->%s" % (self._data['description'],
                                          more,
                                          self._data['mt_text_more'])
            else:
                return self._data['description']

        _type = { 'native'     : native,
                  'wp'         : wp,
                  'metaweblog' : metaweblog, }
        return _type[self._type]()

    @content.setter
    def content(self, value):
        def native(v):
            self._content = v

        def wp(v):
            self._data['post_content'] = v

        def metaweblog(v):
            self._data['description'] = v
            self._data['mt_text_more'] = ''
            
        _types = { 'native'     : native,
                   'wp'         : wp,
                   'metaweblog' : metaweblog, }
        _types[self._type](value)

    @property
    def categories(self):
        def native():
            return self._categories

        def wp():
            cats = []
            for term in self._data['terms']:
                if term['taxonomy'] == 'category':
                    cats.append(term['name'])
            return cats

        def metaweblog():
            return self._data['categories']

        _types = { 'native'     : native,
                   'wp'         : wp, 
                   'metaweblog' : metaweblog, }
        return _types[self._type]()
        
    @categories.setter
    def categories(self, value):
        self._nativeonlyset('categories')(self, value)

    @property
    def tags(self):
        def native():
            return self._tags

        def wp():
            tags = ''
            for term in self._data['terms']:
                if term['taxonomy'] == 'post_tag':
                    if tags != '':
                        tags += ', '
                    tags += term['name']
            return tags

        def metaweblog():
            return self._data['mt_keywords']

        _types = { 'native'     : native,
                   'wp'         : wp,
                   'metaweblog' : metaweblog, }
        return _types[self._type]()
 
    @tags.setter
    def tags(self, value):
        self._nativeonlyset('tags')(self, value)
