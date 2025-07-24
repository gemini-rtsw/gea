#!/usr/bin/env python

import math
import datetime
import time
import pytz

# Need this order for things to work properly - note that some rc options
# (example numerix) need should be set in the /usr/share/matplotlib/matplotlibrc
# file directly. matplotlibConfig() only sets up stuff that can be easily set
# after modules already imported.

import matplotlib
matplotlib.use('Agg')  #For writting to file.  Using the Agg backend. Need to do this before importing other matplotlib stuff.
from matplotlib.pylab import *
import GEAPlot
GEAPlot.matplotlibConfig()

from GEADataHandler import RemedyDataExtractor
from GEATime import Time
import GEAVars
from GEAHtml import HTMLDynTable, HTMLSimpleCont 
from GEAGeneral import util

from GEAMetrics import getDataFromRemedy

gMkColors  = ((0.0, 0.0, 1.0 ), (1.0, 0.0,  0.0 ))
gCpColors  = ((0.0, 0.5, 0.0 ), (0.0, 0.75, 0.75))
gColors    = ((0.6, 0.1, 0.25), (0.6, 0.75, 0.25))
gGoalColor =  (1.0, 1.0, 0.0 )
Float64 = 'd'

def multiBarChart(dataList, xTickLabels=None, colorGen=None, width=0.5, aTitle=None, yLabel=None, xLabel=None, indOffset=0):
    """Need len(dataList[n])==len(xTickLabels)
    where n is the number of data arrays.

    Also need: len(nameList)==len(dataList) (if colorList not None)

    """

    n = len(dataList[0])
    ind = arange(n) + indOffset

    if colorGen is None:
        colorGen = GEAPlot.Colors()    #use colorGen.next() to get a color tuple

    lines = []
    sumArray = zeros(n)

    for data in dataList:
        lines.append(bar(ind - width / 2.0, data, width, color = colorGen.next(), bottom = sumArray))
        sumArray = sumArray + data

    if xTickLabels is not None: xticks(ind, xTickLabels , rotation=90) 
    if aTitle      is not None: title(aTitle)
    if yLabel      is not None: ylabel(yLabel)
    if xLabel      is not None: xlabel(xLabel)

    return lines


def addGeaStamp():
    kwargs={}
    kwargs['horizontalalignment'] = 'center'
    kwargs['verticalalignment']   = 'center'

    font = {'family':'serif', 'color':'k', 'weight':'normal','size':8,}
    text(-0.072, -0.1 ,"GEA V%s" % GEAVars.versionStr,  font, **kwargs)

def cumAve(dataList):
    """
    Returns a list with cumulitve averages.
    So input [x1, x2, x3, ...] will return [x1, ave(x1,x2), ave(x1,x2,x3), ...]
    example:
    input=[2,4,8] gives output=[2, 3, 7]
    """
    #could call mean on each sub array... but would be re-summing each time.
    sums=add.accumulate(dataList)
    return  sums/arange(1, len(sums)+1)

def drawLegend(lines, names, **kwargs):

    return figlegend(tuple([i[0] for i in lines]), tuple(names), loc=8, **kwargs)  #bottom center


def ave(dataArray, numPoints):
    """prototype.. gotta rewrite this to make it fast... probably one-liner with numarray.
    """
    n=len(dataArray)
    #Size of our new array.
    nNew=int(math.ceil(float(n)/float(numPoints)))
    newArray=[]
    j=0
    for i in range(1, nNew+1):
        #newArray.append(dataArray[j:i*numPoints].mean())
        newArray.append(mean(dataArray[j:i*numPoints]))
        j=i*numPoints
    return array(newArray)

def _getSortedKeys(d):
    keys= d.keys()
    keys.sort()
    return keys

def _getSelKeys(d, exceptList):
    return _getSelItems(d.keys(), exceptList)

def _getSelItems(l, exceptList):
    return [i for i in l if i not in exceptList]

def _pickBestNLCandidate(tup):
    """Lets try to pick which nightlog is more likely to be the valid one
    """
    # Here want to do some checks on which is valid...
    # Should come up with something clever here based on current cases.
    #if item[dataKeysDict['tha']]>timeStampDict[s][timeStamp][dataKeysDict['tha']]:
    #    #have cases where ssa/astro forgot input tha.
    #        timeStampDict[s][timeStamp]=item
    return 1





def laserMetrics(theSite, plotType=None, startTime=None, endTime=None, horizLines=None,
               time2Ave=None, fileName=None, dataFileName=None, dpi=75, stream=sys.stdout,
               theTitle=None, yLabel=None, yMin=None, yMax=None, addStamp=False, units='Hours'):
    """Heavy duty on memory allocation... should stream-line a little...
    Data needs lots of massaging/manipulating before can use.  
    """

    # Throw away HH:MM:SS because there's only one NL per day. This fixes tz issues.

    # Keys for things that come from the NL table.

    dataKeysDict = dict(tha   = 'Total hours',	
                        shut  = 'Shuttered',
                        blank = 'Blanket Closures',
                        ut    = 'UT Date')

    rKeys=tuple(dataKeysDict.values())

    if theSite == 'MK' or theSite == 'CP':
        site = theSite
    elif theSite == 'ave(MK,CP)' or theSite == 'MK_and_CP':
        site = ''   #Get data for both'
    else:
        raise RuntimeError("Don't understand site %s" % theSite)

    #Will store multi-site query results in the form. For example:
    #{'MK':<data>, 'CP':<data>, 'ave(MK,CP)':<data>}

    qResDict      = dict()
    timeStampDict = dict()

    if theSite == 'MK' or theSite == 'CP':
        qResDict[theSite] = getDataFromRemedy(rKeys=rKeys, site=site, startTime=startTime, endTime=endTime)

        timeStampDict = {theSite:{}}
        dataDict      = {theSite:{}}
    else:
        #Could make one request, and reorganize data after...
        qResDict['MK'] = getDataFromRemedy(rKeys=rKeys, site='MK', startTime=startTime, endTime=endTime)
        qResDict['CP'] = getDataFromRemedy(rKeys=rKeys, site='CP', startTime=startTime, endTime=endTime)

        timeStampDict = {'MK':{},'CP':{}}
        dataDict      = {'MK':{},'CP':{}}

    for s, dataList in qResDict.items():
        #s is a site and dataList is a list of dictionaries with remedy data:
        #[{'key1':<val>, 'key2':<val>...}, {'key1':<val>, ....}..]
        for item in dataList:

            if 'shut' in dataKeysDict.keys():
                if item[dataKeysDict['shut']] is None:
                    item[dataKeysDict['shut']] = 0.0

            if 'blank' in dataKeysDict.keys():
                if item[dataKeysDict['blank']] is None:
                    item[dataKeysDict['blank']] = 0.0

            timeStamp=Time(item[dataKeysDict['ut']], site=s).string1[:10]

            badData=False
            for key in item.keys():
                if item[key] is None:
                    stream.write('Found invalid (None) data in the entry for %s %s %s; <strong>skipping</strong>.\n' % (key, item[key], timeStamp))

            """
            for value in item.values():
                if value is None:
                    stream.write('Found invalid (None) data in the entry for %s; <strong>skipping</strong>.\n' % timeStamp)
                    badData=True
                    break
            """

            if badData:
                continue

            if timeStampDict[s].has_key(timeStamp):
                stream.write('Found duplicate %s nightlog entry for %s; <strong>picking one</strong>\n' % (s, timeStamp) )

                #Have multiple entries for the same date. We have to try to be clever, and pick which one
                #is more likely to be valid, and which was a 'misfire' on the astronomer's part.
                tup=(item, timeStampDict[s][timeStamp])
                timeStampDict[s][timeStamp]=tup[_pickBestNLCandidate(tup)]
            else:
                #Don't have a data from this date yet; add it.
                timeStampDict[s][timeStamp]=item

    #If creating plots with data from both sites (MK_and_CP or ave(MK,CP)), make
    #sure that for each day have data at both sites. If for some dates, only have data
    #for one of the sites, disregard data from that date.

    if theSite=='ave(MK,CP)' or theSite=='MK_and_CP':
        toDelList=[]
        for timeStamp in timeStampDict['MK'].keys():
            if not timeStampDict['CP'].has_key(timeStamp):
                #toDelList.append(timeStamp)
                del(timeStampDict['MK'][timeStamp])
                stream.write("Data for %s only found at MK and not at CP; <strong>skipping</strong>.\n" % timeStamp)

        #for i in toDelList:
        #    del(timeStampDict['MK'][i])

        toDelList=[]
        for timeStamp in timeStampDict['CP'].keys():
            if not timeStampDict['MK'].has_key(timeStamp):
                toDelList.append(timeStamp)
                stream.write("Data for %s only found at CP and not at MK; <strong>skipping</strong>.\n" % timeStamp)

        for i in toDelList:
            del(timeStampDict['CP'][i])


    #Now fill in the dataDict for each site based on the data in timeStampDict.
    for s, data in timeStampDict.items():
        #Now data is a dictionary such as:
        #{'<timeStamp>':{...}, '<timeStamp>':{...}, ...}
        #and s is a site (MK or CP)

        #First initialize each list to be empty.
        for dataKey in dataKeysDict.keys():
            dataDict[s][dataKey]=[]

        #Now go throught all the data keys for each timestamp:
        for tStamp in _getSortedKeys(data):
            for dataKey in _getSelKeys(dataKeysDict, ['ut']):
                dataDict[s][dataKey].append(data[tStamp][dataKeysDict[dataKey]])

            #Add the time.
            dataDict[s]['ut'].append(tStamp[:10])

    #At this point the dataDict is of the form:
    #{<site>:{<dataKeysDict key>:[dataPoint1, dataPoint2, etc....], ...}, ...}

    #Do a quick check if we actually have any data to plot.
    if len(dataDict[_anySite(theSite)]['ut']) < 1:
        #Don't have any data to produce a plot...
        raise RuntimeError('Found no data to plot.')

    elif plotType is None:
        raise RuntimeError('No plot type selected.')

    elif plotType=='bothhrs':
        dataDict=timeUsage(dataDict,dataKeysDict,theSite,time2Ave=time2Ave, stream=stream, units='Hours')

    elif plotType=='shutteredhrs':
        dataDict=timeUsage(dataDict,dataKeysDict,theSite,time2Ave=time2Ave, stream=stream, units='Hours')

    elif plotType=='blankethrs':
        dataDict=timeUsage(dataDict,dataKeysDict,theSite, time2Ave=time2Ave, stream=stream, units='Hours')

    elif plotType=='bothpct':
        dataDict=timeUsage(dataDict,dataKeysDict,theSite,time2Ave=time2Ave, stream=stream, units='Percentage')

    elif plotType=='shutteredpct':
        dataDict=timeUsage(dataDict,dataKeysDict,theSite,time2Ave=time2Ave, stream=stream, units='Percentage')

    elif plotType=='blanketpct':
        dataDict=timeUsage(dataDict,dataKeysDict,theSite, time2Ave=time2Ave, stream=stream, units='Percentage')

    else:
        raise RuntimeError("Don't understand plotType '%s'" % str(plotType))

    #Here we overwrite the defults setup for each plot if they're specified by the caller.
    if theTitle is not None:
        title(theTitle)
    if yLabel is not None:
        ylabel(yLabel)

    if yMin is not None:
        ca=gca()
        set(ca, 'ylim', [yMin, ca.get_ylim()[1]])

    if yMax is not None:
        ca=gca()
        set(ca, 'ylim', [ca.get_ylim()[0],yMax])

    if addStamp:
        addGeaStamp()

    if horizLines is not None:
        for y in horizLines:
            if y is not None:
                try:
                    yFloat=float(y)
                    axhline(y=yFloat, linewidth=1, color='k')
                except ValueError:
                    stream.write('Could not convert %s to a float, when plotting horizontal goal line; disregarding.' % y)

    if fileName is None:
        show()
    else:
        savefig(fileName, dpi=int(dpi))

    if dataFileName is not None:
        """ Changed to be a csv table for import into exhell.
        #If given a file name, want to write all the data in html.
        html=HTMLSimpleCont()
        html.append(createHtmlTable(dataDict=dataDict, plotType=plotType, site=theSite, stream=stream))

        writeData(fileName=dataFileName, data=str(html))
        """
        csv = createCSVTable(dataDict=dataDict, plotType=plotType, site=theSite, stream=stream)
        writeData(fileName=dataFileName, data=csv)

    return dataDict

def writeData(fileName, data):

    f=file(fileName, 'w')
    f.write(data)
    f.close()

def _addXTicks(dataDict, theSite):

    ind=range(len(dataDict[theSite]['ut']))
    xticks(ind, dataDict[theSite]['ut'] , rotation=90)

    #Need this to adjust the layout, especially if using not a standard size axes (which depends on the nubmer of elements plotted)
    setp(gca(), 'xlim', [-1,len(ind)])


def _doPlot(dataDict, theSite, indOffset=0, width=0.4, colorGen=None, pointFmt='ko', dataTitle=''):
    """Helper to simplify some of the plotting with cumulative averages.
    """

    if colorGen is None:
        colorGen=GEAPlot.Colors()

    lines, legNames=[], []

    #Calculate the cumulitive averages.
    dataDict[theSite]['cAve']=cumAve(dataDict[theSite]['result'])

    c=colorGen.next()
    lines.append(plot(arange(len(dataDict[theSite]['cAve']))+indOffset, dataDict[theSite]['cAve'],  color=c,
                      marker='o', markeredgecolor=c, markerfacecolor=c))
    legNames.append(theSite+' Cumulative '+ dataTitle)

    # multiBarChart will actually return a list of rectangles. We only need to return one of them, so that we
    # know how to construct the legend; so grab the first one
    line=multiBarChart([dataDict[theSite]['result']], colorGen=colorGen, indOffset=indOffset, width=width)[0]
    lines.append(line)

    legNames.append(theSite+' '+dataTitle)

    return lines, legNames

def _anySite(theSite):
    """Helper to get us first site available.
    """
    if theSite=='MK' or theSite=='CP':
        return theSite
    else:
        #Here theSite is either 'ave(MK,CP)' or 'MK_and_CP', so could return either.
        return 'MK'

def setupAxes(elNum, elMax=15, width=0.2):
    """
    elMax - Max number of elements before start enlarging figure
    """
    if elNum<elMax:
        #If only have few elements, use the 'standard' size.
        figure(1, figsize=(8,6), facecolor='w', edgecolor='w')
        axes([0.1, 0.4, 0.8, 0.55])
    else:
        figWidth=8+(elNum-elMax)*width
        #Attempt to scale the size based on how much data we have to plot.
        figure(1, figsize=(figWidth,6), facecolor='w', edgecolor='w')
        axes([0.8/figWidth, 0.4, 1.0-2*0.8/figWidth, 0.55])

def list2Array(dataDict, dataKeysList=None, defType=Float64):

    if dataKeysList is  None:
        dataKeysList=dataDict.keys()

    for name in dataKeysList:
        dataDict[name]=array(dataDict[name])
        # dataDict[name]=array(dataDict[name], typecode=defType) original code. Has array(.. ) changed since python 2.3.3?

def aveOverPeriod(dataDict, dataKeysList=None, time2Ave=None, autoAdjustTime=True):
    """Note: here dataDict does not have data for multiple sites.

    Assuming dataDict['ut'] exists.

    time2Ave - number of days (or rather array items) to average over.
    """
    defType=Float64

    if time2Ave is not None:

        if dataKeysList==None:
            #Here we assume that data corresponding to all (except ut) the keys should be averaged.
            dataKeysList=_getSelKeys(dataDict.keys(), ['ut'])

        for name in dataKeysList:
            dataDict[name]=ave(dataDict[name],time2Ave)

        if autoAdjustTime:
            if time2Ave==7:
                dataDict['ut']=['Week of %s' % s for s,i in zip(dataDict['ut'], range(0, len(dataDict['ut']))) if i%time2Ave==0]
            elif time2Ave==30:
                dataDict['ut']=['Month of %s' % s for s,i in zip(dataDict['ut'], range(0, len(dataDict['ut']))) if i%time2Ave==0]
            else:
                dataDict['ut']=['XX day ave. starting %s' % s for s,i in zip(dataDict['ut'], range(0, len(dataDict['ut']))) if i%time2Ave==0]

    #Return for convenience.
    return dataDict

def timeUsage(dataDict, dataKeysDict, theSite, time2Ave=None, stream=sys.stdout, units='Hours'):

    aSite=_anySite(theSite)

    for s in dataDict.keys():

        #Convert all the data (except time) to arrays
        list2Array(dataDict=dataDict[s], dataKeysList=_getSelItems(dataKeysDict.keys(), ['ut']))

        if units == 'Percentage':
            for name in _getSelItems(dataKeysDict.keys(),['ut', 'tha']):
                dataDict[s][name] = dataDict[s][name] / dataDict[s]['tha']  * 100.0


        #Do a little averaging, depending on what time2Ave is set to.
        aveOverPeriod(dataDict=dataDict[s], dataKeysList=_getSelItems(dataKeysDict.keys(), ['ut']), time2Ave=time2Ave)

    elNum=len(dataDict[aSite]['tha'])    #Pick any element.. all should have the same length (could assert).
    setupAxes(elNum)

    lines=[]
    legNames=[]

    colorGen=GEAPlot.Colors()

    if theSite=='MK' or theSite=='CP' or theSite=='ave(MK,CP)':
        #Only have one item to plot

        if theSite=='ave(MK,CP)':
            #Here have to massage the data a little.  Need to add the data from MK and CP before plotting.
            #At this point we assume have normalized data for both MK and CP.
            dataDict[theSite] = {}
            for item in _getSelItems(dataKeysDict.keys(), ['ut','tha']):
                dataDict[theSite][item] = (dataDict['MK'][item] + dataDict['CP'][item]) / 2

        lines+=multiBarChart([dataDict[theSite]['shut'], dataDict[theSite]['blank']], colorGen=colorGen, width=0.6, indOffset=0)

    elif theSite=='MK_and_CP':

        lines+=multiBarChart([dataDict['MK']['shut'], dataDict['MK']['blank']], colorGen=colorGen, width=0.4, indOffset=-0.22,)

        #Want to reset the colors.
        colorGen.i=0

        multiBarChart([dataDict['CP']['shut'], dataDict['CP']['blank']], colorGen=colorGen, width=0.4, indOffset=0.22)
    else:
        raise RuntimeError('The site %s not uderstood. Aborting')

    legNames += [dataKeysDict['shut'], dataKeysDict['blank']]


    drawLegend(tuple(lines), tuple(legNames))  #bottom center

    if units=='Percentage':
        ylim(0, 110)
        title("%s Time Usage As Percentage" % theSite.replace('_and_', ' and '))
    else:
        #Assume hours
        ylim(0, 12)
        title("%s Hourly Time Usage" % theSite.replace('_and_', ' and '))

    ylabel(units)

    #Want to have the date/time data in the dictionary for each site. In case of ave(MK,CP)
    #have to put it there manually - just use one for MK or CP. This comes in handy later when create an html
    #table using the data.
    if theSite=='ave(MK,CP)':
        dataDict[theSite]['ut']=dataDict[aSite]['ut']

    #Could be passing 'theSite' variable instead of 'aSite', but expect xtics to be the same,
    #and this way don't have to handle a special case for MK_and_CP, which is a valid 'theSite', but
    #there is no data dicionary for it in dataDict (ie. there is no dataDict['MK_and_CP']).
    #This way we guarantee if _addXTicks() calls dataDict[aSite] exists.
    _addXTicks(dataDict, aSite)

    return dataDict

def createCSVTable(dataDict, plotType, site, stream=sys.stdout):
    """
    """

    cellFormat="%.2f"
    #Using a lambda function here would be nicer, but wouldn't be able to hanlde exceptions.
    def _formatCell(cell):
        try:
            return cellFormat % cell
        except TypeError:
            return cell

    if plotType is None:
        raise RuntimeError('No plot type selected.')

    elif plotType=='bothhrs':
        theTitle='Shutter and Blanket Closures (%s)' % site
        header=['Date', 'Shuttered', 'Blanket Closure']
        dataKeys='ut','shut', 'blank'

    elif plotType=='shutteredhrs':
        theTitle='Shutter (%s)' % site
        header=['Date', 'Shuttered']
        dataKeys='ut','shut'

    elif plotType=='blankethrs':
        theTitle='Blanket Closure (%s)' % site
        header=['Date', 'Blanket Closure']
        dataKeys='ut','blank'

    elif plotType=='bothpct':
        theTitle='Shutter and Blanket Closures (%s)' % site
        header=['Date', 'Shuttered', 'Blanket Closure']
        dataKeys='ut','shut', 'blank'

    elif plotType=='shutteredpct':
        theTitle='Shutter (%s)' % site
        header=['Date', 'Shuttered']
        dataKeys='ut','shut'

    elif plotType=='blanketpct':
        theTitle='Blanket Closure (%s)' % site
        header=['Date', 'Blanket Closure']
        dataKeys='ut','blank'

    else:
        raise RuntimeError("Don't understand plotType '%s'" % str(plotType))

    csv = theTitle + "\n"

    if site=='MK_and_CP':
        #Special case here; have to show two sets of data in the same table

        #First lets adjust the header a little; each column (except the first; the date),
        #should have a colspan of 2 to accomodate data for both MK and CP.s
        for item in header:
            csv += item + ","
            # newHeader+=[item, '']

        csv += "\n"

        #Lets now add the MK/CP header row

        sites=['MK', 'CP'] * (len(header)-1)

        # csv += sites + "\n"

        #dataKeys will start with 'ut', but in this case lets get rid of it; we'll manually account for it later.
        #Also modify it a little to include duplicate keys - to account for both MK and CP.
        #So going from ['ut', 'key1', 'key2', ....]  to ['key1', 'key1', 'key2', 'key2']
        dataKeys=_listExpand(dataKeys[1:])

        #Need to manipulate the lists/tupples a little to get things lined up properly
        dataLists=zip(*map(lambda tup: dataDict[tup[0]][tup[1]],  zip(sites, dataKeys)))

        #Finally want to zip it with the time stamps. Noting that we expect dataDict['MK']['ut'] to
        #exist at this point - since we extracted data for both MK and CP.
        for timeStamp, dataRow in zip(dataDict['MK']['ut'], dataLists):
            row=[timeStamp] + map(_formatCell, list(dataRow))
            csv += ','.join(row) + '\n'

    else:
        #Here we only need to worry about one column of data for each dataKey.
        for item in header:
            csv += item + ","
            # newHeader+=[item, '']

        csv += "\n"

        for row in zip(*map(lambda key: dataDict[site][key], dataKeys)):

            #Want to format each cell. Leave date untouched.
            row=[row[0]]+map(_formatCell, list(row[1:]))
            csv += ','.join(row) + '\n'

    return csv

def createHtmlTable(dataDict, plotType, site, stream=sys.stdout):
    """
    """
    #NOTE: One has to be careful when showing data for certain dataKeys, when the averaging!=Daily
    #For performance reasons, only certain data is averaged - whatever needs to be plotted.
    #Hence for example when showing a timeLoss plot, with averaging==Week, the timeLoss (which is plotted) will
    #be averaged, but data for 'thlo' may not be. For each plot type one should check/modify the corresponding function
    #to be sure all data that is to be shown here in the table is averaged.

    cellFormat="%.2f"
    #Using a lambda function here would be nicer, but wouldn't be able to hanlde exceptions.
    def _formatCell(cell):
        try:
            return cellFormat % cell
        except TypeError:
            return cell

    def _date2html(d, site):
        """A helper function used to turn dates into nightlog links.
        """
        #TODO... not ready
        if d.startswith('Month'):
            timeStamp=d.lstrip('Month of').strip()
        elif d.startwith('Week'):
            timeStamp=d.lstrip('Week of').strip()
        else:
            timeStamp=d.strip()

        t=Time()
        t.strptime('%y/%m/%d', timeStamp)

        return HtmlHelper.createLink(timeStamp, 'pages/remedy/nightLogPage', SITE=site, FORMAT='Night', **t.toStartTimeDict(allCaps=True, monthAsWord=True))

    if plotType is None:
        raise RuntimeError('No plot type selected.')

    elif plotType=='both':
        theTitle='Shutter and Blanket Closures (%s)' % site
        header=['Date', 'Shutter', 'Blanket Closure']
        dataKeys='ut','shut', 'blank'

    elif plotType=='shuttered':
        theTitle='Shutter (%s)' % site
        header=['Date', 'Shutter']
        dataKeys='ut','shut'

    elif plotType=='blanket':
        theTitle='Blanket Closure (%s)' % site
        header=['Date', 'Blanket Closure']
        dataKeys='ut','blank'

    else:
        raise RuntimeError("YDon't understand plotType '%s'" % str(plotType))

    table=HTMLDynTable(tableAttrs={'class':"tableList", 'border':"1"})
    table.add_array_after_last_row(['<strong>%s</strong>' % theTitle])

    if site=='MK_and_CP':
        #Special case here; have to show two sets of data in the same table

        #First lets adjust the header a little; each column (except the first; the date),
        #should have a colspan of 2 to accomodate data for both MK and CP.s
        newHeader=['Date']
        for item in header[1:]:
            newHeader+=[item, '']

        table.add_array_after_last_row(newHeader)

        for i in range(1, len(newHeader), 2):
            table.setCellColSpan(1, i, 2)

        #Lets now add the MK/CP header row
        sites=['MK', 'CP'] * (len(header)-1)
        table.add_array_after_last_row(['']+sites)

        #dataKeys will start with 'ut', but in this case lets get rid of it; we'll manually account for it later.
        #Also modify it a little to include duplicate keys - to account for both MK and CP.
        #So going from ['ut', 'key1', 'key2', ....]  to ['key1', 'key1', 'key2', 'key2']
        dataKeys=_listExpand(dataKeys[1:])

        #Need to manipulate the lists/tupples a little to get things lined up properly
        dataLists=zip(*map(lambda tup: dataDict[tup[0]][tup[1]],  zip(sites, dataKeys)))

        #Finally want to zip it with the time stamps. Noting that we expect dataDict['MK']['ut'] to
        #exist at this point - since we extracted data for both MK and CP.
        for timeStamp, dataRow in zip(dataDict['MK']['ut'], dataLists):
            row=[timeStamp]+map(_formatCell, list(dataRow))
            table.add_array_after_last_row(row)

    else:
        #Here we only need to worry about one column of data for each dataKey.
        table.add_array_after_last_row(header)

        #Here we handle site=='MK' or site=='CP' or site=='ave(MK,CP)'
        for row in zip(*map(lambda key: dataDict[site][key], dataKeys)):

            #Want to format each cell. Leave date untouched.
            row=[row[0]]+map(_formatCell, list(row[1:]))
            table.add_array_after_last_row(row)

    #Some cosmetic stuff...
    table.setCellattrs(0, 0, {'align':'center'}, overwrite=True)

    #Lets have the title row span over all the columns.
    table.setCellColSpan(0, 0, table.getmaxCol()+1)

    return table


def _listExpand(aList,num=2):
    tempList=[]
    for item in aList:
        tempList+=[item]*num
    return tempList

if __name__=='__main__':

    startTimeStamp = 1343815200 # UT  8/1/2012  00:00:00
    startTimeStamp = 1343779200 # HST 7/31/2012 14:00:00

    startTimeStamp = 1332633600	# UT 3/25/2012 00:00:00
    startTimeStamp = 1332669600	# HST 3/25/2012 00:00:00, UT 3/25/2012 10:00:00
    startTimeStamp = 1332644400	# CST 3/25/2012 00:00:00, UT 3/25/2012 03:00:00

    startTimeStamp = 1332644400 # Time.seconds value for geasouth NL for 3/25 querying for CP NL	UTC + 3 hours
    startTimeStamp = 1332633600 # Time.seconds value for geasouth NL for 3/25 querying for MK NL	UTC + 0 hours
    startTimeStamp = 1332669600 # Time.seconds value for geanorth NL for 3/25 querying for MK NL	UTC + 10 hours
    startTimeStamp = 1332633600 # Time.seconds value for geanorth NL for 3/25 querying for CP NL	UTC + 0 hours


    startTimeStamp = 1332633601	# UT 3/25/2012 00:00:00
    endTimeStamp = startTimeStamp + 14 * 24 * 60 * 60 - 1	# two weeks.
    
    startTime = Time(startTimeStamp, site="MK")
    endTime   = Time(endTimeStamp,   site="MK")

# Run these from geanorth. All should return 1332669600 (3/25 00:00:00 HST), (1332734400, 1332781200) (3/25 18:00:00, 3/26 07:00:00)

    print "s/b 1332669600 (3/25 00:00:00 HST), (1332734400, 1332781200) (3/25 18:00:00, 3/26 07:00:00)"

    print
    print "XXXXXXXXXX"
    print

    print startTime.seconds, endTime.seconds
    foobar = laserMetrics('MK', plotType = 'timeUsage', startTime=startTime, endTime=endTime)
    """
    foobar = laserMetrics('MK_and_CP', plotType = 'timeUsage', startTime=startTime, endTime=endTime)
    foobar = laserMetrics('MK', plotType = 'timeUsage', startTime=startTime, endTime=endTime)
    foobar = laserMetrics('MK_and_CP', plotType = 'timeUsagePercentage', startTime=startTime, endTime=endTime)
    foobar = laserMetrics('MK', plotType = 'timeUsagePercentage', startTime=startTime, endTime=endTime)
    """

