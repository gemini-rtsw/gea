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
                MenuItem('Nightlog Entry Form', GEAVars.dispatchScript+'/pages/nightlog/nightLogEntry'),
                MenuItem('Nightlog', GEAVars.dispatchScript+'/pages/nightlog/nightLogPage'),
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
        weekdays = ("Bad", "Mon", "Tue", "Wed", "Thu", "Fri", "Sun")
        months   = ("Bad", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

        html=self.html

        import datetime, time, re
        from Almanac import getAlmanac
        from nightLogDB import nightLogDB

        self.site = site = request.get('SITE', 'MK')

        self.nlDB = nightLogDB()






        #
        # Figure out what night we're logging. If there is no date defined, then
        # default to today. This needs to be smarter, but I need user feedback
        # first.
        #
        # RIGHT NOW IT USES LOCAL TIME. THIS IS WRONG, THE NIGHTLOG WILL MAGICALLY
        # CHOOSE THE WRONG DATE after 2pm HST, or around 7pm CST.
        #

        if request.get('logdate'):
            nd = request.get('logdate')
            requestDate = datetime.date(year = int(nd[0:4]), month = int(nd[5:7]), day = int(nd[8:10]))
        else:
            requestDate = datetime.date.today()
            
        # For testing
        # requestDate = datetime.date.today() - datetime.timedelta(days = 40)
        # End for testing

        #
        # If the user has changed the date, then don't write anything to the database because the values
        # coming in are for the prior date, and you'll nuke the values for the date your changing too.
        #

        bgcolor = "#f3f3f3"	# Tonight's log is lightgreen, updating a prior log is lightblue, future log is pink
        datewarning = ''

        if requestDate > datetime.date.today():		# Check if log is in the future.
            bgcolor = "#fff3f3"	# Light pink with warning.
            datewarning = '<h3 style="color:red">Warning: Modifying <i>future</i> nightlog</h3>'

        if requestDate < datetime.date.today():		# Check if log is in the past.
            bgcolor = "#f3fff3"	# Light green, with warning.  
            datewarning = '<h3 style="color:red">Warning: Modifying <i>past</i> nightlog</h3>'

        weekday = weekdays[requestDate.weekday()]
        month   = months[requestDate.month]



        #
        # Get the almanac and extract AvailableTime from it.
        #

        self.Almanac = getAlmanac(self.site)

        m = re.search('Nautical twilights.* (\d+.\d+) hrs', self.Almanac)
        self.AvailableTime = float(m.group(1))


        #
        # If user has changed days, request.get('changenight') true, then we don't write any values
        # in request[.. ]. Instead we fetch values from the database.
        #

        self.nlEntry = nlE = self.nlDB.getNightLog(site, requestDate)
        if nlE is None:
            datewarning += "<h4> No recorded data for %s using default values </h4>" % requestDate
            self.nlEntry = nlE = self._dreamUpDummyData(site, requestDate)

#        if not request.get('changenight'):
#            self.nlEntry = self.nlDB.putNightLog(requestDate, self.nlEntry)




        def emit_checkbox(name, value):
            foo = """checked"""




        def emit_inst_selection(name, value):
            instNames = open("/gemsoft/etc/gea/pages/instruments.txt").read().split()

            instruments = value.split()

            selection = ""

            n = 0
            for i in instNames:
                if i in instruments: selection += '      %s <input type="checkbox" name="inst" value="%s" checked> &nbsp; &nbsp;\n' % (i, i)
                else:                selection += '      %s <input type="checkbox" name="inst" value="%s">  &nbsp; &nbsp;\n' % (i, i)

                n += 1
                if (n % 6) == 0:
                    selection += "      <br>\n"

            return selection

        def emit_wave_selection(name, value):
            wavelengths = ("", "R", "Y", "M", "COW", "0.350", "0.475", "0.550", "0.630", "0.700", "0.780", "0.860 ", \
                          "0.925", "1.1", "1.25 ", "1.65", "2.2 ", "3.0", "3.8", "5.0", "8.0", \
                          "9.0 ", "10.5", "12.0", "13.0", "18.5 ", "21.0", "24.5")

            selection = ""

            if value is None:
                for w in wavelengths:
                    selection            += "            <option> %s\n" % w
            else:
                if w in value: selection += "            <option selected> %s\n" % w
                else:          selection += "            <option> %s\n" % w

            return selection

        def emit_quality_log():
            return """
       <tr>
        <td> <input type="image" name="qlogdel:18:50" src="/www_media/images/del.gif" title="Delete entry">
        <td> 18:50
        <td> 0.925
        <td> 1.20
        <td> 1.31
        <td> 1.42
        <td> Example log entry
       <tr>
        <td> <input type="image" name="qlogdel:18:50" src="/www_media/images/del.gif" title="Delete entry">
        <td> 18:52
        <td> 0.925
        <td> 1.20
        <td> 1.31
        <td> 1.42
        <td> Example log entry"""

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
            if type(name) == type(None): return ""
            return nlE[name]






        logdatmsg = "%s %s %02d, %04d" % (weekday, month, requestDate.day, requestDate.year)

        d = datetime.date.today()
        logtonight   = "%04d-%02d-%02d" % (d.year, d.month, d.day)

        d = d - datetime.timedelta(days = 1)
        logyesterday = "%04d-%02d-%02d" % (d.year, d.month, d.day)
        dogyesterday = "%s %d" % (months[d.month], d.day)


        d = d + datetime.timedelta(days = 2)
        logtomorrow  = "%04d-%02d-%02d" % (d.year, d.month, d.day)
        dogtomorrow = "%s %d" % (months[d.month], d.day)

        foo = """
 <form method="get" action="/pages/nightlog/nightLogEntry">
 <div style="border: thin solid black">
  <table bgcolor="%s" width="100%%">
   <tr>
    <td width="30%%">
      &nbsp; <input type="submit" value="Save"    style="width:70px" title="Save nightlog so far so it doesn't get lost."><br>
      &nbsp; <input type="submit" value="Email"   style="width:70px" title="Email nightlog."><br>
      &nbsp; <input type="submit" value="Preview" style="width:70px" title="Preview nightlog that will get emailed.">
    <td width="50%%" style="text-align:center">
       <h2> CP Non-functional <i>Prototype</i> Nightlog Entry Form </h2>
       <h3> Night of %s</h2>
       %s
    <td width="20%%" style="text-align:right">
      <table>
       <tr>
         <td style="text-align:left">   <a href="/pages/nightlog/nightLogEntry?logdate=%s&changenight=1"> %s</a>
         <td style="text-align:center"> <a href="/pages/nightlog/nightLogEntry?logdate=%s&changenight=1"> Tonight </a> 
         <td style="text-align:right">  <a href="/pages/nightlog/nightLogEntry?logdate=%s&changenight=1"> %s </a> 
       <tr>
         <td colspan="3"> <input type="date" name="logdate" value="%s">
       <tr>
         <td colspan="3"> <input type="submit" name="changenight" value="Change Date" style="width:100%%" >
      </table>
  </table>
""" % (bgcolor, logdatmsg, datewarning, logyesterday, dogyesterday, logtonight, logtomorrow, dogtomorrow, logtonight)

        html.doc.append(foo)


        bar = (
            self.AvailableTime,
            emit_generic('scihrs'),
            emit_generic('enghrs'),
            emit_generic('commhrs'),
            emit_generic('weatherhrs'),
            0.0,
            emit_generic('lasershut'),
            emit_generic('blankshut') )


        foo = """
  <table width="100%%" style="border: thin solid black; background-color:white">
   <tr style="text-align:center; font-weight:bold; background-color:#e5d5b5">
    <td> Available
    <td> Science
    <td> Engineering
    <td> Commissioning
    <td> &nbsp;Weather&nbsp;
    <td> &nbsp;Faults&nbsp;
    <td> Laser Shuttered
    <td> Blanket Closure
   <tr>
    <td> %s
    <td> <input type="text" name="scihrs" value="%s" size="3"> hours
    <td> <input type="text" name="enghrs" value="%s" size="3"> hours
    <td> <input type="text" name="commhrs" value="%s" size="3"> hours
    <td> <input type="text" name="weatherhrs" value="%s" size="3"> hours
    <td> %s hours
    <td> <input type="text" name="lasershut" value="%s" size="3"> hours
    <td> <input type="text" name="blankshut" value="%s" size="3"> hours
  </table>
""" % bar
        html.doc.append(foo)






        bar = (
            bgcolor,
            emit_generic('submitter'),
            request.get('cceaddr',''),
            bgcolor,
            emit_generic('ssupport'),
            emit_generic('bsupport'),
            bgcolor,
            emit_generic('psupport') )

        foo = """
  <table width="100%%" style="border: thin solid black">
   <tr>
    <td class="heading"> Nightlog&nbsp;Author:
    <td bgcolor="%s"> <input type="text" name="submitter" value="%s" size="40">
   <tr>
    <td class="heading" title="Use commas to separate email addresses"> Email To:
    <td> <input type="text" name="cceaddr" value="%s" size="40">
   <tr>
    <td class="heading"> Summit&nbsp;Support:
    <td bgcolor="%s"> <input type="text" name="ssupport" value="%s" size="40">
   <tr>
    <td class="heading"> Base Support:
    <td> <input type="text" name="bsupport" value="%s" size="40">
   <tr>
    <td class="heading"> Phone Support:
    <td bgcolor="%s"> <input type="text" name="psupport" value="%s" size="40">
""" % bar

        html.doc.append(foo)





        from Programs import getPrograms

        pgms = getPrograms(site, requestDate)
        if pgms == None: pgms = ""

        bar = (
            pgms,
            bgcolor,
            emit_generic('entprog'))

        foo = """
   <tr>
    <td class="heading" title="Science Program Type &amp; ID Number"> Programs Observed
    <td> <textarea cols="80" name="sciobserved">%s</textarea>
   <tr>
    <td class="heading" title="Engineering Tasks Observed (e.g., ENT1234)"> Engineering Tasks:
    <td bgcolor="%s"> <textarea cols="80" name="entprog">%s</textarea>
""" % bar

        html.doc.append(foo)






        bar = (
            emit_checkbox('telshut', request.get('telshut')),
            emit_checkbox('weathershut', request.get('weathershut')),
            bgcolor,
            emit_inst_selection('inst', nlE['inst']))

        foo = """
   <tr>
    <td class="heading"> Night Lost
    <td>
      Shutdown <input type="radio" name="telshut" value="%s">
      Weather  <input type="radio" name="weathershut" value="%s">
   <tr>
    <td class="heading"> Instrument(s)&nbsp;Used:
    <td bgcolor="%s">
%s
""" % bar

        html.doc.append(foo)





        bar = (
            emit_quality_log(),
            request.get('qlogtime', 'now'),
            emit_wave_selection('qlogwave', request.get('qlogwave')),
            bgcolor,
            emit_generic('plan'),
            emit_generic('summary'),
            bgcolor,
            emit_fault_reports(),
            emit_generic('problems'),
            bgcolor,
            self.Almanac,
            emit_generic('details'))

        foo = """
   <tr>
    <td class="heading"> Quality Log
    <td>
      <table>
       <thead>
        <td> &nbsp;
        <td title="Leave blank to use current time"> Local Time
        <td title="Use closest value"> Wavelength
        <td> FWHM(arcsec)
        <td> Strehl
        <td> AirMass
        <td> Notes
       <thead>
        <td> &nbsp;
        <td> HH:MM
        <td> (microns)
        <td> n.nn
        <td> n.nn
        <td> n.nn
        <td> &nbsp;
%s
       <tr>
        <td> <input type="image" name="qlogsubmit" src="/www_media/images/add.gif" title="Add entry">
        <td> <input type="text" name="qlogtime" value="%s" size="3">
        <td>
          <select name="qlogwlen">
%s
          </select>
        <td> <input type="text" name="qlogfwhm"    size="5">
        <td> <input type="text" name="qlogstrehl"  size="5">
        <td> <input type="text" name="qlogairmass" size="5">
        <td> <input type="text" name="qlognotes"   size="34">
      </table>
   <tr>
    <td class="heading"> Plan for the Night
    <td bgcolor="%s"> <textarea cols="80" name="plan">%s</textarea>
   <tr>
    <td class="heading"> Summary for the Night
    <td> <textarea cols="80" name="summary">%s</textarea>
   <tr>
    <td class="heading"> Fault Reports 
    <td bgcolor="%s">
      <table>
        <thead>
         <td> FR#
         <td> Time
         <td> TimeLost
         <td> Summary
     %s
       </table>
   <tr>
    <td class="heading"> Additional Comments
    <td> <textarea cols="80" name="problems">%s</textarea>
   <tr>
    <td class="heading"> Almanac
    <td bgcolor="%s"> <pre> %s </pre>
   <tr>
    <td class="heading" title="Please DO NOT use target names or classes, only use program IDs in the nightlog"> Detailed Entry 
    <td> <textarea cols="80" rows="20" name="details">%s</textarea>
  </table>
  <br>
  <br>
  <input type="submit" value="Save" title="Save nightlog so far so it doesn't get lost.">
  <input type="submit" value="Email" title="Email nightlog.">
  <input type="submit" value="Preview" title="Preview nightlog that will get emailed.">
 </div>
 </form>
""" % bar
        
        html.doc.append(foo)

    def _dreamUpDummyData(self, site, requestDate):
        r = {}
        r['date']       = requestDate
        r['submitter']  = ""
        r['almanac']    = self.Almanac
        r['ssupport']   = ""
        r['bsupport']   = ""
        r['psupport']   = ""
        r['programs']   = ""
        r['entprog']    = ""
        r['scihrs']     = 0.0
        r['enghrs']     = 0.0
        r['weatherhrs'] = 0.0
        r['commhrs']    = 0.0
        r['lasershut']  = 0.0
        r['blankshut']  = 0.0
        r['inst']       = ""
        r['plan']       = ""
        r['summary']    = ""
        r['problems']   = ""
        r['details']    = ""
        rt = []
        r['qlog'] = rt 
        return r

def main(outStream=GEAVars.outStream, standAlone=False):

    NightLogEntry(outStream, standAlone).run()

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)


