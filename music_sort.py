#! /usr/bin/env python

import mutagen
import mutagen.mp3
import os, sys
import shutil
import logging
import re

def sanitize (string):
    return re.sub('[/\\\?\*:]', '_', string)

UNSORTED_DIR= "/media/raptor/Music-Inbox/"
SORTED_DIR  = "/media/raptor/Music/"
ERROR_DIR   = "/media/raptor/Music-Errors/"

#UNSORTED_DIR= './Unsorted/'
#SORTED_DIR  = './Sorted/'
#ERROR_DIR   = './Error/'

BLANK_TAG   = {'blank': True}

def get_tags (unsorted_file, unsorted_dir=UNSORTED_DIR, error_dir=ERROR_DIR):

    try:
        tags = mutagen.File(unsorted_dir + unsorted_file, easy=True)
    except mutagen.mp3.HeaderNotFoundError, why:
        tags = BLANK_TAG
        logging.info(" ** Could not get mutagen to read headers: " 
            + unsorted_file + "using blank tags instead")
    except IOError, why:
        logging.info(" ** Could not get mutagen to read file: " 
            + unsorted_file + "\n" + str(why))
        return None

    if not tags:
        shutil.move(unsorted_dir + unsorted_file, 
                error_dir + os.path.split(unsorted_file)[1])
        logging.warning(" ** Unable to find music interpreter for file "
             + unsorted_file)
        return None

    return tags

def process_tags (unsorted_file, tags):

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
            title = u"{0:0>2} {1}".format(
                    tags['tracknumber'][0].split('/')[0], title)
            if 'discnumber' in tags and tags['discnumber'][0] != u'1/1':
                title = tags['discnumber'][0].split('/')[0] + '-' + title
    else:
        (head, tail) = os.path.split(unsorted_file)
        title = tail

    title = sanitize(title)
    album = sanitize(album)
    artist= sanitize(artist)

    return (artist, album, title)

# expand recursively into the directories
def get_all_files_in_dir(directory=UNSORTED_DIR):
    if directory[-1] != '/':
        directory = directory + '/'
    unsorted    = os.listdir(directory)
    found_dir   = True
    folders     = []
    while found_dir:
        found_dir   = False
        newunsorted = []
        for entry in unsorted:
            if os.path.isdir(directory+ entry):
                logging.info("Expanding into directory %s", entry)
                folders.insert(0, entry)
                newunsorted.extend([entry + "/" + x for x in 
                        os.listdir(directory+ entry)])
                found_dir = True
            else:
                newunsorted.append(entry)
        unsorted = newunsorted[:]
    return (unsorted, folders)

def sort_file(unsorted_file, unsorted_dir=UNSORTED_DIR, 
        sorted_dir=SORTED_DIR, error_dir=ERROR_DIR):

    tags = get_tags(unsorted_file)
    if tags is None:
        return False

    (artist, album, title) = process_tags(unsorted_file, tags)

    logging.info("    " + sorted_dir + artist + '/' + album + '/' + title)
    try:
        os.makedirs(sorted_dir + artist + '/' + album)
    except OSError, why:
        logging.info('    OSERROR: ' + str(why))
    
    try:
        shutil.move(unsorted_dir + unsorted_file, 
            sorted_dir+artist + '/' + album + '/' + title)
    except IOError, why:
        shutil.move(unsorted_dir + unsorted_file, error_dir + Title)
        logging.warning(' ** IOERROR: ' +  str(why))
        return False
    return True


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(message)s', 
        datefmt='%m/%d/%Y %H:%M:%S', 
        filename='/var/log/music_sort.log', level=logging.DEBUG)
    #logging.basicConfig(format='%(asctime)s %(message)s', 
    #    datefmt='%m/%d/%Y %H:%M:%S', 
    #    filename='./music_sort.log', level=logging.DEBUG)

    if len(os.listdir(UNSORTED_DIR)) == 0:
        sys.exit()

    logging.info("---")
    logging.info("Starting new music scan...")
    logging.info("")


    (unsorted, folders) = get_all_files_in_dir()

    if unsorted:
        logging.info("Sorting %d files: " + str(unsorted), len(unsorted))

    # process files
    [sort_file(unsorted_file) for unsorted_file in unsorted]

    # post process
    logging.info("Removing directories " + str(folders))
    for entry in folders:
        os.rmdir(UNSORTED_DIR + entry)
