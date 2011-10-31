#! /usr/bin/env python

import mutagen
import os
import shutil
import logging
import re

#logging.basicConfig(format='%(asctime)s %(message)s', 
#    datefmt='%m/%d/%Y %H:%M:%S', 
#    filename='/var/log/music_sort', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s %(message)s', 
    datefmt='%m/%d/%Y %H:%M:%S', 
    filename='./log.log', level=logging.DEBUG)

def sanitize (string):
    return re.sub('[/\\\?\*:]', '_', string)

#UNSORTED_DIR= "/media/raptor/Music-Inbox/"
#SORTED_DIR  = "/media/raptor/Music/"
#ERROR_DIR   = "/media/raptor/Music-Errors/"

UNSORTED_DIR= './Unsorted/'
SORTED_DIR  = './Sorted/'
ERROR_DIR   = './Error/'

logging.info("---")
logging.info("Starting new music scan...")
logging.info("")

unsorted    = os.listdir(UNSORTED_DIR)
found_dir   = True
folders     = []
while found_dir:
    found_dir   = False
    newunsorted = []
    for entry in unsorted:
        if os.path.isdir(UNSORTED_DIR + entry):
            logging.info("Expanding into directory %s", entry)
            folders.insert(0, entry)
            newunsorted.extend([entry + "/" + x for x in 
                    os.listdir(UNSORTED_DIR + entry)])
            found_dir = True
        else:
            newunsorted.append(entry)
    unsorted = newunsorted[:]

if unsorted and len(unsorted):
    logging.info("Sorting %d files: " + str(unsorted), len(unsorted))

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
        (head, tail) = os.path.split(unsorted_file)
        title = tail

    title = sanitize(title)
    album = sanitize(album)
    artist= sanitize(artist)

    logging.info("    " + SORTED_DIR + artist + '/' + album + '/' + title)

    try:
        os.makedirs(SORTED_DIR + artist + '/' + album)
    except OSError, why:
        logging.info('    OSERROR: ' + str(why))
    
    try:
        shutil.move(UNSORTED_DIR + unsorted_file, 
            SORTED_DIR+artist + '/' + album + '/' + title)
    except IOError, why:
        shutil.move(UNSORTED_DIR + unsorted_file, ERROR_DIR + unsorted_file)
        logging.warning(' ** IOERROR: ' +  str(why))

logging.info("Removing directories " + str(folders))
for entry in folders:
    os.rmdir(UNSORTED_DIR + entry)
