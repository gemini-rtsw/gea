#!/usr/bin/env python

"""
Now that only using > python 2.2, might be worth while rewriting the Time class (and simplifying it!)
and using python's date utils... it nicely handles timezones.
"""

import sys
from time import gmtime, localtime, mktime, strftime, strptime, time
from calendar import timegm #inverse of gmtime
from GEAException import NotImplemented 
import GEAVars
import datetime
import pytz

class Time(object):
    """Wrapper class for handling time. 
    Uses properties extensivelly. 
    
    Arguments:
        secs - Time in seconds since the last epoch.
    NOTE:
    """
    secPerMinute = 60
    secPerHour   = 3600
    secPerDay    = 86400
    secPerWeek   = 604800
    secPerMonth  = 2678400 #secPerDay*31
    secPerYear   = 977616000 #secPerDay*365

    month2Num={"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}; 

    num2Month={1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"};
            
    def __init__(self, seconds=None, site=GEAVars.site, option='', fromAttr=None, attrVal=None, useOS='Auto' ): 
        """
        Arguments:
        secs - Seconds since the last epoch.
        
        useOS - If True,  use localtime/mktime, if false use offsets based on which site we are at. When useOS is set to True,:
        the offset (stored in self._offset) is not used, and the localtime is obtained from the operiating system's time settings.
        option - Create 'special' times.
        """
        #Want to do it this way for the first time (instead of self.site=site) so that we can
        #specifically tell self._setSite not to attempt to update useOS - since it hasnt been defined yet.
        self._setSite(site, updateUseOS=False)   
        self.useOS=useOS
        
        if fromAttr is not None:
            #This allows for something like:
            # a=Time(fromAttr='string4a', attrVal='2004_11_04-12:00:01')
            #instead of a=Time();a.string4a='2004_11_04-12:00:01')
            #When attrVal is of wrong format, an excpetion will be raised.
            self.__setattr__(fromAttr,attrVal)
        elif seconds is None:
            self.seconds=time()
        else:
            self.seconds=seconds
            
        if option:
            self.__getattribute__('_option_'+option)()
                    
    def strftime(self, format):
        return strftime(format, self.sec2struct(self.seconds))
              
    def strptime(self, value, format):
        import time, datetime
        self.seconds = time.mktime(datetime.datetime.strptime(value, format).timetuple())

    def _modifyStruct(self, attrIndex, value):
        """Helper method.
        """
        s=list(self.struct)
        s[attrIndex]=value
        self.struct=s
    
    def _lambdaRaiser(self, exception):
        """Helper method.
        """
        raise exception

    def __str__(self):
        """Default string format is string1
        """
        return self.string1
        
    def _sec2structUsingOffset(self, seconds):
        return gmtime(seconds - self._offset)
        
    def _struct2secUsingOffset(self, struct):
        return self._offset + timegm(struct)
      
    def _setUseOS(self, value):
        if str(value)=='Auto':
            if self.site==GEAVars.site:  
                value=True
            else:
                value=False
        if value is True:
            self._useOS=True
            #Use the OS facilities.. here we depend on the site
            if self.site is None:
                self.struct2sec=timegm
                self.sec2struct=gmtime
            else:
                self.struct2sec=mktime
                self.sec2struct=localtime
        else:
            self._useOS=False
            #Now using the _offset:
            self.struct2sec=self._struct2secUsingOffset
            self.sec2struct=self._sec2structUsingOffset
            
    useOS=property(lambda self: getattr(self, '_useOS'), _setUseOS)
            
    def _setSite(self, site, updateUseOS=True):
        self._site=site

        self._offset = 0
        
        #Want to call useOS since  self.struct2sec and self.sec2struct are setup in there and they depend on what site is.
        if updateUseOS:
            self._setUseOS(self.useOS)

    site=property(lambda self: getattr(self, '_site'), _setSite) 
        
    seconds=property(lambda self: getattr(self, '_seconds'), 
                     lambda self, value: setattr(self, '_seconds', value))    
    
    struct=property(lambda self: getattr(self, 'sec2struct')(self.seconds), 
                    lambda self, value: setattr(self, 'seconds', self.struct2sec(value)))
                
    year=property(lambda self: getattr(self, 'struct').tm_year, 
                  lambda self, value: getattr(self, '_modifyStruct')(0, int(value)))
    
    yearStr=property(lambda self: getattr(self, 'strftime')('%Y'), 
                     lambda self, value: getattr(self, '_modifyStruct')(0, int(value)))
        
    month=property(lambda self: getattr(self, 'struct').tm_mon, 
                  lambda self, value: getattr(self, '_modifyStruct')(1, int(value)))

    monthStr=property(lambda self: getattr(self, 'strftime')('%m'), 
                     lambda self, value: getattr(self, '_modifyStruct')(1, int(value)))
    
    # Note that using this:
    # lambda self, value: getattr(self, 'strptime')(value, '%b')) 
    # would show undesired results, as it the other date components (year, day, min, etc)
    # would be automatically assigned.
    monthWord=property(lambda self: getattr(self, 'strftime')('%b'), 
                     lambda self, value: getattr(self, '_modifyStruct')(1, int(Time.month2Num[value])))
    
    # This is identical to monthWord. Having this alias, allows for treating monthWord
    # as all the other properties (for example in fromTimeDict(), toTimeDict(), etc...).
    monthWordStr=monthWord
    
    day=property(lambda self: getattr(self, 'struct').tm_mday, 
                  lambda self, value: getattr(self, '_modifyStruct')(2, int(value)))
    
    dayStr=property(lambda self: getattr(self, 'strftime')('%d'), 
                     lambda self, value: getattr(self, '_modifyStruct')(2, int(value)))
                     
    hour=property(lambda self: getattr(self, 'struct').tm_hour, 
                  lambda self, value: getattr(self, '_modifyStruct')(3, int(value)))
    
    hourStr=property(lambda self: getattr(self, 'strftime')('%H'), 
                     lambda self, value: getattr(self, '_modifyStruct')(3, int(value)))
                     
    minute=property(lambda self: getattr(self, 'struct').tm_min, 
                  lambda self, value: getattr(self, '_modifyStruct')(4, int(value)))
    
    minuteStr=property(lambda self: getattr(self, 'strftime')('%M'), 
                       lambda self, value: getattr(self, '_modifyStruct')(4, int(value)))
                     
    second=property(lambda self: getattr(self, 'struct').tm_sec, 
                  lambda self, value: getattr(self, '_modifyStruct')(5, int(value)))
    
    secondStr=property(lambda self: getattr(self, 'strftime')('%S'), 
                     lambda self, value: getattr(self, '_modifyStruct')(5, int(value)))
        
    weekday=property(lambda self: getattr(self, 'strftime')('%a'), 
                     lambda self, value: getattr(self, '_lambdaRaiser')(NotImplemented('setting weekday\n')))
                     
    string1=property(lambda self: getattr(self, 'strftime')('%Y/%m/%d %H:%M:%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%Y/%m/%d %H:%M:%S')) 
        
    string2=property(lambda self: getattr(self, 'strftime')('%Y-%m-%d_%H-%M-%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%Y-%m-%d_%H-%M-%S')) 
        
    string3=property(lambda self: getattr(self, 'strftime')('%H:%M:%S_%Y/%m/%d HST'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%H:%M:%S_%Y/%m/%d HST')) 
                
    string4=property(lambda self: getattr(self, 'strftime')('%Y_%m_%d'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%Y_%m_%d')) 
       
    string4a=property(lambda self: getattr(self, 'strftime')('%Y_%m_%d-%H:%M:%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%Y_%m_%d-%H:%M:%S')) 
       
    string5=property(lambda self: getattr(self, 'strftime')('%a, %b %d, %Y %H:%M:%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%a, %d %m,%Y %H:%M:%S')) 
       
    #Used with Remedy data
    string6=property(lambda self: getattr(self, 'strftime')("%a %b %d %H:%M:%S %Y"), 
                     lambda self, value: getattr(self, 'strptime')(value, "%a %b %d %H:%M:%S %Y")) 
       
    #Used with Remedy data
    string7=property(lambda self: getattr(self, 'strftime')("%a %b%d, %Y"), 
                     lambda self, value: getattr(self, 'strptime')(value, "%a %b%d, %Y")) 
                     
    string8=property(lambda self: getattr(self, 'strftime')('%a, %b %d, %Y'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%a, %b %d, %Y')) 
                     
    string9=property(lambda self: getattr(self, 'strftime')('%b %d'), 
                     lambda self, value: getattr(self, '_lambdaRaiser')(NotImplemented('setting string9\n')))
                        
    string10=property(lambda self: getattr(self, 'strftime')("%H:%M:%S\n%d %b %Y"), 
                     lambda self, value: getattr(self, 'strptime')(value, "%H:%M:%S\n%d %b %Y")) 
                    
    string11=property(lambda self: getattr(self, 'strftime')("%m/%d/%y %H:%M:%S"), 
                     lambda self, value: getattr(self, 'strptime')(value, "%m/%d/%y %H:%M:%S")) 

    string12=property(lambda self: getattr(self, 'strftime')("%Y%m%d"), 	# Used for cal data YYYMMDD path.
                     lambda self, value: getattr(self, 'strptime')(value, "%Y%m%d")) 
                     
    #tmt data obsolete? make it go away???
    #2005 09 20 13:57:42                     
    string13=property(lambda self: getattr(self, 'strftime')('%Y %m %d %H:%M:%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%Y %m %d %H:%M:%S')) 
    
    string14=property(lambda self: getattr(self, 'strftime')('%Y%m%d%H%M%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%Y%m%d%H%M%S'))   
    
    string15=property(lambda self: getattr(self, 'strftime')('%m/%d% H:%M:%S'), 
                     lambda self, value: getattr(self, 'strptime')(value, '%m/%d% H:%M:%S'))     
    
    string16=property(lambda self: getattr(self, 'strftime')("%m/%d/%Y %H:%M:%S"), 
                     lambda self, value: getattr(self, 'strptime')(value, "%m/%d/%y %H:%M:%S")) 

    string17=property(lambda self: getattr(self, 'strftime')("%Y/%m%d"),
                     lambda self, value: getattr(self, 'strptime')(value, "%Y/%m%d")) 
                     
 
    def __eq__(self, x):
        """Allows comparisons of the form:
        a==b
        given that a and b are both instances of Time.
        """
        if x == None: return 0
        return self.seconds == x.seconds
        
    def __lt__(self, x):
        return self.seconds<x.seconds
        
    def __gt__(self, x):
        return self.seconds>x.seconds
    
    def __cmp__(self, x):
        return __cmp__(self.seconds, x.seconds)
        
    def option(self, option):
        self.__getattribute__('_option_'+option)()
        
    def _option_weekStart(self):
        """
        Define the start of the week as Friday 7:30am
        """
        self.seconds-=Time.secPerDay * (int(self.strftime("%w")) + 2)
        self._option_0730()

    def _option_twoweekStart(self):
        """
        Define the start of the week as Friday 7:30am
        """
        self.seconds -= (Time.secPerDay * (int(self.strftime("%w")) + 2) + Time.secPerWeek)
        self._option_0730()

    def _option_0730(self):
 
        self.hour=7
        self.minute=30
        self.second=0
        
    def _option_1200(self):
        
        self.hour=12
        self.minute=0
        self.second=0
        
    def _option_rollover0730(self):
        """
        Go back 24 hours.
        If monday, go back to friday. 
        Go to 7:30am.
        """
        if self.weekday=='Mon':
            offset=Time.secPerDay * 3
        else:
            offset=Time.secPerDay
            
        self.seconds -= offset
        self._option_0730()
        
    def _option_yesterday(self):
        """
        Go back 24 hours.
        """
        self.seconds-=Time.secPerDay
    
    def _option_tomorrow(self):
        """
        Go forward 24 hours.
        """
        self.seconds+=Time.secPerDay
        
    def _option_yesterday0730(self):
        """
        Go back 24 hours.
        Go to 7:30am.
        """
        self.seconds-=Time.secPerDay
        self._option_0730()
        
    def _option_yesterday1200(self):
        """
        Go back 24 hours.
        Go to noon.
        """
        self.seconds-=Time.secPerDay
        self._option_1200()
     
    def toTimeDict(self, allCaps=False, keyPrefix='', useStr=True, monthAsWord=False):
        """Return a dictionary with time data.
        
        Arguments:
        monthAsWord - If true, handle month as a word (ex. Jan, Feb, Mar, etc...). Otherwise treat as all the others.
        """
        d={}
        
        for item in ['year', 'day', 'hour', 'minute', 'second']:
            
            key=keyPrefix+item
            if allCaps:
                key=key.upper()
                
            if useStr:
                item+='Str'
                
            d[key]=self.__getattribute__(item)
            
        #Have to handle 'month' seperately, since it could be number (ex. 12) or a word (ex. Dec).
        item='month'
        key=keyPrefix+item
        if allCaps:
            key=key.upper()
        
        if monthAsWord:
            item+='Word'

        if useStr:
            item+='Str'

        d[key]=self.__getattribute__(item)
        
        return d
        
    def fromTimeDict(self, timeDict, allCaps=False, keyPrefix='', useStr=True,  monthAsWord="Auto"):
        """Build the object from a dictionary.
        
        Arguments:
        monthAsWord - If true, handle month as a word (ex. Jan, Feb, Mar, etc...). If false, treat as a all the others (ex. 01, 02, etc)
        Finally, when monthAsWord is "Auto", automatically decide what we are dealing with (len > 2 implies it's a word).
        
        """
        #Have to handle 'month' separately, since it could be number (ex. 12) or a word (ex. Dec).
        #It *needs* to be processed BEFORE the day; otherwise month is undefined when processing day, 
        #and the default may not have the correct number of days (therefore day 31 may not exist)
        item='month'
        key=keyPrefix+item
        if allCaps:
            key=key.upper()
        try:
            value=timeDict[key]
        except KeyError:
            raise KeyError("'%s' missing when setting up time.\n" % key)    
        
        # God this is messy. Value could be an int, a string with '01' or 'Jan'
        # monthAsWord could be, 'Auto', True, or False

        if monthAsWord == "Auto":
            if type(value) == int:
                month = value
            elif len(value) > 2:	# E.g., 'Jan'
                month = Time.month2Num[value]
            else:		# E.g., '01'
                month = int(value)
        elif monthAsWord is True:
            month = Time.month2Num[value]
        else:
            month = value

        dateList=[]
        for item in [ 'year','day', 'hour', 'minute', 'second']:

            key = keyPrefix + item
            if allCaps:
                key = key.upper()
        
            dateList.append(timeDict[key])

        dateList.insert(1, month)
        
        date="%s/%s/%s %s:%s:%s" % (tuple(dateList))
  
        self.strptime(date, '%Y/%m/%d %H:%M:%S')

        return self         #So can do stuff like t=Time().fromStartTimeDict(timeDict)
    
    def toStartTimeDict(self, allCaps=False, monthAsWord=False):
        return self.toTimeDict(allCaps=allCaps, keyPrefix='start', monthAsWord=monthAsWord)
    
    def toEndTimeDict(self, allCaps=False, monthAsWord=False):
        return self.toTimeDict(allCaps=allCaps, keyPrefix='end', monthAsWord=monthAsWord)
    
    def fromStartTimeDict(self, timeDict, allCaps=True, monthAsWord="Auto"):
        return self.fromTimeDict(timeDict=timeDict, keyPrefix='start', allCaps=allCaps, monthAsWord=monthAsWord)
                
    def fromEndTimeDict(self, timeDict, allCaps=True,  monthAsWord="Auto"):
        return self.fromTimeDict(timeDict=timeDict, keyPrefix='end', allCaps=allCaps, monthAsWord=monthAsWord)


    # Convert to python datetime
    def toDatetime(self):
        #print "toDatetime", datetime.datetime.utcfromtimestamp(self.seconds).strftime('%Y-%m-%d %H:%M:%S %Z (%z)')
        return datetime.datetime.utcfromtimestamp(self.seconds)

    # Convert to localized datetime with timezone.
    def toLocaldatetime(self):
        mz = pytz.timezone("US/Hawaii" if self.site == "MK" else "Chile/Continental")
        dt = datetime.datetime.utcfromtimestamp(self.seconds)
        #print "toLocaldatetime", (mz.localize(dt) + mz.utcoffset(dt)).strftime('%Y-%m-%d %H:%M:%S %Z (%z)')
        return mz.localize(dt) + mz.utcoffset(dt)


    # Convert to naive datetime but localzone adjusted.
    def toNaivedatetime(self):
        mz = pytz.timezone("US/Hawaii" if self.site == "MK" else "Chile/Continental")
        dt = datetime.datetime.utcfromtimestamp(self.seconds)
        #print "toNaivedatetime", (dt + mz.utcoffset(dt)).strftime('%Y-%m-%d %H:%M:%S %Z (%z)')
        return dt + mz.utcoffset(dt)
           
    # Helper methods:
    def startEndTime2Dict(startTime, endTime, allCaps=False, monthAsWord=False):
        """Helper static method.. 
        """
        d=startTime.toStartTimeDict(allCaps=allCaps, monthAsWord=monthAsWord)
        d.update(endTime.toEndTimeDict(allCaps=allCaps, monthAsWord=monthAsWord))
        return d
        
    startEndTime2Dict=staticmethod(startEndTime2Dict)    
    
    def timeRange2Str(startTime, endTime, attr=None, format=None):
        """Takes a start and end times, and formats a string based on the difference between the two.
        """
        delta=60
        diff=endTime.seconds-startTime.seconds
        #Check if the ending time is about now?
        now=Time()
        if now.seconds-delta<endTime.seconds<now.seconds+delta:
            if Time.secPerHour-delta<diff<Time.secPerHour+delta:
                return 'the last hour'
            elif Time.secPerDay-delta<diff<Time.secPerDay+delta:
                return 'the last 24 hours'     
            elif Time.secPerWeek-delta<diff<Time.secPerWeek+delta:
                return 'the last 7 days'     
            elif Time.secPerMonth-delta<diff<Time.secPerMonth+delta:
                return 'the last month'   
        if attr is not None:
            if startTime.site is not None:
                return '%s - %s local <strong>%s</strong> time' % (startTime.__getattribute__(attr), endTime.__getattribute__(attr), startTime.site) 
            else:
                return '%s - %s' % (startTime.__getattribute__(attr), endTime.__getattribute__(attr))
        elif format is None:  #Check if we were give a format to use.
            #Figure out a nice time stamps depending on the time range.
            if diff>Time.secPerDay*7+delta:
                format='%b%d,%Y'
            elif diff>Time.secPerDay+delta:
                format='%H:%M, %b%d,%Y'
            elif diff>Time.secPerMinute*5:
                format='%H:%M, %b%d'
            else:
                format='%H:%M:%S, %b%d'
        
        if startTime.site is not None:
            return '%s - %s local <strong>%s</strong> time' % (startTime.strftime(format), endTime.strftime(format), startTime.site) 
        else:
            return '%s - %s' % (startTime.strftime(format), endTime.strftime(format))

    timeRange2Str=staticmethod(timeRange2Str)    
    

if __name__=='__main__':
   
    t=Time()
    print t.string5
    print t.site
    t=Time(site='MK')
    print t.string5
    print t.site
    t=Time(site='CP')
    print t.string5
    print t.site
    t=Time(site=None)
    print t.string5
    print t.site
    
    t=Time()
    print t.string5
    t=Time(seconds=time()-Time.secPerDay*3, site='MK', option='rollover0730')
    print t.string5

    t.site='CP'
    print t.string5
    
    t=Time(option='weekStart')
    print t.string5
    print '---'
   
    print t.weekday
    print "string1:", t.string1
    print "string2:", t.string2
    print "string3:", t.string3
    print "string4:", t.string4
    print "string5:", t.string5
    print "string6:", t.string6
    print "string7:", t.string7

    print "string10:", t.string10
    print "string11:", t.string11
    print "string12:", t.string12
    print "string13:", t.string13
    print "string14:", t.string14
            

    print "weekday:", t.weekday
    
    print "strftime:", t.strftime("%a %a %a %H:%M:%S %Y")
    
    t.strptime('Thu Aug 22 08:12:12 2004', "%a %b %d %H:%M:%S %Y")
    
    print "strftime:", t.strftime("%a %b %d %H:%M:%S %Y")  
    
    print
    t=Time()
    print str(t)
    #t.seconds=1092110999.84
    #print str(t)
    print t.hourStr
    t.hour='011'
    print t.hourStr

    print t.toStartTimeDict(allCaps=True, monthAsWord=True)
    print t.toEndTimeDict(monthAsWord=True)
    print t.weekday
    print "string1:", t.string1

    print Time.startEndTime2Dict(t, t, allCaps=True, monthAsWord=True)
    
    print Time.timeRange2Str(t, t)
    
    tt=Time().fromStartTimeDict({'STARTYEAR': '2004', 'STARTDAY': '1', 'STARTMONTH': 'Mar', 'STARTMINUTE': '46', 'STARTSECOND': '39', 'STARTHOUR': '11'}, monthAsWord=True)
    
    print tt.string1
    
    print
    print 
    print
    print 'TESTING useOS'
    a=Time(useOS=True)

    print a.string1
    
    a.useOS=False
    print a.string1
    a.site='CP'
    print a.string1
    a.useOS=True
    print a.string1
    a.useOS=False
    print a.string1

    print "TESTING Time to datetime/timezone"
    a=Time(1543708800)		# 12/02/2018 @ 12:00am (UTC) (CLST) -3), 12/01/2018 21:00
    a.site='CP'
    print
    print a.toDatetime()	# Just converted to python dattime
    print a.toLocaldatetime()	# Converted to localized datetime with timezone.
    print a.toNaivedatetime()	# Converted to naive datetime but localzone adjusted.
    a=Time(1528588800)		# 06/10/2018 @ 12:00am (UTC) (CLT -4), 06/09/2018 20:00
    a.site='CP'
    print
    print a.toDatetime()	# Just converted to python dattime
    print a.toLocaldatetime()	# Converted to localized datetime with timezone.
    print a.toNaivedatetime()	# Converted to naive datetime but localzone adjusted.
    a=Time(1533859200)		# 08/10/2018 @ 12:00am (UTC) (HST -10), 08/09/2018 14:00
    a.site='MK'
    print
    print a.toDatetime()	# Just converted to python dattime
    print a.toLocaldatetime()	# Converted to localized datetime with timezone.
    print a.toNaivedatetime()	# Converted to naive datetime but localzone adjusted.
