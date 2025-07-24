#!/usr/bin/python

import GEAVars
from GEATime import Time
from GEARequest import RequestCollection, Request
from GEAHtml import HTMLDynTable, HTMLDynListTable, HTMLTextBox, HTMLFormContSideSubmit, HTMLOptionsNLNightly,  HtmlHelper, HTMLCont, MenuItem, HTMLOptionsNLReport, HTMLTimeSelectorNLReport, HTMLPlot
from GEADataHandler import RemedyDataExtractor
from GEAAnalyzer import Stats
from GEAGeneral import util, naming
from pages.remedyBasePage import RemedyBasePage
import os

from specialized.telMetrics import telMetrics
from GEAMetrics import getNLMetricsFromRemedy


class NightLogPage(RemedyBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    format2Title={'Nightly':'Nightly',
                  'Report':'Report',
                  }

    menuItemList=[
                MenuItem('Nightly', GEAVars.dispatchScript+'/pages/nightlog/nightLogPage?FORMAT=Nightly&SITE=%s'% GEAVars.site),
                MenuItem('Report', GEAVars.dispatchScript+'/pages/nightlog/nightLogPage?FORMAT=Report&SITE=%s' % GEAVars.site),
                ]

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """
        topMenuList=topMenuList or []
        RemedyBasePage._assemblePage(self,  topMenuList=[NightLogPage.menuItemList]+topMenuList)
        html=self.html

        html.form=HTMLFormContSideSubmit() #Form container.
        #cgifile is of the form:   /run/dispatch.gea/some_directories/file_without_py_extenstion
        html.form.vars.update(cgifile=self.calledName)
        html.doc.append(html.form)

        html.table=HTMLDynListTable(tableAttrs={'width':"100%",  'class':"tableList"})
        html.doc.append(html.table)

    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is
        a need for a default requests. See self.run() how this is used.

        A dictionary (or a RequestCollection) of nameTag/request pairs should be returned.
        """
        #Being very explicit, so that it is clear what is being done.

        nameTag=None

        request={'FORMAT':'Nightly',
                      'SITE':GEAVars.site,
                 }
        #Setup time query; Default to yesterday as the 'night of' time.
        request.update(Time(site=GEAVars.site, option='yesterday1200').toStartTimeDict(allCaps=True, monthAsWord=True))

        r=Request(request=request, nameTag=nameTag)

        return {nameTag:r}

    def _processRequest(self, request, stream):
        """Process the request.

        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function _assemblePage().
        """
        if request.get('FORPRINTING', ''):
            self.html.doc=HTMLCont()
            #Only show the table - no menus/options
            self.html.doc.append(self.html.table)

        format=request.get('FORMAT', 'Nightly')
        site=request.get('SITE', GEAVars.site)

        #These specify the time range for which to query for data.
        startTime, endTime=None, None

        rQuery, rKeys='', ''

        try:
            if format=='Nightly':

                try:
                    startTime=Time(site=site).fromStartTimeDict(request, allCaps=True)
                except KeyError:
                    startTime=Time(site=site, option='yesterday1200')

                endTime=Time(seconds=startTime.seconds+Time.secPerDay, site=site)

                rQuery=''
                rKeys=('Plan','Total hours','Total hours lost faults','Weather','Observed',
                        'Summary','Additional Comments','Details','UT Date','Observers','Additional Support','Phone Support' ,
                         'Science usage', 'Engineering', 'Commissioning', 'Shutdown', 'Shuttered', 'Blanket Closures',
                        )

            elif format=='Report':
                try:
                    endTime=Time(site=site).fromEndTimeDict(request, allCaps=True, monthAsWord=True)
                except KeyError:
                    endTime=Time(site=site)
                try:
                    startTime=Time(site=site).fromStartTimeDict(request, allCaps=True, monthAsWord=True)
                except KeyError:
                    startTime=Time(endTime.seconds-Time.secPerWeek, endTime.site)

                rQuery=''
                rKeys=('Plan','Total hours','Total hours lost faults','Weather','Observed',
                        'Additional Comments','Details','UT Date', 'Blanket Closures')
            else:
                #Should raise here maybe...
                pass

            #Extract data and update page.
            dataList=self._extractRemedyData(rQuery=rQuery, rKeys=rKeys, request=request, stream=stream, startTime=startTime, endTime=endTime)

            if dataList:
                for dL in dataList:
                    dL['NLandFRsummary'] = getNLMetricsFromRemedy(Time(dL['UT Date'], site))

            self.__getattribute__('_updatePage_'+format)(dataList=dataList, format=format,
                                                                                request=request, stream=stream,
                                                                                startTime=startTime,
                                                                                endTime=endTime,)
        finally:
            try:
                #Want to make sure we update the html widget with old values.
                #Assuming here that we always have html.options.
                for widget in (self.html.table, self.html.options):
                        self._setWidgetVars(widget, request, [])
            except AttributeError:
                #Could have a case where an exception has been thrown before one of the widgets has been
                #created (ex. self.html.optons may not exist)
                pass

            #Want to update the header title based on what FORMAT was requested. This was already done when the page was first assembed,
            #but now the QUERY_STRING has been parsed and we have info of the FORMAT.
            if NightLogPage.format2Title.has_key(format):
                extra=':%s' % NightLogPage.format2Title.get(format, '')
                self.html.doc.vars.update(headerinfo=self._getHeaderInfo()+extra)

            #self.html.optionsSelector.vars.update({'format':'Nightly'})


    def _updatePage_Nightly(self, dataList, format, request, stream, **options):

        html=self.html

        html.options=HTMLOptionsNLNightly(vars={'site':GEAVars.site})
        html.options.vars.update(Time(site=GEAVars.site, option='yesterday1200').toStartTimeDict(allCaps=False, monthAsWord=True))
        html.form.append(html.options)

        startTime=options['startTime']
        endTime=options['endTime']

        table=html.table
        calledName=self.calledName.rstrip('?')+'?'      #Want to make sure have '?' at the end.

        site=request.get('SITE', GEAVars.site)

        tBefore, tAfter=Time(startTime.seconds-Time.secPerDay, site=startTime.site), Time(startTime.seconds+Time.secPerDay, site=startTime.site)

        title='<pre>%s<strong>&lt;&lt;</strong>     %s    <strong>&gt;&gt;</strong>%s' % (
                                                    HtmlHelper.createLink("%s" % tBefore.string9,
                                                                            self.calledName,
                                                                            SITE=site,
                                                                            FORMAT='Nightly',
                                                                            **tBefore.toStartTimeDict(allCaps=True, monthAsWord=True)),
                                                     "<strong>%s</strong> Night Log (Night of %s, localtime)" % (site,
                                                                                        startTime.string7, ),
                                                    HtmlHelper.createLink("%s" % tAfter.string9,
                                                                            self.calledName,
                                                                            SITE=site,
                                                                            FORMAT='Nightly',
                                                                            **tAfter.toStartTimeDict(allCaps=True, monthAsWord=True)), )
        title+='\nSwitch to <strong>%s</strong> view</pre>' % HtmlHelper.createLink("%s" % util.getOtherSite(site),
                                                                                                                           self.calledName,
                                                                                                                          SITE=util.getOtherSite(site),
                                                                                                                          FORMAT='Nightly',
                                                                                                                          **startTime.toStartTimeDict(allCaps=True, monthAsWord=True))

        table.setCellColSpan(0,0,2)
        table.setCellcontents(0,0,title,{'class':'NLLabel'})

        if len(dataList)   > 1:
            table.setCellColSpan(1,0,2)
            table.setCellcontents(1,0, "NOTE: Multiple NL entries have been found",
                                {'class':'heading'})
        elif len(dataList) < 1:
            table.setCellColSpan(1,0,2)
            table.setCellcontents(1,0, "No Night Log entries were found in the Remedy database for the requested day.",
                                {'class':'heading'})
            return

        hoursHeading=('Available', 'Observed', 'Science', 'Comm','Eng', 'Faults', 'Weather', 'Shutdown', 'Shuttered', "Blanket Closures")
        hoursKeys=('Total hours','Observed', 'Science usage', 'Commissioning','Engineering', 'Total hours lost faults','Weather', 'Shutdown', 'Shuttered', 'Blanket Closures')

        keys=('Plan', 'Summary','Observers','Additional Support','Phone Support' ,'Additional Comments','Details')

        item = dataList[0]	# Query returns a array of NL's. We only do one per day here.

        #Add hours statistics
        hoursTable=HTMLDynTable(tableAttrs={'class':'withBorder', 'width':'100%'})
        hoursTable.add_array_after_last_row(hoursHeading, {'class':'heading'})

        if item['Shutdown'] is None: item['Shutdown']  = 0.0
        if item['Shuttered'] is None: item['Shuttered'] = 0.0
        if item['Blanket Closures'] is None: item['Blanket Closures'] = 0.0

        hoursTable.add_array_after_last_row(map(lambda x: str(item[x])+' Hours', hoursKeys))

        #Make 'Science usage', 'Commissioning','Engineering' cells appear a little different from the rest.
        row=hoursTable.getmaxRow()
        for i in (2,3,4):
            hoursTable.setCellattrs(row,i,{'bgcolor':'#e0e0de'})

        table.add_array_after_last_row([hoursTable])
        table.setCellColSpan(table.getmaxRow(),0,2)

        frs = {}
        if item['NLandFRsummary']:
            if item['NLandFRsummary']['Fault Reports']:
                frs = item['NLandFRsummary']['Fault Reports']

        frsTable = HTMLDynTable()

        caseId = None

        for fr in frs:
            caseId = fr['CaseID']
            caseIdQuery = '/pages/remedy/frsPage?FORMAT=ticket&CASEID=%s' % caseId
            link='<a href="%s">%s</a>' % (caseIdQuery, caseId)

            fr['Date'] = fr['Date'].strftime("%H:%M")
            l = "&nbsp;"
            line = [link + l, l + fr['Date'] + l, l + fr['Status'] + l, "&nbsp;%.2f&nbsp;" % fr['TimeLost'] + l, l + fr['AssignedTo'] + l, l + fr['One line summary'] + l]

            frsTable.add_array_after_last_row(line)

        if caseId:
            # table.add_array_after_last_row(['Fault Reports', '%s%s%s' % ('<pre>', '\n'.join(frsList), '</pre>')])
            table.add_array_after_last_row(['Fault Reports', '&nbsp;'])
            table.setCellattrs(table.getmaxRow(), 0, {'class':'heading', 'valign':'top'}, overwrite=True)
            table.setCellcontents(table.getmaxRow(), 1, frsTable)


        for key, value in [(key, item[key]) for key in keys]:

            if key in ['Plan', 'Details', 'Additional Comments', 'Summary']:
                value=util.wordWrap(str(value))

            data=[key, '%s%s%s' % ('<pre>', value, '</pre>')]
            table.add_array_after_last_row(data)
            table.setCellattrs(table.getmaxRow(), 0, {'class':'heading','valign':'top'}, overwrite=True)

    def _updatePage_Report(self, dataList, format, request, stream, **options):

        html=self.html
        startTime=options['startTime']
        endTime=options['endTime']

        html.timeSelector=HTMLTimeSelectorNLReport(vars=Time.startEndTime2Dict(startTime, endTime, allCaps=False, monthAsWord=True))
        html.form.append(html.timeSelector)

        html.options=HTMLOptionsNLReport(vars={'site':GEAVars.site})
        html.form.append(html.options)

        table=html.table

        calledName=self.calledName.rstrip('?')+'?'      #Want to make sure have one '?' at the end.

        site=request.get('SITE', GEAVars.site)

        #Have to keep track of what has been processed already; Remedy returns multiple (identical) entries
        #for the same requests.
        processedDates=[]

        #Keep track of all the stats; keep the looooong nasty names for consistency.
        stats=Stats({'Observed':[], 'Total hours lost faults':[], 'Weather':[], 'Total hours':[], 'Blanket Closures':[] })

        table.setCellColSpan(0,0,9)

        keys=('Total hours', 'Observed','Total hours lost faults','Weather', 'Blanket Closures')

        header=['Night Log Date', 'Hours avail.', 'Hours observed', 'Hours lost to faults',  'Hours lost to weather', 'Blanket Closures',
                'Fault Reports', 'FR Count', 'Zero time loss FR count']

        table.add_array_after_last_row(header, {'class':'heading'})

        uniqItemCount=0

        for item in dataList:

            # if item['Shutdown'] is None: item['Shutdown']  = 0.0
            # if item['Shuttered'] is None: item['Shuttered'] = 0.0
            if item['Blanket Closures'] is None: item['Blanket Closures'] = 0.0

            itemTime=Time(item['UT Date'], site=site)

            nightOfTime=Time(itemTime.seconds-12*Time.secPerHour, site=site, option='yesterday1200')

            if itemTime in processedDates: continue

            uniqItemCount += 1

            processedDates.append(itemTime)

            #Update the statistics.
            for key in stats.keys():
                if item[key] is not None:
                    stats[key].append(item[key])

            #First column is the time. Create a link to the corresponding 'Nightly' report.
            nightOfTime=Time(itemTime.seconds-Time.secPerHour*12, site)
            link=HtmlHelper.createLink("%s - %s" % (nightOfTime.string7, itemTime.string7),
                                        self.calledName,
                                        FORMAT='Nightly',
                                        SITE=site,
                                        **nightOfTime.toStartTimeDict(allCaps=True))
            data=[link]

            for key, value in [(key, item[key]) for key in keys]:

                #data.append('%s%s%s' % ('<pre>', value, '</pre>'))
                data.append(value)

            zeroTimeLossFrCount = 0
            FrCount             = 0

            frs = {}

            if 'NLandFRsummary' in item:
                if 'Fault Reports' in item['NLandFRsummary'] and item['NLandFRsummary']['Fault Reports']:
                    frs = item['NLandFRsummary']['Fault Reports']

            frsTable=HTMLDynTable()

            caseId = None

            for fr in frs:
                caseId = int(fr['CaseID'])
                caseIdQuery = '/pages/remedy/frsPage?FORMAT=ticket&CASEID=%s' % caseId
                link='<a href="%s">%d</a>' % (caseIdQuery, caseId)

                l = "&nbsp;"

                line = [link + l, l + fr['One line summary'] + l]

                frsTable.add_array_after_last_row(line)

                if float(fr['TimeLost']) == 0.0:
                    zeroTimeLossFrCount += 1
                FrCount += 1

            if caseId is None: frsTable = ""

            table.add_array_after_last_row(data + [frsTable, FrCount, zeroTimeLossFrCount])

        #Add the heading with item count.
        table.setCellColSpan(0,0,9)
        table.setCellcontents(0,0, "<strong>%s</strong> Night Log Report (%s - %s),  Records found: <strong>%d</strong>" % (site,
                                                                                        options['startTime'].string7,
                                                                                        options['endTime'].string7,
                                                                                        uniqItemCount),
                                        {'class':'NLLabel', 'align':'center'})

        #Finally add statistics to the beginning of the page. Create a new table.
        totalsList=['Totals']
        averageList=['Averages']

        for key in ('Total hours', 'Observed','Total hours lost faults','Weather', 'Blanket Closures'):

            if (key not in stats) or len(stats[key]) < 1:
                return   #No data; return.

            totalsList.append("%.2f" % stats.sum(key))
            averageList.append("%.2f" % stats.average(key))

        self.html.statTable=HTMLDynListTable(tableAttrs={'align':'center'})
        if request.get('FORPRINTING', ''):
            self.html.doc.insert(0,self.html.statTable)
        else:
            self.html.doc.insert(1,self.html.statTable)
        statTable=self.html.statTable

        statTable.setCellColSpan(0,0,6)
        statTable.setCellcontents(0,0, "<strong>%s</strong> Statistics Report (%s - %s)" % (site,
                             options['startTime'].string7,
                             options['endTime'].string7),
                             {'class':'NLLabel','align':'center'})

        header=['', 'Hours avail.', 'Hours observed', 'Hours lost to faults',  'Hours lost to weather', 'Blanket Closures']
        statTable.add_array_after_last_row(header, {'class':'heading'})

        statTable.add_array_after_last_row(totalsList)
        #statTable.setCellattrs(statTable.getmaxRow(), 0, {'class':'heading'}, overwrite=True)
        statTable.add_array_after_last_row(averageList)
        #statTable.setCellattrs(statTable.getmaxRow(), 0, {'class':'heading'}, overwrite=True)

        #Finally add a summary
        self.html.summaryTable=HTMLDynListTable(tableAttrs={'align':'center'})
        if request.get('FORPRINTING', ''):
            self.html.doc.insert(1, self.html.summaryTable)
        else:
            self.html.doc.insert(2, self.html.summaryTable)
        summaryTable=self.html.summaryTable

        try:
            timeLossWeatherPercent=float(stats.sum('Weather'))/float(stats.sum('Total hours'))*100.0
        except ZeroDivisionError:
            timeLossWeatherPercent=0;
        summaryTable.add_array_after_last_row(['Percent time loss due to weather',
                                                '%.2f%%' % timeLossWeatherPercent])
        #summaryTable.setCellattrs(summaryTable.getmaxRow(), 0, {'width':200, 'class':'heading'}, overwrite=True)
        totalHObserved=float(stats.sum('Observed'))
        try:
            timeLossFaultsPercent=float(stats.sum('Total hours lost faults'))/float(stats.sum('Observed'))*100.0
        except ZeroDivisionError:
            timeLossFaultsPercent=0;
        summaryTable.add_array_after_last_row(['Percent time loss due to faults',
                                                '%.2f%%' % timeLossFaultsPercent])

        #summaryTable.setCellattrs(summaryTable.getmaxRow(), 0, {'class':'heading'}, overwrite=True)

        if request.get('INCLUDEPLOT', 'No')=='Yes':
            #TODO:... need to cache the plot... only create if one does not already exist.

            imFileName, dataFileName=naming.genImDataNames()

            #We expect data to be in html, so add an extension.
            dataFileName+='.html'
            time2Ave=7   #Week
            #The plot should start at the beginning of a semester... so take the defined startTime, and find the semester start time.
            st,et=util.getSemesterRange(startTime)

            #st, et=startTime, endTime

            #The plot should start at the start of the current semester, but only plot data until endTime.
            dataDict=telMetrics(site, plotType='timeLossPercentage', startTime=st, endTime=endTime,
            #dataDict=telMetrics(site, plotType='timeUsage', startTime=st, endTime=endTime,
                        fileName=os.path.join(GEAVars.path.fileSys.wwwData, imFileName),
                        dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName),
                        time2Ave=time2Ave,
                        stream=stream,
                        horizLines=(3,4),
                        theTitle='Semester Time Loss Percentage on %s' % site,
                        yLabel='Percent',
                        dpi=65,
                        yMin=None,
                        yMax=None)

            #Want to keep the 'http://server' bit. This is needed when geasouth, needs to grab the
            #generated images from geanorth.
            self.html.plotImage=HTMLPlot(vars={'imagefilename':os.path.join(GEAVars.path.web.wwwData, imFileName),
                                                'datafilename':os.path.join(GEAVars.path.web.wwwData, dataFileName)})

            self.html.doc.insert(3, self.html.plotImage)


    def _extractRemedyData(self, rQuery, rKeys, request, stream, startTime=None, endTime=None):
        """Extract data from Remedy.
        """
        extractor=RemedyDataExtractor(rQuery=rQuery, request=request,  startTime=startTime, endTime=endTime, rKeys=rKeys, dBase='NL')
        return extractor.extract()

def main(outStream=GEAVars.outStream, standAlone=False):

    NightLogPage(outStream, standAlone).run()

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
