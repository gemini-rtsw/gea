#!/usr/bin/python

from pages.remedyBasePage import RemedyBasePage
    
from GEATime import Time
from GEARequest import RequestCollection, Request, RequestProcessor
from GEAHtml import HTMLDynListTable, HTMLFormFrs, HTMLCont, HtmlHelper, HTMLFormCont2, \
                                      HTMLTimeSelectorFrsStats, HTMLOptionsFrsStats, MenuItem, \
                                      HTMLOptionsFrsUser, HTMLOptionsFrsTicket, HTMLPlot, HTMLTextBox
from GEADataHandler import RemedyDataExtractor      
from GEAGeneral import util, naming
import pytz
import GEAVars
import os
import re
import cgi   #for escape()
import unicodedata
        
import matplotlib
matplotlib.use(GEAVars.plot.backend)  
from matplotlib.pylab import *

import GEAPlot
GEAPlot.matplotlibConfig()          
from urllib import quote_plus

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
                        
        rKeys=('Site', 'CaseID', 'Date', 'Status', 'Disposition', 'TimeLost', 'One line summary',
               'Master', 'Duplicate', 'AssignedTo', 'Components', 'Labels')

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

                # Check if CASEID is valid.

                if caseId:
                    try:
                        caseId = "FR-%06d" % int(re.sub('[^0-9]*', '', caseId))
                    except:
                        caseId = ""
                        rKeys=()
                    else:
                        rQuery='BT"key"="%s"' % caseId
                        rKeys=('CaseID', 'Site', 'Name', 'Date', 'Duplicate', 'AssignedTo', 'Status', 'Priority',
                               'Master', 'TimeLost', 'One line summary', 'Detailed description', 'Work done',
                               'Attachments', 'Resolution', 'Components', 'Labels')
                else:
                    rQuery=""
                    rKeys=()
                       
            elif format=='user':

                user=request.get('USER', '')
            
                if user:
                    rQuery='BT"assignee"="%s"' % user
                    
                    filter=request.get('FILTER', 'Work+in+progress')

                    if filter=='Work in progress':
                        rQuery += '+AND+"status"="Work+in+progress"'
                    elif filter=='Closed':
                        rQuery += '+AND+"status"="Closed"'
                else:
                    rQuery=""
                    rKeys=()
                            
            elif format=='label':
                queryList=[]
    
                labs=request.get('LABELS', '')

                if labs:
                    rQuery='%s"labels"="%s"' % (GEAVars.site, quote_plus(labs))
                else:
                    rQuery=""
                    rKeys=()

            elif format=='component':
                queryList=[]
    
                comp=request.get('COMPONENTS', '')

                if comp:
                    rQuery='%s"component"="%s"' % (GEAVars.site, quote_plus(comp))
                else:
                    rQuery=""
                    rKeys=()


            else:
                raise RuntimeError('FORMAT not understood, "%s".' % format)
                
            #Extract data and update page.
# TCC
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

        header=['CaseID', 'R', 'Status', 'TimeLost', 'AssignedTo', 'One line summary']
        table.add_array_after_last_row(header, {'class':'heading'})

        for item in dataList:

            fmt = '%Y/%m/%d %H:%M:%S %Z'
            additional_information  = 'Time:\n'
            additional_information += '    %s' % item['Date'].strftime(fmt)
            additional_information += ' (%s)\n' % (item['Date']).astimezone(pytz.utc).strftime(fmt)
            additional_information += 'Components:\n'
            additional_information += '    %s\n' % ", ".join(item['Components'])
            additional_information += 'Labels:\n'
            additional_information += '    %s\n' % ", ".join(item['Labels'])

            relationship = 'U '	# Unrelated.
            if item['Master']: relationship = 'M ' 
            elif item['Duplicate']: relationship = 'D '

        
            item['CaseID']=HtmlHelper.createLink('<span title="' + additional_information + '">' + item['CaseID'] + '</span>',
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

            table.add_array_after_last_row([item['CaseID'],
                                            relationship,
                                            item['Status'],
                                            item['TimeLost'],
                                            item['AssignedTo'],
                                            item['One line summary']])
        self.html.doc.append(table)
        
    def _extractStatsData(self, dataList, showComponents=True, showLabels=True):

    
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
                    if len(d) > 0:
                        lists = d.toLists(prefixName=prefixName+name+' | ')
                        names += lists[0]
                        
                        mkTimeLoss += lists[1]
                        mkZeroTimeFaultCount += lists[2]
                        
                        cpTimeLoss += lists[3]
                        cpZeroTimeFaultCount += lists[4]

                    else:
                        name = prefixName+name
                        names.append(name)
                        
                        mkTimeLoss.append(d.timeLostMK)
                        mkZeroTimeFaultCount.append(d.zeroTimeFaultCountMK)
                        
                        cpTimeLoss.append(d.timeLostCP)
                        cpZeroTimeFaultCount.append(d.zeroTimeFaultCountCP)
                    
                return [names, mkTimeLoss, mkZeroTimeFaultCount, cpTimeLoss, cpZeroTimeFaultCount]
                
        data = modDict()

        for item in dataList:

            site     = item['Site']
            timeLost = float(item['TimeLost'])

            if not data.has_key('Component'):
                data['Component'] = modDict()
                data['Component'].timeLostMK=0.0
                data['Component'].timeLostCP=0.0
                data['Component'].zeroTimeFaultCountMK=0
                data['Component'].zeroTimeFaultCountCP=0
                data['Component'].count=0

            data['Component'].count += 1
            data['Component'].__dict__['timeLost'+site] += timeLost
            if float(timeLost)==0.0:
                data['Component'].__dict__['zeroTimeFaultCount'+site]+=1

            if not data.has_key('Label'):
                data['Label'] = modDict()
                data['Label'].timeLostMK=0.0
                data['Label'].timeLostCP=0.0
                data['Label'].zeroTimeFaultCountMK=0
                data['Label'].zeroTimeFaultCountCP=0
                data['Label'].count=0

            data['Label'].count += 1
            data['Label'].__dict__['timeLost'+site] += timeLost
            if float(timeLost)==0.0:
                data['Label'].__dict__['zeroTimeFaultCount'+site]+=1

            for component in item['Components']:

                # if not data.has_key('Component'): data['Component'] = modDict()
                if not data['Component'].has_key(component):
                    data['Component'][component] = modDict()
                    data['Component'][component].timeLostMK=0.0
                    data['Component'][component].timeLostCP=0.0
                    data['Component'][component].zeroTimeFaultCountMK=0
                    data['Component'][component].zeroTimeFaultCountCP=0
                    data['Component'][component].count=0

                data['Component'][component].count += 1
                data['Component'][component].__dict__['timeLost'+site]+=timeLost
                if float(timeLost)==0.0:
                    data['Component'][component].__dict__['zeroTimeFaultCount'+site]+=1



            # Same as above but for, "Label"

            for label in item['Labels']:

                if not data.has_key('Label'): data['Label'] = modDict()
                if not data['Label'].has_key(label):
                    data['Label'][label]=modDict()
                    data['Label'][label].timeLostMK=0.0
                    data['Label'][label].timeLostCP=0.0
                    data['Label'][label].zeroTimeFaultCountMK=0
                    data['Label'][label].zeroTimeFaultCountCP=0
                    data['Label'][label].count=0

                data['Label'][label].count+=1
                data['Label'][label].__dict__['timeLost'+site] += timeLost
                if float(timeLost)==0.0:
                    data['Label'][label].__dict__['zeroTimeFaultCount'+site]+=1

        return data
            
    def _updatePage_stats(self, dataList, format, request, stream, **options):

        startTime=options['startTime']
        endTime=options['endTime']

        import json

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
        show=request.get('SHOW', 'Components/Labels').lower()  #By default show all.
       
        showComponents = True
        showLabels     = True 
        data=self._extractStatsData(dataList, showComponents=True, showLabels=True)
        
        view=request.get('VIEW', 'StatsTable')
        
        self.__getattribute__('_updatePage_stats_'+view)(request, stream, data, showComponents, showLabels, **options)
        
    def _updatePage_stats_Plot(self, request, stream, data, showComponent, showLabel, **options):
        
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
            f.write('%#-80s%#10s%#10s\n' % ('Component','MK data', 'CP data'))
            for index in range(len(dataList[0])):
                f.write('%#-80s%#10s%#10s\n' % (dataList[0][index],dataList[1][index],dataList[2][index]))
            f.close()
        
        cla()   #Cleanup.
        
    def _updatePage_stats_StatsTable(self, request, stream, data, showComponents, showLabels, **options):
        
        startTime=options['startTime']
        endTime=options['endTime']
        
        totalTimeMK, totalTimeCP, zeroTimeTotalFaultsMK, zeroTimeTotalFaultsCP = 0.0, 0.0, 0, 0
        
        self.html.table = HTMLDynListTable(tableAttrs={'width':"100%"})
        table=self.html.table

        table.setCellColSpan(0,0,8)
        table.setCellcontents(0, 0, 'Time loss data for %s' % Time.timeRange2Str(startTime, endTime), {'class':'FRSLabel', 'align':'center'})
                
        #Setup the header.

        header1=['','','Time Lost (hours)', '', '', 'Zero Time Loss Events', '', '']
        table.add_array_after_last_row(header1, {'class':'heading'}) 
        table.setCellColSpan(1,0,2)
        table.setCellColSpan(1,2,3)
        table.setCellColSpan(1,5,3)

        header2=['Selection', '', 'MK', 'CP', 'MK/CP', 'MK', 'CP', 'MK/CP '] 
        table.add_array_after_last_row(header2, {'class':'heading'}) 
        table.setCellColSpan(2,0,2)
 
        #table.setCellColSpan(table.getmaxRow(), 1, 3)
                 
        cmplabs = data.keys()	# Components or labels.
        cmplabs.sort()

        for cmplabitem in cmplabs:	# cmplabitem will be either, "Component", or "Label".
            cmplabval = data[cmplabitem]

            cmplabLink=HtmlHelper.createLink(cmplabitem + "s", self.calledName, FORMAT=cmplabitem.lower(), COMPONENTS=cmplabitem)
            row=[cmplabitem + "s", ' ',
                  '%s' % cmplabval.timeLostMK,
                  '%s' % cmplabval.timeLostCP,
                  '%s' % (cmplabval.timeLostMK + cmplabval.timeLostCP),
                  '%d' % cmplabval.zeroTimeFaultCountMK,
                  '%d' % cmplabval.zeroTimeFaultCountCP,
                  '%d' % (cmplabval.zeroTimeFaultCountMK + cmplabval.zeroTimeFaultCountCP)]

            table.add_array_after_last_row(row)

            bzyd=data[cmplabitem].keys()
            bzyd.sort()
            for bzyditem in bzyd:
                bzydval = data[cmplabitem][bzyditem]

                totalTimeMK           += bzydval.timeLostMK
                totalTimeCP           += bzydval.timeLostCP
                zeroTimeTotalFaultsMK += bzydval.zeroTimeFaultCountMK
                zeroTimeTotalFaultsCP += bzydval.zeroTimeFaultCountCP

                if cmplabitem == "Component":
                    bzydLink=HtmlHelper.createLink(bzyditem, self.calledName, FORMAT='component', COMPONENTS=bzyditem)
                else:
                    bzydLink=HtmlHelper.createLink(bzyditem, self.calledName, FORMAT='label', LABELS=bzyditem)

                row=['', "%s [%s]" % (bzydLink, bzydval.count),
                        '%s' % bzydval.timeLostMK,
                        '%s' % bzydval.timeLostCP,
                        '%s' % (bzydval.timeLostMK + bzydval.timeLostCP,),
                        '%d' % bzydval.zeroTimeFaultCountMK,
                        '%d' % bzydval.zeroTimeFaultCountCP,
                        '%d' % (bzydval.zeroTimeFaultCountMK + bzydval.zeroTimeFaultCountCP,)]
                
                table.add_array_after_last_row(row)


        """
        table.add_array_after_last_row(['Totals', '',
            totalTimeMK, totalTimeCP, totalTimeMK + totalTimeCP,
            zeroTimeTotalFaultsMK,  zeroTimeTotalFaultsCP,
            zeroTimeTotalFaultsMK + zeroTimeTotalFaultsCP],
            {'class':'heading'})

        table.setCellColSpan(table.getmaxRow(), 0,2)
        """
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

        if not dataList:
            table.add_array_after_last_row(["No entries were found for ticket '%s'. " % caseId], {'class':'heading'})
            html.doc.append(html.table)
            return 

        data = dataList[0]

#
# Do the link at the top.
#
        url = '%s/browse/%s' % (GEAVars.JiraHost[GEAVars.site], data['CaseID'])
        lnk = '<a href="%s">See in Jira: %s</a>' % (url, data['CaseID'])

        table.setCellColSpan(0, 0, 2)

        table.setCellcontents(0, 0, lnk, {'class':'FRSLabel'})

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

        comp  = data['Components']
        labs  = data['Labels']

        msg  = []
        complist = []
        for comp in data['Components']:
            complist += (HtmlHelper.createLink(comp, self.calledName, FORMAT='component', COMPONENTS=comp),)
        if complist: msg += ("Components: %s" % ", ".join(complist),)

        labslist = []
        for labs in data['Labels']:
            labslist += (HtmlHelper.createLink(labs, self.calledName, FORMAT='label', LABELS=labs),)
        if labslist: msg += ("Labels: %s" % ", ".join(labslist),)

        table.add_array_after_last_row(['Components/Labels', " ".join(msg)])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     
                                          
        fmt = '%Y/%m/%d %H:%M:%S %Z'
        date_msg  = '  %s' % data['Date'].strftime(fmt)
        date_msg += '  (%s)\n' % (data['Date']).astimezone(pytz.utc).strftime(fmt)

        import time
        frstamp = int(data['Date'].strftime("%s"))
        fixedlink  = '&nbsp;&nbsp;<input title="Fix time" type="button" value="" onClick="setFixedTime(' + "%d" % frstamp + ');"\>'

        date_msg += fixedlink
        table.add_array_after_last_row(["Date", date_msg])

        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     
        

# Priority

        table.add_array_after_last_row(['Priority', data['Priority']])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Status
        if data['Duplicate']:
            dup = data['Duplicate'][0]	# There s/b only one ticket for this query
            fr  = unicodedata.normalize('NFKD', dup['Master']).encode('ascii','ignore')
            url = '/pages/remedy/frsPage?CASEID=%s&FORMAT=ticket' % fr
            lnk = '<a href="%s">%s</a>' % (url, fr)
            sts = "Duplicate: Master (%s, %s)" % (dup['Status'], lnk)
        else:
            sts = data.get('Status')

        table.add_array_after_last_row(['Status', sts])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

# Time Lost

        if data['Master']: 
            mstr = data['Master']
            msg = '%.2f, total time loss of %.2f from %d duplicates.' % (data['TimeLost'],
               mstr['TotalTimelost'] + data['TimeLost'], len(mstr['Duplicates']))
        else:
            msg = data.get('TimeLost', '')
        table.add_array_after_last_row(['Time Lost', msg])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     


# One line summary

        table.add_array_after_last_row(['One line summary', data.get('One line summary', '')])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     


# Local method in common for Detailed description, Work done, and Resolution.

        """
        def replacer(m):            
            return ' <a href="%s">[see_link]</a> %s' % m.groups() 
        r=re.compile(r'(http://.*?)(<|\s)')
        """

        def replacer(m): return ' <a href="%s">[see_link]</a>' % m.group(1) 

        # r=re.compile(r'\[(http://.*?)\]')
        r=re.compile(r'[[!](https?://.*?)[]!]')
 

# Detailed description, including link munging. Unicode chars were removed in remedyWrapper.py already.

        dd = r.sub(replacer,str(data.get('Detailed description' , 'No description')))
        dd = util.wordWrap(dd)

        table.add_array_after_last_row(['Detailed description', "<pre>%s</pre>" % (dd, )])
        table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)  

# Ditto for work done

        wd = ""
        for w in data['Work done']:
            wd += "<b>"
            wd += w['Date'].strftime("%x %H:%M")
            wd += "&nbsp;&nbsp;"
            wd += w['author']
            wd += "</b>"
            wd += "&nbsp;&nbsp;"
            wd += w.get('time' , '')
            wd += "<br>"
            wd += "<pre>"
            wd += util.wordWrap(r.sub(replacer, cgi.escape(str(w.get('body' , 'No work done.')).replace('<br>', '\n'))))
            wd += "</pre>"

        table.add_array_after_last_row(['Work done', wd])
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
                att += at['filename']
                att += '    <br>'
                att += '    <a href="'
                att += at['url']
                att += '">'
                att += '<img width="200" src="'
                att += at['url']
                att += '"/></a><br>'
            table.add_array_after_last_row(['Attachments', att])
            table.setCellattrs(table.getmaxRow(), 0, {'class':'heading'}, overwrite=True)     

        html.doc.append(html.table)

    def _updatePage_user(self, dataList, format, request, stream, **options):
   
        filter=request.get('FILTER', 'Work in progress')
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

        header=['CaseID', 'Date', 'Status', 'TimeLost', 'One line summary']
        table.add_array_after_last_row(header, {'class':'heading'})
         
        fmt = '%Y/%m/%d %H:%M:%S %Z'

        for item in dataList:

            item['CaseID']=HtmlHelper.createLink(item['CaseID'], self.calledName, FORMAT='ticket', CASEID=item['CaseID'])

            table.add_array_after_last_row((item['CaseID'], item['Date'].strftime(fmt), item['Status'], item['TimeLost'], item['One line summary']))
   
        html.doc.append(table)
   
    def _updatePage_component(self, dataList, format, request, stream, **options):
        """Handles component
        """

        html=self.html
   
        table = self.html.table = HTMLDynListTable(tableAttrs={'width':"100%"})

        #Construct the title.

        title='Tickets for Component:<strong>%s</strong>' % (request.get('COMPONENTS') or 'All')
                
        table.setCellColSpan(0,0,6)
        table.setCellcontents(0,0, title, {'align':'center','class':'FRSLabel'})
        
        header=('CaseID', 'Date', 'Status','TimeLost','One line summary','AssignedTo')
        table.add_array_after_last_row(header, {'class':'heading'})
        
        for item in dataList:
        
            #item['Date']=item['Date']
        
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

        html.doc.append(table)


    def _updatePage_label(self, dataList, format, request, stream, **options):
        """Handles labels
        """

        html=self.html

        table = self.html.table = HTMLDynListTable(tableAttrs={'width':"100%"})

        #Construct the title.

        title='Tickets for label:<strong>%s</strong>' % (request.get('LABELS') or 'All')

        table.setCellColSpan(0,0,6)
        table.setCellcontents(0,0, title, {'align':'center','class':'FRSLabel'})

        header=('CaseID', 'Date', 'Status','TimeLost','One line summary','AssignedTo')
        table.add_array_after_last_row(header, {'class':'heading'})

        for item in dataList:

            #item['Date']=item['Date']

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

        html.doc.append(table)



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
