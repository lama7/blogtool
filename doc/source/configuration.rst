Configuration
=============

In order to do any of this stuff, blogtool_ needs some basic info about the blog.
Also, as mentioned, it really only supports Wordpress blogs since that's what my
blog software is and therefore what blogtool_ has been tested on.

The basic blog info is provided via keywords and values separated by colons.
Dont' worry- there aren't a lot and they're intuitive with regards to blogging.
Where repetition is concerned, only three would be used on a regular basis for
multiple blogs.  If posting to a single blog, only two keywords are needed with
any regularity.

The keywords form the header.  Once the header is completed, a blank line
follows.  Everything thereafter is considered post text or coment text and will
be written as appropriate to a post on the blog.

Contents:

- `Header Keywords`_
- `Keyword Definitions`_
- `Groups`_
- `Configuration Files`_

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
capitalized in the header.  Each keyword should be followed by a ':' and then an
appropriate value.  More on those below.  Each line of the header is terminated
with a carriage return, so don't try to put all the header stuff on a single
line.  To terminate the header, simply create a blank line.  Everything after
that blank line is processed as post text and will be published on the blog.

Keywords may also be given a list of values by using a comma (',') to separate
each value.  Because of this, the comma character *cannot* be used as part of a
keyword value, for instance in the title of a post.

For the purposes of posting, the required keywords are ``XMLRPC``, ``NAME``,
``USERNAME``, ``PASSWORD``, and ``BLOGTYPE``.  Without these, blogtool_ can't
push anything up to a weblog.

Keyword Definitions
-------------------

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
    Specifies the blog type being posted to.  For now, this is only 'wp' for
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
    can be obtained with the `readcomments`_ option or by hovering on the
    comment link in a browser.

.. _parentid:

PARENTID  
    The ``COMMENT_ID`` of the comment being replied to.  Typically used when
    writing a comment using the `comment`_ option.

.. _author:

AUTHOR  
    Specifies the name to be associated with a comment.  When writing a comment
    via the `comment`_ option, this will default to the username for the blog
    specified, but can be overwritten to anything.

.. _authorurl:

AUTHORURL  
    Specifies the URL for the comment's author's website.  Can be left blank.

.. _authoremail:

AUTHOREMAIL  
    Specifies an email address for the author of the comment.  Can be left
    blank.

Groups
------

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
            USERNAME: user
            PASSWORD: secret
            CATEGORIES: Tedium
          }

Configuration Files
-------------------

To reduce the amount of header typing, it is possible to create a configuration
file for blogtool_ to obtain parameter settings that are used all the time.  The
file '~/.btrc' is automatically looked for when blogtool_ is started.
Alternatively, a configuration file can be specified on the command line using
the `-c`_ option.

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
.. _readcomments: commandline.html#readcomments
.. _comment: commandline.html#comment
.. _-c: commandline.html#config
