# `Blogtool` #

`Blogtool` is a command line blog client for Wordpress weblogs.

Contents:

1. [Intro](#intro)
2. [The Details](#the-details)  
    a. [Keywords](#header-keywords)  
    b. [Definitions](#keyword-definitions)  
    c. [Groups](#groups)  
    d. [Configuration Files](#configuration-files)  
    e. [Command Line Options](#command-line-options)  
3. [Usage and Examples](#usage-and-examples)  
    a. [Command Line](#command-line)  
    b. [Headers](#headers)  
    c. [Multiple Blogs](#multiple-blogs)  

## Intro  ##

### Huh? ###

I've tried a variety of graphical blog clients.  All of them had spotty
behavior.  As I continued blogging, I realized that the gui based clients were
overkill for what I was doing.

What was I doing?  Pushing text up to my blog.  Occasionally with some pictures
in it.  I didn't require any fancy formatting or visual gimmickery or visual
control.  Even for the pictures, I mainly had to orient them horizontally,
vertically, center them and size them.

So all I really needed was an editor with a backend that could take the text and
publish it on my blog.  Actually, my blogs.  I had a backup that I posted
everything to as well.  Remarkably, none of the clients I used really dealt well
with multiple blogs.

Thus was born `blogtool`.

### Whats it do? ###

In addition to writing a post to a blog via xmlrpc, it also supports post
deletion and edits.  Categories and tags can be specified for the post.  A post
can be sent to multiple blogs, with slightly different configurations (different
categories or tags, for instance).  Additionally, image files embedded in the
post are uploaded to the blog as part of the publishing process.  Post can be
scheduled and can also be written as 'drafts' (not published).

Blog categories can be listed and created and any number of recent
entries can be retrieved and listed.  These actions are accomplished independent
of posts.  As a matter of fact, it's possible to do any combination of these
things with an entry on the command line.

Also, it supports Markdown syntax.  So the post can be formatted using Markdown
and the resulting file will be posted with the appropriate markup.

## The Details ##

In order to do any of this stuff, `blogtool` needs some basic info about the blog.
Also, as mentioned, it really only supports Wordpress blogs since that's what my
blog software is and therefore what `blogtool` has been tested on.

The basic blog info is provided via keywords and values separated by colons.
Dont' worry- there aren't a lot and they're intuitive with regards to blogging.
Where repetition is concerned, only three would be used on a regular basis for
multiple blogs.  If posting to a single blog, only two keywords are needed with
any regularity.

The keywords form the header.  Once the header is completed, a blank line
follows.  Everything thereafter is considered post text and will be written into
a post on the blog.

### Header Keywords ###

A `blogtool` header can consists of any combination of the following keywords:

+ TITLE
+ BLOG
+ NAME
+ XMLRPC
+ CATEGORIES
+ POSTID
+ USERNAME
+ PASSWORD
+ TAGS
+ POSTTIME
+ BLOGTYPE 

Notice, these are listed in caps.  That's because the keywords should be
capitalized in the header.  Each keyword should be followed by a ':' and then an
appropriate value.  More on those below.  Each line of the header is terminated
simply with a carriage return.  So don't try to put all the header stuff on a
single line.  To terminate a header, simply create a blank line.  Everything
after that blank line is processed as post text and will be published on the
blog.

For the purposes of posting, the required keywords are XMLRPC, NAME, USERNAME,
PASSWORD, and BLOGTYPE.  Without these, `blogtool` can't push anything up to a
weblog.

For keywords such as CATEGORIES and TAGS, a comma separated list can be supplied
as the value.

### Keyword Definitions ###

+   TITLE  
    Defines the post title that will appear on the blog.  

+   BLOG  
    Serves dual purposes.  With a single value it defines the name of the blog
    for posting to.  Again, basically any character can be used, excepting a
    comma.
  
    A comma separated list of blog names can be supplied if it's desired to
    publish to multiple blogs.

    Alternatively, a group can be assigned.  See "Groups" below.

+   BLOGTYPE  
    Specifies the blog type being posted to.  For now, this is only 'wp' for
    Wordpress blogs.

+   NAME  
    Specifies the actual name of the blog.  If posting to an individual blog,
    then it is synonymous with the 'BLOG' keyword.  If posting to multiple
    blogs, then it should be used inside a group for the 'BLOG' keyword.

+   XMLRPC  
    The location of the xmlrpc file for the blog.

+   CATEGORIES  
    The category the post should be filed under on the blog.  If filing under a
    subcategory, then it should be listed as a dotted representation of the
    category.  Example: parentcat.subcat1.subcat2

    Can be a single value or a comma separated list.

+   POSTID  
    The ID number of a post.  The presence of this in the header means that the
    post will be updated.

+   USERNAME  
    The login name for posting to the blog.  The is required to be able to post to
    a weblog.

+   PASSWORD  
    The password for the USERNAME for gaining access to the weblog.

+   TAGS  
    For defining the tags for a post.  Can be a single value or a comma separated
    list.

+   POSTTIME  
    Used to schedule a post.  See section at the end on time strings to see how
    to spell this.

The following keywords are specific to editting and or writing comments:

+   COMMENTSTATUS  
    Valid values are `approve`, `hold` and `spam` and are determined by the
    Wordpress blog software.  

+   COMMENTID  
    Every Wordpress comment has a unique ID, like the posts.  The value for this
    can be obtained with the `--readcomments` option or by hovering on the
    comment link in a browser.

+   PARENTID  
    The `comment_id` of the comment being replied to.  Typically used when
    writing a comment using the `--comment` option.

+   AUTHOR  
    Specifies the name to be associated with a comment.  When writing a comment
    via the `--comment` option, this will default to the username for the blog
    specified, but can be overwritten to anything.

+   AUTHORURL  
    Specifies the URL for the comment's author's website.  Can be left blank.

+   AUTHOREMAIL  
    Specifies an email address for the author of the comment.  Can be left
    blank.

### Groups ###

The header syntax also supports grouping for the BLOG keyword.  Grouping
provides a means to supply information for multiple blogs.  Use the 'NAME'
keyword within a group to specify a blog.

A group consists of a keywords enclosed within brackets.  Groups can be listed
using a comma.

EXAMPLE:

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

### Configuration Files ###

To reduce the amount of header typing, it is possible to create a configuration
file for `blogtool` to obtain parameter settings that are used all the time.  The
file '~/.btrc' is automatically looked for when `blogtool` is started.
Alternatively, a configuration file can be specified on the command line using
the '-c' options.

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

### Command Line Options ###

Following are command line options that can be specified for `blogtool`:

+   -h, --help  
    Command line help message

+   -c CONFIGFILE, --config=CONFIGFILE  
    Specifies a config file.  This takes precedence over the default '.btrc'
    file if specified.

+   -b BLOGNAME, --blog=BLOGNAME  
    Specifies a blog within a config file.  Should match the 'NAME' keyword.
    
+   -a, --add-categories  
    `Blogtool` will attempt to verify categories specified in a post file to
    account for typos.  If the catgories aren't found, then the category will
    not be used.  This overrides that default.  Useful when adding a new
    category to the blog.

+   --draft  
    The post will not be published when it is pushed up to the blog.

+   -s TIMESTR, --schedule=TIMESTR  
    Allows for scheduling of posts.   See below for how to spell TIMESTR.

+   -A, --allblogs  
    If multiple blogs are specified in a config file, normally they must be
    specified using the 'NAME' or 'BLOG' keyword.  This provides a shortcut for
    sending a post to all the blogs listed in the config file.

+   -d POSTID, --delete=POSTID  
    Delete the post.  Requires a config file to provide blog information.  If
    multiple blogs are defined, then specify which blog to delete from with the
    -b option.

+   -t NUM_RECENT_TITLES, --recent-titles=NUM_RECENT_TITLES  
    Returns a list of the most recent blog posts.  Requires a config file to
    provide blog information.  If multiple blogs are defined, then a list is
    returned for each blog.  If used with the -b option, only posts for that
    blog are listed.

+   -C, --catgories  
    Returns a list of categories for a blog.  Requires a config file to provide
    blog information.  If multiple blogs are defined, then specify the blog
    using the -b option.

+   -n NEWCAT_NAME, --new-categories=NEWCAT_NAME  
    Adds NEWCAT_NAME to the category list for the blog.  Requires a config file
    to provide blog information.  If multiple blogs are defined, then use the
    -b option to specify which one to add the category to.

+   -g GET_POSTID, --getpost=GET_POSTID  
    Retrieves a post from a blog.  Requires a config file to provide blog
    information.  If multiple blogs are defined, then use the -b option to
    specify which blog to retrieve from.

    The returned post is printed out to STDOUT along with a header and an
    attempt is made to format it using Markdown syntax.  If the output is
    captured, it should be possible to use `blogtool` to repost the captured
    output.

+   -u UPLOAD_FILE, --uploadmedia=UPLOAD_FILE  
    Uploads a file to a blog.  Requires a config file to provide blog
    information.  If multiple blogs are defined, then use the -b option to
    specify which blog to retrieve from.

+   --comment==POSTID  
    Post text from a file as a comment to post POSTID.

+   --charset=CHARSET  
    Set the CHARSET to use to decode text prior to running it through markdown.

+   -D COMMENTID, --deletecomment=COMMENTID  
    Delete COMMENTID from a blog.

+  -r POSTID, --readcomments=POSTID  
    Retrieves all comments for a post and displays them on the console.  Comment
    text is converted to markdown syntax to ease reading.

+   --editcomment=COMMENTID  
    Edit comment COMMENTID already on the blog.  The comment will be downloaded
    and an editor will be launched with the comment text formatted into Markdown
    syntax.  A header is also generated with the metadata from the blog in it so
    it can also be edited, for instance to approce a comment held in moderation.

### Miscellaneous ###

Time Strings

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

KEY:
+ YYYY = 4 digit year
+ MM = 2 digit month (padded with leading 0's if necessary)
+ DD = 2 digit day of month (padded with leading 0's if necessary)
+ hh = 2 digit hour
+ mm = 2 digit minute (padded with leading 0's if necessary)
+ AM/PM = specifies either 'AM' or 'PM' for time
+ Month = abbreviated month name
+ T = a literal 'T' character
+ / = a literal '/' character
+ : = a literal ':' character

## Usage and Examples  ##

Basic usage:

bt \[options\] \[filelist\]

If no options nor files are specified, then `blogtool` will attempt to launch an
editor as specified by the $EDITOR environment variable. 

### Command Line ###

Assume the following `~/.btrc` file exists for the following examples:

    BLOG: {
            NAME: My Blog
            XMLRPC: http://my.server/xmlrpc.php
            USERNAME: user
            PASSWORD: secret
          }

To post a file to the blog:

    > bt mypostfile

To post a file and make sure that all categories are added to the blog:

    > bt -a mypostfile

To manually add a new category to a blog:

    > bt -n cat.subcat1.subcat2

Catgories can be supplied as a hierarchy by using a dotted notation as above.
All necessary categories will be added to the blog to fulfill the command.  So
if all 3 categories are new, 3 new categories will be added.  If only the final
`subcat2` is new, that is the only new one created with it's parent being
`subcat1`.  This same syntax is used when specifying categories in the header of
a post file.

To retrieve the 5 latest blog titles:

    > bt -t 5

To retrieve a blogpost for editting:

    > bt -g 12345 > postfile

This assumes the `POSTID` of the post to edit is 12345.  The retrieve option
will list blog post titles along with the ID to use for this command.  The
resulting `postfile` will contain an appropriately filled out header and the
post text in `markdown` syntax.

To upload a picture:

    > bt -u file_to_upload

To see the comments for a post:

    > bt -r 12345

To write a comment:

    > bt --comment 12345

Note that if you wish to *reply* to a comment, you'll need to note the
`commentid` and add a line like this to the header:

    PARENTID: 54321

### Headers ###

Given the following `~/.btrc` file:

    NAME: My Blog
    XMLRPC: http://my.server/xmlrpc.php
    USERNAME: user
    PASSWORD: secret
    BLOGTYPE: wp

When simply launching blogtool with an empty command line like:

    > bt

The editor will launch with the following header:

    TITLE:
    CATEGORIES:

These are the minimal header entries that must be completed for blogtool to be
able to process the file.  Make sure there is a blank line following the final
header line or `blogtool` will not be able to parse the file properly.

### Multiple Blogs ###

It is possible to specify multiple blogs in a single `~/.btrc` file:

    BLOG: {
           NAME: First Blog
           XMLRPC: http://firstblog.server/xmlrpc.php
           USERNAME: user
           PASSWORD: secret
          },
          {
           NAME: Other Blog
           XMLRPC: http://otherblog.server/xmlrpc.php
           USERNAME: user
           PASSWORD: secret2
          }
    BLOGTYPE: wp

If you wish to compose a new blog post that will go to both blogs:

    > bt -A

The resulting header that appears in the editor will be as so:

    TITLE:
    CATEGORIES:
    BLOG: First Blog, Other Blog

Now you'll know which blogs the post will be posted to.  If you don't want it to
go to both blogs, simply remove the blog name from the `BLOG` header line.

If you only want a post to go to a specific blog:

    > bt -b 'Other Blog'

Similarly, the `-b` option can be used in conjunction with other options like
retrieving titles, categories or posts.


