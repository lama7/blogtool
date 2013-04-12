.. contents::

Usage
=====

Basic usage::

    bt [options] [filelist]

If no options nor files are specified, then blogtool_ will attempt to launch an
editor as specified by the $EDITOR environment variable.

It is possible to specify a number of files on the command line.  blogtool_ will
iterate through each one.  In general, blogtool_ tries to fail such that it will
continue to process files.  Header syntax errors are one error, however, where
all processing ceases.

Command Line
------------

Assume the following **~/.btrc** file exists for the following examples::

    BLOG: {
            NAME: My Blog
            XMLRPC: http://my.server/xmlrpc.php
            USERNAME: user
            PASSWORD: secret
          }

To post a file to the blog::

    > bt mypostfile

To post several files to a blog::

    > bt postfile1 postfile2 postfile3

This is useful when scheduling posts.  Each post can have its own post time
set in the header while all 3 files are uploaded at the same time.

To post a file and make sure that all categories are added to the blog::

    > bt -a mypostfile

Any categories specified in the file will now be added to the blog automatically
if they are not already valid categories.  The default is not to do so in the
case of typos, in which case the default category for the blog is will be used.

To manually add a new category to a blog::

    > bt -n cat.subcat1.subcat2

Catgories can be supplied as a hierarchy by using a dotted notation as above.
All necessary categories will be added to the blog to fulfill the command.  So
if all 3 categories are new, 3 new categories will be added.  If only the final
``subcat2`` is new, that is the only new one created with it's parent being
``subcat1``.  This same syntax is used when specifying categories in the header
of a post file.

To retrieve the 5 latest blog titles::

    > bt -t 5

This command will produce the following output::

    POSTID  TITLE                                   DATE CREATED
    ======  ===================================     =====================
    1000    My Latest Blog Post                     Mar 21, 2012 at 08:31
    999     Something I Thought Was Interesting     Mar 20, 2012 at 07:07
    995     You Won't Believe This                  Mar 19, 2012 at 20:34
    993     The Dog Ate My Homework                 Mar 19, 2012 at 10:39
    991     An Obligatory baz and foo Ref           Mar 18, 2012 at 22:03

If there are multiple blogs specified in the configuration file, blogtool_ will
iterate through each of them and retrieve a recent entry list.

To retrieve a blogpost for editting::

    > bt -g 12345 > postfile

This assumes the ``POSTID`` of the post to edit is 12345.  The retrieve option
will list blog post titles along with the ID to use for this command.  The
resulting post file will contain an appropriately filled out header and the
post text will be formatted using markdown_ syntax.  Without the shell
redirection, it will just spill the post text to the standard output.

To upload a picture::

    > bt -u funnypic.jpg

To see the comments for a post::

    > bt -r 12345

Retrieving comments will retrieve *all* comments for the post requested.  It
will also list the usual information about the commenter as well as the comment
ID.  The ID can be used when replying to a comment.

To write a comment::

    > bt --comment 12345 67890

This command will result in an editor being opened with a header setup for a
comment.  The comment will be associated with post ID 12345 and will be in reply
to comment 67890.  If just writing a comment that isn't doesn't need to be a
reply, just use 0 as the comment ID::

    > bt --comment 12345 0

Post Files
----------

Given the following **~/.btrc** file::

    NAME: My Blog
    XMLRPC: http://my.server/xmlrpc.php
    USERNAME: user
    PASSWORD: secret
    BLOGTYPE: wp

When simply launching blogtool_ with an empty command line like::

    > bt

The editor will launch and the following header will appear in the file::

    TITLE:
    CATEGORIES:

Given the above configuration file, these are the minimal header entries that
must be completed for blogtool to be able to process the file.  Make sure there
is a blank line following the final header line or blogtool_ will not be able to
parse the file properly.

If there are conflicting entries between a the **~/.btrc** file and the header
of a post file, blogtool_ uses the value specified in the header.  For
instance, given the following **~/.btrc** file::

    NAME: My Blog
    XMLRPC: http://my.server/xmlrpc.php
    USERNAME: user
    PASSWORD: secret
    BLOGTYPE: wp
    CATEGORIES: Software

and the following post file::

    TITLE: The Most Important Post in the World
    CATEGORIES: Misc
    
    This is the most important post you will read, because I said so.

The post will be assigned the category ``Misc`` rather than ``Software``.  Note
the blank line following the header.

As of V1.1.2, for blog software that supports hiding a portion of the post
content behind a link, blogtool_ has a simple means of supporting this feature.
Simply add a line that starts with at least 3 **'+'** characters, spacing between
them is optional, into the post content where you want the software to split the
post.  Make sure the line is preceded by a blank line and followed by a blank
line.

For example::

    This is the beginning of the post content.  Not all of it will be visible
    until you click on the link created by the following line:

    + + +

    All content from this point forward is hidden until the `MORE` link is
    clicked on.  Note the preceding blank line and trailing blank line- those
    are both necessary.

For Wordpress blogs, the `MORE` text in the link can be replaced with custom
text by simply adding the desired text after the leading **'+'** characters.  The
text can then optionally be followed by more **'+'** characters, which will not
appear in the resulting custom text::

    This is the beginning of the post content.  Not all of it will be visible
    until you click on the link created by the following line:

    + + + + + + + +  Bang It Here for the Exciting Conclusion  + + + + + + + + 

    All of this is hidden.  The trailing plus characters will not appear in the
    `MORE` text field.  Also note the extra plus characters preceding the text.
    Again, all of those are discarded, it is the leading 3 that mark the line as
    the separator for the blog software.

The spacing between the **'+'** characters is optional as well::

    This is the beginning of the post content.  Not all of it will be visible
    until you click on the link created by the following line:

    ++++++++++++++++++++++++++ Click Here to Read the Rest

    The above will also be parsed as a content separator for the post.  No
    spacing between the plus characters and no trailing plus characters, but
    with custom text for the link.

To facilitate reading from the standard input, it is possible to supply
``STDIN`` as a file name on the command line::

    > bt STDIN

To be honest, I'm not sure what it can be practically used for.  I added it for
testing purposes and it seemed harmless to leave as a possibility for a user.
Someone more clever than I might be able to come up with a practical use.

Multiple Blogs
--------------

It is possible to specify multiple blogs in a single **~/.btrc** file::

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

If you wish to compose a new blog post that will go to both blogs::

    > bt -A

The resulting header that appears in the editor will be as so::

    TITLE:
    CATEGORIES:
    BLOG: First Blog, Other Blog

Now you'll know which blogs the post will be posted to.  If you don't want it to
go to both blogs, simply remove the blog name from the ``BLOG`` header line.

If you only want a post to go to a specific blog::

    > bt -b 'Other Blog'

Similarly, the `-b`_ option can be used in conjunction with other options like
retrieving titles, categories or posts.

Pictures
--------

It is possible with blogtool_ to add pictures to your post as provided by
markdown_ syntax.  To specify a file on your local machine, simply specify the
path to the image file using the markdown_ syntax for images::

    ![](path/to/picture.jpg )

When such a syntax is encountered by blogtool_ while processing a post file, it
will attempt to locate the ``JPG`` file and upload it to the blog.  If successful,
it will then modify the link information so that the image will be linked on the
blog and the picture will appear in the post without further direction from you.
Note that the space character preceding the closing paren is needed.  Also, if a
URL is supplied instead of a path, then blogtool does nothing extra and simply
posts the link as supplied.

Because blogtool_ utilizes python-markdown_, it takes advantage of the
attribute feature provided.  This is useful for resizing and locating a picture
for display in a blogpost.

For example, let's say `mypic.jpg` is a 1024x768 sized image.  The following
can be used to display it::

    {@class=aligncenter}
    ![{@width=614}{@height=531}](path/to/mypic.jpg )

This will set the ``width`` and ``height`` attributes in the subsequent markup for
the picture.  It will also place the picture in a ``p`` tag with its ``class``
attribute set to ``aligncenter`` so the picture will appear centered in the post.
This takes advantage of the builtin alignment classes for a Wordpress blog.

Another possibility::

    {@class=aligncenter}
    ![{@width=614}{@height=531}](path/to/mypic1.jpg )
    ![{@width=614}{@height=531}](path/to/mypic2.jpg )

This would center 2 pictures, potentially both on the same line if width allows
for it, within the same ``p`` tag.  Other alignment possibilities are
``alignright`` and ``alignleft`` or whatever other values are supported by your
blog theme.  Thus, while not exactly a tool for a photo blog, blogtool_
affords the user quite a bit of control over pictures.

.. _markdown: http://daringfireball.net/projects/markdown/
.. _python-markdown: http://pythonhosted.org/Markdown/index.html
.. _blogtool: https://pypi.python.org/pypi/blogtool
.. _-b: commandline.html#options
