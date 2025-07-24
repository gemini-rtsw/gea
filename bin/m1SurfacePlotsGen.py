#!/usr/bin/python

import sys 
import os
import time
from GEATime import Time
from GEAGeneral import naming
from specialized.m1Surface import PlotToMake, Algorithms, makePlot
import GEAVars

def initData():
    
    #Generate the names of the images. 
    randName1=naming.genName()
    randName2=naming.genName()
    randName3=naming.genName()
    
    imageName1="%s%s%s" % ('axHydLC', randName1, '.png')
    imageName2="%s%s%s" % ('axPnuLC', randName2, '.png')
    imageName3="%s%s%s" % ('axPnuLC', randName3, '.png')
    
    plotsToMake=[
                PlotToMake((os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/axHydLC.channels'),), 
                            imageName1, 
                            '',             #Do not need a large version of the plot
                            'axHydLC',
                            dpi=100,
                            dir=createDir(topDir='axHydLC'),  #Where to save the plot images to.
                            minMax=(100, 1000)),
                PlotToMake((os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/axPnuLC.channels'),), 
                           imageName2, 
                           '',             #Do not need a large version of the plot
                           'axPnuLC',
                           dpi=100,
                           dir=createDir(topDir='axPnuLC'),  #Where to save the plot images to.
                           minMax=(-350, 350)),
                PlotToMake((os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/axPnuDmd.channels'),
                            os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/axPnuLC.channels')), 
                           imageName3, 
                           '',
                           'axPnuError',
                           dpi=100,
                           dir=createDir(topDir='axPnuError'),  #Where to save the plot images to.
                           minMax=(-5, 5),
                           algorithm=Algorithms.diff12)
                ]
                
    return plotsToMake

        
def createDir(topDir=None):
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
        
    if not os.path.isdir(dataDir):
        os.makedirs(dataDir, mode=0777)
        
    return dataDir
    
def generatePlots():
        
    plotsToMake=initData()
        
    for item in plotsToMake:
        item.title="%s Generated: %s" % (item.title, Time().string1)
        makePlot(item)
            
def timedGeneratePlots():

    for i in xrange(120):
        generatePlots()
        time.sleep(2)
            
def usage():
    print "Usage:....\n"
            
def main(argv):

    if len(argv)>1:
        if argv[1]=='timed':
            timedGeneratePlots()
        else:
            usage()
    else:
        generatePlots()

if __name__=='__main__':

    main(sys.argv)
