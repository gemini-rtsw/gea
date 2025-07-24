#!/usr/bin/python
"""Script which creates a surface plot of the primary. It prompts for data using EPICS' caGet.

Requirements:
- Need caGet to be in the path.

This is a specialized script and is currently not a part of pyGEA. In the future, could extend DataExtractor
to get live data via caGet and GEAPlot to allow pcolor()/imshow() plots.

To add a new surface plot, simply add another entry to gPlotsToMake. 

"""
from specialized.common import gDiskWrite, gUseImshow, gDataDir, PlotToMake, caGet, Algorithms
import sys
import os
from GEATime import Time
import GEAVars          

if gDiskWrite:
    import matplotlib
    matplotlib.use('Agg')            #For writting to file.  Using the Agg backend. Need to do this before importing other matplotlib stuff.
    
from matplotlib.pylab import *
from matplotlib.ticker import NullLocator
import numpy.numarray
import numpy.linalg

import GEAPlot
GEAPlot.matplotlibConfig()    
   
#Make sure have proper environment setup so that caGet can operate. 
if not GEAVars.environ.has_key('EPICS_CA_ADDR_LIST'):
    raise ValueError('Need EPICS_CA_ADDR_LIST to be defined')

#Positions of the actuators (x, y).
gActPos=[
[0.2331, -0.8698],
[0.6367, -0.6367],
[0.8698, -0.2331],
[0.8698, 0.2331],
[0.6367, 0.6367],
[0.2331, 0.8698],
[-0.2331, 0.8698],
[-0.6367, 0.6367],
[-0.8698, 0.2331],
[-0.8698, -0.2331],
[-0.6367, -0.6367],
[-0.2331, -0.8698],
[0.2824, -1.6018],
[0.8132, -1.4086],
[1.246, -1.0455],
[1.5284, -0.5563],
[1.6265, 0],
[1.5284, 0.5563],
[1.246, 1.0455],
[0.8132, 1.4086],
[0.2824, 1.6018],
[-0.2824, 1.6018],
[-0.8133, 1.4086],
[-1.246, 1.0455],
[-1.5284, 0.5563],
[-1.6265, 0],
[-1.5284, -0.5563],
[-1.246, -1.0455],
[-0.8132, -1.4086],
[-0.2824, -1.6018],
[0.3074, -2.3352],
[0.9014, -2.1761],
[1.4339, -1.8687],
[1.8687, -1.4339],
[2.1761, -0.9014],
[2.3352, -0.3074],
[2.3352, 0.3074],
[2.1761, 0.9014],
[1.8687, 1.4339],
[1.4339, 1.8687],
[0.9014, 2.1761],
[0.3074, 2.3352],
[-0.3074, 2.3352],
[-0.9014, 2.1761],
[-1.4339, 1.8687],
[-1.8687, 1.4339],
[-2.1761, 0.9014],
[-2.3352, 0.3074],
[-2.3352, -0.3074],
[-2.1761, -0.9014],
[-1.8687, -1.4339],
[-1.4339, -1.8687],
[-0.9014, -2.1761],
[-0.3074, -2.3352],
[0.3158, -3.0048],
[0.9337, -2.8735],
[1.5107, -2.6166],
[2.0217, -2.2453],
[2.4444, -1.7759],
[2.7602, -1.2289],
[2.9554, -0.6282],
[3.0214, 0],
[2.9554, 0.6282],
[2.7602, 1.2289],
[2.4444, 1.7759],
[2.0217, 2.2453],
[1.5107, 2.6166],
[0.9337, 2.8735],
[0.3158, 3.0048],
[-0.3158, 3.0048],
[-0.9337, 2.8735],
[-1.5107, 2.6166],
[-2.0217, 2.2453],
[-2.4444, 1.7759],
[-2.7602, 1.2289],
[-2.9554, 0.6282],
[-3.0214, 0],
[-2.9554, -0.6282],
[-2.7602, -1.2289],
[-2.4444, -1.7759],
[-2.0217, -2.2453],
[-1.5107, -2.6166],
[-0.9337, -2.8735],
[-0.3158, -3.0048],
[0.328, -3.749],
[0.974, -3.6351],
[1.5904, -3.4107],
[2.1585, -3.0827],
[2.6611, -2.6611],
[3.0827, -2.1585],
[3.4107, -1.5904],
[3.6351, -0.974],
[3.749, -0.328],
[3.749, 0.328],
[3.6351, 0.974],
[3.4107, 1.5904],
[3.0827, 2.1585],
[2.6611, 2.6611],
[2.1585, 3.0827],
[1.5904, 3.4107],
[0.974, 3.6351],
[0.328, 3.749],
[-0.328, 3.749],
[-0.974, 3.6351],
[-1.5904, 3.4107],
[-2.1585, 3.0827],
[-2.6611, 2.6611],
[-3.0827, 2.1585],
[-3.4107, 1.5904],
[-3.6351, 0.974],
[-3.749, 0.328],
[-3.749, -0.328],
[-3.6351, -0.974],
[-3.4107, -1.5904],
[-3.0827, -2.1585],
[-2.6611, -2.6611],
[-2.1585, -3.0827],
[-1.5904, -3.4107],
[-0.974, -3.6351],
[-0.328, -3.749]]

class MultiQuadricInterpolator:
    def __init__ (self, x, y, z, rsq):
        """MultiQuadricInterpolator(x, y, z, rsq=0.8)
           Applies a simple version of Hardy's multiquadric fit algorithm.
           Then use mqsolve to interpolate z = f(x, y)
           where data given was z(i) = f(x(i), y(i)).
           rsq is a tuning parameter that in theory depends
           on x and y.
 
           Caution. This algorithm involves solving an n by n
           system where n is the length of the inputs x, y, z.
           It has a condition number that grows with n.
           This algorithm should probably not be used for more than
           500 points or so.
        """
        x1 = ravel(x)
        y1 = ravel(y)
        z1 = ravel(z)
        n = len(x1)
        if n != len(y1) or n != len(z1):
            raise ValueError, 'mqfit inputs must all have same length (' + str(len(x1)) + ', ' + str(len(y1)) + ', ' + str(len(z1)) + ').'
        t = outer(x1, ones(n))
        xa = transpose(t) - t
        t = outer(y1, ones(n))
        ya = transpose(t) - t
        del t
        aa = sqrt(xa**2 + ya**2 + rsq)
        del xa, ya
        self.alpha = solve(aa, z1)
        self.x = x1
        self.y = y1
        self.rsq = rsq
        
    def interpolate (self, xp, yp):
        """Given the arrays xp, yp, apply the fit previously calculated
           to each point xp(i), yp(i).
        """
        f = zeros(shape(xp), np.float)
        xp = array(xp, copy=0)
        yp = array(yp, copy=0)
        if shape(f) != shape(yp):
            raise ValueError, 'xp and yp must have same shape.'
        n = len(self.alpha)
        for k in range(n):
            f += self.alpha[k] * sqrt((xp-self.x[k])**2 + (yp-self.y[k])**2 + self.rsq)
        return f
    
def getData(chanFileNameTup, algorithm=None):
    """Will throw exceptions of algorithm cannot process data.
    """
    if len(chanFileNameTup)<1:
        raise RuntimeError('No data to get.\n')
    
    #Always need an algorithm defined if dealing with multiple data
    if algorithm is None and len(chanFileNameTup)>1:
        raise RuntimeError('Have no algorithm defined to deal with multiple data sets.\n')
    
    #First need to get data from EPICS for every file in the chanFileNameTup
    dataTup=map(lambda x: array(caGet(x)), chanFileNameTup)
        
    if algorithm is not None:
        z=algorithm(*dataTup)
    else:
        #Only have one item in the tuple; no need to apply an algorithm.
        z=dataTup[0]
        
    actNames=[str(i) for i in xrange(1, len(gActPos)+1)]
    
    actPos=array(gActPos)
    xp=actPos[:,0]
    yp=actPos[:,1]
    
    return actNames, xp, yp, z
    
def drawLegend(yMin, yMax, useAxes=None):
    """Adds the legend (ie. the colored vertical stripe showing the  number<->color correspondence).
    """
    if useAxes is None:
        theAxes=gca() 
    else:
        theAxes=axes(useAxes)
        
    dy=float(abs((yMax)-(yMin)))/256.0
    x=arange(0,50)    #When this is smaller, imshow() does not display the legend properly.
    y=arange(yMin,yMax,dy)

    Xi,Yi=meshgrid(x,y)
    
    if gUseImshow:
        #Have to adjust the rows a little (so that row[0] is row[n-1], row[1] is row[n-2], and so on). This seems to be
        #a difference between pcolor() and imshow()
        Yi=take(Yi, range(shape(Yi)[0]-1, -1, -1))

        jet = cm.get_cmap('jet', 65353)
        imshow(Yi, cmap=jet, extent=(min(x), max(x), yMin, yMax))

    else:
        pcolor(Xi, Yi, Yi, shading='flat')
    
    theAxes.xaxis.set_major_locator(NullLocator())
    theAxes.set_ylim([yMin,yMax])
    
    return theAxes
    
def drawMirror(actNames, xp, yp, useAxes=None):
    """Draws the mirror, the actuators, and fills the regions outside the mirror white. 
    When using pcolor for plotting, this function should be called after plotData().
    This is to make sure that the reqions outside the mirror get overwritten properly.
    """
    if useAxes is None:
        theAxes=gca()
    else:
        theAxes=axes(useAxes)
         
    #Draw the mirror boundaries
    arg=arange(0,2*pi,0.01)
    rad=ones(shape=(len(arg),))
    ri=rad*0.6 #Inner
    ro=rad*4   #Outer
        
    #Draw the inner edge and get rid of data spilling outside the mirror (on the inner edge).
    xx, yy=ri*cos(arg), ri*sin(arg)
    plot(xx, yy, color='k')
    fill(xx, yy, 'w')
    
    #Draw the outer edge and get rid of data spilling outside the mirror (on the outer edge).
    xx, yy=ro*cos(arg), ro*sin(arg)
    half=len(xx)/2
    plot(xx, yy, color='k')
    fill(concatenate((xx[0:half], array([-4,4])), 1), concatenate((yy[0:half], array([4,4])), 1), 'w')  #Top half
    fill(concatenate((xx[half:], array([4,-4])), 1), concatenate((yy[half:], array([-4,-4])), 1), 'w')  #Bottom half

    #Draw spokes.
    arg=array([7*pi/6, pi/6])
    ro=4*ones(shape=(len(arg),))
    xx, yy=ro*cos(arg), ro*sin(arg)
    plot(xx, yy, color='k', linestyle='--')

    arg=array([pi/2, 3*pi/2])
    xx, yy=ro*cos(arg), ro*sin(arg)
    plot(xx, yy, color='k', linestyle='--')
    
    arg=array([5*pi/6, 11*pi/6])
    xx, yy=ro*cos(arg), ro*sin(arg)
    plot(xx, yy, color='k', linestyle='--')
    
    #Name sectors.
    secNames=['2','3','4','5','6','1']
    arg=array([0, pi/3, 2*pi/3, pi, 4*pi/3, 5*pi/3])
    ro=0.4*ones(shape=(len(arg),))
    xx, yy=ro*cos(arg), ro*sin(arg) 
    for x,y,name in zip(xx, yy, secNames):
        text(x-0.09, y-0.1, name, fontsize=10, color='r')

    #Draw the actuators.s
    plot(xp,yp,'ok', markerfacecolor=None)    
    for x,y,name in zip(xp, yp, actNames):
        text(x+0.05, y+0.05, name, fontsize=8)
 
    return theAxes

def plotData(x, y, z, rsq=0.2, useAxes=None, minMax=None):
    """Returns a tuple of the min and max values in the image.
    """
    if not useAxes is None:
        theAxes=axes(useAxes)
    else:
        theAxes=gca()  
    
    #Create a mesh
    xi=linspace(-4,4,200)
    yi=linspace(-4,4,200)
    [Xi,Yi]=meshgrid(xi,yi)

    #Interpolate the data on the whole grid.
    Zi=MultiQuadricInterpolator(x, y, z, rsq).interpolate(Xi,Yi)
      
    #Setting some non-visible values to a known min/max, allows for constant scales accross different images
    # (as long as the given min/max are extremas)
    if minMax is not None and len(minMax)==2:
        Zi[0][0]=minMax[0]
        Zi[0][1]=minMax[1]
      
    if gUseImshow:
        #Have to adjust the rows a little (so that row[0] is row[n-1], row[1] is row[n-2], and so on). This seems to be
        #a difference between pcolor() and imshow()
        Zi=take(Zi, range(shape(Zi)[0]-1, -1, -1))
    
        jet = cm.get_cmap('jet', 65353)
        imshow(Zi, cmap=jet, extent=(-4, 4, -4, 4))
    else:
        pcolor(Xi, Yi, Zi, shading='flat')

    theAxes.xaxis.set_major_locator(NullLocator())
    theAxes.yaxis.set_major_locator(NullLocator())  
    
    ravelZi=ravel(Zi)
    
    return (min(ravelZi), max(ravelZi))

def setTitle(theTitle=None, useAxes=None):
    
    if not useAxes is None:
        theAxes=axes(useAxes)
    else:
        theAxes=gca() 
    
    if theTitle is None:
        #Should generate dynamically.. say based on current time.
        theTitle='title...'
    
    title(theTitle)
    
    return theAxes
        
def makePlot(plotToMake):

    actNames, xp, yp, z=getData(chanFileNameTup=plotToMake.chanFileNameTup, algorithm=plotToMake.algorithm) #xp, yp  are the positions of the actuators.

    #Set up the image structure.
    fig=figure(1, figsize=(6,5), facecolor='w', edgecolor='w', dpi=150) #dpi here only works when using show(). For saving see bottom of this function.
    clf() #Probably redundant.
    mainAxes=axes([0.125, 0.05, 0.655, 0.83], frameon=0) 
    legendAxes=axes([0.85, 0.05, 0.05, 0.83])
      
    minZi, maxZi=plotData(xp, yp, z, useAxes=mainAxes, minMax=plotToMake.minMax)
  
    drawMirror(actNames, xp, yp, useAxes=mainAxes)
    drawLegend(minZi, maxZi, useAxes=legendAxes) 

    setTitle(plotToMake.title, useAxes=mainAxes)
    
    if gDiskWrite:
        savefig(os.path.join(plotToMake.dir, plotToMake.name), dpi=plotToMake.dpi)
        
        if plotToMake.nameLarge:
            savefig(os.path.join(plotToMake.dir, plotToMake.nameLarge), dpi=plotToMake.dpiLarge)
    else:
        show()
        
def main():

    #To create more plots, add entries to the list below:
    plotsToMake=[PlotToMake(('axHydLC.channels',), 'axHydLC.png', 'axHydLC.Large.png', 'Hydraulic Loadcells'),
                 PlotToMake(('axPnuLC.channels',), 'axPnuLC.png', 'axPnuLC.Large.png', 'Pneumatic Loadcells')
                ]

    for item in plotsToMake:
        makePlot(item)
    
#Optimizing using psyco
if GEAVars.usePsyco:
    import psyco
    psyco.bind(MultiQuadricInterpolator)
    
if __name__=='__main__':

    main()
    
