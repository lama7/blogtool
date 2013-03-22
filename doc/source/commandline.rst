Command Line
============

In addition to posting files to a blog, `blogtool`_ can also do a number of
other blog maintenance related operations like deleting posts, downloading
posts, adding categories in addition to querying recent posts and current
category lists.

There are also a number of options that allow for controling how `blogtool`_
operates such as specifying a blog to interact with (if you have multiples
blogs), setting a time for a post to publish, using a different config file as
well as several others.

A number of these options require a `configuration file`_ in order to work.
They are marked with an '\*' below.

Contents:

- Options_
- `Time Strings`_

  - `Time String Key`_

Options
-------
Following are command line options that can be specified for `blogtool`_:

.. _config:

-c CONFIGFILE, --config=CONFIGFILE 
    Specifies ``CONFIGFILE`` to use as for configuration information.  This
    takes precedence over the default '.btrc' file if specified. `\*`_

.. _blog:

-b BLOGNAME, --blog=BLOGNAME  
    Specifies to interact with blog ``BLOGNAME`` within a config file.  Should
    match the `NAME`_ keyword. `\*`_
    
-a, --add-categories  
    `blogtool`_ will attempt to verify categories specified in a post file to
    account for typos.  If the catgories aren't found, then the category will
    not be used.  This overrides that default.  Useful when adding a new
    category to the blog. `\*`_

--draft  
        The post will not be published when it is pushed up to the blog.

-s TIMESTR, --schedule=TIMESTR  
    Allows for scheduling of posts.   See `Time Strings`_ below for how to spell
    ``TIMESTR``.

-A, --allblogs  
    If multiple blogs are specified in a config file, normally they must be
    specified using the 'NAME' or 'BLOG' keyword.  This provides a shortcut for
    sending a post to all the blogs listed in the config file. `\*`_

-d POSTID, --delete=POSTID  
    Delete the post ``POSTID``.  If multiple blogs are defined, then specify
    which blog to delete from with the -b option. `\*`_

-t NUM_RECENT_TITLES, --recent-titles=NUM_RECENT_TITLES
    Returns ``NUM_RECENT_TITLES`` of the most recent blog posts.  If multiple
    blogs are defined, then a list is returned for each blog.  If used with the
    -b option, only posts for that blog are listed. `\*`_

-C, --categories  
    Returns a list of categories for a blog.  If multiple blogs are defined,
    then specify the blog using the -b option. `\*`_

-n NEWCAT_NAME, --new-categories=NEWCAT_NAME 
    Adds ``NEWCAT_NAME`` to the category list for the blog.  If multiple blogs
    are defined, then use the -b option to specify which one to add the category
    to. `\*`_

-g POSTID, --getpost=POSTID 
    Retrieves post ``POSTID`` from a blog.  If multiple blogs are defined, then
    use the -b option to specify which blog to retrieve from. `\*`_

    The returned post is printed out to STDOUT along with a header and an
    attempt is made to format it using Markdown syntax.  If the output is
    captured, it should be possible to use `blogtool`_ to repost the captured
    output.

-u UPLOAD_FILE, --uploadmedia=UPLOAD_FILE 
    Uploads file ``UPLOAD_FILE`` to a blog.  Requires a config file to provide
    blog information.  If multiple blogs are defined, then use the -b option to
    specify which blog to retrieve from. `\*`_

.. _comment:

--comment=POSTID   
    Post text from a file as a comment to post ``POSTID``. `\*`_

--charset=CHARSET 
    Set the ``CHARSET`` to use to decode text prior to running it through
    markdown. `\*`_

-D COMMENTID, --deletecomment=COMMENTID 
    Delete ``COMMENTID`` from a blog. `\*`_

.. _readcomments:

-r POSTID, --readcomments=POSTID 
    Retrieves all comments from post ``POSTID`` and displays them on the
    console.  Comment text is converted to markdown syntax to ease reading. `\*`_ 

--editcomment=COMMENTID 
    Edit comment ``COMMENTID`` already on the blog.  The comment will be
    downloaded and an editor will be launched with the comment text formatted
    into Markdown syntax.  A header is also generated with the metadata from the
    blog in it so it can also be edited, for instance to approce a comment held
    in moderation. `\*`_

-h, --help
    Command line help message

--version    
    Output `blogtool`_ version string: ``blogtool version x.y.z``.

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

.. _blogtool: https://pypi.python.org/pypi/blogtool
.. _configuration file: configuration.html#configuration-files
.. _NAME: configuration#name
