Usage and Examples
==================

Basic usage::

    bt [options] [filelist]

If no options nor files are specified, then blogtool_ will attempt to launch an
editor as specified by the $EDITOR environment variable. 

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

To post a file and make sure that all categories are added to the blog::

    > bt -a mypostfile

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

To retrieve a blogpost for editting::

    > bt -g 12345 > postfile

This assumes the ``POSTID`` of the post to edit is 12345.  The retrieve option
will list blog post titles along with the ID to use for this command.  The
resulting post file will contain an appropriately filled out header and the
post text will be formatted using markdown_ syntax.

To upload a picture::

    > bt -u funnypic.jpg

To see the comments for a post::

    > bt -r 12345

To write a comment::

    > bt --comment 12345

Note that if you wish to *reply* to a comment, you'll need to note the
``COMMENTID`` and add a line like this to the header::

    PARENTID: 54321

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
.. _-b: commandline.html#blog
