#!/usr/bin/python

from pages.remedyBasePage import RemedyBasePage
    
from GEATime import Time
from GEARequest import RequestCollection, Request, RequestProcessor
from GEAHtml import HTMLDynListTable, HTMLFormFrs, HTMLCont, HtmlHelper, HTMLFormCont2, \
                                      HTMLTimeSelectorFrsStats, HTMLOptionsFrsStats, MenuItem, \
                                      HTMLOptionsFrsUser, HTMLOptionsFrsTicket, HTMLPlot, HTMLTextBox
from GEADataHandler import RemedyDataExtractor      
from GEAGeneral import util, naming
import GEAVars
import os
import re
import cgi   #for escape()

        
import matplotlib
matplotlib.use(GEAVars.plot.backend)  
from matplotlib.pylab import *

import GEAPlot
GEAPlot.matplotlibConfig()          


class FrsPage(RemedyBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    format2Title={'last24Hours':'Fault Summary:Last 24 Hours',
                  'last7Days':'Fault Summary:Last 7 Days',
                  'thisWeek':'Fault Summary:This Week',
                  'thistwoWeeks':'Fault Summary:Last 2 weeks',
                  'night':'Nightly',
                  'ticket':'Ticket',
                  'user':'User',
                  'section':'Section',
                  'stats':'Statistics/Graphs',
                  }
                    
    
    menuItemList=[MenuItem('Faults Summary', GEAVars.dispatchScript+'/pages/remedy/frsPage?'),
                  MenuItem('Ticket Search', GEAVars.dispatchScript+'/pages/remedy/frsPage?FORMAT=ticket'),
                  MenuItem('User Search', GEAVars.dispatchScript+'/pages/remedy/frsPage?FORMAT=user'),
                  MenuItem('Stats/Graphs', GEAVars.dispatchScript+'/pages/remedy/frsPage?FORMAT=stats'),  
                 ]
                
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        if topMenuList is None: topMenuList=[]   
        #Want to keep a reference to the top menu in case want to add links from inside _processRequest()
        self.topMenuList=[FrsPage.menuItemList]+topMenuList 
        
        RemedyBasePage._assemblePage(self,  topMenuList=self.topMenuList)
        html=self.html  
                      
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A dictionary (or a RequestCollection) of nameTag/request pairs {<nameTag>:<request>, ...} should be returned. 
        """
        #Being very explicit, so that it is clear what is being done.
        
        nameTag=None            #Do not need a nameTag,  because do not have multiple objects (widgets) of the same type on this page.
        request={'FORMAT':'last24Hours', 'SITE':GEAVars.site}
               
        r=Request(request=request, nameTag=nameTag)
       
        return RequestCollection({nameTag:r})
    
    def _processRequest(self, request, stream):
        """Process the request.
        
        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which 
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function _assemblePage().
        
        NOTE... could actually get rid of last24Hours, last7Days, etc... formatf
        d use timeRange along with 
        LAPSE query string variable instead... swomething like:
        
        /pages/remedy/frsPage?SITE=CP&FORMAT=timeRange&LAPSE=1440
        
        to see the last 24 hours..
                
        """ 
        #Need to process request a little to make it usable (ex. deal with LAPSE=<number>)
        request = RequestProcessor.process(request)
        
        format=request.get('FORMAT', '')                      
                        
        rKeys=('Site', 'CaseID', 'Occurrence Date', 'Create Date', 'Status', 'Disposition',
            'TimeLost', 'One line summary', 'Category', 'System', 'Subsystem',
            'Component', 'AssignedTo', 'Related_Master_Flag', 'Related ID')

        rQuery=''

        try:
            options={'startTime':None, 'endTime':None}
        
            if format=='last24Hours': 
                site=request['SITE'] 
                options['endTime']=Time(site=site)
                options['startTime']=Time(seconds=options['endTime'].seconds-Time.secPerDay, site=site)
 
            elif format=='last7Days': 
                site=request['SITE']                
                options['endTime']=Time(site=site)
                options['startTime']=Time(seconds=options['endTime'].seconds-Time.secPerDay*7, site=site)
                
            elif format=='last30Days': 
                site=request['SITE']                
                options['endTime']=Time(site=site)
                options['startTime']=Time(seconds=options['endTime'].seconds-Time.secPerDay*30, site=site)

            elif format=='last3Months':
                site=request['SITE']                
                options['endTime']=Time(site=site)
                options['startTime']=Time(seconds=options['endTime'].seconds-Time.secPerDay*92, site=site)
 
            elif format=='night':
                site=request['SITE']    
                #Start time has been chosen by the user.
                options['startTime']=Time(site=site).fromStartTimeDict(request, allCaps=True)
                #endTime is startTime+36hours.
                options['endTime']=Time(seconds=options['startTime'].seconds+1.5*Time.secPerDay, site=site)

            elif format=='thisWeek':
                #Look at data from last friday 0730
                site=request['SITE']    
                options['startTime']=Time(site=site, option='weekStart')  #Friday 0730
                options['endTime']=Time(site=site)
                
            elif format=='thistwoWeeks':
                #Look at data from last friday + a week at 0730
                site=request['SITE']    
                options['startTime']=Time(site=site, option='twoweekStart')  #Friday 0730
                options['endTime']=Time(site=site)
                
            elif format=='timeRange':
                site=request['SITE']   
                #Look at data for some arbitrary time period, given in the request. 
                options['startTime']=Time(site=site).fromStartTimeDict(request, allCaps=True)
                options['endTime']=Time(site=site).fromEndTimeDict(request, allCaps=True)

            elif format=='stats':
                site=request.get('SITE', GEAVars.site)
                try:
                    options['startTime']=Time(site=site).fromStartTimeDict(request, allCaps=True)
                    options['endTime']=Time(site=site).fromEndTimeDict(request, allCaps=True)
                except KeyError:
                    #Can't create time from the request... default to data from the last 7 days
                    options['endTime']=Time(site=site)
                    options['startTime']=Time(seconds=options['endTime'].seconds-Time.secPerWeek, site=site) 
                
            elif format=='ticket':
                caseId=request.get('CASEID', '')

                #Do some checks
                try:
                    i=int(caseId)
                    assert(i>0)
                except (AssertionError, ValueError):
                    caseId=''  #Treat bad format as empty str.
        
                if caseId:
                    rQuery="'CaseID'=%s" % request.get('CASEID', '')
                    rKeys=('CaseID', 'Site', 'Name', 'Occurrence Date', 'Create Date', 'Priority',
                           'Related ID', 'AssignedTo', 'Also Notify', 'Status', 'Disposition', 'Related_Master_Flag',
                           'TimeLost', 'One line summary', 'Detailed description', 'Work done', 'Attachments',
                           'Resolution', 'Category','System', 'Subsystem', 'Component', 'AssignedTo')
                else:
                    rQuery=""
                    rKeys=()
                       
            elif format=='user':

                user=request.get('USER', '')
            
                if user:
                    rQuery="'AssignedTo'=\"%s\"" % user
                    
                    filter=request.get('FILTER', 'Assigned/InProgress')
                    if filter=='Assigned/InProgress':
                        rQuery += " AND ('Status'=\"Assigned\" OR 'Status'=\"Work In Progress\")"
                    elif filter=='Closed':
                        rQuery += " AND 'Status'=\"Closed\""
                else:
                    rQuery=""
                    rKeys=()
                            
            elif format=='category':

                #This case handles category/system/subsystem/component
        
                def queryAdd(queryList, queryKey, itemKey):
                    if request.get(itemKey):
                        queryList.append('(\'%s\'="%s")' % (queryKey, request[itemKey]))
                    return queryList
    
                #Construct the query.
                queryList=[]
    
                # for queryKey, itemKey in (('Category', 'CATEGORY'), ('System', 'SYSTEM'), ('Subsystem', 'SUBSYSTEM'), ('Component', 'COMPONENT')):
                for queryKey, itemKey in (('Category', 'CATEGORY'), ('System', 'SYSTEM'), ('Subsystem', 'SUBSYSTEM')):
                    queryList=queryAdd(queryList, queryKey, itemKey)
                
                rQuery=' AND '.join(queryList)
                rKeys=('CaseID','Status','Disposition', 'TimeLost','One line summary','AssignedTo','Create Date',)

            else:
                raise RuntimeError('FORMAT not understood.')
                
            #Extract data and update page.
            if rKeys:
                dataList=self._extractRemedyData(request=request, 
                                                                    rQuery=rQuery,
                                                                    rKeys=rKeys, 
                                                                    stream=stream, 
                                                                    startTime=options['startTime'], 
                                                                    endTime=options['endTime'])
            else:
                dataList=[]
            self.__getattribute__('_updatePage_'+format)(dataList=dataList, 
                                                                                format=format, 
                                                                                request=request, 
                                                                                stream=stream,
                                                                                **options)
                
        finally:
            if self.html.has_key('form'):

                #Now that frsPage is so versitile, maybe should come up with a prettier way to do this.. 
                if format=='last24Hours' or format=='last7Days' or format=='thisWeek' or format=='thistwoWeeks':
                    #If format was not 'night'  (but last24Hours for example) then request may not  have the neccessary
                    #time data (ie keys like STARTDAY, STARTMINUTE, etc) to update the time selectoin widget...
                    #therefore need to create them.
                    request.update(Time(site=GEAVars.site, option='rollover0730').toStartTimeDict(monthAsWord=False))

                self._setWidgetVars(self.html.form, request, [])
            
            for widget in ('options', 'timeSelector'):
                if self.html.has_key(widget):
                    self._setWidgetVars(self.html[widget], request, [])

            #Want to update the header title based on what FORMAT was requested. This was already done when the page was first assembed, 
            #but now the QUERY_STRING has been parsed and we have info of the FORMAT.
            if FrsPage.format2Title.has_key(format):
                extra=':%s' % FrsPage.format2Title.get(format, '')
                self.html.doc.vars.update(headerinfo=self._getHeaderInfo()+extra)
            
    def _updatePage_last24Hours(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)
            
    def _updatePage_last7Days(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)
        
    def _updatePage_last30Days(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)
                
    def _updatePage_last3Months(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)                
            
    def _updatePage_night(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)
        
    def _updatePage_thisWeek(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)
                                
    def _updatePage_thistwoWeeks(self, dataList, format, request, stream, **options):
        #Same as self._update_timeRange()
        self._updatePage_timeRange(dataList, format, request, stream, **options)
                                
    def _updatePage_timeRange(self, dataList, format, request, stream, **options):
   
        #Want to add a form with some options to the page.
        self.html.form=HTMLFormFrs(vars={'cgifile':self.calledName}) #Form container.
        #Add the form to the beginning of the doc
        self.html.doc.insert(0, self.html.form) 

        table=HTMLDynListTable(tableAttrs={'width':"100%"})
        # table.setCellColSpan(0,0,6)

        site=request['SITE']
        
        startTime=options['startTime']
        endTime=options['endTime']
        table.setCellcontents(0,0, '<strong>%s</strong> Fault Reports (%s)' % (site, Time.timeRange2Str(startTime, endTime)),
                                  {'class':'FRSLabel', 'align':'center'})

        self.html.doc.append(table)
        
        self.html.table = HTMLDynListTable(tableAttrs={'width':"100%",  'class':"sortable", 'id':"sortable_frs"})
        table = self.html.table

        header=['CaseID', 'R', 'Status', 'TimeLost', 'Category|System|Subsystem', 'AssignedTo', 'One line summary']
        table.add_array_after_last_row(header, {'class':'heading'})

        for item in dataList:

            if item['Occurrence Date'] is None: item['Date'] = item['Create Date']
            else:                               item['Date'] = item['Occurrence Date']
            item['Date'] = item['Date'].strftime("%a %b %d %H:%M:%S %Y")

            relationship = 'U '	# Unrelated.
            if item['Related_Master_Flag'] == 'Master': relationship = 'M ' 
            if item['Related ID']:
                relationship = '<span title="' + item['Related ID'] + '">D </span>'

            # item['Status'] = relationship + item['Status']
        
            item['CaseID']=HtmlHelper.createLink('<span title="' + item['Date'] + '">' + item['CaseID'] + '</span>',
                                                self.calledName,
                                                FORMAT='ticket',
                                                SITE='MK/CP',               #Want to probe both sites.
                                                CASEID=item['CaseID'])
                                            
            item['AssignedTo']=HtmlHelper.createLink(item['AssignedTo'],
                                                    self.calledName,
                                                    FORMAT='user',
                                                    SITE='MK/CP',               #Want to probe both sites.
                                                    USER=item['AssignedTo'])
                                            
            #Want to have links to not only the categories, but also to systems, subsystems, and components.

            caty=HtmlHelper.createLink(item['Category'],
                                              self.calledName,
                                              FORMAT='category',
                                              CATEGORY=item['Category']
                                              )
            syst=HtmlHelper.createLink(item['System'],
                                              self.calledName,
                                              FORMAT='category',
                                              CATEGORY=item['Category'],
                                              SECTION=item['System']
                                              ) 
            ssys=HtmlHelper.createLink(item['Subsystem'],
                                              self.calledName,
                                              FORMAT='category',
                                              CATEGORY=item['Category'],
                                              SYSTEM=item['System'],
                                              SUBSYSTEM=item['Subsystem']
                                              )     
            """
            comp=HtmlHelper.createLink(item['Component'],
                                              self.calledName,
                                              FORMAT='category',
                                              CATEGORY=item['Category'],
                                              SYSTEM=item['System'],
                                              SUBSYSTEM=item['Subsystem'],
                                              COMPONENT=item['Component']
                                              )     
    
            table.add_array_after_last_row([item['CaseID'],
                                            item['Status'],
                                            item['TimeLost'],
                                            '%s | %s | %s | %s' % (caty, syst, ssys, comp),
                                            item['AssignedTo'],
                                            item['One line summary']])
            """
            table.add_array_after_last_row([item['CaseID'],
                                            relationship,
                                            item['Status'],
                                            item['TimeLost'],
                                            '%s | %s | %s ' % (caty, syst, ssys),
                                            item['AssignedTo'],
                                            item['One line summary']])
        self.html.doc.append(table)
        
    def _extractStatsData(self, dataList, showCategory=True, showSystem=True, showSubsystem=True):
    
        class modDict(dict):
            """Want to be able to have a dict with user defined attributes.
            """            
            def toLists(self, prefixName=''):
                """
                """
                names=[]
                mkTimeLoss=[]
                mkZeroTimeFaultCount=[]

                cpTimeLoss=[]
                cpZeroTimeFaultCount=[]                

                for name, d in self.iteritems():
                    if len(d)>0:
                        lists=d.toLists(prefixName=prefixName+name+' | ')
                        names+=lists[0]
                        
                        mkTimeLoss+=lists[1]
                        mkZeroTimeFaultCount+=lists[2]
                        
                        cpTimeLoss+=lists[3]
                        cpZeroTimeFaultCount+=lists[4]
                    else:
                        name=prefixName+name
                        names.append(name)
                        
                        mkTimeLoss.append(d.timeLostMK)
                        mkZeroTimeFaultCount.append(d.zeroTimeFaultCountMK)
                        
                        cpTimeLoss.append(d.timeLostCP)
                        cpZeroTimeFaultCount.append(d.zeroTimeFaultCountCP)
                    
                return [names, mkTimeLoss, mkZeroTimeFaultCount, cpTimeLoss, cpZeroTimeFaultCount]
                
        data=modDict()

        for item in dataList:

            category=item['Category']
            site={'GN':'MK', 'GS':'CP'}[item['Site']]
            timeLost=float(item['TimeLost'])

            if not data.has_key(category):
                data[category]=modDict()
                data[category].timeLostMK=0.0
                data[category].timeLostCP=0.0
                data[category].zeroTimeFaultCountMK=0
                data[category].zeroTimeFaultCountCP=0
                data[category].count=0

            data[category].count+=1
            data[category].__dict__['timeLost'+site]+=timeLost
            if float(timeLost)==0.0:
                data[category].__dict__['zeroTimeFaultCount'+site]+=1

            if showSystem:
                system=item['System']
                if not data[category].has_key(system):
                    data[category][system]=modDict()
                    data[category][system].timeLostMK=0.0
                    data[category][system].timeLostCP=0.0
                    data[category][system].zeroTimeFaultCountMK=0
                    data[category][system].zeroTimeFaultCountCP=0
                    data[category][system].count=0

                data[category][system].count+=1  
                data[category][system].__dict__['timeLost'+site]+=timeLost
                if float(timeLost)==0.0:
                    data[category][system].__dict__['zeroTimeFaultCount'+site]+=1

                if showSubsystem: 
                    subsystem=item['Subsystem']
                    if not data[category][system].has_key(subsystem):
                        data[category][system][subsystem]=modDict()
                        data[category][system][subsystem].timeLostMK=0.0
                        data[category][system][subsystem].timeLostCP=0.0
                        data[category][system][subsystem].zeroTimeFaultCountMK=0
                        data[category][system][subsystem].zeroTimeFaultCountCP=0
                        data[category][system][subsystem].count=0
                        
                    data[category][system][subsystem].count+=1
                    data[category][system][subsystem].__dict__['timeLost'+site]+=timeLost
                    if  float(timeLost)==0.0:
                        data[category][system][subsystem].__dict__['zeroTimeFaultCount'+site]+=1

# TODO (maybe): Component
    
        return data
            
    def _updatePage_stats(self, dataList, format, request, stream, **options):

        startTime=options['startTime']
        endTime=options['endTime']

        html=self.html
    
        #Want to add a form with some options to the page.
        html.form=HTMLFormCont2(vars={'cgifile':self.calledName}) #Form container.
        html.doc.insert(0, html.form) 
        
        #Add a time selector and some optoins
        html.timeSelector=HTMLTimeSelectorFrsStats()
        html.timeSelector.vars.update(Time.startEndTime2Dict(startTime, endTime, allCaps=False, monthAsWord=True)) 
        html.form.append(html.timeSelector)
        html.options=HTMLOptionsFrsStats(vars={'format':'stats', 'view':'StatsTable','ymin':'', 'ymax':''})
        html.form.append(html.options)
        
        #Decide hot much detail to show...
        show=request.get('SHOW', 'Category/System/Subsysten').lower()  #By default show all.
        showCategory  = True
        showSystem    = True
        showSubsystem = True
        if show == 'category/system':
            showSubsystem = False
        if show == 'category':
            showSystem    = False
            showSubsystem = False
        
        data=self._extractStatsData(dataList, showCategory=showCategory, showSystem=showSystem)
        
        view=request.get('VIEW', 'StatsTable')
        
        self.__getattribute__('_updatePage_stats_'+view)(request, stream, data, showCategory, showSystem, showSubsystem, **options)
        
    def _updatePage_stats_Plot(self, request, stream, data, showCategory, showSystem, showSubsystem, **options):
        
        self.html.table = HTMLDynListTable(tableAttrs={'width':"100%"})
        table=self.html.table
        table.add_array_after_last_row(['Coming Soon'], {'class':'heading'}) 
        
        startTime=options['startTime']
        endTime=options['endTime']
         
        timeRange='(%s - %s)' % (options['startTime'].string7,  options['endTime'].string7)

        #TESTING... this should all be done in pyGEA/GEAPlot.py. For now more of a 'proof of concept' type code.
        
        names, mkTimeLoss, mkFaultCount, cpTimeLoss, cpFaultCount=data.toLists()
        
        self.html.doc.append(HTMLTextBox(vars={'text':'Click on the images to see raw data as text.'}))

        #Time Loss
        imageFileName, dataFileName=naming.genImDataNames()
        self._plotStatsData(request, stream, 'Time Loss '+timeRange , 'Hours', imageFileName, dataFileName, (names,  mkTimeLoss, cpTimeLoss))
        self.html.timeLossPlot=HTMLPlot(vars={'imagefilename':os.path.join(GEAVars.path.web.wwwData, imageFileName),
                                              'datafilename':os.path.join(GEAVars.path.web.wwwData, dataFileName)})
        self.html.doc.append(self.html.timeLossPlot)
        
        #Fault Count
        imageFileName, dataFileName=naming.genImDataNames()
        self._plotStatsData(request, stream, 'Zero Time Loss Events '+timeRange, 'Count', imageFileName, dataFileName, (names, mkFaultCount, cpFaultCount )) 
        self.html.faultCountPlot=HTMLPlot(vars={'imagefilename':os.path.join(GEAVars.path.web.wwwData, imageFileName),
                                                'datafilename':os.path.join(GEAVars.path.web.wwwData, dataFileName)})
        self.html.doc.append(self.html.faultCountPlot)
        
    def _plotStatsData(self, request, stream, aTitle, aYLabel, imageFileName, dataFileName, dataList):
        """Hope to move most of the stuff here to pyGEA/GEAPlot.py
        """
                
        aXTickLabels, data1, data2=dataList

        elNum=len(aXTickLabels)          #All the lists will have the same lenght.
        ind=arange(elNum)
        width = 0.2 
        
        maxEl=20   #Max number of elements before start enlarging figure
        if elNum<maxEl:
            #If only have few elements, use the 'standard' size.
            figure(1, figsize=(8,6), facecolor='w', edgecolor='w')
            ax=axes([0.1, 0.4, 0.8, 0.55]) 
        else:
            figWidth=8+(elNum-maxEl)*width
            #Attempt to scale the size based on how much data we have to plot.
            figure(1, figsize=(figWidth,6), facecolor='w', edgecolor='w')
            ax=axes([0.8/figWidth, 0.4, 1.0-2*0.8/figWidth, 0.55]) 
                      
        grid(True)
        ylabel(aYLabel)
        title(aTitle)
        mkLines=bar(ind, data1, width, color='r')
        cpLines=bar(ind+width, data2, width, color='b')    
        setp(gca(), 'xticks', ind+width)
        labels = setp(gca(), 'xticklabels', aXTickLabels)
        setp(labels, 'rotation', 'vertical')
        setp(labels, 'fontsize', 8)
        setp(gca(), 'xlim', [-width,len(ind)])
        if mkLines and cpLines:
            legend( (mkLines[0], cpLines[0]), ('Mauna Kea', 'Cerro Pachon') )
        
        #Setup axis ranges. If values provided in options are not '', use them; otherwise use the defaults.
        #Took this from pyGEA/GAEPlot.py... for now.
        request['XMIN']=request.get('XMIN','')
        request['XMAX']=request.get('XMAX','')
        request['YMIN']=request.get('YMIN','')
        request['YMAX']=request.get('YMAX','')

        for newMin, newMax, orgMin, orgMax, a  in ((request['XMIN'], request['XMAX'], 
                                                     ax.get_xlim()[0], ax.get_xlim()[1], 'x'),
                                                    (request['YMIN'], request['YMAX'], 
                                                     ax.get_ylim()[0], ax.get_ylim()[1], 'y')):        
            if newMin=='':
                newMin=orgMin
            if newMax=='':
                newMax=orgMax

            if float(newMin)==float(newMax)  and str(newMin) != '':
                raise PlotException('Min and Max for the %s-axis are both %s.  Cannot have zero range.' % (a, newMin))
    
            setp(ax, a+'lim', [newMin, newMax])

        savefig(os.path.join(GEAVars.path.fileSys.wwwData, imageFileName)) 
        
        #Write the raw data.
        f= file(os.path.join(GEAVars.path.fileSys.wwwData, dataFileName), 'w')
        if f:
            f.write('%#-80s%#10s%#10s\n' % ('Category','MK data', 'CP data'))
            for index in range(len(dataList[0])):
                f.write('%#-80s%#10s%#10s\n' % (dataList[0][index],dataList[1][index],dataList[2][index]))
            f.close()
        
        cla()   #Cleanup.
        
    def _updatePage_stats_StatsTable(self, request, stream, data, showCategory, showSystem, showSubsystem, **options):
        
        startTime=options['startTime']
        endTime=options['endTime']
        
        totalTimeMK, totalTimeCP, zeroTimeTotalFaultsMK, zeroTimeTotalFaultsCP = 0.0, 0.0, 0, 0
        
        self.html.table = HTMLDynListTable(tableAttrs={'width':"100%"})
        table=self.html.table

        table.setCellColSpan(0,0,9)
        table.setCellcontents(0,0, 'Time loss data for %s' % Time.timeRange2Str(startTime, endTime), {'class':'FRSLabel', 'align':'center'})
                
        #Setup the header.
        header1=['','','', 'Time Lost (hours)', '', '', 'Zero Time Loss Events', '', '']
        header2=['Category','System', 'Subsystem', 'MK', 'CP', 'MK/CP', 'MK', 'CP', 'MK/CP '] 

        table.add_array_after_last_row(header1, {'class':'heading'}) 
        table.add_array_after_last_row(header2, {'class':'heading'}) 
        table.setCellColSpan(1,0,3)
        table.setCellColSpan(1,3,3)
        table.setCellColSpan(1,6,3)
 
        #Might need some colspan adjusting.
        if showCategory:
            pass
        elif showSystem:
            header1[2]=''
            table.setCellColSpan(table.getmaxRow(), 1,2)
        else:
            header1[1:2]=['','']
            table.setCellColSpan(table.getmaxRow(), 0,3)
                
        categorys=data.keys()
        categorys.sort()
        
        for cat in categorys:
                 
            category=data[cat]
            
            #Update item stats.
            totalTimeMK           += category.timeLostMK
            totalTimeCP           += category.timeLostCP
            zeroTimeTotalFaultsMK += category.zeroTimeFaultCountMK
            zeroTimeTotalFaultsCP += category.zeroTimeFaultCountCP
    
            catLink=HtmlHelper.createLink(cat, self.calledName, FORMAT='category', SECTION=cat)
        
            row=[ "%s   [%s]" % (catLink, category.count), '','',
                    '%s' % category.timeLostMK, '%s' % category.timeLostCP, 
                    '%s' % (category.timeLostMK + category.timeLostCP,),
                    '%d' % category.zeroTimeFaultCountMK, '%d' % category.zeroTimeFaultCountCP, 
                    '%d' % (category.zeroTimeFaultCountMK + category.zeroTimeFaultCountCP,)]
            table.add_array_after_last_row(row)
            table.setCellColSpan(table.getmaxRow(), 0,3)
        
            if showSystem: 
            
                systems=category.keys()
                systems.sort()

                for sys in systems:
                
                    system=category[sys]

                    sysLink=HtmlHelper.createLink(sys, self.calledName, FORMAT='category', CATEGORY=cat, SYSTEM=sys)                       
                    
                    row=['', "%s   [%s]" % (sysLink, system.count), '', 
                        '%s' % system.timeLostMK, '%s' % system.timeLostCP, 
                        '%s' % (system.timeLostMK + system.timeLostCP,), 
                        '%d' % system.zeroTimeFaultCountMK, '%d' % system.zeroTimeFaultCountCP, 
                        '%d' % (system.zeroTimeFaultCountMK + system.zeroTimeFaultCountCP,)]
                    table.add_array_after_last_row(row)
                    table.setCellColSpan(table.getmaxRow(), 1,2) 


                    if showSubsystem:
                        
                        subsystems=system.keys()
                        subsystems.sort()
        
                        for sbs in subsystems:
                        
                            subsystem=system[sbs]

                            sbsLink=HtmlHelper.createLink(sbs, self.calledName, FORMAT='category', CATEGORY=cat, SYSTEM=sys, SUBSYSTEM=sbs)       
                            row=['', '', "%s   [%s]" % (sbsLink, subsystem.count), 
                                '%s' % subsystem.timeLostMK, '%s' % subsystem.timeLostCP, 
                                '%s' % (subsystem.timeLostMK + subsystem.timeLostCP),
                                '%d' % subsystem.zeroTimeFaultCountMK, '%d' % subsystem.zeroTimeFaultCountCP, 
                                '%d' % (subsystem.zeroTimeFaultCountMK+subsystem.zeroTimeFaultCountCP,)]
                            table.add_array_after_last_row(row)

        table.add_array_after_last_row(['Totals', '', '', 
                                       totalTimeMK, totalTimeCP, totalTimeMK + totalTimeCP,
                                       zeroTimeTotalFaultsMK,  zeroTimeTotalFaultsCP,
                                       zeroTimeTotalFaultsMK + zeroTimeTotalFaultsCP],
                                       {'class':'heading'})

        table.setCellColSpan(table.getmaxRow(), 0,3)
        self.html.doc.append(table)
        
    def _updatePage_ticket(self, dataList, format, request, stream, **options):
        caseId=request.get('CASEID', '')
        
        html=self.html
        #Want to add a form with some options to the page.
        html.form=HTMLFormCont2(vars={'cgifile':self.calledName}) #Form container.
        html.doc.insert(0, html.form) 
        html.options=HTMLOptionsFrsTicket(vars={'caseid':caseId, 'format':'ticket'})
        html.form.append(html.options)
        
        table = HTMLDynListTable(tableAttrs={'width':"100%", 'class':"tableList"})
        html.table = table
        
        # Assume have one dataList item per caseId.

        try:
            data=dataList[0]
        except IndexError:
            if caseId != '':
                table.add_array_after_last_row(["No entries were found for ticket '%s'. " % caseId], {'class':'heading'})
            return 

#
# Do the link at the top.
#
        url = 'https://remedy.gemini.edu/arsys/forms/alderaan.hi.gemini.edu/GEMINI:Telescope:FRS/Default+Admin+View/?eid=%s' % data['CaseID']
        lnk = '<a href="%s">%s</a> [Link to FRS home page]' % (url, data['CaseID'])

        table.setCellColSpan(0,0,2)
        table.setCellcontents(0,0, lnk, {'class':'FRSLabel'})

#
# Converted to inline instead of for.. because each row was too different to make it DRY
#

# Site

        table.add_array_after_last_row(['Site', data.get('Site', 'unknown')])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Submitter

        table.add_array_after_last_row(['Submitter', data.get('Name', 'unknown')])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Assigned To

        at = HtmlHelper.createLink(data['AssignedTo'], self.calledName, FORMAT='user', USER=data['AssignedTo']) 

        table.add_array_after_last_row(['Assigned To', at])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Category / System / Subsystem / Component

        caty  = data.get('Category',  'unknown')
        syst  = data.get('System',    'unknown')
        ssys  = data.get('Subsystem', 'unknown')
        comp  = data.get('Component', 'unknown')

        cssc  = HtmlHelper.createLink(caty, self.calledName, FORMAT='category', CATEGORY=caty)
        cssc += " | "
        cssc += HtmlHelper.createLink(syst, self.calledName, FORMAT='category', CATEGORY=caty, SYSTEM=syst)
        cssc += " | "
        cssc += HtmlHelper.createLink(ssys, self.calledName, FORMAT='category', CATEGORY=caty, SYSTEM=syst, SUBSYSTEM=ssys)
        cssc += " | "
        cssc += HtmlHelper.createLink(comp, self.calledName, FORMAT='category', CATEGORY=caty, SYSTEM=syst, SUBSYSTEM=ssys, COMPONENT=comp)

        table.add_array_after_last_row(['Category/System/Subsystem', cssc])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     
                                          
# Occurrence Date, or if none, use Create Date.

        if data['Occurrence Date'] == None:
            frdate     = data.get('Create Date','unknown')
            frdatetype = "Create Date"
        else:
            frdate     = data.get('Occurrence Date','unknown')
            frdatetype = "Occurrence Date"

        if frdate == 'unknown':
           table.add_array_after_last_row(['Date', 'unknown'])
        else:
           import time
           frstamp = time.mktime(frdate.timetuple())
           fixedlink  = '&nbsp;&nbsp;<input title="Fix time" type="button" value="" onClick="setFixedTime(' + "%d" % frstamp + ');"\>'

           table.add_array_after_last_row([frdatetype, frdate.strftime("%a %b %d %H:%M:%S %Y") + fixedlink])

        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     
        

# Priority

        table.add_array_after_last_row(['Priority', data.get('Priority', '')])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Status
        if data['Related ID']:
            url = '/pages/remedy/frsPage?CASEID=%s&FORMAT=ticket' % data['Related ID']
            lnk = '<a href="%s">%s</a>' % (url, data['Related ID'])
            sts = "Duplicate (%s): Master (%s, %s)" % (data.get('Status'), lnk, data.get('Related Status', 'unknown'))
        else:
            sts = data.get('Status')
        table.add_array_after_last_row(['Status', sts])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Time Lost

        if data['Related_Master_Flag'] == 'Master':
            msg = "%s, total timeloss of %.2f hours from %d duplicates." % \
                (data.get('TimeLost', '(unknown)'), data.get('Total Timelost', 0), data.get('Number Duplicates', 1))
        else:
            msg = data.get('TimeLost', '')
        table.add_array_after_last_row(['Time Lost', msg])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     


# One line summary

        table.add_array_after_last_row(['One line summary', data.get('One line summary', '')])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     



# Local method in common for Detailed description, Work done, and Resolution.

        def replacer(m):            
            return ' <a href="%s">[see_link]</a> %s' % m.groups() 
        r=re.compile(r'(http://.*?)(<|\s)')
 

# Detailed description, including link munging. Unicode chars were removed in remedyWrapper.py already.

        dd = r.sub(replacer,str(data.get('Detailed description' , 'No description')))
        dd = util.wordWrap(dd)

        table.add_array_after_last_row(['Detailed description', "<pre>%s</pre>" % (dd, )])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)  

# Ditto for work done

        wd = r.sub(replacer,cgi.escape(str(data.get('Work done' , 'No work done.')).replace('<br>', '\n')))
        wd = util.wordWrap(wd, width = 200)

        table.add_array_after_last_row(['Work done', "<pre>%s</pre>" % wd])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Resolution. Don't do any filler if it doesn't exist.

        if data['Resolution']:
            res = util.wordWrap(r.sub(replacer,cgi.escape(str(data['Resolution']).replace('<br>', '\n'))))
            table.add_array_after_last_row(['Resolution', "<pre>%s</pre>" % (res)])
            table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     
            
# Attachements if any.

        if data['Attachments']:
            att = ''
            for at in data['Attachments']:
                att += "    <p> "
                att += at['Name']
                att += " </p>"
                att += "    <img src=\"data:image;base64, "
                att += at['Data']
                att += "\"//><br>"
            table.add_array_after_last_row(['Attachments', "<pre>%s</pre>" % (att)])
            table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

        html.doc.append(html.table)

    def _updatePage_user(self, dataList, format, request, stream, **options):
   
        filter=request.get('FILTER', 'Assigned/InProgress')
        user=request.get('USER', '')
    
        html=self.html
        #Want to add a form with some options to the page.
        html.form=HTMLFormCont2(vars={'cgifile':self.calledName}) #Form container.
        html.doc.insert(0, html.form) 
        html.options=HTMLOptionsFrsUser(vars={'user':user, 'filter':filter, 'format':'user'})
        html.form.append(html.options)
   
        table = HTMLDynListTable(tableAttrs={'width':"100%"})
        
        #Check if have any data...
        if dataList==[]:
            if user!='':
                table.add_array_after_last_row(["No entries found."], {'class':'heading'})
                html.doc.append(table)
            return 

        table.setCellColSpan(0,0,5)
        table.setCellcontents(0,0, "Tickets assigned to user '%s'" % user, {'class':'FRSLabel'})
        html.doc.append(table)
        
        self.html.table = HTMLDynListTable(tableAttrs={'width':"100%",  'class':"sortable", 'id':"sortable_frs"})
        table=self.html.table

        header=['CaseID', 'Created', 'Status', 'TimeLost', 'One line summary']
        table.add_array_after_last_row(header, {'class':'heading'})
         

        for item in dataList:

            item['Created']=item['Create Date']

            item['CaseID']=HtmlHelper.createLink(item['CaseID'], self.calledName, FORMAT='ticket', CASEID=item['CaseID'])
                                
            table.add_array_after_last_row([item[key] for key in header])
   
        html.doc.append(table)
   
    def _updatePage_category(self, dataList, format, request, stream, **options):
        """Handles category/system/subsystem/component.
        """
        table=self.html.table
        
        #Construct the title.

        title='Tickets for Category:<strong>%s</strong>, System:<strong>%s</strong>, Subsystem:<strong>%s</strong>, Component:<strong>%s</strong>' % (
             request.get('CATEGORY') or 'All', request.get('SYSTEM') or 'All', request.get('SUBSYSTEM') or 'All', request.get('COMPONENT') or 'All')
                
        table.setCellColSpan(0,0,6)
        table.setCellcontents(0,0, title,
                              {'align':'center','class':'FRSLabel'})
        
        header=('CaseID', 'Create Date', 'Status','TimeLost','One line summary','AssignedTo')
        table.add_array_after_last_row(header, {'class':'heading'})
        
        for item in dataList:
        
            item['Create Date']=item['Create Date']
        
            #Create links for some of the entries.
            item['AssignedTo']=HtmlHelper.createLink(item['AssignedTo'],
                                      self.calledName,
                                      FORMAT='user',
                                      USER=item['AssignedTo'])
        
            item['CaseID']=HtmlHelper.createLink(item['CaseID'],
                                      self.calledName,
                                      FORMAT='ticket',
                                      CASEID=item['CaseID'])
                   
            table.add_array_after_last_row([item[key] for key in header],)

    def _extractRemedyData(self, rQuery, rKeys, request, stream, startTime=None, endTime=None):
        """Extract data from Remedy.
        """
        extractor=RemedyDataExtractor(rQuery=rQuery, request=request,  startTime=startTime,
                                      endTime=endTime, rKeys=rKeys, dBase='FRS')
        return extractor.extract()
        
def main(outStream=GEAVars.outStream, standAlone=False):

    FrsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
