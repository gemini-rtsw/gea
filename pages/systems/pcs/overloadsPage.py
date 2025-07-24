#!/usr/bin/python

# This code has been removed from the menu b/c there is a bug in GEADataHandler where it reads pv's that return an array of floats.
#
import os
from GEAGeneral import util, naming
from GEATime import Time
from GEAHtml import HTMLFormCont, HTMLTimeSelectorOverloads, HTMLOptionsOverloads, HTMLDynListTable, HtmlHelper
from GEADataHandler import EpicsDataExtractor             
import GEAVars
from pages.systems.pcsBasePage import PcsBasePage

class Constants:    
    class pnu:
        loadCellMax=500                   #Consider values over this number worth reporting.
        numberMax=10                  #If have more occurences that this number,  need a different cell color.
    
    class hyd:
        loadCellMax=2000
        sectorMax=40000
    
    plotterPageLink=GEAVars.dispatchScript+'/pages/common/plotterPage'

class OverloadsPage(PcsBasePage):
    """Core functionality is inherited from GEAPage.BasePage
    """        
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """ 
        PcsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        #Main form
        html.form=HTMLFormCont() #Form container.
        #cgifile is of the form:   /run/dispatch.gea/some_directories/file_without_py_extenstion
        html.form.vars.update(cgifile=self.calledName)
        html.doc.append(html.form)    
        
        #Time selector widget.
        html.timeSelector=HTMLTimeSelectorOverloads()
        html.timeSelector.vars.update(util.combineDict(Time(self.genTime.seconds-Time.secPerDay).toStartTimeDict(monthAsWord=True),
                                                       self.genTime.toEndTimeDict(monthAsWord=True)))  #Update the time vars (startday, startmonthr, etc..)
        html.form.append(html.timeSelector)
        
        html.options=HTMLOptionsOverloads()
        html.options.vars.update(source='Pneumatic')
        html.form.append(html.options)

    def _processRequest(self, request, stream):
        """Process the request.
        
        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which 
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function _assemblePage().
        """ 
        format=request.get('SOURCE', '')

        #For some extra data that may need to be passed to the _updatePage_* methods.
        options={}
            
        try:
            if format=='Pneumatic':
                #Set a channel for wchich to extract data.
                request['CHANNELS']='m1:apss:AxlOvrld'

            elif format=='Hydraulic':
                #Set a channel for wchich to extract data.
                request['CHANNELS']='m1:pss:AxlOvrld'
            else:
                pass
                        
            request['SYSTEMS']='pcs'

            request['TEXTDATA']=True     #Dealing with data that should be treated as text when extracting from the archive.
    
            fileName=naming.genName(prefix='overloads')
            
    
            #Extract data and update page.
            extractor=EpicsDataExtractor(request=request, 
                                                         dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, fileName), 
                                                         fStream=stream, archNames=['pcs']
                                                        )
            dataList=extractor.extract()

            self.__getattribute__('_updatePage_'+format)(dataList=dataList, 
                                                                                format=format, 
                                                                                request=request, 
                                                                                stream=stream, 
                                                                                startTime=extractor.startTime,
                                                                                endTime=extractor.endTime)
        finally:
            #Want to make sure we update the html widget with old values. 
            for widget in (self.html.options, self.html.timeSelector):
                self._setWidgetVars(widget, request, [])
            
    def _updatePage_Pneumatic(self, dataList, format, request, stream, **options):
   
        self.html.table=HTMLDynListTable()
        table=self.html.table  #So don't have to write so much.
        
        calledName=self.calledName.rstrip('?')+'?'      #Want to make sure have '?' at the end.
   
        table.setCellColSpan(0,0,2)
        table.setCellcontents(0,0, 
                              "<strong>Pneumatic</strong> Overloads for : %s - %s" % (options['startTime'].string1,  
                                                                              options['endTime'].string1),
                              {'class':'label1'})
         
        for data in dataList:   

            #Want the results in reverse order:
            data.x.reverse()
            data.y.reverse()
        
            #data.x is the time stamp and data.y a string containing the data.
            for timeStamp, dataStr in zip(data.x, data.y):
            
                eventTime=Time(float(timeStamp))
                
                #Setup times around the event time used for plotting.
                #HACK... have to offset times by one minute... 
                startTime=Time(eventTime.seconds-60)
                endTime=Time(eventTime.seconds+60)                
                
                dataStrList=map(lambda x: float(x.strip(',')), dataStr.split())
                num, nodes=dataStrList[0], dataStrList[1:]
            
                if num<1:
                    continue
                
                if num>Constants.pnu.numberMax:  
                    color='red'
                else:
                    color='orange'
                
                table.add_array_after_last_row(['Event time: %s' % eventTime.string11], 
                                               {'class':'heading'})
                table.setCellColSpan(table.getmaxRow(),0,2)
                    
                for index, node in zip(range(1, len(nodes)+1), nodes):
                    if node<=Constants.pnu.loadCellMax:
                        continue
                    
                    #Setup the queryString 
                    queryStringDict={'SYSTEMS':'pcsact', 'LEGEND':'On', 'GRIDLINES':'On',
                                    'PATTERN':'m1:ANB%03d:(PnuDemand|PnuLoadCell)' % index}
                    queryStringDict.update(startTime.toStartTimeDict(allCaps=True, monthAsWord=True))
                    queryStringDict.update(endTime.toEndTimeDict(allCaps=True, monthAsWord=True))
                    
                    link=HtmlHelper.createLink('ANB%03d' % index, Constants.plotterPageLink, **queryStringDict)
                        
                    table.add_array_after_last_row([link, '%s N' % node])
                    
        #Update the page. Note, adding self.html.table and NOT self.html.table.table. See GEAHtml.HTMLDynTable
        #to see the difference.
        self.html.doc.append(self.html.table)

    def _updatePage_Hydraulic(self, dataList, format, request, stream, **options):
        """
        """
        self.html.table=HTMLDynListTable()
        table=self.html.table  #So don't have to write so much.
        
        calledName=self.calledName.rstrip('?')+'?'      #Want to make sure have '?' at the end.
   
        table.setCellColSpan(0,0,2)
        table.setCellcontents(0,0, 
                              "<strong>Hydraulic</strong> Overloads for : %s - %s" % (options['startTime'].string1,  
                                                                              options['endTime'].string1),
                              {'class':'label1'})
        
        sectorsDict={1:'A', 2:'B', 3:'C', 4:'D', 5:'E', 6:'F'}
       
        for data in dataList:   #Should only have one item in dataList (only extracted data from one channel).
            
            #Want the results in reverse order:
            data.x.reverse()
            data.y.reverse()
            
            #data.x is the time stamp and data.y a string containing the data.
            for timeStamp, dataStr in zip(data.x, data.y):

                eventTime=Time(float(timeStamp))
                #Setup times around the event time used for plotting.
                startTime=Time(eventTime.seconds-60)
                endTime=Time(eventTime.seconds+60)                
                
                dataStrList=map(lambda x: int(x.strip(',')), dataStr.split())    #NOTE: values seem to be integers. 
                secAlarm, loadCellAlarm, axialLoad= dataStrList[0], dataStrList[1], dataStrList[2]
                sectors, nodes=dataStrList[3:9], dataStrList[9:]
            
                #First deal with sectors.
                if secAlarm>0:
    
                    table.add_array_after_last_row(['Event time: %s' % eventTime.string11, '%d sector(s) overloaded' % secAlarm],
                                                            {'class':'heading'})
                    
                    #Noticed a a couple of cases where had secAlarm>0 but none of the secotr values weve over Constants.hyd.sectorMax
                    #According to the pcs src, this should not happen.
                    secOverFlag=False           #Helper to remember if dealing with the situation outlined above.
                        
                    for index, sector in zip(range(1, len(sectors)+1), sectors):
                        if sector<=Constants.hyd.sectorMax:
                            continue
                            
                        secOverFlag=True

                        #Setup the queryString 
                        queryStringDict={'SYSTEMS':'pcsact', 'LEGEND':'On', 'GRIDLINES':'On',
                                                 'PATTERN':'m1:pss:ps:AxHydLoad.VAL%s' % sectorsDict[index]}
                        queryStringDict.update(startTime.toStartTimeDict(allCaps=True, monthAsWord=True))
                        queryStringDict.update(endTime.toEndTimeDict(allCaps=True, monthAsWord=True))
                        
                        link=HtmlHelper.createLink('Sector %s' % sectorsDict[index], Constants.plotterPageLink, **queryStringDict)
                            
                        table.add_array_after_last_row([link, '%s N' % sector])
                    
                    if not  secOverFlag:
                        #If endup here, had secAlarm>0 but no sectors actually overloaded.
                        table.add_array_after_last_row(['Sector Alarm set to %d but no sectors overloaded.' % secAlarm, 
                                                                      'Sector Values: %s' % str(sectors)])
                                            
                #Now with loadcells.
                if loadCellAlarm>0:

                    table.add_array_after_last_row(['Event time: %s' % eventTime.string11, '%d loadcell(s) overloaded' % loadCellAlarm],
                                                                  {'class':'heading'})
                        
                    for index, node in zip(range(1, len(nodes)+1), nodes):
                        
                        if node<Constants.hyd.loadCellMax:
                            continue
                            
                        #Setup the queryString 
                        queryStringDict={'SYSTEMS':'pcsact', 'LEGEND':'On', 'GRIDLINES':'On',
                                                'PATTERN':'m1:ANB%03d:HydLoadCell' % index}
                        queryStringDict.update(startTime.toStartTimeDict(allCaps=True, monthAsWord=True))
                        queryStringDict.update(endTime.toEndTimeDict(allCaps=True, monthAsWord=True))
                        
                        link=HtmlHelper.createLink('ANB%03d' % index, Constants.plotterPageLink, **queryStringDict)
                            
                        table.add_array_after_last_row([link, '%s N' % node])
                    
        self.html.doc.append(self.html.table)
        
def main(outStream=GEAVars.outStream, standAlone=False):


    OverloadsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(sys.stdout, standAlone=True)


    
    
