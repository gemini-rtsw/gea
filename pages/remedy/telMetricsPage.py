#!/usr/bin/python

from pages.remedyBasePage import RemedyBasePage

from GEATime import Time
from GEARequest import RequestCollection, Request, RequestProcessor
from GEAHtml import HTMLDynListTable, HtmlHelper, HTMLFormCont, \
                                      HTMLTimeSelectorTelMetrics, HTMLOptionsTelMetrics, \
                                      HTMLPlot, HTMLTextBox, PyHtmlTableGEA
from GEADataHandler import RemedyDataExtractor
from GEAGeneral import util, naming
import GEAVars
import os

from specialized.telMetrics import telMetrics

class TelMetricsPage(RemedyBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """
        if topMenuList is None: topMenuList=[]

        RemedyBasePage._assemblePage(self,  topMenuList=topMenuList)
        html=self.html

        #Want to add a form with some options to the page.
        html.form=HTMLFormCont(vars={'cgifile':self.calledName}) #Form container.
        html.doc.append(html.form)

        #Add a time selector and some optoins.
        html.timeSelector=HTMLTimeSelectorTelMetrics()
        html.timeSelector.vars.update(Time.startEndTime2Dict(Time(self.genTime.seconds - 60 * Time.secPerDay), self.genTime, allCaps=False, monthAsWord=True))
        html.form.append(html.timeSelector)

        html.options=HTMLOptionsTelMetrics(vars={'plottitle':'',
                                                 'ymax':'',
                                                 'ymin':'',
                                                 'line1':'',
                                                 'line2':'',
                                                 'line3':'',
                                                 'line4':'',
                                                 'ylabel':'',
                                                 'dpi':100,
                                                 'time2ave':'7 Days',
                                                 'plottype':'Time Usage [ % (Faults, Weather, Eng, Comm, Sci) / Avail ]',
                                                 'site':GEAVars.site})
        html.form.append(html.options)

        #Table which will contain results from queries.
        #html.table=HTMLDynListTable(tableAttrs={'width':"100%",  'class':"tableList"})
        #html.doc.append(html.table)

    def _processRequest(self, request, stream):
        """
        """

        #Should probably move this somewhere higher up.
        request=RequestProcessor.process(request)

        #Generate equevalent names for the data and image. They will be random generated, bupetrrecheert have the same random 'stamp' and
        #different prefix and suffix.
        imFileName, dataFileName=naming.genImDataNames()

        #We expect data to be in csv, so add an extension.
        dataFileName+='.csv'

        startTime = Time().fromStartTimeDict(request, allCaps=True)
        endTime   = Time().fromEndTimeDict(request, allCaps=True)

        try:
            plotType={'Science Availability [ % Sci / (Night - Weather) ]':'scienceAvailabilityPercentage',
                      'Time Loss [ % Faults / Obs ]':'timeLossPercentage',
                      'Time Loss [ Hours ]':'timeLoss',
                      'Time Usage [ % (Faults, Weather, Eng, Comm, Sci) / Avail ]':'timeUsagePercentage',
                      'Time Usage [ Hours ]':'timeUsage',
                      'Weather Loss [ % Weather / Avail ]':'weatherLossPercentage',
                      'Weather Loss [ Hours ]':'weatherLoss'}[request['PLOTTYPE']]

        except KeyError:
            stream.write("Don't understand PLOTTYPE \"%s\". " % request['PLOTTYPE'])
            plotType=''

        time2Ave={'Daily':None, 'Weekly':7, 'Monthly':30}.get(request.get('TIME2AVE'))

        try:
            dataDict=telMetrics(request['SITE'], plotType=plotType, startTime=startTime, endTime=endTime,
                    fileName=os.path.join(GEAVars.path.fileSys.wwwData, imFileName),
                    dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName),
                    time2Ave=time2Ave,
                    stream=stream,
                    horizLines=(request.get('LINE1'),request.get('LINE2'),request.get('LINE3'),request.get('LINE4')),
                    theTitle=request.get('PLOTTITLE'),
                    yLabel=request.get('YLABEL'),
                    dpi=request.get('DPI'),
                    yMin=request.get('YMIN'),
                    yMax=request.get('YMAX'))

            self.html.plotImage=HTMLPlot(vars={'imagefilename':os.path.join(GEAVars.path.web.wwwData, imFileName),
                                                'datafilename':os.path.join(GEAVars.path.web.wwwData, dataFileName)})

            text="""<strong>Click on the plot to see tabulated data.</strong>"""
            self.html.textBox=HTMLTextBox(vars={'text':text})
            self.html.doc.insert(0, self.html.textBox)
            self.html.doc.insert(1, self.html.plotImage)

        finally:
            #Update the htlm widgets with options from the current request.
            for widget in ('options', 'timeSelector'):
                self._setWidgetVars(self.html[widget], request, [])


def main(outStream=GEAVars.outStream, standAlone=False):

    TelMetricsPage(outStream, standAlone).run()

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
