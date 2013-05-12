"""data.py
   author: Gerry LaMontagne
   date: 04/23/2013

    Contains data structures to insulate the application code from the details
    of the various data structures used by the XMLRPC methods.
"""
from xmlrpclib import DateTime
import time

################################################################################
"""DataError

    Class for data exceptions
"""
class DataError(Exception):
    
    def __init__(self, errmsg):
        self._message = "DataError Exception:  %s" % errmsg

    def __str__(self):
        return self.message

################################################################################
"""Post

    An kind of container class for post structures.  It serves to provide a
    consistent interface between the application and the actual data.

    Can be called with no initialization parms, in which case it returns an
    empty object, otherwise it contains the data structure which will be
    accessible through instance attributes.

    Objects that are initialized as non-native types are essentially read-only.
    The native type objects can hae their attibutes modified.
"""
class Post(object):

    _supported_types = ('native', 'wp', 'metaweblog')
    _wp_map = { 'id'         : 'post_id',
                'title'      : 'post_title',
                'dategmt'    : 'post_date_gmt',
                'status'     : 'post_status',
                'posttype'   : 'post_type',
                'author'     : 'post_author',
                'excerpt'    : 'post_excerpt',
                'comments'   : 'comment_status',
                'ping'       : 'ping_status',
                'content'    : 'post_content', }

    _metaweblog_map = { 'id'         : 'postid',
                        'title'      : 'title',
                        'dategmt'    : 'date_created_gmt',
                        'status'     : 'post_status',
                        'posttype'   : 'post_type',
                        'author'     : 'wp_author_id',
                        'excerpt'    : 'mt_excerpt',
                        'comments'   : 'mt_allow_comments',
                        'ping'       : 'mt_allow_pings',
                        'content'    : 'description',
                        'publish'    : 'publish',
                        'categories' : 'categories',
                        'tags'       : 'mt_keywords', }

    def __init__(self, data = None, type = 'native'):
        if data != None:
            if type not in self._supported_types:
                raise DataError("Post object type '%s' not supported." % type)
        self._data = data
        self._type = type

    def __getattr__(self, name):
        if name in ['id', 'title', 'dategmt', 'status', 'posttype', 'author',
                    'excerpt', 'comments', 'ping', ]:
            def native(n):
                return getattr(self, "_%s" % n)
            def wp(n):
                return self._data[self._wp_map[n]]
            def metaweblog(n):
                return self._data[self._metaweblog_map[n]]

            return { 'native'     : native,
                     'wp'         : wp,
                     'metaweblog' : metaweblog, }[self._type](name)
        else:
            raise AttributeError

    ############################################################################
    """__setattr__

        What's convenient here is that __setattr__ is _always_ called when
        setting an attribute, as opposed to __getattr__ above which is only
        called if the attribute isn't found by normal means.
    """
    def __setattr__(self, name, value):
        if name in ['id', 'title', 'status', 'posttype', 'author', 'excerpt',
                    'comments', 'ping', 'content', 'categories', 'tags' ]:
            if self._type != 'native':
                raise ValueError
            object.__setattr__(self, "_%s" % name, value)
        elif name is 'dategmt':
            object.__setattr__(self, 
                                    "_%s" % name,
                                    self._convertTime(value))
        else:
            object.__setattr__(self, name, value)

    ################################################################################
    """_convertTime

        method that attempts to convert a date time string to a datetime object
        in UTC time.  Defaults to assuming string is a local time representation.

        It's a staticmethod because it doesn't affect a `Post` instance, ie it
        has no side-effects.  This means it can also be called directly from the
        class.

       ``timestr``:: a string object that specifies a time like 
                     "8:00AM 12/31/2002"

       ``returns``:: an XMLRPC DateTime object for the time string.
                     Raises ``DataError`` if unable to convert ``timestr``
    """
    @staticmethod
    def _convertTime(timestr):
        # List of formats to attempt to match up.
        time_fmts = [
                      "%Y%m%dT%H:%M",        #YYYYMMDDThh:mm
                      "%Y%m%dT%I:%M%p",      #YYYYMMDDThh:mmAM/PM
                      "%Y%m%dT%H:%M:%S",     #YYYYMMDDThh:mm:ss
                      "%Y%m%dT%I:%M:%S%p",   #YYYYMMDDThh:mm:ssAM/PM
                      "%b %d, %Y %H:%M",     #Month Day, Year hour:min
                      "%b %d, %Y %I:%M%p",   #Month Day, Year hour:min AM/PM
                      "%m/%d/%Y %H:%M",      #MM/DD/YYYY hh:mm
                      "%m/%d/%Y %I:%M%p",    #MM/DD/YYYY hh:mmAM/PM
                      "%H:%M %m/%d/%Y",      #hh:mm MM/DD/YYYY
                      "%I:%M%p %m/%d/%Y",    #hh:mmAM/PM MM/DD/YYYY
                    ]

        # the timestamp is provided as "local time" so we need to convert it to
        # UTC time- do this by converting timestamp to seconds from epoch, then
        # to UTC time.  Finally, pass it to xmlrpclib for formatting
        for tf in time_fmts:
            try:
                timeStruct = time.strptime(timestr, tf)
                utctime = time.gmtime(time.mktime(timeStruct))
                posttime = time.strftime("%Y%m%dT%H:%M:%SZ", utctime)

                # the following merely makes the string into a xmlrpc datetime
                # object
                return DateTime(posttime)

            except ValueError:
                continue
        else:
            # the time format could not be parsed properly
            raise DataError("Unable to parse timestring: %s" % timestamp)

    ############################################################################
    """ Beginning of public API... """

    ############################################################################
    """metaweblogStruct

        Returns a metaweblog post structure suitable for use with the metaWeblog
        XMLRPC methods.  It is implemented as a property.  It raises a DataError
        if the object is not of type ``native``- we aren't trying to convert
        between different post structure types.
    """
    @property
    def metaweblogStruct(self):
        if self._type != 'native':
            raise DataError("Can't build metaweblog post structure, post object not 'native'.")
        post = { v: getattr(self, k) for k,v in self._metaweblog_map.iteritems()
                                     if hasattr(self,k) }
        return post

    ############################################################################
    """wpStruct

        Returns a Wordpress post structure suitable for use with the Wordpress
        XMLRPC methods.  It is implemented as a property.  A ``DataError`` is
        raised if the object is not of type ``native``.
    """
    @property
    def wpStruct(self):
        if self._type != 'native':
            raise DataError("Can't build Wordpress post structure, post object not 'native'.")
        post = { v: getattr(self, k) for k,v in self._wp_map.iteritems() 
                                     if hasattr(self,k) }
        post['terms_names'] = { 'category' : self._categories }
        if len(self._tags) != 0:
            post['terms_names']['post_tag'] = self._tags
        return post
        
    ############################################################################
    """publish
    """
    @property
    def publish(self):
        def native():
            return self._publish
        def wp():
            if self._data['post_status'] == 'publish':
                return 1
            else:
                return 0
        def metaweblog():
            return self._data['publish']
        
        return { 'native'     : native,
                 'wp'         : wp,
                 'metaweblog' : metaweblog, }[self._type]()

    @publish.setter
    def publish(self, value):
        def native(v):
            self._publish = v
        def wp(v):
            if v == 1:
                self._data['post_status'] = 'publish'
            else:
                self._data['post_status'] = 'draft'
        def metaweblog(v):
            self._data['publish'] = v

        { 'native'     : native,
          'wp'         : wp,
          'metaweblog' : metaweblog, }[self._type](value)

    ############################################################################
    """content
    """
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

        return { 'native'     : native,
                 'wp'         : wp,
                 'metaweblog' : metaweblog, }[self._type]()

    ############################################################################
    """categories
    """
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

        return { 'native'     : native,
                 'wp'         : wp, 
                 'metaweblog' : metaweblog, }[self._type]()

    ############################################################################
    """tags
    """
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

        return { 'native'     : native,
                 'wp'         : wp,
                 'metaweblog' : metaweblog, }[self._type]()
 
