#!/usr/bin/python

import GEAVars
from GEAGeneral import util
from GEAException import RemedyException, NotImplemented
from GEATime import Time
from remedyWrapper import GemQ  #inside packages/internal/pyRemedy

class Remedy(object):
    """Wrapper that allows consistency when dealing with FRS and NL databases. 
    Hiddes the inconsistency between the databaes (ex. for site, time, etc..)
    """
    
    def __init__(self, server='10.1.5.80', user='gea' ,passwd='gea99', site=None, dBase=None):
        #10.1.5.11 - galah
        #10.1.5.80 - ehu
        
        self._setupDBase(dBase)
        self._setupSite(site)
        
        self.user=user
        self.passwd=passwd    
        self.server=server
    
    def _setupDBase(self, dBase):
    
        self.dBase=dBase
    
        if self.dBase=='NL':
            self._timeKey='UT Date'
        elif self.dBase=='FRS':
            self._timeKey='Create Date'
        elif self.dBase=='fFRS':
            self._timeKey='otime'
        else:
            raise RemedyException('Database %s not not known.\n' % self.dBase)

    def _setupSite(self, site):
        """self.site should either be MK, CP or MK/CP.
        Should be called after self._setupDBase()
        """
        self.siteQueryStr=''
        
        if self.dBase=='NL':
            
            if site=='MK':
                tmpSite="North"
            elif site=='CP':
                tmpSite="South"
            elif site=='MK/CP':
                tmpSite=''
            else:
                tmpSite=''   #For now if no site given, assume mean both MK and CP
                #raise RemedyException('Telescope site unrecognized.\n')   
           
            self.site=site
            
            if tmpSite!='':
                self.siteQueryStr="('Telescope'=\"%s\")" % (tmpSite,)
        
        elif self.dBase=='FRS':
        
            if site=='MK':
                tmpSite=0
            elif site=='CP':
                tmpSite=1
            elif site=='MK/CP':
                tmpSite=''
            else:
                tmpSite=''   #For now if no site given, assume mean both MK and CP
                #raise RemedyException('Telescope site unrecognized.\n')  
                
            self.site=site
            
            if tmpSite!='':
                self.siteQueryStr="('Site'=%d)" % (tmpSite,)
        
        elif self.dBase=='fFRS':
            tmpSite = ''

        else:
            raise RemedyException('Database %s not not known.\n' % self.dBase)
    
    def _addTimeQuery(self, query, startTime, endTime):
        """Times are assumed to be universal (ie. UT).
        """
        #Nothing to do.
        if startTime is None and endTime is None:
            return query
            
        def updateQ(q, timeQ):
            if q=='':
                q=timeQ
            else:
                q="(%s) AND (%s)" % (q, timeQ)
            return q
           
        if startTime is not None and  \
           endTime is not None and   \
           startTime.seconds == endTime.seconds:
                timeQuery="'%s'=\"%d\"" % (self._timeKey, startTime.seconds)
                query=updateQ(query, timeQuery)
        
        else:    
            if startTime is not None:
                timeQuery="'%s'>=\"%d\"" % (self._timeKey, startTime.seconds)
                query=updateQ(query, timeQuery)
                
            if endTime is not None:
                timeQuery="'%s'<=\"%d\"" % (self._timeKey, endTime.seconds)
                query=updateQ(query, timeQuery)
            
        return query
        
    def _addSiteQuery(self, query):
    
        if self.siteQueryStr:
            if query=='':
                query=self.siteQueryStr
            else:
                query="(%s) AND (%s)" % (query, self.siteQueryStr)
        
        return query
    
    def query(self, query='', keys=(), startTime=None, endTime=None):

        query=self._addTimeQuery(query, startTime, endTime)
        query=self._addSiteQuery(query)
                
        # print "QUERY: ", query
        # import datetime
        # print "starTime: ",   datetime.datetime.utcfromtimestamp(startTime.seconds)
        # print "endTime: ",   datetime.datetime.utcfromtimestamp(endTime.seconds)

        #For now creating a GemQ object with each query.. should modify GemQ and change how loging in/out is done.
        gemQ=GemQ(self.dBase, self.user, self.passwd, self.server)
         
        #TESTING
        #print util.dictStr(gemQ.fieldId)
               
        self.dataList=gemQ.query(query, keys)
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
        rKeys=('CaseID','Status','TimeLost','One line summary','Components','Labels','AssignedTo');

        r=Remedy(dBase='FRS', site='MK/CP')
        result=r.query(rQuery, rKeys)
       
    elif 0:
        #rQuery="('CaseID'=%s) OR ('CaseID'=%s)" % ('3148', '3150')
        rQuery="('CaseID'=%s)" % ('3148',)
        rKeys=('CaseID', 'Site', 'Name', 'Create Date', 'Priority', 'AssignedTo',
                       'Also Notify', 'Status', 'Components', 'Labels','TimeLost',                       
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
        rKeys=('CaseID','Status') #,'TimeLost','One line summary','Components','Labels','AssignedTo');

        r=Remedy(dBase='FRS', site='MK/CP')
        result=r.query(rQuery, rKeys)
    elif 0:
    
        rQuery="('CaseID'=%s)" % "3056"
        #rQuery="('Site'=23233)"
        rKeys=('Priority', 'CaseID', 'Site', 'Name', 'Create Date', )#'Priority', 'AssignedTo',)
##~                        'Also Notify', 'Status', 'Components', 'Labels','TimeLost',                       
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
        
        print tFmt % 'Date'+''.join([fmt % s for s in hoursHeading])
        print '\n'.join(lines)        
       
    else:
        rQuery="('Site'=%d) AND ('Create Date'>=\"%d\")" % (0, startTime.seconds)
        rQuery=''
        
        rKeys=('Total hours available','Total hours lost faults','Total hours lost weather','Total hours observed',
                    'Science usage', 'Engineering', 'Commissioning')     
        rKeys=() 
                    
        r=Remedy(dBase='NL', site='MK')
        
        result=r.query(rQuery, rKeys, startTime=startTime, endTime=endTime)
        for key, val in result[0].items():
            print key, val

    #for item in result:
    #    print util.dictStr(item)
    
    #Want to see the keys.
    #keys=result[0].keys()
    #keys.sort()
    #print '\n'.join(keys)
