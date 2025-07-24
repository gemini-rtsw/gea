#!/usr/bin/python

"""
THIS MODULE IS TO BE REWRITTEN/CLEANED UP... RIGHT NOW IT'S A MESS...
WANT TO DO THIS AFTER UPGRADING TO matplotlib > 0.72.
SHOULD ONLY STICK TO OO INTERFACE THEN...

need to properly account for how many figures have at any one time... and keep track of 
those that are destroyed...
also need to rewrite/combine setting of plot options and parameters... 

"""
import sys
import os
from random import random
from copy import deepcopy

import GEAVars
from GEAGeneral import Validator
from GEAException import PlotException
from GEAData import Data
from GEATime import Time

#Define matplotlibConfig function before importing pylab stuff.
def matplotlibConfig():
    """
    Setup a few plotting defaults.  
    """

    # Check if matplotlib.use() has already been called. Generates warning.
    if 'matplotlib.backends' not in sys.modules:
        matplotlib.use(GEAVars.plot.backend)	# This lines generates an error.
    
    matplotlib.rcParams['lines.linewidth'] = 0.8

    #Want to tell matplotlib how to treat the time/date data
    if GEAVars.site=='MK':
        matplotlib.rcParams['timezone']='Pacific/Honolulu'
    else:  #CP
        matplotlib.rcParams['timezone']='America/Santiago'

    matplotlib.rcParams['grid.linewidth']=0.2
    matplotlib.rcParams['grid.linestyle']=':'
    matplotlib.rcParams['grid.color']='k'

    matplotlib.rcParams['axes.formatter.limits'] = -6, 6

    matplotlib.rcParams['legend.fontsize']=8
    matplotlib.rcParams['xtick.labelsize']=8     # fontsize of the tick labels
    matplotlib.rcParams['ytick.labelsize']=8     # fontsize of the tick labels

import matplotlib
matplotlibConfig()
#Should call matplotlibConfigure() before doing an import like this, to make sure get right numerix module.
from matplotlib.pylab import *

#Could use generators, but the eric3 IDE does weird things when use: 'from __future__ import generators'
class Colors(object):
    """Used for (consistently) generating colors when have plots of multiple curves on one graph.
    Should technically make sure that randomly generated colors are returned only once, 
    but the chances of repetition are small, so don't want to deal with the overhead.
    """
    def __init__(self, colors=None):
        if colors is None:
            self.colors=((0.0,  0.0,  1.0),
                         (0.0,  1.0,  0.0),
                         (0.2,  0.6,  0.2),
                         (0.7,  0.0,  0.7),
                         (0.8,  0.1,  0.1),
                         (1.0,  0.0 , 0.0),
                         (0.0,  0.0 , 0.5),
                         (0.6,  0.6 , 0.6),
                         (0.6,  0.2 , 0.2),
                         (0.0,  0.0 , 0.0),
                         (0.9,  0.9 , 0.9)           #
                         )                         #If need more colors than above, generate them at "random"
        else:
            self.colors=colors

        self.i=0
        self.rand=random() * 9.67  #Want the sequence to be always the same so setting a seed.
        
    def next(self):
        try:
            color=self.colors[self.i]
            self.i+=1
        except IndexError:
            #Not checking if the tuple like this has already been generated. 
            color=random(), random(), random()
            
        return color
        
    def reset(self):
        self.i=0
 
class BasePlot(object):
    """Base plot class. All plots should inherit from this class.
    """
    def __init__(self, dataList, fStream=GEAVars.errStream, options=None):
        """
        Arguments:
            data - Data to be plotted.
            outFile - Where the plot is to be written
            fStream - Where any non critical errors and other info is written to.
            options - Dictionary with plotting options. This is usually a GEARequest.Request object. 

        """ 
        self.fStream=fStream
        
        #Defaults
        self._options={'XLABEL':GEAVars.plot.XLABEL,
                       'YLABEL':GEAVars.plot.YLABEL, 
                       'PLOTTITLE':GEAVars.plot.PLOTTITLE,
                       'XMIN':GEAVars.plot.XMIN, 
                       'XMAX':GEAVars.plot.XMAX, 
                       'YMIN':GEAVars.plot.YMIN, 
                       'YMAX':GEAVars.plot.YMAX,
                       'YSCALE':GEAVars.plot.YSCALE,
                       }
                       
        self.dataList=dataList
        
        if not options is None:
            self.updateOptions(options)
        
    def updateOptions(self, newDict, **kwargs):
        """Sets plot options, from CGI keywords. This method disregards keys it does not "know".
        
        When a value for a particular key is None, that key is not processed. Empty values which are to 
        be processed should be set to '' (empty string).
        
        """
        tempDict=deepcopy(newDict)         #Don't want to modify the original 
        tempDict.update(kwargs)
        
        for key, val in tempDict.items():
        
            if val is None:                   #Don't process None values. Those are GEARequest blanks
                continue
        
            if self._options.has_key(key):              #Only modify values for keys which are already present.
                key, val=self._convertOptionType(key, val)
                self._options[key]=val
                
    def _convertOptionType(self, key, val):
        """Converts certain values to proper types (ie. str->int, str->float, etc...). This is needed
        so that the values that are passed into matplotlib or other graphing library are as expected.
            
        Each child should have a version of this method
        which takes care of child-specific options. 
            
        """
        if key in ['XMIN', 'XMAN', 'YMIN', 'YMAX']:
            val=Validator.validateFloat(option=val, stream=self.fStream, valueOnError='', 
                                        errorPreText='Validating %s... ' % key)
        elif key in ['YSCALE',]:
            if val not in ['linear', 'log']:
                self.fStrem.write("Error validating '%s'. Don't understand '%s'; defaulting to '%s'." % (key, val, GEAVars.plot.YSCALE))
                val=GEAVars.plot.YSCALE
                    
        return key, val
        
    def plot(self):
        """Each child plot must implement its own version of this method.
        """
        raise NotImplemented("plotData() not implemented.")
        
        
class GNUBasePlot(BasePlot):
    """Used to create plots using GNUPlot.
    """
    #Not using GNUPlot right now.
    pass 

class GEADateFormatter(matplotlib.ticker.Formatter):
    """
    This class attempts to figure out the best format to use.  This is
    most useful when used with the :class:`AutoDateLocator`.
    """

    def __init__(self, tz=None):
        self._formatter = DateFormatter("%b %d %Y %H:%M:%S %Z", tz)
        self._tz = tz

    def __call__(self, x, pos=0):
        scale = float( self._locator._get_unit() )

        if ( scale == 365.0 ):
            self._locator = YearLocator(tz=tz)
            self._formatter = DateFormatter("%Y", self._tz)
        elif ( scale == 30.0 ):
            self._locator = MonthLocator(tz=tz)
            self._formatter = DateFormatter("%b %Y", self._tz)
        elif ( (scale == 1.0) or (scale == 7.0) ):
            self._locator = DayLocator(tz=tz)
            self._formatter = DateFormatter("%b %d %Y", self._tz)
        elif ( scale == (1.0/24.0) ):
            self._locator = HourLocator(tz=tz)
            self._formatter = DateFormatter("%H:%M:%S", self._tz)
        elif ( scale == (1.0/(24*60)) ):
            self._locator = MinuteLocator(tz=tz)
            self._formatter = DateFormatter("%H:%M:%S", self._tz)
        elif ( scale == (1.0/(24*3600)) ):
            self._locator = MinuteLocator(tz=tz)
            self._formatter = DateFormatter("%H:%M:%S", self._tz)
        else:
            self._locator = MinuteLocator(tz=tz)
            self._formatter = DateFormatter("%b %d %Y %H:%M:%S %Z", self._tz)

        return self._formatter(x, pos) 
 
class MatBasePlot(BasePlot):
    """Used to create plots using the matplotlib library.
    
    Inspect destroying figures... talk to matplotlib people...
    """
    figCount=0
    
    def __init__(self, dataList, fStream=GEAVars.errStream, options=None):

        BasePlot.__init__(self, dataList=dataList, fStream=fStream)
    
        #Setup defaults for these values by updating self._options directly. Using self.updateOptions() ONLY updates key/value
        #pairs for which the key already exists.
        self._options.update({'LEGEND':GEAVars.plot.LEGEND, 
                              'DPI':GEAVars.plot.DPI, 
                              'AA':GEAVars.plot.AA, 
                              'GRIDLINES':GEAVars.plot.GRIDLINES
                              })
        if not options is None:
            self.updateOptions(options)

        self._lines=[]              
        self._initialized=False    
        
    def _initFigure(self):
            """The size/type depends on whether to include the legend..
            """
            if self._initialized:
                return
            MatBasePlot.figCount+=1
            self.figureNum=MatBasePlot.figCount
            
            if self._options['LEGEND'].lower()=='outside':
                f = figure(self.figureNum, figsize=(11,6))
                self.axes=axes([0.075, 0.10, 0.55, 0.78])
            else:
                f = figure(self.figureNum)
                self.axes=axes()
                
#            ax = f.add_subplot(111)
#            foo = GEADateFormatter()
#            ax.xaxis.set_major_formatter(foo)

            f.autofmt_xdate()
            self._initialized=True
            
            self._addGeaStamp()
                 
    def makeCurrent(self):
        """ Should be called before any operation of the contents of the figure/axes.
        """
        self._initFigure()
        figure(self.figureNum)
        axes(self.axes)
        
    def _convertOptionType(self, key, val):
        """Converts certain values to proper types (ie. str->int, str->float, etc...). This is needed
        so that the values that are passed into matplotlib lib are as expected.
            
        Each child should have a version of this method which takes care of child-specific options. 
            
        """
        #string->int
        if key in ['DPI']:
            val=Validator.validateInt(option=val, stream=self.fStream, valueOnError=100, 
                                      errorPreText='Validating %s... ' % key)
        #string->bool
        elif key in ['AA', 'GRIDLINES']:
            val=Validator.validateBoolean(option=val, stream=self.fStream, valueOnError=True, 
                                         errorPreText='Validating %s... ' % key)
        else:           #Use parent's method.
            key, val=BasePlot._convertOptionType(self, key, val)

        return key, val
        
    def plotEmpty(self):
        
        #self._initFigure()    
        self.makeCurrent()
        
        cla()
        plot([0],[0])
        
        self._setPlotOptions()
        
    def _setPlotOptions(self):
        """
        """
        pass
    
    def title(self, titleText):
        self.makeCurrent()
        title(titleText)
    
    def write(self, fileName, dpi=None):
        self.makeCurrent()
        
        dpi=dpi or self._options['DPI']
        savefig(fileName, dpi=dpi)  
    
    def show(self):
        """Only works when both:
            matplotlib.use('GD')
            matplotlib.use('Agg')
        are commented out at the top.
        """
        self.makeCurrent()
        show()
        
    def text(self, x, y, label, fontdict=None, **kwargs):
        
        self.makeCurrent()
        

        #Setup some defaults if not given.
        for key, value in [('horizontalalignment','center'), 
                           ('verticalalignment','center'), 
                           ('transform', gca().transAxes)]:
            if not kwargs.has_key(key):
                kwargs[key]=value
                pass
                    
        t=text(x, y, label, fontdict=fontdict, **kwargs)        

    def axhline(self, y, linewidth=1, color='k'):
    
        self.makeCurrent()
        axhline(y, linewidth=linewidth, color=color) 
    
    def axvline(self, x, linewidth=1, color='k'):
    
        self.makeCurrent()
        axvline(x, linewidth=linewidth, color=color)         
        
    def _addGeaStamp(self):
        fontdict={'family':'serif','color':'k','weight':'bold','size': 8,}
        self.text(-0.0125, -0.25 ,"GEA %s" % GEAVars.versionStr, fontdict=fontdict)  
                
        
class MatXYPlot(MatBasePlot):
    """Simple line plot.
    """
    def __init__(self, dataList, fStream=GEAVars.errStream, options=None):

        MatBasePlot.__init__(self, dataList=dataList, fStream=fStream)

        #Setup defaults for these values by updating self._options directly. Using self.updateOptions() ONLY updates key/value
        #pairs for which the key already exists.
        self._options.update({'MAXDELTAX':GEAVars.plot.MAXDELTAX,
                              'HANDLEDISCON':GEAVars.plot.HANDLEDISCON,
                              'DISCRETEDATA':GEAVars.plot.DISCRETEDATA,
                              'LINESTYLE':GEAVars.plot.LINESTYLE,
                              }
                            ) #MAXDELTAX==-1 means always join points
        
        if not options is None:
            self.updateOptions(options)
      
    def _convertOptionType(self, key, val):
        """Converts certain values to proper types (ie. str->int, str->float, etc...). This is needed
        so that the values that are passed into matplotlib lib are as expected.
            
        Each child should have a version of this method which takes care of child-specific options. 
            
        """
        #string->float
        if key in ['MAXDELTAX']:
            #MAXDELTAX==-1 means that all points are joined.
            val=Validator.validateFloat(option=val, minVal=-1, maxVal=10000, stream=self.fStream, valueOnError=-1, 
                                        errorPreText='Validating %s... ' % key)
                                        
        elif key in ['HANDLEDISCON']:
            val=Validator.validateBoolean(option=val, stream=self.fStream, valueOnError=True, 
                                             errorPreText='Validating %s... ' % key)
                
        elif key in ['DISCRETEDATA']:
            val=Validator.validateFloat(option=val, minVal=0, maxVal=1000, stream=self.fStream, 
                                        valueOnError=GEAVars.plot.DISCRETEDATA, 
                                        errorPreText='Validating %s... ' % key)
        elif key in ['LINESTYLE']:
            #Should go throught the list of permitted values... need to consult matplotlib docs.
            pass
        else:
            key, val=MatBasePlot._convertOptionType(self, key, val)
    
        return key, val
    
    def plot(self):
        """Plots all the data stored in self.dataList.
        """
        #self._initFigure()
        self.makeCurrent()
        self._lines=[]
        
        #Could have an empty self.dataList, or a non-empty list of empty Data objects. Can handle the first case right away.
        if not self.dataList:
            raise PlotException('Have no data to plot.')
                
        emptyDataSet=False                  #If trying to plot empty data, will need to raise an exception.
        
        legendData=[]    #List of tuples (line, tuple_with_legend_text)
        colors=Colors()
        
        fmt='' #Needs to be passed to the plot_date command... we are not using this, but setting options via the rest of the arguments.
        
        for item in self.dataList:
                       
            if len(item.x) < 1 or len(item.y) < 1:  
                emptyDataSet=True
                continue
            
            options={'antialiased':self._options['AA'],
                    'linestyle':self._options['LINESTYLE'],
                    'color':colors.next()}
            
            if len(item.x) < self._options['DISCRETEDATA']:
                options.update({'marker':'o',
                                'markerfacecolor':options['color']})
        
            if self._options['HANDLEDISCON']:

                lines=[]
            
                index=0
                for el in item.discList:
                    if len(item.x[index:el]):
                        lines.append(plot(item.x[index:el], item.y[index:el], fmt, **options))   
                    index=el
                
                if len(item.x[index:]):
                    lines.append(plot(item.x[index:], item.y[index:], fmt, **options))
                if lines:
                    self._lines.append(lines)
                    
                if self._options['LEGEND'] and item.name:
                    theName=item.name
                    if item.legendName:
                        theName=item.legendName                    
                    #For now also show number of data points used.
                    legendData.append((lines[0] ,("%s (%d)" % (theName, len(item.x)),)))

            else:
                self._lines.append(plot(item.x, item.y, fmt, **options))  
      
                if self._options['LEGEND'] and item.name:
                    theName=item.name
                    if item.legendName:
                        theName=item.legendName                      
                    #For now also show number of data points used.
                    legendData.append((self._lines[0] ,("%s (%d)" % (theName, len(item.x)),)))

        if emptyDataSet and not self._lines:
            raise PlotException('Have no data to plot.')
                
        # Want to call self._setPlotOptions() after using the MatPlotFormatter so that some parameters can be updated
        #based on the values in options.
        self._setPlotOptions(legendData=legendData)
 
    def _setPlotOptions(self, legendData=None):
        
        self.makeCurrent()
        
        if legendData:
            lines    = ()
            textTups = ()
            for line, textTup in legendData:
                lines+=(line,)
                textTups+=textTup

            if   self._options['LEGEND'].lower()=='outside':
                legend(textTups, loc=2, bbox_to_anchor=(1.0, 1.0)) 
            elif self._options['LEGEND'].lower()=='inside':
                legend(textTups, loc='upper right') 
                gca().get_legend().get_frame().set_alpha(0.0)
            else:
                pass
        
        grid(self._options['GRIDLINES'])

        xlabel(self._options['XLABEL'])
        ylabel(self._options['YLABEL'])
                    
        title(self._options['PLOTTITLE'])
        
        if self._options['YSCALE']!='linear':
            setp(self.axes, 'yscale', self._options['YSCALE'])        
            
        #Setup axis ranges. If values provided in options are not '', use them; otherwise use the defaults.
        for newMin, newMax, orgMin, orgMax, ax  in ((self._options['XMIN'], self._options['XMAX'], 
                                                     self.axes.get_xlim()[0], self.axes.get_xlim()[1], 'x'),
                                                    (self._options['YMIN'], self._options['YMAX'], 
                                                     self.axes.get_ylim()[0], self.axes.get_ylim()[1], 'y')):        
            if newMin=='':
                newMin=orgMin
            if newMax=='':
                newMax=orgMax

            if float(newMin)==float(newMax)  and str(newMin) != '':
                raise PlotException('Min and Max for the %s-axis are both %s.  Cannot have zero range.' % (ax, newMin))
    
            setp(self.axes, ax+'lim', [newMin, newMax])

    def _segPlot(self, x, y, maxdelta, fmt, color,  **kwargs):
        """
        Plot x versus y, breaking the plot at any point where x[i] -
        x[i-1] > maxdelta. kwargs are passed on to plot
        """
        x=asarray(x)
        y=asarray(y)
        d=diff(x)
        lines=[]
        ind=nonzero(greater(d, maxdelta))
        ind=ind+1
        if not len(ind):
            lines.extend(plot(x,y, fmt, color=color, **kwargs)) 
        else:
            allind=[0]
            allind.extend(ind)
            allind.append(len(x))
            for i1,i2 in zip(allind[:-1], allind[1:]):
                lines.extend(plot(x[i1:i2], y[i1:i2], fmt, color=color, **kwargs))
        return lines

        
class MatTimePlot(MatXYPlot):

    def __init__(self, dataList, fStream=GEAVars.errStream, options=None):

        MatXYPlot.__init__(self, dataList=dataList, fStream=fStream)

        #Setup defaults for these values by updating self._options directly. Using self.updateOptions() ONLY updates key/value
        #pairs for which the key already exists.
        self._options.update({}) #Empty for now..
        
        if not options is None:
            self.updateOptions(options)
         

    def _setupLinestyle(self, linestyle, color, default=None):

        if linestyle=='steps':
            d=dict(linestyle='steps-post')
        elif linestyle=='steps-o':
            d=dict(linestyle='steps-post',marker='o',markeredgecolor=color, markerfacecolor=color)
        elif linestyle=='o-o':
            d=dict(linestyle='-',marker='o',markeredgecolor=color, markerfacecolor=color)
        elif linestyle=='o':
            d=dict(linestyle=None,marker='o',markeredgecolor=color, markerfacecolor=color)
        elif linestyle=='-':
            d=dict(linestyle='-')
        elif linestyle=='--':
            d=dict(linestyle='--')
        elif linestyle=='d-d':
            d=dict(linestyle='-',marker='d',markeredgecolor=color, markerfacecolor=color)    
        elif linestyle=='d':
            d=dict(linestyle=None,marker='d',markeredgecolor=color, markerfacecolor=color)          
        elif linestyle=='x-x':
            d=dict(linestyle='-',marker='x',markeredgecolor=color, markerfacecolor=color)    
        elif linestyle=='x':
            d=dict(linestyle=None,marker='x',markeredgecolor=color, markerfacecolor=color)    
        elif linestyle=='+-+':
            d=dict(linestyle='-',marker='+',markeredgecolor=color, markerfacecolor=color)    
        elif linestyle=='+':
            d=dict(linestyle=None,marker='+',markeredgecolor=color, markerfacecolor=color)                                       
        else:
            d={}
            if default is not None:
                d.update(default)         
        return d                
        
    def plot(self):
        """Plots all the data stored in self.dataList.
        """
        #self._initFigure()
        self.makeCurrent()
        self._lines=[]
        
        #Could have an empty self.dataList, or a non-empty list of empty Data objects. Can handle the first case right away.
        if not self.dataList:
            raise PlotException('Have no data to plot.')        
        
        emptyDataSet=False                  #If trying to plot empty data, will need to raise an exception.
        
        minTime, maxTime=None, None         #Used when labeling ticks.
        
        legendData=[]    #List of tuples (line, tuple_with_legend_text)
        colors=Colors()
        
        fmt=''

        def HHMMSS2Decimal(hhmmss):
            hh, mm, ss = hhmmss.split(":")
            hh = float(hh)
            mm = float(mm)
            ss = float(ss)
            return hh + mm / 60.0 + ss / 3600.0

        for item in self.dataList:

            if len(item.x) < 1 or len(item.y) < 1:  
                emptyDataSet=True
                continue

            for i in range(0, len(item.y)):
                val = item.y[i]
                if type(val) == str:
                    if ':' in val: item.y[i] = HHMMSS2Decimal(val)
            
            options={'antialiased':self._options['AA'],                    
                    'color':colors.next()}
            
            options.update(self._setupLinestyle(linestyle=self._options['LINESTYLE'], 
                                                color=options['color'], 
                                                default=dict(linestyle=GEAVars.plot.LINESTYLE)))
      
            if len(item.x) < self._options['DISCRETEDATA']:
                options.update({'marker':'o', 'markerfacecolor':options['color']})        
            if minTime is None:
                minTime=item.x[0]
            else:
                minTime=min([minTime, item.x[0]])
            if maxTime is None:
                maxTime=item.x[-1]
            else:
                maxTime=max([maxTime, item.x[-1]])

            if self._options['HANDLEDISCON']:
                lines=[]
            
                index=0
                for el in item.discList:
                    if len(item.x[index:el]):
                        lines.append(plot_date(epoch2num(item.x[index:el]), item.y[index:el], fmt, **options))   
                    index=el
                

                if len(item.x[index:]):
                    lines.append(plot_date(epoch2num(item.x[index:]), item.y[index:], fmt, **options))   

                if lines:
                    self._lines.append(lines)
                    
                if self._options['LEGEND'] and item.name:
                    theName=item.name
                    if item.legendName:
                        theName=item.legendName
                        
                    #Also show number of data points used.
                    legendData.append((lines[0], ("%s (%d)" % (theName, len(item.x)),)))

            else:

                self._lines.append(plot_date(epoch2num(item.x), item.y, fmt, **options))  
      
                if self._options['LEGEND'] and item.name:
                    theName=item.name
                    if item.legendName:
                        theName=item.legendName
                    
                    #For now also show number of data points used.
                    legendData.append((self._lines[0] ,("%s (%d)" % (theName, len(item.x)),)))

        if emptyDataSet and not self._lines:
            raise PlotException('Have no data to plot.')

        # Want to call self._setPlotOptions() after using the MatPlotFormatter so that some parameters can be updated
        #based on the values in options.
        self._setPlotOptions(legendData=legendData)

class MatHistPlot(MatBasePlot):

    def __init__(self, dataList, fStream=GEAVars.errStream, options=None):

        MatBasePlot.__init__(self, dataList=dataList, fStream=fStream)

        #Setup defaults for these values by updating self._options directly. Using self.updateOptions() ONLY updates key/value
        #pairs for which the key already exists.
        self._options.update({'BINS':GEAVars.plot.BINS})
        
        if not options is None:
            self.updateOptions(options)
        
    def _combineData(self):
        """Combine data for all the items (channels) present in self.dataList.

           NOTE: Should raise an exception if each element of self.dataList does not have the same amount of dimensions. 
        """
        combData=self.dataList[0]         #self.dataList always non-empty
        
        for data in self.dataList[1:]:
            combData.addComponents(data)
        
        self.dataList=[combData]
            
    def plot(self):
        
        #self._initFigure()
        self.makeCurrent()
        self._combineData()
        
        legendData=[]
        
        if not self.dataList[0].y:
            raise PlotException('Have no data to plot.')
            
        self._lines.append(hist(self.dataList[0].y, self._options['BINS']))    #self.dataList always non-empty (althought GEAData inside might be)
            
        if self._options['LEGEND'] and self.dataList[0].name:
            #For now also show number of data points used.
            legendData+=[(self._lines[0], ("%s (%d)" % (self.dataList[0].name, len(self.dataList[0].x)),))]
            
        self._setPlotOptions(legendData=legendData)

    def _setPlotOptions(self, legendData=None):
        
        self.makeCurrent()
        
        if legendData:
            
            lines    = ()
            textTups = ()
            for line, textTup in legendData:
                lines+=(line,)
                textTups+=textTup
            
            if   self._options['LEGEND'].lower()=='outside':
                legend(textTups, loc=2, bbox_to_anchor=(1.0, 1.0)) 
            elif self._options['LEGEND'].lower()=='inside':
                legend(textTups, loc='upper right') 
                gca().get_legend().get_frame().set_alpha(0.0)
            else:
                pass
        
        grid(self._options['GRIDLINES'])
        
        xlabel(self._options['XLABEL'])
        ylabel(self._options['YLABEL'])
        
        title(self._options['PLOTTITLE'])
        
        if self._options['YSCALE']!='linear':
            setp(self.axes, 'yscale', self._options['YSCALE'])
        
        #Setup axis ranges. If values provided in options are not '', use them; otherwise use the defaults.
        for newMin, newMax, orgMin, orgMax, ax  in ((self._options['XMIN'], self._options['XMAX'], 
                                                     self.axes.get_xlim()[0], self.axes.get_xlim()[1], 'x'),
                                                    (self._options['YMIN'], self._options['YMAX'], 
                                                     self.axes.get_ylim()[0], self.axes.get_ylim()[1], 'y')):        
            if newMin=='':
                newMin=orgMin
            if newMax=='':
                newMax=orgMax

            if float(newMin)==float(newMax)  and str(newMin) != '':
                raise PlotException('Min and Max for the %s-axis are both %s.  Cannot have zero range.' % (ax, newMin))
            
            setp(self.axes, ax+'lim', [newMin, newMax])
                
    def _convertOptionType(self, key, val):
        """Converts certain values to proper types. (ie. str->int, str->float, etc...)
            
        Each child should have a version of this method which takes care of child-specific options. 
            
        """        
        #string->float
        if key in ['BINS']:
            val=Validator.validateInt(option=val, minVal=1, maxVal=200, stream=self.fStream, 
                                      valueOnError=10, errorPreText='Validating %s... ' % key)                
        else:
            key, val=MatBasePlot._convertOptionType(self, key, val)
    
        return key, val                

    
class MatBarPlot(MatBasePlot):

    def __init__(self, dataList, fStream=GEAVars.errStream, options=None):

        MatBasePlot.__init__(self, dataList=dataList, fStream=fStream)

        #Setup defaults for these values by updating self._options directly. Using self.updateOptions() ONLY updates key/value
        #pairs for which the key already exists.
        #self._options.update({'BINS':GEAVars.plot.BINS})
        
        if not options is None:
            self.updateOptions(options)
        

    def plot(self):
        
        #self._initFigure()
        self.makeCurrent()
        self._combineData()
        
        legendData=[]
        
        if not self.dataList[0].y:
            raise PlotException('Have no data to plot.')
            
        self._lines.append(hist(self.dataList[0].y, self._options['BINS']))    #self.dataList always non-empty (althought GEAData inside might be)
            
        if self._options['LEGEND'] and self.dataList[0].name:
            #For now also show number of data points used.
            legendData+=[(self._lines[0], ("%s (%d)" % (self.dataList[0].name, len(self.dataList[0].x)),))]
            
        self._setPlotOptions(legendData=legendData)

    def _setPlotOptions(self, legendData=None):
        
        self.makeCurrent()
        
        if legendData:
            
            lines    = ()
            textTups = ()
            for line, textTup in legendData:
                lines+=(line,)
                textTups+=textTup
            
            if   self._options['LEGEND'].lower()=='outside':
                legend(textTups, loc=2, bbox_to_anchor=(1.0, 1.0)) 
            elif self._options['LEGEND'].lower()=='inside':
                legend(textTups, loc='upper right') 
                gca().get_legend().get_frame().set_alpha(0.0)
            else:
                pass
        
        grid(self._options['GRIDLINES'])
        
        xlabel(self._options['XLABEL'])
        ylabel(self._options['YLABEL'])
        
        title(self._options['PLOTTITLE'])
        
        #Setup axis ranges. If values provided in options are not '', use them; otherwise use the defaults.
        for newMin, newMax, orgMin, orgMax, ax  in ((self._options['XMIN'], self._options['XMAX'], 
                                                     self.axes.get_xlim()[0], self.axes.get_xlim()[1], 'x'),
                                                    (self._options['YMIN'], self._options['YMAX'], 
                                                     self.axes.get_ylim()[0], self.axes.get_ylim()[1], 'y')):        
            if newMin=='':
                newMin=orgMin
            if newMax=='':
                newMax=orgMax

            if float(newMin)==float(newMax)  and str(newMin) != '':
                raise PlotException('Min and Max for the %s-axis are both %s.  Cannot have zero range.' % (ax, newMin))
            
            setp(self.axes, ax+'lim', [newMin, newMax])
                
    def _convertOptionType(self, key, val):
        """Converts certain values to proper types. (ie. str->int, str->float, etc...)
            
        Each child should have a version of this method which takes care of child-specific options. 
            
        """        
        #string->float
        if key in ['BINS']:
            val=Validator.validateInt(option=val, minVal=1, maxVal=200, stream=self.fStream, 
                                      valueOnError=10, errorPreText='Validating %s... ' % key)                
        else:
            key, val=MatBasePlot._convertOptionType(self, key, val)
    
        return key, val                
        
if __name__=='__main__':
     
    d1=Data([[1,2,3],[2,54,66]])
    p1=MatTimePlot([Data], fStream=sys.stdout)
    print p1._options
    p1.plot()

    c=Colors()
    
    for i in range(20):
        print c.next()
        
        
if GEAVars.usePsyco:
    import psyco
    psyco.bind(MatTimePlot, rec=6)
