#MediaOrg

This is my attempt to sort out media (movies and series) once they have completed downloading
by moving them intelligently to predefined directories based on their type. Great to use with OSMC for the ultimate solution. 

Ideally, this is used in conjunction with Cron so that the sorting can happen autonomously

##Features

- Supports multiple destination paths
- Default destination for new series unless it finds an existing match
- Coded to work in Linux or Windows.
- Automatically unrars files
- Too easy to configure

##Process Overview

1. Source path scanned for rar files
2. rar files extracted to same directory
3. Source path scanned for video media type files
4. Each file inspeced and the following information gathered:
   -  Serie / Movie name (Determined from file name)
   -  Type (TV Series or Movie) (Bing search -> IMDb -> info - customizable)
5. Based on the type of file (movie or series), a destination path is created on the destination directory
   -  movie: destination/MovieName ([Year])/
   -  series: destination/SerieName/Season [season no]/
6. If the file doesn't exist in the destination directory, it is copied.


##Installation Process

1. Execute the following:
'''
sudo sh OSMCSetup_Base.sh && sudo sh OSMCSetup_Dependencies
'''

2. Edit MediaOrg.py 'Paths and Dirs'
3. Edit crontab:
'''
sudo crontab -e 
'''
For media or to run every hour, add this to the end:
''' 
59 * * * * python /*path to script*/MediaOrg.py
'''

