#! /usr/bin/env python

import mutagen
import os
import shutil
import logging

logging.basicConfig(filename='/var/log/music_sort', level=logging.DEBUG)

UNSORTED_DIR = "/media/raptor/Music-Inbox/"
SORTED_DIR = "/media/raptor/Music/"
ERROR_DIR = "/media/raptor/Music-Errors/"

#UNSORTED_DIR = './Unsorted/'
#SORTED_DIR = './Sorted/'
#ERROR_DIR = './Error/'

unsorted = os.listdir(UNSORTED_DIR)
if unsorted and len(unsorted):
    logging.info("Sorting " + len(unsorted) + " files")

for unsorted_file in unsorted:
    tags = mutagen.File(UNSORTED_DIR + unsorted_file, easy=True)

    if not tags:
        shutil.move(UNSORTED_DIR + unsorted_file, ERROR_DIR + unsorted_file)
        logging.warning(" ** Unable to find music interpreter for file "
             + unsorted_file)
        continue

    if 'albumartist' in tags:
        artist = tags['albumartist'][0]
    elif 'artist' in tags:
        artist = tags['artist'][0]
    else:
        artist = 'Unknown'

    if 'album' in tags:
        album = tags['album'][0]
    else:
        album = 'Unknown'

    if 'title' in tags:
        title = tags['title'][0] + os.path.splitext(unsorted_file)[1].strip()
        if 'tracknumber' in tags:
            title = "{0:0>2} {1}".format(
                    tags['tracknumber'][0].split('/')[0], title)
            if 'discnumber' in tags and tags['discnumber'][0] != u'1/1':
                title = tags['discnumber'][0].split('/')[0] + '-' + title
    else:
        title = unsorted_file

    logging.info("    " + SORTED_DIR + artist + '/' + album + '/' + title)

    try:
        os.makedirs(SORTED_DIR + artist + '/' + album)
    except OSError, why:
        logging.info('    OSERROR: ' + str(why))
    
    try:
        shutil.move(UNSORTED_DIR + unsorted_file, 
            SORTED_DIR+artist + '/' + album + '/' + title)
    except IOError, why:
        logging.warning(' ** IOERROR: ' +  str(why))
