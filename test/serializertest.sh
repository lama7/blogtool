#!/bin/bash

# NOTE: before using this script, there is a block of code commented out in the
# fileprocessor.py file, located in the _procText method.  Uncomment that
# section prior to running this test.

# The name of the blog to test against.  Obviously, this is my blog's name,
# change it appropriately to your own or one you have access to.
blog='A Stay At Home Dad'
# check if we got an argument on the command line, if so, assume it's a number
if [ $# -eq 0 ]
  then
    testlen=100
  else
    testlen=$1
fi
bt -b "$blog" -t $testlen > ./recent
postids=(`./parserecent`)
for postid in "${postids[@]}"
do
    echo $postid
    bt -b "$blog" -g $postid | bt STDIN
done
