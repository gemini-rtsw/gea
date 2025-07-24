#!/usr/bin/python

"""Creates animations from m1 surface plots.
"""

import sys
import os
from GEATime import Time
import GEAVars

def createAnimation(dir=None):
    """
    Arguments:
    dir - Location of the images used to create an animation.
    """
    os.chdir(dir)

    # Ffmpeg expects input files to have a certain naming scheme. Link files to
    # new name, encode them, then remove links.
    import glob
    i = 0
    for d in sorted(glob.glob('*.png')):
        os.system('ln %s img%d.png' % (d, i))
        i = i + 1
    os.system('ffmpeg -sameq -f image2 -i img%%d.png %sAnimation%s.mpeg' % (os.path.split(dir)[-1], Time().string2))
    os.system('rm -f img[0-9]*.png')
    
def removeImageFiles(dir=None):
    os.chdir(dir)   #Might raise an exception.
    os.remove(os.path.join(dir, "*.png"))

def getDirName(topDir=None):
    """
    """
    now=Time()
    if int(now.hour)>=12:        #Passed noon.
        tomorrow=Time(now.seconds+Time.secPerDay)
        subDirName="%s-%s" % (now.string4, tomorrow.string4)
    else:
        yesterday=Time(now.seconds-Time.secPerDay)
        subDirName="%s-%s" % (yesterday.string4, now.string4)

    dataDir=os.path.join(GEAVars.path.fileSys.m1SurfacePlots, subDirName, topDir or '')
               
    return dataDir
    
def main(argv):

    for dir in (getDirName('axHydLC'), getDirName('axPnuLC'), getDirName('axPnuError')):
        createAnimation(dir)
        
if __name__=='__main__':

    main(sys.argv)
