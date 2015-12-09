# Author:  David Kruger
# Date  :  07 November 2015
# Desc  :  This is my attempt to sort out media (movies and series) once they have completed downloading
#          by moving them intelligently to predefined directories based on their type.
#          The files are picked up from the specified source directory and inspected.  The first test is to check IMdb 
#          to see whether it is a movie, if it is not found, the file is assumed to be a series.
#          In either case, the correct path is built based on the supplied destination directories and the file is
#          moved.  For series, multiple destinations can be defined, with one being the default (for cases 
#          where a new series is added).  All other series that already have a directory will be picked up 
#          and sorted accordingly.
#
#          Ideally, this is used in conjunction with cron so that the sorting can happen autonomously
#          Great to use with osmc for the ultimate solution.
#
#          Missing functionality:
#          - general efficiency
#          - improve diagnostics - check if copy is successful based on size comparison (power failure)



import platform
import sys
import os
import shutil
import urllib2
from BeautifulSoup import BeautifulSoup
from mechanize import Browser
import re
import datetime
import socket
import patoolib
import pwd
import grp

# =================================================================================================================
# Paths and Dirs
# =================================================================================================================

# Where the Unsorted stuff is kept
sourcedirectory = os.sep + os.path.join('media', '00_Media', '02_WorkDir', '01_Done')

# Where Series are kept
seriedest1 = os.sep + os.path.join('media', '00_Media', '00_Series')
seriedest2 = os.path.join('')

# Where Movies are kept
moviedest1 = os.sep + os.path.join('media', '01_Media', '00_Movies')
moviedest2 = os.path.join('')

destinationdirectory = (seriedest1, seriedest2)
moviedirectory = (moviedest1, moviedest2)

# Where should new series entries be created? Starts @ 0
defaultdest = destinationdirectory[0]

# Log file path
logfile = os.sep + os.path.join('home', 'osmc', 'Scripts', 'MediaOrg_Log.txt')

# Summary file path
summaryfile = os.sep + os.path.join('home', 'osmc', 'Scripts', 'MediaOrg_Summary.txt')


# =================================================================================================================
# Constants
# =================================================================================================================

verbose = True
debug = ''
# maxseriesize = 9000000000
REMOTE_SERVER = "www.google.com"
USERNAME = 'osmc'
GROUP = 'osmc'

# Video types to scan for
mediatypes = ('.mp4', '.avi', '.mkv', '.wmv', '.mpeg', '.mpg')

# Exclude files with the following in their name:
exclusions = ('sample', '._')

# What should be removed from the file name
crapdict = ('webrip', 'bluray', 'divx')


# =================================================================================================================
# Check that all drives specified are available
# =================================================================================================================


def drives_available():

    flag = 'OK'
    if not(os.path.exists(sourcedirectory)):
        flag = 'error'
    for drive in destinationdirectory:
        if not(os.path.exists(drive)) and drive != '':
            flag = 'error'
    for drive in moviedirectory:
        if not(os.path.exists(drive)) and drive != '':
            flag = 'error'
    return flag

# =================================================================================================================
# Add some colour to the output
# =================================================================================================================


def printcolour(stringput, colour):
    if colour == 'gr':
        print("\033[1;30m%s\033[1;m" %stringput)
    if colour == 'r':
        print("\033[1;31m%s\033[1;m" %stringput)
    if colour == 'g':
        print("\033[1;32m%s\033[1;m" %stringput)
    if colour == 'y':
        print("\033[1;33m%s\033[1;m" %stringput)
    if colour == 'b':
        print("\033[1;34m%s\033[1;m" %stringput)
    if colour == 'm':
        print("\033[1;35m%s\033[1;m" %stringput)
    if colour == 'cy':
        print("\033[1;36m%s\033[1;m" %stringput)
    if colour == 'w':
        print("\033[1;37m%s\033[1;m" %stringput)
    if colour == 'cr':
        print("\033[1;38m%s\033[1;m" %stringput)

# =================================================================================================================
# Check internet connectivity
# =================================================================================================================


def is_connected():
    try:
        host = socket.gethostbyname(REMOTE_SERVER)
        s = socket.create_connection((host, 80), 2)
        return 'connected'
    except:
        printcolour('Error connecting to the web...', 'r')
        return 'error'


# =================================================================================================================
# Gets the OS used to determine dir syntax
# =================================================================================================================


def what_os():
    if (platform.platform().lower().find("windows")) > -1:
        printcolour('-----  OS: Windows ------', 'y')
    if (platform.platform().lower().find("ubuntu")) > -1:
        printcolour('-----  OS: Ubuntu -----', 'y')
    return

# =================================================================================================================
# Check if it is a movie!
# =================================================================================================================

# Credit to this guy for web scraping:
# Author : Jay Rambhia
# email  : jayrambhia777@gmail.com
# Git    : https://github.com/jayrambhia
# gist   : https://gist.github.com/jayrambhia


def getunicode(soup):
    body = ''
    if isinstance(soup, unicode):
        soup = soup.replace('&#39;', "'")
        soup = soup.replace('&quot;', '"')
        soup = soup.replace('&nbsp;', ' ')
        body = body + soup
    else:
        if not soup.contents:
            return ''
        con_list = soup.contents
        for con in con_list:
            body += getunicode(con)
    return body


def movieyn(title):

    # Search using google (The block robots)
    #movie = title
    #movie_search = '+'.join(movie.split())
    #base_url = 'https://www.google.com/search?q='
    #url = base_url+movie_search+'&ie=utf-8&oe=utf-8#q=' + movie_search

    # Search using yahoo (not as accurate)
    movie = title
    movie_search = '+'.join(movie.split())
    base_url = 'https://za.search.yahoo.com/search?p='
    url = base_url+movie_search+'&fr=yfp-t-915'

    # Search using bing
    movie = title
    movie_search = '+'.join(movie.split())
    base_url = 'https://www.bing.com/search?q='
    url = base_url+movie_search

    title_search = re.compile('/title/tt\d+')

    br = Browser()
    br.set_handle_robots(False)
    #br.set_proxies({'http':'http://username:password@proxy:port',
    #            'https':'https://username:password@proxy:port'})
    if verbose:
        printcolour('(movieyn) Getting info from: ' + url, 'g')

    try:
        br.open(url)
        link = br.find_link(url_regex=re.compile(r'/title/tt.*'))
        res = br.follow_link(link)

        soup = BeautifulSoup(res.read())

        movie_title = getunicode(soup.find('title'))
        movie_title = movie_title.replace(' - IMDb', '')

        # Look for 'TV Episode' in the soup
        if (soup.find('meta', {'property': 'og:title'})['content']).find('TV Episode') > -1:
            if verbose:
                printcolour('(movieyn) ' + movie + ' detected as series...', 'cy')
            return '-'

        if debug:
            rate = soup.find('span', itemprop='ratingValue')
            rating = getunicode(rate)

            actors = []
            actors_soup = soup.findAll('a', itemprop='actors')
            for i in range(len(actors_soup)):
                actors.append(getunicode(actors_soup[i]))

            des = soup.find('meta', {'name': 'description'})['content']

            genre = []
            infobar = soup.find('div', {'class': 'infobar'})
            r = infobar.find('', {'title': True})['title']
            genrelist = infobar.findAll('a', {'href': True})

            for i in range(len(genrelist)-1):
                genre.append(getunicode(genrelist[i]))
            release_date = getunicode(genrelist[-1])

            printcolour('Title: ' + movie_title, 'y')
            printcolour('Rating: ' + rating +'/10.0', 'y')
            printcolour('Relase Date: ' + release_date, 'y')
            printcolour('Rated ' +r, 'y')
            printcolour('', 'y')
            printcolour('Genre: ' + ', '.join(genre), 'y')
            printcolour('Actors: ' + ', '.join(actors), 'y')
            printcolour('Description: ' + des, 'y')

        if verbose:
            printcolour('(movieyn) Found: ' + movie_title, 'g')
        return movie_title

    except:
        if verbose:
            printcolour('(movieyn) ' + movie + ' not found! Must be a series??', 'cy')
        return '-'


# =================================================================================================================
# Returns a list of all files in the given path based on criteria such as .extension and size
# =================================================================================================================


def sniffer(path, typesearch, exclude):

    returnlist = []

    for path, subdirs, files in os.walk(path):
        for fileinstance in files:

            conform_ext = 0
            conform_exc = 1

            # Test for the right extension
            for extensions in typesearch:
                if fileinstance.endswith(extensions):
                    conform_ext = 1

            # Test for exclusion
            for excluded in exclude:
                if fileinstance.lower().find(excluded) > -1:
                    conform_exc = 0
                    break

            if conform_exc == 1 and conform_ext == 1:
                returnlist.append(os.path.join(path, fileinstance))

    return[returnlist]


# =================================================================================================================
# Strips all the crap out of a filename
# =================================================================================================================


def stripcrap(stringin):

    stringout = stringin
    for word in crapdict:
        stringout = stringout.replace(word, '',-1)

    return stringout

# =================================================================================================================
# Creates the directory passed to it.
# =================================================================================================================


def directorycreator(path):

    dirlist = []
    d = 0
    pathstring = str(path) + os.sep

    while not(os.path.exists(path) and not(d >= 30)):

        pathstring = pathstring[:pathstring.rfind(os.sep)]

        if pathstring.find(os.sep) < 0:
            pathstring += os.sep

        if os.path.exists(pathstring):

            os.mkdir(dirlist.pop())

        else:
            dirlist.append(pathstring)
            d += 1
    return os.path.exists(path)

# =================================================================================================================
# Get all the components that make up the file name
#
# Takes the full path /blabla/bla/MovieorSerie.XXXX.Crap  and gets:
#
# Name of file            : Movie/Serie
# 4 digits after name     : XXXX          (Could be season info or movie year)
# =================================================================================================================


def filedetail(fullpath):

    gotdigits = 0
    truncated = 0
    firstpartdone = 0
    bufffirstpart = ''
    buffsecondpart = ''

    filename = fullpath[fullpath.rfind(os.sep)+1:]
    if debug:
        printcolour('(filedetail) Filename: ' + filename + ' \nPath: ' + fullpath, 'y')
    for char in filename:

        #
        if char.isdigit() and not gotdigits:
            bufffirstpart += char

        else:

            gotdigits = 1

            # Determine if we have the season info
            if char == '.' and buffsecondpart.__len__() > 2:
                firstpartdone = 1

            # Collect all digits that represent series
            if char.isdigit():
                if firstpartdone:
                    break
                buffsecondpart += char

            # Get all chars to make up series name
            elif buffsecondpart.__len__() == 0:
                bufffirstpart += char

    # Format the first part  ------------------------------------

    if bufffirstpart.lower().endswith('.s'):
        bufffirstpart = bufffirstpart[:-2]
        truncated = True

    if not truncated:
        bufffirstpart = bufffirstpart[:bufffirstpart.rfind('.')]

    bufffirstpart = bufffirstpart.title().replace('.', ' ').strip(' ')

    if verbose:
        printcolour('---------------------------------------------', 'cy')
        printcolour('Processing: ' + filename, 'cy')

    # Send it to movieyn
    propername = stripcrap(bufffirstpart.lower())
    result = movieyn(propername + ' (' + buffsecondpart + ')')

    if debug:
        printcolour('(filedetail) - ' + bufffirstpart, 'y')
        printcolour('(filedetail) - ' + result, 'y')

    # Check the result and make a choice
    if result != '-':     # MOVIE
        return['movie', filename, result, ' ']

    elif result == '-':       # SERIE

        # Format the secondpart  ------------------------------------

        buffsecondpart.replace('.', ' ')

        if (buffsecondpart.__len__()) == 3:
            buffsecondpart = '0' + buffsecondpart[:1]
        elif (buffsecondpart.__len__()) == 4:
            buffsecondpart = buffsecondpart[:2]
        else:
            # If there are not at least 2 digits, raise error.
            printcolour('ERROR:  There is an error with ' + filename, 'r')
            #bufffirstpart = "--- Manual Sort ---"
            #buffsecondpart = '00'
            return['error', filename, bufffirstpart, buffsecondpart]

        if (buffsecondpart.__len__() < 0) or (bufffirstpart.__len__() < 0):
            printcolour('ERROR:  Series: ' + bufffirstpart + ' -  Season: ' + buffsecondpart, 'r')
            return['error', filename, bufffirstpart, buffsecondpart]
        else:
            return['serie', filename, bufffirstpart, buffsecondpart]

# ======================================================================================================================
# Do copy and log activity
# ======================================================================================================================


def copandlog(source, destination, action):

    file = open(logfile, 'a')
    datetimenow = datetime.datetime.now()

    if action == 'msg':
        if verbose:
            #printcolour('-----------------------------', 'g')
            printcolour('File  : ' + source + ' requires renaming before it can be processed accurately\n', 'g')
            #printcolour('------------------------------', 'g')

        print >> file, '\r\n -------------------------------\n'
        print >> file, '\r\n' + datetimenow.ctime()
        print >> file, source + ' requires renaming before it can be processed accurately\n'
        erroritems.append(source)

    if action == 'cl':
        if verbose:
            #printcolour('-----------------------------', 'g')
            printcolour('File  : ' + source, 'g')
            printcolour('To    : ' + destination, 'g')
            #printcolour('------------------------------', 'g')
        shutil.copy(source, destination)

        print >> file, '\r\n -------------------------------'
        print >> file, '\r\n' + datetimenow.ctime()
        print >> file, '\r\nFrom: ' + source
        print >> file, '\r\nTo: ' + destination

    if action == 'l':
        print >> file, '\r\n -------------------------------'
        print >> file, '\r\n' + datetimenow.ctime()
        print >> file, '\r\nFrom: ' + source
        print >> file, '\r\nTo: ' + destination

    if action == 'el':

        if verbose:
            #printcolour('-----------------------------', 'g')
            printcolour('Rarfile         : ' + source, 'g')
            printcolour('Extracted To    : ' + destination, 'g')
            #printcolour('------------------------------', 'g')

        print >> file, '\r\n -------------------------------'
        print >> file, '\r\n' + datetimenow.ctime()
        print >> file, '\r\nRar File: ' + source
        print >> file, '\r\nExtracted To: ' + destination

    file.close()

# ======================================================================================================================
# Don't do again prevents the same shit from being scanned over and over and over and over and over and over.....
# ======================================================================================================================


def dontdoagain(logfilein, searchterm):

    searchfile = open(logfilein, 'a+')
    for line in searchfile:
        if searchterm in line:
            return 'f'
    searchfile.close()
    return 'nf'

# ======================================================================================================================
# Sanity Checking
# ======================================================================================================================


def sanity_check():

    # Check internet connectivity each time
    if is_connected() == 'connected':
        pass
    else:
        file = open(logfile, 'a')
        datetimenow = datetime.datetime.now()
        print >> file, '\r\n' + datetimenow.ctime()
        print >> file, '\r\nNo internet connection! Cannot function.  Error... Call Dave'
        file.close()
        printcolour('ERROR: No Internet Connection! ', 'r')
        sys.exit()

    # Check that all drives specified are available
    if drives_available() == 'OK':
        pass
    else:
        file = open(logfile, 'a')
        datetimenow = datetime.datetime.now()
        print >> file, '\r\n' + datetimenow.ctime()
        print >> file, '\r\nNot all drives are available! Cannot function.  Error... Call Dave'
        file.close()
        printcolour('ERROR: Not all drives specified are available!', 'r')
        sys.exit()

# ======================================================================================================================
# Change ownership and group
# ======================================================================================================================


def pinkslip(filename):

    uid = pwd.getpwnam(USERNAME).pw_uid
    gid = grp.getgrnam(USERNAME).gr_gid
    os.chown(filename, uid, gid)


# ======================================================================================================================
# Procedure for dealing with series.
# ======================================================================================================================


def seriecopy():

    DDrive = ''

    File_Name = FileInfo[1]
    SSName = FileInfo[2]
    SSSeason = FileInfo[3]

    for dirs in DestTree:

        i = dirs.lower().find(SSName.lower())

        if i > 0:
            DDrive = dirs[:i]
            break

    if DDrive == '':

        if directorycreator(os.path.join(defaultdest, SSName.title(), 'Season ' + SSSeason)):
            DDrive = defaultdest

    fullpath = os.path.join(DDrive, SSName.title(), 'Season ' + SSSeason)
    directorycreator(fullpath)
    serieitems.append(File_Name)
    if not(os.path.isfile(os.path.join(fullpath, File_Name))):
        copandlog(entry, fullpath, 'cl')
        pinkslip(fullpath + entry[entry.rfind(os.sep):])
    else:
        copandlog(entry, fullpath, 'l')

# ======================================================================================================================
# Procedure for dealing with movies.
# ======================================================================================================================


def moviecopy():

    MovieName = FileInfo[2]

    Folder = MovieName.replace(':', ' -')
    fullpath = os.path.join(moviedirectory[0], Folder)
    if directorycreator(fullpath):
        copandlog(entry, fullpath, 'cl')
        movieitems.append(MovieName)
        pinkslip(fullpath + entry[entry.rfind(os.sep):])
    else:
        copandlog(entry, fullpath, 'l')


# ======================================================================================================================
# Summary log
# ======================================================================================================================


def logsummary(item_extracted, item_serie, item_movie, item_error):

    file = open(summaryfile, 'a')
    datetimenow = datetime.datetime.now()

    print >> file, '\r\n-------------------------------------------------\r\n' + datetimenow.ctime()

    print >> file, '\r\nExtracted'
    while len(item_extracted) > 0:
        print >> file, '\r\n->' + (item_extracted.pop())

    print >> file, '\r\nSerie'
    while len(item_serie) > 0:
        print >> file, '\r\n->' + (item_serie.pop())

    print >> file, '\r\nMovies'
    while len(item_movie) > 0:
        print >> file, '\r\n->' + (item_movie.pop())

    print >> file, '\r\nErrors'
    while len(item_error) > 0:
        print >> file, '\r\n->' + (item_error.pop())

    file.close()

# ======================================================================================================================
# MAIN
# ======================================================================================================================

# Initialize variables

foldername = ''
DestTree = []
SSName = ''
SSSeason = ''
extracteditems = []
serieitems = []
movieitems = []
erroritems = []


# Do a sanity check ........
sanity_check()


what_os()

if verbose:
    printcolour('------------------------------------------------------------------------------------------------------', 'g')
    printcolour('Source Directory: ' + sourcedirectory + '\n -- Valid: ' + str(os.path.exists(sourcedirectory)), 'g')
    print(' ')
    printcolour('Serie Destination Directory 1 (Default): ' + seriedest1 + '\n -- Valid: ' + str(os.path.exists(destinationdirectory[0])), 'g')
    print(' ')
    printcolour('Serie Destination Directory 2: ' + seriedest2 + '\n -- Valid: ' + str(os.path.exists(destinationdirectory[1])), 'g')
    print(' ')
    printcolour('Movie Destination Directory 1 (Default): ' + moviedest1 + '\n -- Valid: ' + str(os.path.exists(moviedirectory[0])), 'g')
    print(' ')
    printcolour('Movie Destination Directory 2: ' + moviedest2 + '\n -- Valid: ' + str(os.path.exists(moviedirectory[1])), 'g')
    printcolour('------------------------------------------------------------------------------------------------------', 'g')


# ----------------------------------------------------------------------------------------------------------------------
# Deal with all the rar files first
# ----------------------------------------------------------------------------------------------------------------------

# Get the list of Rar files...
RarList = sniffer(sourcedirectory, '.rar', '')

for rarfile in RarList[0]:

    # Check if we hav already unzipped it...
    outputdir = rarfile[:rarfile.rfind(os.sep)]
    if dontdoagain(logfile, outputdir) == 'nf':
        patoolib.extract_archive(rarfile, outdir=outputdir)
        extracteditems.append(rarfile)
        copandlog(rarfile, outputdir, 'el')

# ----------------------------------------------------------------------------------------------------------------------
# Sorting carousel yay!
# ----------------------------------------------------------------------------------------------------------------------

# Get all the files that match the criteria
FileList = sniffer(sourcedirectory, mediatypes, exclusions)

# Get all the files to sort.
for dirs in destinationdirectory:
    try:
        for path, subdirs, files in os.walk(dirs):
            DestTree.append(path)
    except:
            printcolour('ERROR: main - ' + destinationdirectory + ' Error Occurred!', 'r')

for entry in FileList[0]:

    # Do a sanity check ........
    sanity_check()

    if debug == 1:
        printcolour('(main) Current Item: ' + entry, 'y')

    # Check if it has already been processed
    if dontdoagain(logfile, entry) == 'nf':

        # Check if it is a movie/serie
        FileInfo = filedetail(entry)

        if verbose:
            printcolour('(main) File Info: ' + FileInfo[0] + ' ' + FileInfo[1] + ' ' + FileInfo[2] + ' ' + FileInfo[3], 'y')

        # If the file is serie
        if FileInfo[0] == 'serie':

            seriecopy()

        # If the file is movie
        elif FileInfo[0] == 'movie':

            moviecopy()

        # If the file is unknown, try and probe the folder for a valid name.
        elif FileInfo[0] == 'error':

            # Get the parent folder name
            foldername = entry[:entry.rfind(os.sep)]

            if verbose:
                printcolour('Cannot determine serie or movie from file name.  Trying parent folder: ' + foldername, 'y')

            FileInfo = filedetail(foldername + '.ext')

            # If the file is serie
            if FileInfo[0] == 'serie':
                seriecopy()

            # If the file is movie
            elif FileInfo[0] == 'movie':
                moviecopy()

            # If it still cant find some info, log and continue
            elif FileInfo[0] == 'error':
                copandlog(entry, 'none', 'msg')
                continue

if len(extracteditems) > 0 or len(serieitems) > 0 or len(movieitems) > 0 or len(erroritems) > 0:
    logsummary(extracteditems, serieitems, movieitems, erroritems)
# '''''
