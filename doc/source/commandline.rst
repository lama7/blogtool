.. contents::

Command Line
============

In addition to posting files to a blog, blogtool_ can also do a number of
other blog maintenance related operations like deleting posts, downloading
posts, adding categories in addition to querying recent posts and current
category lists.

There are also a number of options that allow for controling how blogtool_
operates such as specifying a blog to interact with (if you have multiples
blogs), setting a time for a post to publish, using a different config file as
well as several others.

A number of these options require a `configuration file`_ in order to work.
They are marked with an '**\***' below.

Options
-------

Following are command line options that can be specified for blogtool_:

+---------------------------------+-------------------------------------------------------------------------+
| -c *CONFIGFILE*,                | Specifies *CONFIGFILE* to use as for configuration information.  This   |
| --config= *CONFIGFILE*          | takes precedence over the default '.btrc' file if specified. `\*`_      |
+---------------------------------+-------------------------------------------------------------------------+
| -b *BLOGNAME*,                  | Specifies to interact with blog *BLOGNAME* within a config file.        |
| --blog= *BLOGNAME*              | Should match the NAME_ keyword. `\*`_                                   |
+---------------------------------+-------------------------------------------------------------------------+
| -a, --add-categories            | blogtool_ will attempt to verify categories specified in a post file    |
|                                 | to account for typos.  If the catgories aren't found, then the category |
|                                 | will not be used.  This overrides that default.  Useful when adding a   |
|                                 | new category to the blog. `\*`_                                         |
+---------------------------------+-------------------------------------------------------------------------+
| --draft                         | The post will not be published when it is pushed up to the blog.        |
+---------------------------------+-------------------------------------------------------------------------+
| -s *TIMESTR*,                   | Allows for scheduling of posts.   See `Time Strings`_ below for how to  |
| --schedule= *TIMESTR*           | spell *TIMESTR*.                                                        |
+---------------------------------+-------------------------------------------------------------------------+
| -A, --allblogs                  | If multiple blogs are specified in a config file, normally they must be |
|                                 | specified using the NAME_ or BLOG_ keyword.  This provides a shortcut   | 
|                                 | for sending a post to all the blogs listed in the config file. `\*`_    |
+---------------------------------+-------------------------------------------------------------------------+
| -d *POSTID*,                    | Delete the post *POSTID*.  If multiple blogs are defined, then specify  |
| --delete= *POSTID*              | which blog to delete from with the -b option. `\*`_                     |
+---------------------------------+-------------------------------------------------------------------------+
| -t *NUM*,                       | Returns *NUM* of the most recent blog posts.  If multiple blogs are     |
| --recent-titles= *NUM*          | blogs are defined, then a list is returned for each blog.  If used with | 
|                                 | the -b option, only posts for that blog are listed. `\*`_               |
+---------------------------------+-------------------------------------------------------------------------+
| -C, --categories                | Returns a list of categories for a blog.  If multiple blogs are         |
|                                 | defined, then specify the blog using the -b option. `\*`_               |
+---------------------------------+-------------------------------------------------------------------------+
| -n *NAME*,                      | Adds *NAME* to the category list for the blog.  If multiple blogs are   |
| --new-categories= *NAME*        | defined, then use the -b option to specify which one to add the         |
|                                 | category to. `\*`_                                                      |
+---------------------------------+-------------------------------------------------------------------------+
| -g *POSTID*,                    | Retrieves post *POSTID* from a blog.  If multiple blogs are defined,    |
| --getpost= *POSTID*             | then use the -b option to specify which blog to retrieve from. `\*`_    |
|                                 |                                                                         |
|                                 | The returned post is printed out to STDOUT along with a header and an   |
|                                 | attempt is made to format it using Markdown syntax.  If the output is   |
|                                 | captured, it should be possible to use blogtool_ to repost the          |
|                                 | captured output.                                                        |
+---------------------------------+-------------------------------------------------------------------------+
| -u *UPLOAD_FILE*,               | Uploads file *UPLOAD_FILE* to a blog.  Requires a config file to        |
| --uploadmedia= *UPLOAD_FILE*    | provide blog information.  If multiple blogs are defined, then use the  | 
|                                 | -b option to specify which blog to retrieve from. `\*`_                 |
+---------------------------------+-------------------------------------------------------------------------+
| --comment= *POSTID*  *PARENTID* | Post text from a file as a comment to post *POSTID*. `\*`_              |
+---------------------------------+-------------------------------------------------------------------------+
| --charset=CHARSET               | Set the *CHARSET* to use to decode text prior to running it through     |
|                                 | markdown. `\*`_                                                         |
+---------------------------------+-------------------------------------------------------------------------+
| --posttype=POSTTYPE             | By default, content is published to posts on main page of a blog, so    |
|                                 | this option is not needed.  Setting this option to "page" will cause    |
|                                 | the content to be published to it's own page on the blog.  Normal       |
|                                 | content files can be used to create blog pages this way. `\*`_          |
+---------------------------------+-------------------------------------------------------------------------+
| -D *COMMENTID*,                 | Delete *COMMENTID* from a blog. `\*`_                                   |
| --deletecomment= *COMMENTID*    |                                                                         | 
+---------------------------------+-------------------------------------------------------------------------+
| -r *POSTID*,                    | Retrieves all comments from post *POSTID* and displays them on the      |
| --readcomments= *POSTID*        | console.  Comment text is converted to markdown syntax to ease          |
|                                 | reading. `\*`_                                                          |
+---------------------------------+-------------------------------------------------------------------------+
| --editcomment= *COMMENTID*      | Edit comment *COMMENTID* already on the blog.  The comment will be      |
|                                 | downloaded and an editor will be launched with the comment text         |
|                                 | formatted into Markdown syntax.  A header is also generated with the    |
|                                 | metadata from the blog in it so it can also be edited, for instance to  |
|                                 | approve a comment held in moderation. `\*`_                             |
+---------------------------------+-------------------------------------------------------------------------+
| -h, --help                      | Command line help message                                               |
+---------------------------------+-------------------------------------------------------------------------+
| --version                       | Output blogtool_ version string: ``blogtool version x.y.z``.            |
+---------------------------------+-------------------------------------------------------------------------+

.. _*:

**\*** - These options require a configuration file in order to work.

Time Strings
------------

The following strings may be used when scheduling a post for publication:

+   YYYYMMDDThh:mm
+   YYYYMMDDThh:mmAM/PM
+   YYYYMMDDThh:mm:ss
+   YYYYMMDDThh:mm:ssAM/PM
+   Month DD, YYYY hh:mm
+   Month DD, YYYY hh:mmAM/PM
+   MM/DD/YYYY hh:mm
+   MM/DD/YYYY hh:mmAM/PM
+   hh:mm MM/DD/YYYY
+   hh:mmAM/PM MM/DD/YYYY

Time String Key
~~~~~~~~~~~~~~~

YYYY 
    4 digit year
MM
    2 digit month (padded with leading 0's if necessary)
DD
    2 digit day of month (padded with leading 0's if necessary)
hh
    2 digit hour
mm
    2 digit minute (padded with leading 0's if necessary)
AM/PM
    specifies either 'AM' or 'PM' for time
Month
    abbreviated month name
T 
    a literal 'T' character
\/  
    a literal '/' character
\: 
    a literal ':' character

Time String Examples
~~~~~~~~~~~~~~~~~~~~

Some example time strings (these are all for the same time):

+ 8:30PM 03/09/2013
+ 20130903T20:30
+ Mar 09, 2013 8:30PM
+ 03/09/2013 20:30

.. _blogtool: https://pypi.python.org/pypi/blogtool
.. _configuration file: configuration.html#configuration-files
.. _NAME: configuration.html#name
.. _BLOG: configuration.html#blog
