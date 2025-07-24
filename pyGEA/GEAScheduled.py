#!/usr/bin/python

import os
import sys
import GEAVars
from GEAException import PlotException
from GEADataHandler import EpicsDataExtractor
from GEAGeneral import naming, printExcept
from GEAPlot import MatTimePlot
from GEARequest import RequestProcessor
from GEATime import Time
from GEAHtml import HTMLDynChanTableWithPlots   #Used for parsing.
from pages.common.plotterPage import PlotterPage

class ScheduledPlotter(object):
    pass
    
class DailyPlotter(ScheduledPlotter):  

    def __init__(self, outStream=GEAVars.outStream):
        self.outStream=outStream
        self.now=Time()
        self.dailyDir=naming.createDailyDir()

    def generatePlots(self, dataStr, overwrite=True):
    
        parsedDataList=HTMLDynChanTableWithPlots(dataStr).parsedDataList
        
        for holder in parsedDataList:
            try:
                if not overwrite:
                    #Check whether a plot (actually a data file) with this name already exists.
                    fileName=os.path.join(self.dailyDir, 
                                          naming.genDailyName(name=holder.chanOrPat,     
                                          prefix=naming.dataPrefix, 
                                          suffix=''))
                                          
                    if os.path.isfile(fileName):
                        self.outStream.write('*** Skipping (Already exists): %s\n' % fileName)
                        continue   #Go to the next item.
                
                request=RequestProcessor.process(holder.queryStrPairs) 
                               
                self._generatePlot(request=request, 
                                   stream=self.outStream, 
                                   chanOrPat=holder.chanOrPat,
                                   humanName=holder.humanName)
                                   
            except KeyboardInterrupt:  
                raise       #Want to break... someone "ctrl-c"-ed 
            except Exception, e:
                self.outStream.write("\n---------\nError:\n%s\n---------\n" % printExcept())
        
    def _generatePlot(self, request, stream, chanOrPat, humanName):
        #Extract data
        fileName=request.get('SAVEDATA', None) or naming.genDailyName(name=chanOrPat, prefix=naming.dataPrefix)

        dataList=EpicsDataExtractor(request=request, 
                                    dataFileName=os.path.join(self.dailyDir, fileName), 
                                    fStream=stream).extract()
        #Plot
        request.update({'PLOTTITLE':"%s [Generated %s]" % (humanName or '', Time().string10)})
        p=MatTimePlot(dataList=dataList, fStream=stream, options=request)
        stream.write('*** Plotting: %s\n' % str(request))
        try:
            p.plot()
        except PlotException, e:  #Should call this PlotEmtpyException?!... 
            p.plotEmpty()  
            p.text(0.5, 0.5, str(e))     
        
        self._writePlots(request, stream, p, chanOrPat)
                   
    def _writePlots(self, request, stream, plot, chanOrPat):
    
        #for suffix, dpi in (('.Small.png', 25), ('.png', 85), ('.Large.png', 125)):
        for suffix, dpi in (('.Small.png', 35), ('.Large.png', 125)):
                        
            plot.write(os.path.join(self.dailyDir, 
                                    naming.genDailyName(name=chanOrPat, 
                                    prefix=naming.imPrefix, 
                                    suffix=suffix)),
                       dpi=dpi)
                                  
if __name__=='__main__':

    #Testing...
    from pages.daily.engineering.iqPage import dataStr 
    
    dailyPlotter=DailyPlotter()
    dailyPlotter.generatePlots(dataStr)
    
    

