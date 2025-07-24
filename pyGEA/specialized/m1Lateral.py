#!/usr/bin/python

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

import GEAPlot
GEAPlot.matplotlibConfig() 

#This corresponds to the order of which the data is in when retrieved.
gLcNames=[
'01',
'02',
'03',
'04',
'05',
'06',
'07',
'08',
'09',
'10',
'11',
'12',
'13',
'14',
'15',
'+X-Y',
'16',
'17',
'18',
'19',
'20',
'21',
'22',
'+X+Y',
'23',
'24',
'25',
'26',
'27',
'28',
'29',
'30',
'31',
'32',
'33',
'34',
'35',
'36',
'37',
'38',
'39',
'40',
'41',
'42',
'43',
'44',
'45',
'-X+Y',
'46',
'47',
'48',
'49',
'50',
'51',
'52',
'-X-Y',
'53',
'54',
'55',
'56',
'57',
'58',
'59',
'60']

###index Name
##0 01
##1 02
##2 03
##3 04
##4 05
##5 06
##6 07
##7 08
##8 09
##9 10
##10 11
##11 12
##12 13
##13 14
##14 15
##
##16 16
##17 17
##18 18
##19 19
##20 20
##21 21
##22 22
##24 23
##25 24
##26 25
##27 26
##28 27
##29 28
##30 29
##31 30
##
##32 31
##33 32
##34 33
##35 34
##36 35
##37 36
##38 37
##39 38
##40 39
##41 40
##42 41
##43 42
##44 43
##45 44
##46 45
##
##48 46
##49 47
##50 48
##51 49
##52 50
##53 51
##54 52
##56 53
##57 54
##58 55
##59 56
##60 57
##61 58
##62 59
##63 60
##
##15 +X-Y
##23 +X+Y
##47 -X+Y
##55 -X-Y

#This shows the order of which is to be used when displaying the data. 
gLcDisplayIndex=[
0,
1,
2,
3,
4,
5,
6,
7,
8,
9,
10,
11,
12,
13,
14,
15,
63,
62,
61,
60,
59,
58,
57,
56,
54,
53,
52,
51,
50,
49,
48,
55,
31,
30, 
29, 
28, 
27, 
26, 
25, 
24, 
22, 
21, 
20, 
19, 
18, 
17, 
16, 
23, 
32, 
33, 
34, 
35, 
36, 
37, 
38, 
39, 
40, 
41, 
42, 
43, 
44, 
45, 
46, 
47
]

#Make sure have proper environment setup so that caGet can operate. 
if not GEAVars.environ.has_key('EPICS_CA_ADDR_LIST'):
    raise ValueError('Need EPICS_CA_ADDR_LIST to be defined')

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
    
    return z
    
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
    
    #Have to adjust the rows a little (so that row[0] is row[n-1], row[1] is row[n-2], and so on). This seems to be
    #a difference between pcolor() and imshow()
    Yi=take(Yi, range(shape(Yi)[0]-1, -1, -1))

    imshow(Yi, cmap=cm.get_cmap('jet', 65353), extent=(min(x), max(x), yMin, yMax))

    theAxes.xaxis.set_major_locator(NullLocator())
    theAxes.set_ylim([yMin,yMax])
    
    return theAxes
    
def plotDataSymmetric(z, useAxes=None, minMax=None):
    """Returns a tuple of the min and max values in the image.
    """
    if not useAxes is None:
        theAxes=axes(useAxes)
    else:
        theAxes=gca()  
    
    #So that can easily adjust later.
    size=64
    itemsPerCol=4
    itemsPerRow=16
    pixPerItem=8
    pixPerRow=itemsPerRow*pixPerItem
    pixPerColumn=itemsPerCol*pixPerItem
    
    #Want to rearange z and gLcNames according to the order provided in gLcDisplayIndex
    z, lcNames=[z[i]  for i in gLcDisplayIndex], [gLcNames[i]  for i in gLcDisplayIndex]
    
    Zi=reshape(z, (itemsPerCol,itemsPerRow))   
    Zi=repeat(Zi, pixPerItem*ones(Zi.shape[0]))         # Turn each enty to pixPerItem entries in y dim.
    Zi=repeat(Zi, pixPerItem*ones(Zi.shape[1]),1)       # Turn each enty to pixPerItem entries in x dim.
 
    #Setting some non-visible values to a known min/max, allows for constant scales accross different images
    # (as long as the given min/max are extremas)
    if minMax is not None and len(minMax)==2:
        Zi[0][0]=minMax[0]
        Zi[0][1]=minMax[1]
    
    #Fill areas between data with white space so that we can add text later.
    for i in range(itemsPerCol):
        #Horizontal stripes
        fill([0,pixPerItem*itemsPerRow,pixPerItem*itemsPerRow,0], [i*pixPerItem, i*pixPerItem ,i*pixPerItem+3,i*pixPerItem+3], 'w', edgecolor='w') 
    
    for i in range(itemsPerRow):
        #Vertical stripes
        fill([i*pixPerItem, i*pixPerItem+1,i*pixPerItem+1, i*pixPerItem], [0, 0,  pixPerItem*itemsPerCol ,pixPerRow*itemsPerCol], 'w', edgecolor='w') 
        
    #Add the names of the cells. 
    for i in range(itemsPerCol):
        for j in range(itemsPerRow):
            index=((itemsPerCol-1-i)*itemsPerRow)+j    #This is hackish.. going backwards...
            #print '<br>', index
            text(j*pixPerItem+5,  i*pixPerItem+5.0, "%s" % (z[index],), color='w',  fontsize=8,  horizontalalignment='center', verticalalignment='center')
            text(j*pixPerItem+3.2,  i*pixPerItem+7, lcNames[index], color='w', fontsize=12, family='monospace', horizontalalignment='center', verticalalignment='center')
    
            if index <16 or 31<index<48:
                #Add the differences.
                text(j*pixPerItem+3,  i*pixPerItem+1.4, "Diff:\n%s" % (z[index]-z[index+16],), fontsize=8, family='monospace', horizontalalignment='center', verticalalignment='center')

    imshow(Zi, interpolation="nearest", cmap=cm.get_cmap('jet', 65353))
    
    theAxes.xaxis.set_major_locator(NullLocator())
    theAxes.yaxis.set_major_locator(NullLocator())  
    
    ravelZi=ravel(Zi)
    
    return (min(ravelZi), max(ravelZi))
    
def plotDataDMScreen(z, useAxes=None, minMax=None):
    """Returns a tuple of the min and max values in the image.
    """
    if not useAxes is None:
        theAxes=axes(useAxes)
    else:
        theAxes=gca()  
        
    #So that can easily adjust later.
    size=64
    itemsPerSide=8
    pixPerItem=6
    pixPerSide=itemsPerSide*pixPerItem

    Zi=reshape(z, (itemsPerSide,itemsPerSide))   #Create an itemsPerSidexitemsPerSide matrix
    Zi=repeat(Zi, pixPerItem*ones(Zi.shape[0]))         # Turn each enty to pixPerItem entries in y dim.
    Zi=repeat(Zi, pixPerItem*ones(Zi.shape[1]),1)       # Turn each enty to pixPerItem entries in x dim.
 
    #Setting some non-visible values to a known min/max, allows for constant scales accross different images
    # (as long as the given min/max are extremas)
    if minMax is not None and len(minMax)==2:
        Zi[0][0]=minMax[0]
        Zi[0][1]=minMax[1]
    
    #Fill areas between data with white space so that we can add text later.
    for i in range(itemsPerSide):
        #Horizontal stripes
        fill([0,pixPerSide,pixPerSide,0], [i*pixPerItem, i*pixPerItem ,i*pixPerItem+2,i*pixPerItem+2], 'w', edgecolor='w') 
        #Vertical stripes
        fill([i*pixPerItem, i*pixPerItem+1,i*pixPerItem+1, i*pixPerItem], [0, 0, pixPerSide ,pixPerSide], 'w', edgecolor='w') 
        
    #Add the names of the cells. 
    for i in range(itemsPerSide):
        for j in range(itemsPerSide):
            index=((itemsPerSide-1-i)*itemsPerSide)+j  
            text(j*pixPerItem+3.5,  i*pixPerItem+1.5, "%s" % (z[index],), fontsize=5,  horizontalalignment='center', verticalalignment='center')
            text(j*pixPerItem+3.5,  i*pixPerItem+4, gLcNames[index], color='w', fontsize=8, family='monospace', horizontalalignment='center', verticalalignment='center')
    
    imshow(Zi, interpolation="nearest", cmap=cm.get_cmap('jet', 65353))
    
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

    #Set up the image structure - depends on the type of view.
    if plotToMake.view=='Symmetric':
        figSize=(10.5,3.2)
        mainAx=[0.025, 0.05, 0.88, 0.83]
        legendAx=[0.95, 0.05, 0.03, 0.83]
        plotterFunc=plotDataSymmetric
    else:
        figSize=(6,5)
        mainAx=[0.025, 0.05, 0.80, 0.83]
        legendAx=[0.90, 0.05, 0.05, 0.83]
        plotterFunc=plotDataDMScreen

    fig=figure(1, figsize=figSize, facecolor='w', edgecolor='w', dpi=150) #dpi here only works when using show(). For saving see bottom of this function.    
    clf() #Probably redundant.
    
    mainAxes=axes(mainAx, frameon=0) 
    legendAxes=axes(legendAx)
              
    minZi, maxZi=plotterFunc(z=getData(plotToMake.chanFileNameTup), useAxes=mainAxes, minMax=plotToMake.minMax)
  
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
    plotsToMake=[PlotToMake(('lateralLC.channels',), 'lateralLC.png', 'lateralLC.Large.png', 'Lateral Load Cells'),
                         ]
    
    for item in plotsToMake:
        makePlot(item)
    
if __name__=='__main__':

    main()
    
