#MediaOrg

This program is designed to monitor completed downloads
- Movies
- Series

##Process Overview

Source path scanned for rar files

from there, each file is inspected, and using an inet search, and then based

This is my attempt to sort out media (movies and series) once they have completed downloading
by moving them intelligently to predefined directories based on their type.
The files are picked up from the specified source directory and inspected.  The first test is to check IMdb to see whether it is a movie, if it is not found, the file is assumed to be a series.
In either case, the correct path is built based on the supplied destination directories and the file is moved.  For series, multiple destinations can be defined, with one being the default (for cases 
where a new series is added).  All other series that already have a directory will be picked up 
and sorted accordingly.

Ideally, this is used in conjunction with Cron so that the sorting can happen autonomously
Great to use with OSMC for the ultimate solution.
