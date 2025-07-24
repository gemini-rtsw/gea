#!/usr/bin/env python

import datetime
import httplib
import re

"""
This should result in a return value something like this:

GN-2012A-Q-42 GN-2013A-SV-101 GN-2013A-Q-24 GN-2013A-Q-27 GN-2013A-Q-14 GN-2012B-Q-33 GN-2013A-Q-56 GN-ENG-GNIRS-Engineering GN-2012B-Q-24 GN-CAL20130206 GN-2013A-Q-50 GN-2013A-Q-81

"""

def getPrograms(site, date=None):

    if site == 'MK': aHost = "fits.hi.gemini.edu"
    else:            aHost = "fits.cl.gemini.edu"

    if date:
        aFits = "/programsobserved/%04d%02d%02d" % (date.year, date.month, date.day)
    else:
        aFits = "/programsobserved"

    try:
        con = httplib.HTTPConnection(aHost)
        con.request("GET", aFits)
        req = con.getresponse()
        if req.status != 200: return "Error retrieving programs."
        page = req.read()
    except:
        return "Error retrieving programs."

    m = re.search('To paste into nightlog: ..H2..P.(.*) ..P..H2.With more detail:', page)
    if m: return m.group(1)
    return None


if __name__=='__main__':

    print getPrograms("MK")
    print getPrograms("CP")
    print getPrograms("MK", datetime.date(2019, 2, 3))
    print getPrograms("CP", datetime.date(2019, 2, 3))
