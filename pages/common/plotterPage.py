#!/usr/bin/python

from GEAData import Data 
from GEADataHandler import  autoHandleData, splitArchives, EpicsDataSpreadsheetExporter
from GEAGeneral import naming, util
from GEAHtml import HTMLPlot,  HTMLFormCont, HTMLTimeSelectorPlotting, \
                                HTMLDynChanSelector, \
                                HTMLTextBox, HtmlHelper, HTMLOptionsPlot2, \
                                HTMLChannelConfigOptions, HTMLEquationConfigOptions
from GEAPlot import MatTimePlot, MatHistPlot, MatXYPlot   
from GEARequest import RequestCollection, Request, RequestProcessor
from GEATime import Time
from GEAValidator import IntValidator
from pages.common.plotterBasePage import PlotterBasePage
import GEAVars
import os
import re
import sys
    
#Other imports done lower down; grep for 'import'...

#Have a small problem here. We may still have some channels that are under multiple categories, and 
#in fact be archived by multiple archivers. 
#This could potentially be an minor "issue" if the two archivers have different configurations
#(ie. how we monitor/write/etc a channel) for the same channel. The system does not 
#guarantee which archive the channel data will come from, and hence wich configuration was used.

gChanHier="common/plotterPage.channels"

class PlotterPage(PlotterBasePage):
    '''Core functionality is inherited from GEAPage.BasePage.
    '''
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        PlotterBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
                
        #Main form
        html.form=HTMLFormCont(vars={'cgifile':self.calledName}) #Form container.
        html.doc.append(html.form)    
           
        #Time selector widget.
        html.timeSelector=HTMLTimeSelectorPlotting()
        html.timeSelector.vars.update(Time.startEndTime2Dict(Time(self.genTime.seconds-Time.secPerDay), 
                                                             self.genTime, 
                                                             allCaps=False,
                                                             monthAsWord=True))
        html.form.append(html.timeSelector)
        
        #Plot options widget
        html.plotOptions=HTMLOptionsPlot2(vars={'reduce':GEAVars.plot.REDUCE,
                                                'dpi':GEAVars.plot.DPI,
                                                'fill':GEAVars.dataEx.FILL,
                                                'ylabel':'',
                                                'ymin':'',
                                                'ymax':'',
                                                'legend':GEAVars.plot.LEGEND,
                                                'format':'Plot',
                                                'gridlines':'checked', 
                                                'rateofchange':'',
                                                'xaxischannel':'',
                                                'xlabel':'',
                                                'plottitle':'',
                                                'yscale':'linear',
                                                'linestyle':GEAVars.plot.LINESTYLE,
                                                'interpolate':GEAVars.dataEx.INTERPOLATE
                                                 })
        html.form.append(html.plotOptions)
        
        html.chanConfigOptions=HTMLChannelConfigOptions()
        html.chanConfigOptions.vars.update(chanconfig='')
        html.form.append(html.chanConfigOptions)
      
        html.equationConfigOptions=HTMLEquationConfigOptions()
        html.equationConfigOptions.vars.update(equationconfig='', plotoperands='No', eqinterpolate='10')
        html.form.append(html.equationConfigOptions)
                
        #Channel selector widget.
        html.chanSelector=HTMLDynChanSelector(chanHierFile=gChanHier, vars={'systems':'',
                                                                           'systems2':'',
                                                                           'pattern':'',
                                                                           'channels':''})
        html.form.append(html.chanSelector)        

    def _updateTimeRangeFromCookie(self, request, stream):
        
        #Here we may need to adjust the time range, based on whether it has been "fixed" for 
        #all the requests. Check for a cookie.
        
        try:
            tRange=self.cookie.get('fixedTimeRange').value
            
            #Seems like we can't guarantee that a browser will delete a cookie when needed, 
            #to remedy this, lets consider a value of -1 to mean that no 
            #time range should be applied.
            if tRange.strip()=='-1':
                return False
                        
            #Expect the format to be something like:
            #<num> - <num> 
            d=map(lambda x: float(x.strip()), tRange.split('-'))
            st, et=Time(d[0]), Time(d[1])
            request.update(st.toStartTimeDict(allCaps=True, monthAsWord=True))
            request.update(et.toEndTimeDict(allCaps=True, monthAsWord=True))            
                        
        except (KeyError, IndexError, TypeError, AttributeError):
            return False
        
        return True


    def _processRequest(self, request, stream):
        """Process the request.
        """   
        request=RequestProcessor.process(request)
        
        r=self._updateTimeRangeFromCookie(request, stream)

        try:                
            #When coming from daily plots have a case where want to setup the widgets, but not
            #do the whole plot or create a spreadsheet right away - so need to skip calling self._generatePlot()/_generateSpreadsheet().
            if request.get('SKIPACTION', '').lower()=='true':
                #Add a notice to the beginning.
                self.html.doc.insert(0, HTMLTextBox(vars={'text':"Please select the time range (or use defaults) and click the 'Update' button."}))
            elif request.get('FORMAT', '')=='Spreadsheet':
                self._generateSpreadsheet(request, stream)
            else:                
                self._generatePlot(request, stream)
        finally:
            #Want to make sure we update the html widgets  with values from request. 
            for widget in (self.html.timeSelector, self.html.chanSelector, self.html.plotOptions, 
                            self.html.chanConfigOptions, self.html.equationConfigOptions):
                self._setWidgetVars(widget, request, [])
    
    def _dataConfig(self, dataList, request, stream):
        
        #Create a dictionary to hold all the config data.
        configDict={}        
        
        recSep=GEAVars.recSep  
        fieldSep=GEAVars.fieldSep
                
        chanConfig=request.get('CHANCONFIG', '')    

        if chanConfig:
            #Each record is a tuple of fields such as:
            #(<chan name>, <legend name>, <scaling>, <offset>)
            recordList=[record.split(fieldSep) for record in chanConfig.split(recSep)]
                          
            for chan, name, scale, offset in recordList:
                configDict[chan]=dict(name=name, scale=scale, offset=offset)
                               
        configDict=self._scaleData(dataList, configDict, request, stream)               
        configDict=self._legendConfig(dataList, configDict, request, stream) 
                                    

        #Finally updeate the request, in case some configuration values were changed (ex. blanks are replaced with defaults).
        recList=[]
        for chan, config in configDict.items():            
            recList.append(fieldSep.join([chan, config.get('name',''), str(config['scale']), str(config['offset'])]))
            
        request['CHANCONFIG']=recSep.join(recList)
            
    def _legendConfig(self, dataList, configDict, request, stream):
        
        for i in xrange(0, len(dataList)):            
            if configDict.has_key(dataList[i].name) and configDict[dataList[i].name].has_key('name'):                
                if configDict[dataList[i].name]['name']!='' and dataList[i].name!=configDict[dataList[i].name]['name']:                          
                    #Here we update the Data object with the new legend name.
                    dataList[i].legendName=configDict[dataList[i].name]['name']                                                        
        
        return configDict
                                    
    def _scaleData(self, dataList, configDict, request, stream):    
        """Scales data based on information in request.
        
        configDict is either empty or of the form:
        {<channel1>:{'offset':<val>, 'scale':<val>, ...}, <channel2>:{'offset':<val>, 'scale':<val>, ...}, ...}
        """    
        #Scale data.
        for i in xrange(0, len(dataList)):
            
            if not configDict.has_key(dataList[i].name):
                #If configDict does not have an entry for this channel, create it, and add an empty dictionary.
                #This will let us setup default scaling/offset values later on.
                configDict[dataList[i].name]={}
            
            if configDict[dataList[i].name].has_key('scale') and configDict[dataList[i].name].has_key('offset'):
                    
                scale=configDict[dataList[i].name]['scale']
                offset=configDict[dataList[i].name]['offset']
                                                                         
                if util.isStrLike(scale):
                    if scale=='':scale=1
                try:
                    scale=float(scale)
                except ValueError:                    
                    stream.write("Can't convert <strong>%s</strong> to a float; aborting scaling of channel <strong>%s</strong>\n" % (scale, dataList[i].name))
                    continue
                
                if util.isStrLike(offset):
                    if offset=='':offset=0
                try:
                    offset=float(offset)
                except ValueError:
                    stream.write("Can't convert <strong>%s</strong> to a number; aborting offsetting of channel <strong>%s</strong>\n" % (offset, dataList[i].name))
                    continue                                                                               
                                                                                                                                   
                nameSuffix=''

                #Don't scale if factor is 1.
                if scale!=1.0:
                    for t in range(0, len(dataList[i].y)): dataList[i].y[t] = float(dataList[i].y[t]) * scale	# Hack for now.

                    nameSuffix+='{x%s' % util.formatNum(scale)
            
                #Don't offset if offset is 0.
                if offset!=0:
                    #By default scale the y dimension.... in the future might expand this to any dimension.

                    for t in range(0, len(dataList[i].y)): dataList[i].y[t] = float(dataList[i].y[t]) + offset	# Hack for now.

                    if nameSuffix=='':nameSuffix='{'
                    nameSuffix+='%s' % util.formatNum(offset, showSign=True)                
                                                            
                configDict[dataList[i].name]['scale']=scale
                configDict[dataList[i].name]['offset']=offset      
                
                if nameSuffix:
                    #If have a name suffix, lets update the Data's legendName.                    
                    dataList[i].legendName=dataList[i].name+nameSuffix+'}'
                                
            else:
                #Add the channels that are not are not already in configDict with default values fro scale and offset.
                configDict[dataList[i].name]['scale']=1
                configDict[dataList[i].name]['offset']=0            
                
        return configDict
        
        
    def _equationsConfig(self, dataList, request, stream):
        #Create a dictionary to hold all the config data.
        
        #Lets start with properly setting the interpolation  value, which will be used for all the 
        #channels. Note that we are updating the actual value in the request, hence the form will be 
        #later updated with that, once we return with the plot.
        request['EQINTERPOLATE']=IntValidator(valueOnError=60, minVal=1, maxVal=1000,
                                errorPreText='Validating %s... ' % 'EQINTERPOLATE',
                                stream=stream).validate(request.get('EQINTERPOLATE', 60))        
        
        configDict={}        
        
        recSep=GEAVars.recSep  
        fieldSep=GEAVars.fieldSep
                                        
        equationConfig=request.get('EQUATIONCONFIG', '')    
                
        try:
            if equationConfig:
                #Each record is a tuple of fields such as:
                #(<equation>, <legend name>)
                recordList=[record.split(fieldSep) for record in equationConfig.split(recSep)]
                       
                #recordList now a list of tuples     
                for equation, name in recordList:
                    #Don't want duplicates, so only add if equation not already in.
                    if not configDict.has_key(equation):
                        configDict[equation]=dict(name=name)
                    
                                
            #Want to keep track of the channel names which were used in equations, 
            #in case the user does not want to plot them.
            equationChannelList=self._processEquations(dataList, configDict, request, stream)
            
            self._legendConfig(dataList, configDict, request, stream)

        finally:
            #Finally updeate the request, in case some configuration values were changed.
            recList=[]
            equations=configDict.keys()
            equations.sort()
            for equation in equations:   
                recList.append(fieldSep.join([equation, configDict[equation]['name']]))                
            
            request['EQUATIONCONFIG']=recSep.join(recList)        
        
        if request.get('PLOTOPERANDS','').lower()!='yes':
            #Want to get rid of the data for all channels which were operands in the equations,
            #so that we only keep the results.
            dataList=[item for item in dataList if item.name not in equationChannelList]
            
            #for i in [i for i in range(len(dataList)) if dataList[i].name in equationChannelList]:              
            #    del dataList[i]
                
        return dataList
                                    
    def _processEquation(self, dataList, equation, request, stream):

        #Expect something like:
        #<chan1><operand><chan2>
        #The operands are +,-,*,/
        regExp=re.compile(r"^([\w:\.]+)\s*([\+-/\*])\s*([\w:\.]+)$")

        result=regExp.search(equation.strip())
        if result is None:
            raise RuntimeError("Couldn't understand the equation '<strong>%s</strong>'." % equation)

        chan1, operator, chan2=result.groups()                
        #Start with doing only the selected ones.
        if chan1==chan2:
            #Special case; both operands are the same
            chanToInterList=[chan1]
        else:
            chanToInterList=[chan1, chan2]
                                
        #We expect names to be unique; see GEADataExtractor.py how this is done.                
        nameList=map(lambda x: x.name, dataList)   
        
        #print 'nameList', nameList
        #print 'equation', equation
        
        #Before we do any math, lets make sure that we actually got the right data.
        for chan in chanToInterList:
            if chan not in nameList:
                raise ValueError("Could not find data for channel '<strong>%s</strong>'; aborting calculations." % chan)
                    
        indexDict={}
        #Want to also build a dictionary with channel names and the channel's index 
        #in dataList.
        for i, chan in zip(range(len(nameList)), nameList):
            if chan in chanToInterList:
                indexDict[chan]=i
                    
        #Interpolate the channels that we found in the equeation.
        dataDict=self._interpolate(dataList, indexDict.values(), request, stream)                                  
                                
        #Could use eval here and not check each of the operands, but this is faster.                
        #Currently know, only dealing with two channels...                             
        if operator=='/':
            #Have to mask zeros so don't end up with infitities. 
            nonZero=Numeric.not_equal(dataDict[chan2].y,0)
            
            #How many data points do we have after we take out the zero denominators.
            validPoints=len(Numeric.nonzero(dataDict[chan2].y))
            if validPoints<2:
                raise ValueError('Not enough valid data points to plot the equation <strong>%s</strong>\n' % equation)
            
            totalPoints=len(dataDict[chan2].y)
            if validPoints<totalPoints:
                stream.write('NOTICE: Had to disregard %s data points with zero denominator before doing the division\nin the equation: <strong>%s</strong>\n' % (totalPoints-validPoints, equation))
            
            dataDict[chan1].y=Numeric.compress(nonZero, dataDict[chan1].y)                        
            dataDict[chan2].y=Numeric.compress(nonZero, dataDict[chan2].y)                        
                        
            #Technically we don't need to do this for both the x values for both of the channels
            #as only dataDict[chan1].x is used below to create a new Data object.            
            dataDict[chan1].x=Numeric.compress(nonZero, dataDict[chan1].x)
            #dataDict[chan2].x=compress(nonZero, dataDict[chan2].x)                         
            
            newY=dataDict[chan1].y/dataDict[chan2].y                        
        elif operator=='+':
            newY=dataDict[chan1].y+dataDict[chan2].y
        elif operator=='-':   
            newY=dataDict[chan1].y-dataDict[chan2].y        
        elif operator=='*':    
            newY=dataDict[chan1].y*dataDict[chan2].y           
        else:  
            raise RuntimeError("Do not understand the operator '%s'", operator)
    
        #After interpolating, expect the x values to be the same for channels we're performaing any
        #math on. Lets use the queation as the name of the new data.        
        dataList.append(Data([dataDict[chan1].x, newY], name=equation, legendName='', interpolated=True))
               
        #Want to return a list with the names of the channels we used in the equation, in case
        #decide not to plot them on their own.
        return [chan1, chan2]

    def _processEquations(self, dataList, configDict, request, stream):
        """In the future want to be cleverer, and build a binary tree from the 
        equation; for now only allow for one standard operation.
        Most of the code here is almost ready to handle/analyze/interpolate more than two 
        channels
        
        """        
        #Want to keep track of the channels we used for plotting, in case we do not need to plot them.
        equationChannelList=[]
        
        for equation in configDict.keys():      
            channelsUsed=self._processEquation(dataList, equation, request, stream)                                                                        
                   
            for chan in channelsUsed:
                if chan not in equationChannelList:
                    equationChannelList.append(chan)
                    
        return equationChannelList
          
    def _interpolate(self, dataList, indexList, request, stream):
        """
        Want to interpolate data in dataList with indecies from indexList.
        """    
  
        #Do a quick check if have enough data to interpolate for all the channels involved.
        for i in indexList:
            if len(dataList[i].x)<2:
                raise ValueError("Don't have enough data for channel '<strong>%s</strong>' to interpolate. Try a different time range." % dataList[i].name)
  
        from scipy import interpolate                
        from math import ceil, floor
        from scipy import arange
        
        #The EQINTERPOLATE value is validated in _equationsConfig()
        interDelta=int(request['EQINTERPOLATE'])            
                      
        #First lets find a correct min and max such that only look at
        #data in the time range common to all the channels. 
        #Hence the min will be a max of all the mins, and vice-versa for the max
        #Want to round to the nearest integer (second when dealing with x=time)
        try:
            dataMin=ceil(max(map(lambda i: min(dataList[i].x), indexList)))
            dataMax=floor(min(map(lambda i: max(dataList[i].x), indexList)))
        except ValueError:
            #We might be here if have empty sequences. Re-raise the error
            raise ValueError("Can't process equation. Data for channels does not overlap.\n")
        
        if dataMin > (dataMax-interDelta):
            raise ValueError("Can't process equation. Might want to try a smaller interpolation value.\n")
            
        #Create a new x range over which we'll have data
        xx=arange(dataMin, dataMax, interDelta)
        
        dataDict={}
        for i in indexList:       
            dataDict[dataList[i].name]=Data([xx, interpolate.interp1d(dataList[i].x,dataList[i].y)(xx)], 
											name=dataList[i].name, legendName=dataList[i].legendName, interpolated=True)
        
        return dataDict    
                                            
    def _generatePlot(self, request, stream):
        """Generate a plot. 
        """
        #Generate equevalent names for the data and image. They will be random generated, but have the same random 'stamp' and 
        #different prefix and suffix.
        imFileName, dataFileName=naming.genImDataNames()
        
        #See if got a name to use in the request
        dataFileName=request.get('SAVEDATA','') or dataFileName
                                            
        dataList=autoHandleData(request=request, stream=stream, dataFileName=dataFileName)
                                                                                                                                             
        self._dataConfig(dataList=dataList, request=request, stream=stream)
        
        if request.get('EQUATIONCONFIG') is not None:
            #_equationsConfig may change dataList, hance want to reasign the result.
            dataList=self._equationsConfig(dataList=dataList, request=request, stream=stream)
                            
        #Create a plot.
        if request.get('PLOTTYPE','')=='Histogram':
            #Have a histogram.
            p=MatHistPlot(dataList=dataList, fStream=stream, options=request)
            
        elif request.get('XAXISCHANNEL', ''):
            #Special case... want to have a XY plot - not a time plot.
            #A bit hackish for now... lets see if this works. In the long run, should probably set this up under GEAAnalyzer.
            xChannelName=request['XAXISCHANNEL']
            
            try:
                i=[item.name for item in dataList].index(xChannelName)
            except ValueError:
                raise ValueError("Cannot find the channel <strong>%s</strong> or it does not contain any data. Cannot plot other channels against it.\n" % xChannelName)
                
            xChannelDataLen=len(dataList[i].y)
                
            for j in range(len(dataList)):
                if j==i: 
                    continue
                    
                if len(dataList[j].x)!=xChannelDataLen:
                    raise ValueError("""Number of data points doesn't match for the channels <strong>%s</strong> and <strong>%s</strong>. 
Cannot plot one against the other.\n""" % (xChannelName, dataList[j].name))

                dataList[j].x=dataList[i].y
        
            #Update the xlabel with the channel name.
            request['XLABEL']=xChannelName
            
            del(dataList[i])
            
            p=MatXYPlot(dataList=dataList, fStream=stream, options=request)
        else:
            #Assume TimePlot
            p=MatTimePlot(dataList=dataList, fStream=stream, options=request)
            
        p.plot()

        imFileName=request.get('SAVEIMAGE','') or imFileName
        #When writing the image, need to specify the tmp directory with respect to the file system path.
        p.write(os.path.join(GEAVars.path.fileSys.wwwData, imFileName))
                   
        #Now that generated a plot, lets update self.html with a simple HTMLPlot object which will just show the image.
        self.html.plotImage=HTMLPlot(vars={'imagefilename':os.path.join(GEAVars.path.web.wwwData, imFileName),
                                           'datafilename':os.path.join(GEAVars.path.web.wwwData, dataFileName)}
                                           )
        #Add at the beginning.
        self.html.doc.insert(0, self.html.plotImage)
                   
        #Add the rate of change plot if requested. 
        if request.get('RATEOFCHANGE', '').lower()=='checked':   # Handle rate of chage (ROT) plots.
            from GEAAnalyzer import RateOfChangeAnalyzer
            
            imFileName, dataFileName='%s.roc.png' % imFileName[:-4], dataFileName+'.roc'

            dataList=RateOfChangeAnalyzer(dataList, dataFileName).process()

            #Need to modify the options for the rate of change plot a litle; in the future might want to add widgets and 
            #allow users to specify these.
            rocRequest=dict(request)
            rocRequest.update({'YMIN':None, 'YMAX':None, 'YSCALE':'linear',
                               'PLOTTITLE':request.get('PLOTTITLE', '')+' [RoC]'})
            
            p=MatTimePlot(dataList=dataList, fStream=stream, options=rocRequest)
            
            p.plot()
            #When writing the image, need to specify the tmp directory with respect to the file system path.
            p.write(os.path.join(GEAVars.path.fileSys.wwwData, imFileName))
            
            #Now that generated a plot, lets update self.html with a simple HTMLPlot object which will just show the image.
            self.html.rocPlotImage=HTMLPlot(vars={'imagefilename':os.path.join(GEAVars.path.web.wwwData, imFileName),
                                                  'datafilename':os.path.join(GEAVars.path.web.wwwData, dataFileName)}
                                            )
            #Add at after the main plot.
            self.html.doc.insert(1, self.html.rocPlotImage)

    def _generateSpreadsheet(self, request, stream):
    
        fileName=request.get('EXPORTFILENAME') or naming.genName(prefix=naming.exportPrefix, suffix='.txt')
        
        #Note that here we don't care about the returned data; it has been exported to a file.
        dataList=autoHandleData(request=request, stream=stream, dataFileName=fileName)        

        #EpicsDataSpreadsheetExporter(request=request,  
        #                                                exportFileName=os.path.join(GEAVars.path.fileSys.wwwData, fileName),
        #                                                fStream=stream,
        #                                                ).export()

        link=HtmlHelper.createLink('Spreadsheet', os.path.join(GEAVars.path.web.wwwData, fileName))
        text='''Please click on the following link for the data:
%s
<strong>Note that there is now a new 'Fill' option available, which will fill columns 
with repeated values. It may be useful when looking at or comparing multiple channels.''' % link
                    
        #Have to update the widget.
        self.html.textBox=HTMLTextBox(vars={'text':text})
        #Add at the beggining of the page.
        self.html.doc.insert(0, self.html.textBox)
          
def main(outStream=GEAVars.outStream, standAlone=False):
    PlotterPage(outStream, standAlone).run()

if __name__=='__main__':
    main(GEAVars.outStream, standAlone=True)
        
if GEAVars.usePsyco:
    import psyco
    psyco.bind(MatTimePlot, rec=4)
    

