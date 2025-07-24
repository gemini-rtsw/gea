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

"""

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
