#!/usr/bin/env python

import datetime
import subprocess
import re

"""
This should result in a return value something like this:

Almanac for Mauna Kea, Hawaii:                                                  
  For the night of: Mon, 2013 Feb 4 ---> Tue, 2013 Feb 5                          
  Local Mean Sidereal Time at midnight = 8 40 58.5                                
  Sunset ( 4215 m horizon): 18 25 HST; Sunrise: 6 46 HST                          
  Moonrise: 2 25 HST                                                              
  Moon at civil midnight: illuminated fraction 0.290                              
  Nautical 12-degr twilight: 19 05 HST --> 6 06 HST; night center: 0 36 HST       
  The sun is down for 12.4 hr; 10.2 hr from eve->morn 18 deg twilight.            
  Number of hours between Nautical twilights = 11.02 hrs                          
"""

def getAlmanac(site, date=None):

    if date:
        if site == 'MK': aMsg = "m\ny %4d %d %d a\nQ\n" % (date.year, date.month, date.day)
        else:            aMsg = "t\ny %4d %d %d a\nQ\n" % (date.year, date.month, date.day)
    else:
        if site == 'MK': aMsg = "m\nxU\nn\nT 0\na\nQ\n"
        else:            aMsg = "t\nxU\nn\nT 0\na\nQ\n"

    p = subprocess.Popen("/gemsoft/bin/skycalc", stdout = subprocess.PIPE, stdin = subprocess.PIPE)
    presponse = p.communicate(aMsg)[0]

    for l in presponse.split('\n'):
        if "Almanac for" in l:           tit = l
        if "For the night of" in l:      da1 = l
        if "Local Mean Sidereal" in l:   lst = l
        if "Sunset" in l:                sun = l
        if "Evening twilight" in l:      etw = l
        if "Morning twilight" in l:      mtw = l
        if "12-degr" in l:               twt = l
        if "Moonrise" in l:              moo = l
        if "Moonset" in l:               moo = l
        if "fraction" in l:              fra = l
        if "sun is down" in l:           dow = l

    m = re.match(".*twilight.* (\d+) (\d+).*--.*(\d+) (\d+).*night center", twt)

    if m == None:
        avl = "Number of hours between Nautical twilights unknown"
    else:
        h1 = 24 - int(m.group(1)) + int(m.group(3)) - 1
        h2 = 60 - int(m.group(2)) + int(m.group(4))
        dt = h1 + h2 / 60.0 
        avl = "Number of hours between Nautical twilights = %.2f hrs" % dt

    return "\n  ".join([tit, da1, lst, sun, moo, fra, "Nautical " + twt, dow, avl])

d = datetime.date(2013, 2, 21)

if __name__=='__main__':

    import re

    def getActual(line):
        m = re.search('Nautical twilights.* (\d+.\d+) hrs', line)
        print line
        print "Time between twilights", m.group(1)
        return float(m.group(1))
        
    getActual(getAlmanac("MK"))
    getActual(getAlmanac("CP"))
    getActual(getAlmanac("MK", d))
    getActual(getAlmanac("CP", d))
