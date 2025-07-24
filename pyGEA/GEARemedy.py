#!/usr/bin/python

import GEAVars
from GEAGeneral import util
from GEAException import RemedyException, NotImplemented
from GEATime import Time
from JW import GemQ  #inside packages/internal/pyRemedy
import datetime

class Remedy(object):
    """Wrapper that allows consistency when dealing with FRS and NL databases. 
    Hiddes the inconsistency between the databaes (ex. for site, time, etc..)
    """
    
    def __init__(self, server='localhost', user='gea', passwd='gea99', site=None, dBase=None):
        
        self.site = site if site else GEAVars.site
        self.dBase=dBase
        
        self.user=user
        self.passwd=passwd    
        self.server=server
    
    def query(self, query='', keys=(), startTime=None, endTime=None):

        # print "<br>QUERYA", query, startTime, endTime, self.dBase, self.site, keys, "QUERYA<br>"

        gemQ=GemQ(self.dBase, self.user, self.passwd, self.server)

        # Setup, "site" for query.

        if not query:
            if self.dBase == 'NL':
                if   self.site == 'MK': query ="('Telescope'=\"North\")"
                elif self.site == 'CP': query ="('Telescope'=\"South\")"
                else: raise RemedyException('Telescope site unrecognized, "%s".\n' % self.site)  
            elif self.dBase == 'FRS':
                if self.site != 'MK' and self.site != 'CP':
                    raise RemedyException('Telescope site unrecognized, "%s".\n' % self.site)  
                query =self.site
            else: raise RemedyException('Database %s not not known.\n' % self.dBase)
            
    
            #  General convert GEATime to iso time for Jira queries.
    
            def geatime2iso(t):
                return t.toLocaldatetime().strftime("%F+%H:%M")
    
            # Setup, startTime for query.
    
            if self.dBase == 'NL':
                if startTime: query += " AND ('UT Date' >= \"%d\")" % startTime.seconds
                if endTime:   query += " AND ('UT Date' <= \"%d\")" % endTime.seconds
            else:
                if startTime and endTime: query += '"Occurred">="%s"+AND+"Occurred"<="%s"' % (geatime2iso(startTime), geatime2iso(endTime))
    #            elif startTime:             query += '"Occurred">="%s"'                      % ts2iso(startTime.seconds)
    #            elif endTime:               query += '"Occurred"<="%s"'                      % ts2iso(endTime.seconds)
                else: raise RemedyException('No nightlog time range.\n')
    
            if self.dBase == 'NL': query = "(" + query + ")"
    
        # print "<br>QUERY QUERY", query, "QUERY QUERY<br>"
    
        self.dataList = gemQ.query(query, keys)
        # print self.dataList

        gemQ.logout()
        
        return self.dataList
        
if __name__=='__main__':
    
    endTime=Time()
    startTime=Time(endTime.seconds-Time.secPerWeek*2)
        
    if 0:
        #rQuery="('Wavelength5'>=\"0.550\") OR ('FWHM5'=\"0.8\")" 
        #rQuery="('UT Date'>=\"%d\") AND ('UT Date'<=\"%d\")" % (now.seconds-Time.secPerMonth, now.seconds-Time.secPerWeek)
        rQuery="('Site'=%d) AND ('Create Date'>=\"%d\")" % (0, startTime.seconds)
        #rKeys=('UT Date','UT Date')  #Cannot have keys with length=1
        #rKeys=('Create Date', 'Create Date')
        rKeys=('CaseID','Status','TimeLost','One line summary','Category','System','Subsystem','AssignedTo');

        r=Remedy(dBase='FRS', site='MK/CP')
        result=r.query(rQuery, rKeys)
       
    elif 0:
        #rQuery="('CaseID'=%s) OR ('CaseID'=%s)" % ('3148', '3150')
        rQuery="('CaseID'=%s)" % ('3148',)
        rKeys=('CaseID', 'Site', 'Name', 'Create Date', 'Priority', 'AssignedTo',
                       'Also Notify', 'Status', 'Category', 'System','Subsystem', 'TimeLost',                       
                       'Priority', 'One line summary', 'Detailed description', 'Work done')
       
        r=Remedy(dBase='FRS', site='MK')
        result=r.query(rQuery, rKeys)
       
    elif 0:
        #rQuery="('Wavelength5'>=\"0.550\") OR ('FWHM5'=\"0.8\")" 
        #rQuery="('UT Date'>=\"%d\") AND ('UT Date'<=\"%d\")" % (now.seconds-Time.secPerMonth, now.seconds-Time.secPerWeek)
        #rQuery="('Create Date'>=\"%d\")" % (startTime.seconds)
        #rKeys=('UT Date','UT Date')  #Cannot have keys with length=1
        #rKeys=('Create Date', 'Create Date')
  
        rQuery="'AssignedTo'=\"%s\"" % "mbec"
        rQuery+="AND 'Status'=%s" % 2
        rKeys=('CaseID','Status') #,'TimeLost','One line summary','Category','System','Subsystem','AssignedTo');

        r=Remedy(dBase='FRS', site='MK/CP')
        result=r.query(rQuery, rKeys)
    elif 0:
    
        rQuery="('CaseID'=%s)" % "3056"
        #rQuery="('Site'=23233)"
        rKeys=('Priority', 'CaseID', 'Site', 'Name', 'Create Date', )#'Priority', 'AssignedTo',)
##~                        'Also Notify', 'Status', 'Category', 'System','Subsystem', 'TimeLost',                       
##~                        'Priority', 'One line summary', 'Detailed description','Work done')
##~                        
        startTime=Time(Time().seconds-Time.secPerDay)
                       
        r=Remedy(dBase='FRS', site='MK/CP')
        result=r.query(rQuery, rKeys)
       
    elif 0:

        rQuery="('Site'=%d) AND ('Create Date'>=\"%d\")" % (0, startTime.seconds)
        rQuery=''
        rKeys=('Total hours lost faults','Total hours available' )        
        
        rKeys=('Total hours available','Total hours lost faults','Total hours lost weather','Total hours observed',
                'UT Date','Science usage', 'Engineering', 'Commissioning', 'Telescope shutdown')        
                    
        #Date   Available    Observed    Sci    Comm    Eng    Lost to Faults    Lost to Weather    Tel Shutdown                   
                    
        r=Remedy(dBase='NL', site='CP')
        
        endTime=None
        startTime=None
        
        result=r.query(rQuery, rKeys, startTime=startTime, endTime=endTime)
       
       
        hoursHeading=('Available', 'Observed', 'Sci', 'Comm','Eng', 'Lost to Faults', 'Lost to Weather', 'Tel Shutdown')
        hoursKeys=('Total hours available','Total hours observed', 'Science usage', 'Commissioning','Engineering', 'Total hours lost faults','Total hours lost weather', 'Telescope shutdown')
        
        tFmt="%-22s"
        fmt="%-18s"

        lines=[]
        for item in result:
            t=Time(item['UT Date'], site=GEAVars.site)
            lines.append((tFmt % t.string1)+''.join([fmt % item[s] for s in hoursKeys]))
            
        lines.sort()
        
        # print tFmt % 'Date'+''.join([fmt % s for s in hoursHeading])
        # print '\n'.join(lines)        
       
    else:
        rQuery="('Site'=%d) AND ('Create Date'>=\"%d\")" % (0, startTime.seconds)
        rQuery=''
        
        rKeys=('Total hours available','Total hours lost faults','Total hours lost weather','Total hours observed',
                    'Science usage', 'Engineering', 'Commissioning')     
        rKeys=() 
                    
        r=Remedy(dBase='NL', site='MK')
        
        result=r.query(rQuery, rKeys, startTime=startTime, endTime=endTime)

        # for key, val in result[0].items():
        #     print key, val

    #for item in result:
    #    print util.dictStr(item)
    
    #Want to see the keys.
    #keys=result[0].keys()
    #keys.sort()
    #print '\n'.join(keys)
