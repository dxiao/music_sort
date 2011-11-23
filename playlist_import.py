#! /usr/bin/env python

import os, sys
import shutil
import logging
import re
import music_sort


INBOX_DIR   = "/media/raptor/Playlists-Inbox/"
PLAYLIST_DIR= "/media/raptor/Playlists/"
MUSIC_DIR   = "/media/raptor/Music/"

#INBOX_DIR   = os.path.abspath("./Playlist-Inbox/") + '/'
#PLAYLIST_DIR= os.path.abspath("./Playlist/") + '/'
#MUSIC_DIR   = os.path.abspath("./Sorted/") + '/'

BLANK_ENTRY = ["","",""]
BLANK_OPT   = {'delta': False}
opt         = BLANK_OPT

def sanitize (string):
    return re.sub('[/\\\?\*:]', '_', string)


def make_symlink(entry_raw, old_entry, name, opt=BLANK_OPT, 
        playlist_dir=PLAYLIST_DIR, music_dir=MUSIC_DIR):

    if len(entry_raw) == 1:
        return False

    entry   = list(entry_raw[0:3])
    if len(entry_raw) > 3:
        args= entry_raw[3]
    else:
        args= ''
    for i in range(3):
        if entry_raw[i] == '.':
            entry[i] = old_entry[i]
        else:
            old_entry[i] = entry[i]
    playlist_filepath   = playlist_dir + name + '/' + ' - '.join(entry)
    music_filepath      = music_dir + '/'.join(entry)

    # file option processing
    if '-' in args:
        logging.info("    Removing playlist entry " + playlist_filepath)
        try:
            os.unlink(playlist_filepath)
        except OSError, why:
            logging.info(" ** Could not unlink entry: " + str(why))
        return False

    logging.info('    Adding symlink: ' + music_filepath + 
        ' --> ' + playlist_filepath)
    try:
        os.symlink(music_filepath, playlist_filepath)
    except OSError, why:
        logging.info(' ** OSERROR: ' + str(why))
    except IOError, why:
        logging.info(' ** IOERROR: ' + str(why))
    return True

def process_new_list(listentry): 
    logging.info("Processing " + listentry + "...")

    listfile    = open(INBOX_DIR + listentry)
    name        = sanitize(listfile.readline())[:-1]
    edelims     = listfile.readline()[:-1]
    fdelims     = listfile.readline()[:-1]
    options     = listfile.readline()[:-1].split(' ')
    entrystr    = listfile.read()

    if len(fdelims) == 0:
        fdelims = "\s*\n\s*"
    if len(edelims) == 0:
        edelims = "\s*/\s*"
    
    logging.info('Name: ' + name)
    logging.info('File Delimeter:  ' + fdelims)
    logging.info('Entry Delimeter: ' + edelims)
    logging.info('Options: ' + str(options))

    tokens      = re.split(fdelims, entrystr)
    entries     = [re.split(edelims, token) for token in tokens]
    logging.info("Got entry list " + str(entries))

    # option processing
    if 'delta' in options:
        opt['delta'] = True

    # playlist creation
    if opt['delta'] == False:
        logging.info("Creating playlist folder")
        try:
            os.mkdir(PLAYLIST_DIR + name)
        except OSError, why:
            logging.info('    OSERROR while creating playlist folder: ' + str(why))
    old_entry = list(BLANK_ENTRY)
    for entry_raw in entries:
        make_symlink(entry_raw, old_entry, name, opt)
    
    try:
        shutil.move(INBOX_DIR + listentry, PLAYLIST_DIR + name+'/' + listentry)
    except IOError, why:
        logging.info(' ** IOError while moving playlist file:' + str(why))

def process_new_folder(listfolder):

    logging.info("Adding music, playlist " + listfolder)

    unsorted_dir = INBOX_DIR + listfolder + '/'

    old_entry = list(BLANK_ENTRY)
    (files, folders) = music_sort.get_all_files_in_dir(unsorted_dir)

    logging.info("Creating playlist folder")
    try:
        os.mkdir(PLAYLIST_DIR + listfolder)
    except OSError, why:
        logging.info('    OSERROR while creating playlist folder: ' + str(why))

    for new_file in files:
        logging.info("    Processing file: " + unsorted_dir + new_file)
        tags        = music_sort.get_tags(new_file, unsorted_dir, unsorted_dir)
        entry_tuple = music_sort.process_tags(new_file, tags)
        logging.info("    Got entries: " + str(entry_tuple))
        if music_sort.sort_file(new_file, unsorted_dir):
            make_symlink(list(entry_tuple), old_entry, listfolder)

    # post process
    logging.info("Removing directories " + str(folders))
    for entry in folders:
        os.rmdir(unsorted_dir + entry)
    os.rmdir(unsorted_dir)

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(message)s', 
        datefmt='%m/%d/%Y %H:%M:%S', 
        filename='/var/log/playlist_import.log', level=logging.DEBUG)
    #logging.basicConfig(format='%(asctime)s %(message)s', 
    #    datefmt='%m/%d/%Y %H:%M:%S', 
    #    filename='./playlist_import.log', level=logging.DEBUG)

    if len(os.listdir(INBOX_DIR)) == 0:
        sys.exit()

    logging.info("---")
    logging.info("Starting new music scan...")
    logging.info("")

    incoming    = os.listdir(INBOX_DIR)
    new_lists   = []
    new_folders = []
    for entry in incoming:
        if os.path.isdir(INBOX_DIR + entry):
            new_folders.append(entry)
        elif os.path.splitext(entry)[1] == '.play':
            new_lists.append(entry)

    logging.info("Got new folders: " + str(new_folders))
    logging.info("Got new lists: " + str(new_lists))

    [process_new_list(x) for x in new_lists]
    [process_new_folder(x) for x in new_folders]

