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

    ############################################################################
    """_getter

        Returns a closure of a function designed to return a public attribute
        value.  The closure is made based on the attribute name, which will be
        returned from either a properly interpreted internal dict called
        ``_data`` or will be returned from an internl version of the attribute
        which has an identical name prepended with an ``_`` character.

        It is meant to be used to on attributes decorated with the ``property``
        decorator so the attributes don't look like methods to the caller.

        ``attr``:: name of the attribute to close the ``_get`` function over.
                   This is the public name of the attribute.

        ``returns``: closure of ``_get`` function.
    """
    @staticmethod
    def _getter(attr):
        def _get(self):
            def native():
                return getattr(self, "_%s" % attr)
            def wp():
                return self._data[self._wp_map[attr]]
            def metaweblog():
                return self._data[self._metaweblog_map[attr]]

            return { 'native'     : native,
                     'wp'         : wp,
                     'metaweblog' : metaweblog, }[self._type]()

        return _get

    ############################################################################ 
    """_setter

        Creates a closure of a function designed to set an internal attribute
        value that maps to a public value.  **Only** internal attribute setting
        is supported.  If the object is not of type ``native`` then a
        ``ValueError`` exception is raised when trying to set a value.

        ``attr``:: name of attribute to set.  Note that an internal version of
                   this name will be created.  The actual name of the attribute
                   is a method disguised as an attribute by the property
                   decorator.

        ``returns``:: closure of ``_set`` function over the attribute name
    """
    @staticmethod
    def _setter(attr):
        def _set(self, value):
            if self._type != 'native':
                raise ValueError
            setattr(self, "_%s" % attr, value)
        return _set

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
    """id
    """
    @property
    def id(self):
        return self._getter('id')(self)

    @id.setter
    def id(self, value):
        self._setter('id')(self, value)
 
    ############################################################################
    """title
    """
    @property
    def title(self):
        return self._getter('title')(self)

    @title.setter
    def title(self, value):
        self._setter('title')(self, value)
 
    ############################################################################
    """dategmt
    """
    @property
    def dategmt(self):
        return self._getter('dategmt')(self)

    @dategmt.setter
    def dategmt(self, value):
        self._setter('dategmt')(self, self._convertTime(value))
 
    ############################################################################
    """status
    """
    @property
    def status(self):
        return self._getter('status')(self)

    @status.setter
    def status(self, value):
        self._setter('status')(self, value)

    ############################################################################
    """posttype
    """
    @property
    def posttype(self):
        return self._getter('posttype')(self)

    @posttype.setter
    def posttype(self, value):
        self._setter('posttype')(self, value)

    ############################################################################
    """author
    """
    @property
    def author(self):
        return self._getter('author')(self)

    @author.setter
    def author(self, value):
        self._setter('author')(self, value)

    ############################################################################
    """excerpt
    """
    @property
    def excerpt(self):
        return self._getter('excerpt')(self)

    @excerpt.setter
    def excerpt(self, value):
        self._setter('excerpt')(self, value)

    ############################################################################
    """comments
    """
    @property
    def comments(self):
        return self._getter('comments')(self)

    @comments.setter
    def comments(self, value):
        self._setter('comments')(self, value)

    ############################################################################
    """ping
    """
    @property
    def ping(self):
        return self._getter('ping')(self)

    @ping.setter
    def ping(self, value):
        self._setter('ping')(self, value)

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

    @content.setter
    def content(self, value):
        self._setter('content')(self, value)

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
        
    @categories.setter
    def categories(self, value):
        self._setter('categories')(self, value)

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
 
    @tags.setter
    def tags(self, value):
        self._setter('tags')(self, value)
