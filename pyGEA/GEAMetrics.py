#!/usr/bin/env python

import math
import datetime
import time
import pytz
import os

from GEADataHandler import RemedyDataExtractor
from GEATime import Time
import GEAVars

# Be warned: NightLogs are the, "UT Date" in the NightLog database, but the fault reports are
# all, "local time" - except for a bug where FR's at GS are wrong by HST - CST because of
# a bug in soap.

# A word on timezones.
#
#    The intent of the date selection on the telMetrics page is to choose a UTC date. I.e., at
# GN choosing, the day, 3/25 would mean the day after midnight Hawaii time. This is fine and
# dandy, except that both the fault reports and the night logs all use Hawaii time, even when
# filed from GS. The result is that all queries must be converted to Hawaii time, and times
# in query-data must be converted to UTC.


#    Convert GEATime() object to utc timestamp. This isn't as easy as it sounds because the
# timestamp in a GEATIme() has been, "corrected" for local time. So we have to remove
# this offset. But it gets worse... If we are using geanorth and we choose the, "CP" option
# we will get a utc timestamp. Ditto for geasouth viewing "MK".
#
#    While we're here, we strip off HH:MM:SS so that we always start at a consistent part
# of the day.
# 
#    Note we don't care what CP tz we adjust CP time too, because we're tossing HH:MM:SS anyway.

def Time2UT(Time):

    if Time.site == "MK":
        if time.timezone == 10 * 3600:		# Hawaii's timezone never changes, so we can get away w/ this.
            #print "Site: ", Time.site, "server@ geanorth, ", _UTDayStrip(Time.seconds + time.timezone), time.timezone
            return _UTDayStrip(Time.seconds + time.timezone)
        else:
            #print "Site: ", Time.site, "server@ geasouth, ", _UTDayStrip(Time.seconds), time.timezone
            return _UTDayStrip(Time.seconds)	# We're in MK, but viewing CP's telMetrics page.
    elif Time.site == "CP":
        if time.timezone == 10 * 3600:		# Hawaii's timezone never changes, so we can get away w/ this.
            #print "Site: ", Time.site, "server@ geanorth, ", _UTDayStrip(Time.seconds), time.timezone
            return _UTDayStrip(Time.seconds)	# We're in CP, but viewing MK's telMetrics page.
        else:
            #print "Site: ", Time.site, "server@ geasouth, ", _UTDayStrip(Time.seconds + time.timezone), time.timezone
            return _UTDayStrip(Time.seconds + time.timezone)		# Hack alert. Ignoring HH:MM:SS
    raise RuntimeError("Don't understand site '%s'" % Time.site)

# Used above to strip HH:MM:SS from timestamp.

def _UTDayStrip(utc): 

    import calendar

    utd = datetime.datetime.utcfromtimestamp(utc)
    ut1 = calendar.timegm([utd.year, utd.month, utd.day, 0.0, 0.0, 0.0, 0.0, 0,0, -1.0])
    ut2 = utc - (utc % (24 * 3600))
    
    if ut1 != ut2:
        raise RuntimeError("UT1 is not equal to UT2", ut1, ut2)

    return ut1

#
#    Take a the the gea-standard GEATime() object and return a unix timestamp that is
# adjusted to the beginning of that day, UTC (i.e., +10 hours to get HST). This timestamp
# can be used for NL lookups.
#
#    HOWEVER; Since we're adjusting from beginning-of-day UTC to to beginning-of-day HST,
# so HH:MM:SS will be 00:00:00 _the_prior_day_. Hence, we subtract 1 days worth of seconds.
# 

def Time2HSTTS(Time):
   return Time2UT(Time)

#
#    Return both twilights hawaii time regardless of where the query came from or who
# it's requesting. This is b/c everything in NL or FR is HST time.
#
#    Note that for CP, the twilight is CP twilight in HST time. Hence the funny business.
#

def Time2Twilights(Time):
    hst  = Time2HSTTS(Time)	# Convert to HST timestamp.
    hst -= 24 * 3600		# HST is UTC, but the prior day, + twilight offset.
    if Time.site == "CP":
        etw  = 18 * 3600	# 18:00 CP is 11:00 or 10:00 HST
    else:
        etw  = 18 * 3600	# Evening twilight offset to 18:00
    mtw  = etw + 13 * 3600	# Morning twilight is next day at 07:00

    return hst + etw, hst + mtw


def _getFRDataFromRemedy(attime):

    start_time, end_time = Time2Twilights(attime)
    start_time = Time(seconds = start_time + 10 * 3600)
    end_time   = Time(seconds = end_time   + 10 * 3600)

    site = attime.site

    if site != 'MK' and site != 'CP': raise Exception("Don't understand site %s" % attime.site)

    # Twilights determined (don't know if it's right of wrong) by tossing the HH:MM:SS and using only the date.
    # Start twilight is today's date at 18:00, End twilight is tomorrow's date at 07:00.

    #start_twilight = dt.replace(hour = 18, minute = 0, second = 0, microsecond = 0)
    #end_twilight   = dt.replace(hour = 7,  minute = 0, second = 0, microsecond = 0) + datetime.timedelta(days = 1)

    querydate = '%s"Occurred">="%s"+AND+"Occurred"<="%s"'
    query = querydate % (site, start_time.toLocaldatetime().strftime("%F+%H:%M"), end_time.toLocaldatetime().strftime("%F+%H:%M"))

    NL = {}

    rKeys = ('Date', 'CaseID', 'Status', 'TimeLost')
    extractor = RemedyDataExtractor(rQuery=query, request={}, rKeys=rKeys, dBase='FRS')

    FRs = extractor.extract()

    NL['Not Closed'] = NL['Not A Fault'] = NL['Procedural'] = NL['Unavoidable'] = NL['Technical Fault'] = 0.0

    for FR in FRs:
        # print "FR", FR
        date = FR['Date']

        # Check if a fault was created at night for an occurrence during
        # the day. S/b no timeloss, but just in case...

        # if date < start_time: continue

        if   FR['Status'] == "Closed-Not a fault": NL['Not A Fault']     += float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Unavoidable": NL['Unavoidable']     += float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Procedural":  NL['Procedural']      += float(FR['TimeLost'])
        elif FR['Status'] == "Closed"                or \
             FR['Status'] == "Duplicate"             or \
             FR['Status'] == "Closed-Won't be fixed" or \
             FR['Status'] == "Closed-Long Term Fix"  or \
             FR['Status'] == "Closed-Unresolved"     or \
             FR['Status'] == "Closed-Resolved":    NL['Technical Fault'] += float(FR['TimeLost'])
        else:
            NL['Not Closed'] += float(FR['TimeLost'])

        """
        print "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;", date, FR['Site'], FR['CaseID'], FR['Status'], 

        if   FR['Status'] == "Closed-Not a fault": print 'Not A Fault', float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Unavoidable": print 'Unavoidable', float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Procedural":  print 'Procedural',  float(FR['TimeLost'])
        elif FR['Status'] == "Closed"                or \
             FR['Status'] == "Duplicate"             or \
             FR['Status'] == "Closed-Won't be fixed" or \
             FR['Status'] == "Closed-Long Term Fix"  or \
             FR['Status'] == "Closed-Unresolved"     or \
             FR['Status'] == "Closed-Resolved":    print 'Technical Fault', float(FR['TimeLost'])
        else:
            print 'Not Closed', float(FR['TimeLost'])
        print "<br>\n"
        """
    return NL


# Get night log metrics from Remedy, and while we're at it get a
# list of faults that happened that night.

def getNLMetricsFromRemedy(attime):

    dataKeysDict = dict(tha  = 'Total hours',		# Was tha
                        sci  = 'Science usage',		# Was sci
                        eng  = 'Engineering',		# Was eng
                        comm = 'Commissioning',		# Was comm
                        wthr = 'Weather',		# Was thlw
                        shut = 'Shutdown',		# Was tels
                        obs  = 'Observed',		# Was tho
                        ut   = 'UT Date')		# Was ut

    faultKeysDict = dict(falt = 'Technical Fault',	# Was thlf
                         nflt = 'Not A Fault',		# Was nch
                         proc = 'Procedural',		# New
                         void = 'Unavoidable', 		# new
                         ncls = 'Not Closed')		# Not closed

    rQuery=''
    rKeys=tuple(dataKeysDict.values())

    dataKeysDict = dict(dataKeysDict.items() + faultKeysDict.items())

    start_time  = Time2HSTTS(attime)	# Convert to HST timestamp.
    start_time += 10 * 3600	       	# NL's are funny timestamped.

    querysite = "(('Telescope'==\"%s\") AND ('UT Date'==\"%d\"))"

    if   attime.site == 'CP': query = querysite % ("South", start_time)
    elif attime.site == 'MK': query = querysite % ("North", start_time)
    else: raise RuntimeError("Don't understand site %s" % attime.site)

    extractor = RemedyDataExtractor(rQuery=query, request={}, rKeys=rKeys, dBase='NL')

    NL = extractor.extract()	# Do the remedy NL query

    if len(NL) == 0: return None

    NL = NL[0]

    # End NL query.



    # Begin FL queries.

    start_time, end_time = Time2Twilights(attime)
    start_time = Time(seconds = start_time + 10 * 3600)
    end_time   = Time(seconds = end_time   + 10 * 3600)

    querydate = '%s"Occurred">="%s"+AND+"Occurred"<="%s"'

    frKeys = ('Date', 'CaseID', 'Status', 'TimeLost', 'One line summary', 'AssignedTo')

    query = querydate % (attime.site, start_time.toLocaldatetime().strftime("%F+%H:%M"), end_time.toLocaldatetime().strftime("%F+%H:%M"))

    extractor = RemedyDataExtractor(rQuery=query, request={}, rKeys=frKeys, dBase='FRS')

    FRs = extractor.extract()

    NL['Not Closed'] = NL['Not A Fault'] = NL['Procedural'] = NL['Unavoidable'] = NL['Technical Fault'] = 0

    for FR in FRs:
        date = FR['Date']

        FR['DateTime'] = date

        if   FR['Status'] == "Closed-Not a fault": NL['Not A Fault']     += float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Unavoidable": NL['Unavoidable']     += float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Procedural":  NL['Procedural']      += float(FR['TimeLost'])
        elif FR['Status'] == "Closed"                or \
             FR['Status'] == "Duplicate"             or \
             FR['Status'] == "Closed-Won't be fixed" or \
             FR['Status'] == "Closed-Long Term Fix"  or \
             FR['Status'] == "Closed-Unresolved"     or \
             FR['Status'] == "Closed-Resolved":    NL['Technical Fault'] += float(FR['TimeLost'])
        else:
            NL['Not Closed'] += float(FR['TimeLost'])

        """
        print date, FR['Site'], FR['CaseID'],

        if   FR['Status'] == "Closed-Not a fault": print 'Not A Fault', float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Unavoidable": print 'Unavoidable', float(FR['TimeLost'])
        elif FR['Status'] == "Closed-Procedural":  print 'Procedural',  float(FR['TimeLost'])
        elif FR['Status'] == "Closed"                or \
             FR['Status'] == "Duplicate"             or \
             FR['Status'] == "Closed-Won't be fixed" or \
             FR['Status'] == "Closed-Long Term Fix"  or \
             FR['Status'] == "Closed-Unresolved"     or \
             FR['Status'] == "Closed-Resolved":    print 'Technical Fault', float(FR['TimeLost'])
        else:
            print 'Not Closed', FR['Status'], float(FR['TimeLost'])
        """

    NL['Fault Reports'] = FRs

    return NL


# = getDataFromRemedy(rKeys=rKeys, site='MK', startTime=startTime, endTime=endTime)
def getDataFromRemedy(rKeys, site=None, startTime=None, endTime=None, dBase='NL'):

    querysite = "('Telescope'==\"%s\") AND ((('UT Date'>=\"%d\") AND ('UT Date'<=\"%d\")))"

    if endTime == None: 	# If no endTime, then just get one NL.
        endTime = Time(startTime.seconds, startTime.site)

    # startTime.seconds -= 24 * 3600			# Go back one day so we end up with localday.

    startTime.site = site	# Time.site gets messed up when we do, MK_and_CP.
    endTime.site   = site	# Time.site gets messed up when we do, MK_and_CP.

    start_time = Time2HSTTS(startTime) + 10 * 3600	# NL cares about the HH:MM:SS!
    end_time   = Time2HSTTS(endTime)   + 10 * 3600	# NL cares about the HH:MM:SS!


    if   site == 'CP': query = querysite % ("South", start_time, end_time)
    elif site == 'MK': query = querysite % ("North", start_time, end_time)
    else: raise RuntimeError("Don't understand site %s" % theSite)

    # print "getDataFromRemedy", query, rKeys

    # print "NL Query:", query, "(%s - %s)<br>" % (datetime.datetime.utcfromtimestamp(start_time),  datetime.datetime.utcfromtimestamp(end_time))

    extractor = RemedyDataExtractor(rQuery=query, request={}, rKeys=rKeys, dBase='NL')

    bartime = time.time()
    NLs = extractor.extract()
    # print "NL query took ", time.time() - footime, " seconds."

    result = []

    mytime = Time(startTime.seconds, startTime.site)	# Make a copy so I can ++seconds.

    footime = time.time()
    for NL in NLs:

        result.append(dict(NL.items() + _getFRDataFromRemedy(mytime).items()))

        mytime.seconds += Time.secPerDay

    # print "Query took ", time.time() - bartime, " seconds.<br>"

    return result


if __name__=='__main__':

    
    # Time2UT(Time(1343815200, site = "MK"))
    # Time2UT(Time(1343815200, site = "CP"))

    # print Time2HSTTS(Time(1343815200, site = "MK"))
    # print Time2HSTTS(Time(1343815200, site = "CP"))

    # print Time2Twilights(Time(1343815200, site = "MK"))
    # print Time2Twilights(Time(1343815200, site = "CP"))

    print getNLMetricsFromRemedy(Time(seconds = time.time() - 86400 * 30 * 6 - 86400 * 10, site="MK"))
