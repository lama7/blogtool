.. contents:: 

Configuration
=============

In order to post to a blog, blogtool_ needs some basic info about it: location
of the XMLRPC file, a user name and a password to name a few.  At this time,
blogtool_ only supports Wordpress blogs since that's what my blog software is
and therefore what blogtool_ has been tested on.

The basic blog info is provided in a header section of a file via keywords and
values separated by colons.  Dont' worry- there aren't a lot and they're
intuitive with regards to blogging.  Further, it's possible to setup a
configuration file that will default the crucial settings, reducing the amount
of header keywords that are used during normal blogging to 2 or 3.

The keywords are used to form the header, which must precede the post text when
composing a post file.  Once the header is completed, a blank line follows.
Everything thereafter is considered post content or comment content and will be
written as appropriate to a post on the blog::

    TITLE: My First Post with Blogtool
    CATEGORIES: Misc
    TAGS: blogtool, software
    BLOG: The Most Interesting Blog in the World
    XMLRPC: http://myblog.mydomain.org/xmlrpc.php
    USERNAME: fred
    PASSWORD: secret
    BLOGYPE: wp

    Everything preceding this was the header for this post file.  The text you
    are reading now is considered the content.  You can use [markdown][1] syntax
    to add *emphasis* and other text markup features.

      [1]: http://daringfireball.net/projects/markdown

Header Keywords
---------------

Following is a list of blogtool_ header keywords:

+ TITLE_
+ BLOG_
+ NAME_
+ XMLRPC_
+ CATEGORIES_
+ POSTID_
+ USERNAME_
+ PASSWORD_
+ TAGS_
+ POSTTIME_
+ BLOGTYPE_
+ COMMENTSTATUS_
+ COMMENTID_
+ PARENTID_
+ AUTHOR_
+ AUTHORURL_
+ AUTHOREMAIL_

Notice, these are listed in caps.  That's because the keywords should be
capitalized in the header. 

Each keyword should be followed by a ': ' and then an appropriate value, more
on those below.  Each line of the header is terminated with a carriage return,
so don't try to put all the header stuff on a single line.  To terminate the
header, simply create a blank line.  Everything after that blank line is
processed as post text and will be published on the blog.

Keywords may also be given a list of values by using a comma (',') to separate
each value.  Because of this, the comma character *cannot* be used as part of a
keyword value, for instance in the title of a post.

For the purposes of posting, the required keywords are:

+ XMLRPC_
+ NAME_
+ USERNAME_
+ PASSWORD_
+ BLOGTYPE_

Without these, blogtool_ can't push anything up to a weblog.

Keyword Definitions
~~~~~~~~~~~~~~~~~~~

Following are the keywords that blogtool_ supports along with a description of
what they are used for and what an appropriate value is for them.

.. _title:

TITLE  
    Defines the post title that will appear on the blog.  

.. _blog:

BLOG  
    Serves dual purposes.  With a single value it defines the name of the blog
    for posting to.  Again, basically any character can be used, excepting a
    comma.
  
    A comma separated list of blog names can be supplied if it's desired to
    publish to multiple blogs.

    Alternatively, a group can be assigned.  See "Groups" below.

.. _blogtype:

BLOGTYPE  
    Specifies the blog type being posted to.  For now, this is only **wp** for
    Wordpress blogs.

.. _name:

NAME  
    Specifies the actual name of the blog.  If posting to an individual blog,
    then it is synonymous with the 'BLOG' keyword.  If posting to multiple
    blogs, then it should be used inside a group for the 'BLOG' keyword.

.. _xmlrpc:

XMLRPC  
    The location of the xmlrpc file for the blog.

.. _categories:

CATEGORIES  
    The category the post should be filed under on the blog.  If filing under a
    subcategory, then it should be listed as a dotted representation of the
    category.  Example: parentcat.subcat1.subcat2

    Can be a single value or a comma separated list.

.. _postid:

POSTID  
    The ID number of a post.  The presence of this in the header means that the
    post will be updated.

.. _username:

USERNAME  
    The login name for posting to the blog.  The is required to be able to post to
    a weblog.

.. _password:

PASSWORD  
    The password for the USERNAME for gaining access to the weblog.

.. _tags:

TAGS  
    For defining the tags for a post.  Can be a single value or a comma separated
    list.

.. _posttime:

POSTTIME  
    Used to schedule a post.  See section at the end on time strings to see how
    to spell this.

The following keywords are specific to editting and or writing comments:

.. _commentstatus:

COMMENTSTATUS  
    Valid values are **approve**, **hold** and **spam** and are determined by the
    Wordpress blog software.  

.. _commentid:

COMMENTID  
    Every Wordpress comment has a unique ID, like the posts.  The value for this
    can be obtained with the readcomments_ option or by hovering on the
    comment link in a browser.

.. _parentid:

PARENTID  
    The ``COMMENT_ID`` of the comment being replied to.  Typically used when
    writing a comment using the comment_ option.

.. _author:

AUTHOR  
    Specifies the name to be associated with a comment.  When writing a comment
    via the comment_ option, this will default to the username for the blog
    specified, but can be overwritten to anything.

.. _authorurl:

AUTHORURL  
    Specifies the URL for the comment's author's website.  Can be left blank.

.. _authoremail:

AUTHOREMAIL  
    Specifies an email address for the author of the comment.  Can be left
    blank.

Groups
~~~~~~

The header syntax also supports grouping for the BLOG keyword.  Grouping
provides a means to supply information for multiple blogs.  Use the 'NAME'
keyword within a group to specify a blog.

A group consists of a keywords enclosed within brackets.  Groups can be listed
using a comma::

    BLOG: {
            NAME: My Blog
            XMLRPC: http://my.server/xmlrpc.php
            USERNAME: user
            PASSWORD: secret
          },
          {
            NAME: My Other Blog
            XMLRPC: http://myotherblog.server/xmlrpc.php
            USERNAME: user
            PASSWORD: secret
            CATEGORIES: Tedium
          }

Configuration Files
-------------------

To reduce the amount of header typing, it is possible to create a configuration
file for blogtool_ to obtain parameter settings that are used all the time.  The
file *~/.btrc* is automatically looked for when blogtool_ is started.  It is not
an error if it does not exist unless an attempt it made to perform a blog
operation that requires minimal blog configuration info, like deleting a post.
If just trying to post a file, the file can be successfully processed by
providing all the necessary configuration fields.  An alternate configuration
file can be specified on the command line using the `-c`_ option.

A configuration file basically consists of a header.  The most useful purpose is
to supply redundant configuration information like XMLRPC, BLOGTYPE, NAME,
USERNAME and PASSWORD so that each post file does not require this information.
Given a configuration file with these five settings, then it is possible to
construct post files with only two lines in the header- namely the TITLE and
CATEGORIES of the post.

Because of the way a configuration file's settings are reconciled with settings
specified in a post file, it is possible to use the configuration file to define
default settings for a blog, such as the CATEGORIES or TAGS.  Basically, if
these settings are present in a configuration file, but NOT present in the post
file, then the configuration file setting will be used.  Otherwise, post file
settings ALWAYS override configuration file settings.

The configuration file was implemented as a courtesy to the user so as to avoid
the tedium of constantly entering the same values for every post.

.. _blogtool: https://pypi.python.org/pypi/blogtool
.. _readcomments: commandline.html#options
.. _comment: commandline.html#options
.. _-c: commandline.html#options
