#!/usr/bin/python

import GEAVars
from GEATime import Time
from GEARequest import RequestCollection, Request
from GEAHtml import HTMLDynTable, HTMLDynListTable, HTMLTextBox, HTMLFormCont, HTMLOptionsNLNightly,  HtmlHelper, HTMLCont, MenuItem, HTMLOptionsNLReport, HTMLTimeSelectorNLReport, HTMLPlot
from GEADataHandler import RemedyDataExtractor
from GEAAnalyzer import Stats
from GEAGeneral import util, naming
from pages.geaBasePage import GeaBasePage
import os

from specialized.telMetrics import telMetrics
from GEAMetrics import getNLMetricsFromRemedy


class NightLogEntry(GeaBasePage):
    format2Title={'Log':'Log', 'Enter':'Enter'}

    menuItemList=[
                MenuItem('Nightlog Entry Form', GEAVars.dispatchScript+'/pages/remedy/nightLogEntry'),
                MenuItem('Nightlog', GEAVars.dispatchScript+'/pages/remedy/nightLogPage'),
                ]

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """
        topMenuList = topMenuList or []
        GeaBasePage._assemblePage(self,  topMenuList=[NightLogEntry.menuItemList]+topMenuList)
        html=self.html

        html.form=HTMLFormCont() #Form container.
        #cgifile is of the form:   /run/dispatch.gea/some_directories/file_without_py_extenstion

        html.form.vars.update(cgifile=self.calledName)

        html.table=HTMLDynListTable(tableAttrs={'width':"100%",  'class':"tableList"})
        html.doc.append(html.table)

    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is
        a need for a default requests. See self.run() how this is used.

        A dictionary (or a RequestCollection) of nameTag/request pairs should be returned.
        """

        nameTag=None

        return {nameTag: Request(request={'FORMAT':'Entry', 'SITE':GEAVars.site, }, nameTag=nameTag) }


    def _processRequest(self, request, stream):

        import datetime, time

        site = request.get('SITE', 'MK')

        bgcolor = "#c0e7b5"	# Tonight's log is lightgreen, updating a prior log is lightblue, future log is pink

        if request.get('STARTYEAR', None) and request.get('STARTMONTH', None) and request.get('STARTDAY', None) and request.get('STARTHOUR', None):
            requestTime = datetime.datetime(int(request['STARTYEAR']), int(request['STARTMONTH']), int(request['STARTDAY']), int(request['STARTHOUR']), 0, 0)
            if ((requestTime - datetime.datetime.now()) > datetime.timedelta(0)):
                tonightsLog = False
            if request.get('useutc'):
                requestTime += datetime.timedelta(seconds = time.timezone)	# FIXME - THIS IS BROKEN
        else:
            if request.get('useutc'):
                requestTime = datetime.datetime.utcnow()
            else:
                requestTime = datetime.datetime.today()

        dataList = getNLMetricsFromRemedy(Time(seconds=time.time() - 24 * 3600, site=site))

        print request

        foobazzle = "today"

        def emit_checkbox(name, value):
            foo = """checked"""

        def emit_inst_selection(name, value):
            instNamesNorth = ("GMOS-N", "NIRI", "NIFS", "MICHELLE", "ALTAIR", "AC-N", "GNIRS", "TEXES", "GNIRS", "PHOENIX", "TRECS", "NICI", "FLAMINGO-II", "MCAO")
            instNamesSouth = ("GMOS-S", "NIRI", "NIFS", "MICHELLE", "ALTAIR", "AC-S", "GNIRS", "TEXES", "GNIRS", "PHOENIX", "TRECS", "NICI", "FLAMINGO-II", "MCAO")

            instruments = value.split()

            selection = ""

            for i in instNamesNorth:
                if i in instruments: selection += '    <input type="checkbox" name="inst" value="%s" checked> %s\n' % (i, i)
                else:                selection += '    <input type="checkbox" name="inst" value="%s"> %s\n' % (i, i)

            return selection

        def emit_wave_selection(name, value):
            wavelengths = ("", "0.350", "0.475", "0.550", "0.630", "0.700", "0.780", "0.860 ", \
                          "0.925", "1.1", "1.25 ", "1.65", "2.2 ", "3.0", "3.8", "5.0", "8.0", \
                          "9.0 ", "10.5", "12.0", "13.0", "18.5 ", "21.0", "24.5")

            selection = ""

            for w in wavelengths:
                if value is None:
                    selection += "    <option> %s\n" % w
                else:
                    if w in value: selection += "        <option selected> %s\n" % w
                    else:          selection += "        <option> %s\n" % w

            return selection

        def emit_quality_log():
            return """
   <tr>
    <td> 18:50
    <td> 0.925
    <td> 1.20
    <td> 1.31
    <td> 1.42
    <td> Example log entry
   <tr>
    <td> 18:52
    <td> 0.925
    <td> 1.20
    <td> 1.31
    <td> 1.42
    <td> Example log entry %s""" % foobazzle

        def emit_fault_reports():
            return """
   <tr>
    <td> 123456
    <td> 12:34
    <td> 1.25
    <td> Cows chased my chickens.
   <tr>
    <td> 654321
    <td> 12:34
    <td> 1.25
    <td> Pigs ate my duck."""

        def emit_generic(name):
            return request.get(name, '')

        html=self.html

        bar = (
            bgcolor,
            emit_generic('author'),
            emit_generic('cceaddr'),
            emit_generic('ssupport'),
            emit_generic('bsupport'),
            emit_generic('psupport'),
            emit_generic('entobs'),
            emit_generic('scihrs'),
            emit_generic('enghrs'),
            emit_generic('commhrs'),
            emit_generic('weatherhrs'),
            2.0,
            emit_generic('laserhrs'),
            emit_checkbox('telshut', request.get('telshut', '')),
            emit_checkbox('nightlost', request.get('nightlost', '')),
            emit_inst_selection('inst', request.get('inst', '')),
            emit_quality_log(),
            emit_generic('qlogtime'),
            emit_wave_selection('qlogwave', request.get('qlogwave')),
            emit_generic('plan'),
            emit_generic('summary'),
            emit_fault_reports(),
            emit_generic('problems'),
            emit_generic('details'))

        foo = """
 <div style="border: thin solid black;  background-color:%s">
  <center>
  <h2> Nightlog Entry Form </h2>
  </center>
  <table width="100%%">
   <tr>
    <td> Nightlog Author:
    <td> <input type="text" name="author" value="%s" size="40">
   <tr>
    <td title="Use commas to separate email addresses"> Email To:
    <td> <input type="text" name="cceaddr" value="%s" size="40">
   <tr>
    <td> Observers:
    <td> <input type="text" name="ssupport" value="%s" size="40">
   <tr>
    <td> Base Support:
    <td> <input type="text" name="bsupport" value="%s" size="40">
   <tr>
    <td> Phone Support:
    <td> <input type="text" name="psupport" value="%s" size="40">
   <tr>
    <td> Programs Observed:
    <td id="sciobserved">GN-2011B-C-1 GN-CAL20120126 GN-2011B-SV-101 GN-2011B-Q-75 GN-2011B-Q-41 GN-2010B-Q-3 GN-CAL20120125
   <tr>
    <td title="Engineering Tasks Observed (e.g., ENT1234)"> Engineering Tasks:
    <td> <input type="text" name="entobs" value="%s" size="40">
  </table>
  <table width="100%%" style="border: thin solid black; background-color:white">
   <tr style="text-align:center; font-weight:bold; background-color:#e5d5b5">
    <td style="text-align:center; font-weight:bold; background-color:#e5d5b5"> Available
    <td> Science
    <td> Engineering
    <td> Commissioning
    <td> &nbsp;Weather&nbsp;
    <td> &nbsp;Faults&nbsp;
    <td> Laser Shuttered
    <td> Blanket Closure
   <tr>
    <td> 10.87 hours
    <td> <input type="text" name="scihrs" value="%s" size="3"> hours
    <td> <input type="text" name="enghrs" value="%s" size="3"> hours
    <td> <input type="text" name="commhrs" value="%s" size="3"> hours
    <td> <input type="text" name="weatherhrs" value="%s" size="3"> hours
    <td> 2.0 hours
    <td> <input type="text" name="laserhrs" value="%s" size="3"> hours
    <td> <input type="text" name="blankethrs" value="%s" size="3"> hours
  </table>
  <table>
   <tr>
    <td> Telescope&nbsp;Shutdown:
    <td> <input type="checkbox" name="telshut" value="%s">
   <tr>
    <td> Night&nbsp;Lost&nbsp;to&nbsp;Weather:
    <td> <input type="checkbox" name="nightlost" value="%s">
   <tr>
    <td> Instrument(s) Used:
    <td>
     %s
  </table>
  <h4> Telescope Image Quality Log </h4>
  <table width="100%%">
   <tr>
    <td title="Leave blank to use current time"> Local Time
    <td title="Use closest value"> Wavelength
    <td> FWHM(arcsec)
    <td> Strehl
    <td> AirMass
    <td> Notes
   <tr>
    <td> HH:MM
    <td> (microns)
    <td> n.nn
    <td> n.nn
    <td> n.nn
    <td> &nbsp;
%s
   <tr>
    <td> <input type="text" name="qlogtime" value="%s" size="3">
    <td>
    <select name="qlogwlen"> %s </select>
    <td> <input type="text" name="qlogfwhm"    size="5">
    <td> <input type="text" name="qlogstrehl"  size="5">
    <td> <input type="text" name="qlogairmass" size="5">
    <td> <input type="text" name="qlognotes"   size="40">
  </table>
  <h4> Plan for the Night </h4>
  <textarea cols="80" name="plan">%s</textarea>
  <h4> Summary for the Night </h4>
  <textarea cols="80" name="summary">%s</textarea>
  <h4> Fault Reports </h4>
  <div width="100%%">
  <table>
   <thead>
    <td> FR#
    <td> Time
    <td> TimeLost
    <td> Summary
%s
  </table>
  </div>
  <h4> Additional Comments </h4>
  <textarea cols="80" name="problems">%s</textarea>
  <h4 title="Please DO NOT use target names or classes, only use program IDs in the nightlog"> Detailed Entry </h4>
  <textarea cols="80" rows="20" name="details">%s</textarea>
 </div>
""" % bar
        
        html.form.append(foo)
        html.doc.append(html.form)

def main(outStream=GEAVars.outStream, standAlone=False):

    NightLogEntry(outStream, standAlone).run()

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)



""""
MOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO



#!/usr/bin/python

import sys, os
from GEAPage import BasePage
from GEAPlainPage import BasePlainPage
from GEAMetrics import getNLMetricsFromRemedy
from GEATime import Time
import GEAVars

from specialized.doloresMetrics import doloresMetrics

class DoloresMetricsPage(BasePlainPage):

    def _assemblePage(self):
        pass		# No page to assemble

    def _processRequest(self, request):

        # self.body += request.__str__() + "\n"

        if not 'STARTYEAR' in request:
            import time, datetime
            if time.timezone == 10 * 3600:          			    	# Hawaii's timezone never changes, so we can get away w/ this.
                request['SITE'] = 'MK'
            elif time.timezone == 6 * 3600 or time.timezone == 7 * 3600:	# Chile's tz changes, ...
                request['SITE'] = 'CP'
            else:
                raise RuntimeError("Don't understand site timezone offset of '%d'" % time.timezone)
            today = datetime.datetime.today()
            request['STARTYEAR']  = today.year
            request['STARTMONTH'] = today.month
            request['STARTDAY']   = today.day

        request['STARTHOUR']   = 0	# Request doesn't supply HH:MM:SS, but fromTimeDict requires them.
        request['STARTMINUTE'] = 0
        request['STARTSECOND'] = 0

        # self.body += "After\n"
        # self.body += request.__str__() + "\n"

        startTime = Time().fromStartTimeDict(request, allCaps=True, monthAsWord='Auto')
        startTime.site = request['SITE']

        dataList = getNLMetricsFromRemedy(startTime)
        if dataList is None:
            self.body += "None"
            return
        self.body += "%d,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\n" % \
                  (dataList['UT Date'],     dataList['Total hours'],   dataList['Technical Fault'], dataList['Not Closed'], \
                   dataList['Unavoidable'], dataList['Science usage'], dataList['Observed'],        dataList['Not A Fault'], \
                   dataList['Engineering'], dataList['Weather'],       dataList['Shutdown'],        dataList['Commissioning'],\
                   dataList['Procedural'])

        frs = dataList['Fault Reports']
        for fr in frs:
            self.body += "%s,%s,%s,%s,%s,%s\n" % (fr['CaseID'], fr['Occurrence Date'], fr['AssignedTo'], fr['TimeLost'], fr['Status'], fr['One line summary'])
            # self.body += "%s,%s,%s,%s,%s,%s,%s,%s\n" % (fr['Status'], fr['One line summary'], fr['CaseID'], fr['Occurrence Date'], fr['AssignedTo'], fr['TimeLost'], fr['Disposition'], fr['GPT_Site'])

        # self.body += "dataList" + dataList.__str__()



def main(outStream=GEAVars.outStream, standAlone=False):

    DoloresMetricsPage(outStream, standAlone).run()
        

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)


#!/usr/bin/env python

import math
import datetime
import time
import pytz
import sys

# Need this order for things to work properly - note that some rc options
# (example numerix) need should be set in the /usr/share/matplotlib/matplotlibrc
# file directly. matplotlibConfig() only sets up stuff that can be easily set
# after modules already imported.

from GEADataHandler import RemedyDataExtractor
from GEATime import Time
import GEAVars

from GEAMetrics import getNLMetricsFromRemedy

def doloresMetrics():

    startTime = Time(time.time() - 24 * 3600, "MK")     # Note that we're are looking at last nights NL!

    dataList = getNLMetricsFromRemedy(startTime)

    return dataList


if __name__=='__main__':

    doloresMetrics()

"""
