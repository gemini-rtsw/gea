#!/usr/bin/env python

"""
Needs documenting.
"""
import os
import sys
import copy
from GEAGeneral import *
from GEAException import RequestException
import GEATime
import GEAVars

from cgi import parse_qs, FieldStorage   
#from mod_python import util

#Used to determine how the QUERY_STRING data is parsed
gUseForms=0
 
class Request(dict):
    
    def __init__(self, request=None, nameTag=None, fStream=GEAVars.errStream):
        """
        """
        self.fStream=fStream
        
        if GEAVars.environ.get('REQUEST_METHOD','')=='POST':
            GEAVars.environ['QUERY_STRING']='%s&%s' % (GEAVars.environ.get('QUERY_STRING',''),sys.stdin.read())
                
        #If request has not been provided, parse the QUERY_STRING. 
        #NOTE: It is important to check that 'request' matches None and not just whehter it is True/False, because could have a 
        #case where the user does pass a request dictionary but it is empty; and we do not want to parse QUERY_STRING then.
        if request is None:   
        
            self.request={}
            #Two different ways to parse data. 
            if gUseForms:
                
                #NOTE: check cgi api if this can be done automatically.. with no loops.. 
                tempFS=FieldStorage()
                for key in tempFS.keys():
                    try:                    #tempFS[key] could be a list if had multiple value keys in the QUERY_STRING.
                        self.request[key]=tempFS[key].value
                    except AttributeError:
                        valList=[item.value for item in tempFS[key]]
                        #There is no guarantee of the order in the list.  By sorting, we make sure that the same requests end up being 
                        #processed in the same way. This is useful when for example generating colors for the different channels 
                        #in a plot. By having the same order, the colors are always the same (between requests) for the same data set.
                        valList.sort()          
                        self.request[key]=GEAVars.queryStrSep.join(valList)
            else:
                if GEAVars.environ.has_key('QUERY_STRING') and GEAVars.environ['QUERY_STRING']:
                    for key, val in parse_qs(GEAVars.environ['QUERY_STRING']).iteritems():
                        #There is no guarantee of the order in the list.  By sorting, we make sure that the same requests end up being 
                        #processed in the same way. This is useful when for example generating colors for the different channels 
                        #in a plot. By having the same order, the colors are always the same (between requests) for the same data set.
                        val.sort()          
                        self.request[key]=GEAVars.queryStrSep.join(val)
        else:
            self.request=request
        
        #if self.request=={}:
        #    raise RequestException() #Nothing to do.

        self.nameTag=nameTag 
        
        self.update(self.request)
                                
    def __str__(self):

        keys=self.keys()
        keys.sort()
        
        strRep=[]

        for key in keys:
            strRep+=[str(key),":",str(self[key]),"\n"]
        return ''.join(strRep)
        
    def __repr__(self):
        return "<type 'Request'>"
        
    def __deepcopy__(self, memo):
        """Cannot copy stream objects such as sys.stdout, sys.stderr etc.. so copy all that can be copied.
        """
        obj=dict.__new__(self.__class__, None)
        memo[id(self)]=obj

        for k, v in self.__dict__.iteritems():
            try:
                obj.__dict__[k]=copy.deepcopy(v, memo)
            except TypeError, e:
                if str(k)=='fStream':
                    obj.__dict__[k]=v
                else:
                    raise
                
        for k, v in self.iteritems():
            obj[k]=copy.deepcopy(v, memo)

        return obj
        
class RequestCollection(dict):
    """
    """
    def __init__(self, reqColDict=None, fStream=GEAVars.errStream):
        """
        
        Arguments:
        reqColDict - This is an optional dicionary which if given is used to create
            a RequestCollection type object. The key/value pairs should be of the type:
            <string object>/<Request object>
            where the key is equal to the nameTag in the Request - which is the value.            
        """
        self.fStream=fStream
        
        if not reqColDict is None:
            self.update(copy.deepcopy(reqColDict))
            return 
    
        self.request=Request()   #Parsed CGI key/value pairs.
        
        #Working objects
        tempStorage={}
        generalDict={}      #key/value pairs stored in here will go into all the Requests.
        
        #Two different ways to parse data.
        if gUseForms:
            tempFS=FieldStorage()
            for key in tempFS.keys():
                try:                    #tempFS[key] could be a list if had multiple value keys in the QUERY_STRING.
                    self.request[key]=tempFS[key].value
                except AttributeError:
                    valList=[item.value for item in tempFS[key]]
                    #There is no guarantee of the order in the list.  By sorting, we make sure that the same requests end up being 
                    #processed in the same way. This is useful when for example generating colors for the different channels 
                    #in a plot. By having the same order, the colors are always the same (between requests) for the same data set.
                    valList.sort()          
                    self.request[key]=GEAVars.queryStrSep.join(valList)
                    
        else:
            if GEAVars.environ.has_key('QUERY_STRING') and GEAVars.environ['QUERY_STRING'] != '':      
                for key, val in parse_qs(GEAVars.environ['QUERY_STRING']).iteritems():
                    #There is no guarantee of the order in the list.  By sorting, we make sure that the same requests end up being 
                    #processed in the same way. This is useful when for example generating colors for the different channels 
                    #in a plot. By having the same order, the colors are always the same (between requests) for the same data set.
                    val.sort()          
                    self.request[key]=GEAVars.queryStrSep.join(val)
        
        if len(self.request)==0:
            return
            #raise RequestException('No request to process.') #Nothing to do.
        
        #Create a dictionary where each key is a keyword 'n' (from description above) and the value is another dicionary which contains all the parsed items for that particular keyword.
        for key in self.request.keys():
            try:
                (queryKey, dictKey)=key.split('_')
                
            except ValueError:    #key.split('_') returns one value, not two; this is one of the 'general' key/value pairs which should be added to all the Requests.
                generalDict[key]=self.request[key]
                        
            else:   #No exceptions generated.
                try:
                    tempStorage[dictKey][queryKey]=self.request[key]
                except KeyError:            #Exception if first entry.
                    tempStorage[dictKey]={queryKey:self.request[key]}
            
        if tempStorage=={}:
            #Could have a special case, where the tempStorage is empty; in other words have no tagged keys in QUERY_STRING.
            self[None]=Request(generalDict, nameTag=None) 
        else:
        
            #Now include the key/value pairs which should be present in all the Requests.
            for key, val in generalDict.items():
            
                for d in tempStorage.values():      #d here is itself a dicionary which contains key/value pairs for a singe Request.
                    if not d.has_key(key):      #Only update d if this particular key/value pair is not already there.
                        d[key]=val
                        
            #For each object in tempStorage create a Request.
            for key in tempStorage.keys():
                #printError("Creating a new Request.\n")    #Testing
                self[key]=Request(tempStorage[key], nameTag=key)
                
    def isEmpty(self):
        return len(self)==0

    def __deepcopy__(self, memo):
        """Cannot copy stream objects such as sys.stdout, sys.stderr etc.. so copy all that can be copied.
        """
        obj=dict.__new__(self.__class__, None)
        memo[id(self)]=obj

        for k, v in self.__dict__.iteritems():
            try:
                obj.__dict__[k]=copy.deepcopy(v, memo)
            except TypeError:
                if str(k)=='fStream':
                    obj.__dict__[k]=v
                else:
                    raise
            
        for k, v in self.iteritems():
            obj[k]=copy.deepcopy(v, memo)

        return obj
            
    def __str__(self):
    
        strList=[]
        for key, val in self.iteritems():
            strList+=['---', str(key),'---\nTag: ',str(val.nameTag),'\n', str(val), '\n']
        
        return ''.join(strList)
            
    def __repr__(self):
        return "<type 'RequestCollection'>"
        
                    
class RequestProcessor(object):
    """Helper class to update/combine some of the key/values in a request. 
    """
    def process(request):
        """Updates the request based on values of some of the keys. 
        This function modifies the request provided, so if one does not want to change the 
        original, a copy should be used.
        
        PREFIX,SUFFIX - Update CHANNELS, PATTERN
        
        LAPSE - Updates all the time keys (START|END)SECOND, (START|END)MINUTE, etc...
        
        PLOTMETHOD - Updates LINESTYLE
        """
        request=dict(request)
        
        prefix=request.get('PREFIX', '')
        suffix=request.get('SUFFIX', '')
        if prefix or suffix:
        
            #Update CHANNELS and PATTERN if non empty
            pattern=request.get('PATTERN')
            if pattern:
                request['PATTERN']="%s%s%s" % (prefix, pattern, suffix)
            
            channels=request.get('CHANNELS')
            if channels:
                request['CHANNELS']=' '.join(["%s%s%s" % (prefix, item, suffix) for item in channels.split()])
                
        legend=request.get('LEGEND')
        if legend:
            legend=legend.lower()
            if legend=='on' or legend=='checked' or legend=='true':
                request['LEGEND']='Inside'
                
        lapse=request.get('LAPSE')
        if lapse:
            if lapse=='lastNight':
                startTime=Time()
                if startTime.hour<18:
                    startTime.seconds-=Time.secPerDay
                startTime.hour, startTime.minute, startTime.second=18, 0, 0
                endTime=Time(startTime.seconds+12*Time.secPerHour)
            elif lapse=='lastWeek':
                endTime=Time()
                startTime=Time(endTime.seconds-Time.secPerWeek)
            elif lapse=='lastMonth':
                endTime=Time()
                startTime=Time(endTime.seconds-Time.secPerMonth)
            else:
                #print lapse
                endTime=Time()
                startTime=Time(endTime.seconds-float(lapse)*60)
        
            request.update(startTime.toStartTimeDict(allCaps=True, monthAsWord=True))
            request.update(endTime.toEndTimeDict(allCaps=True, monthAsWord=True))
                     
        #Leaving this for compatibility with older requests/bookmars... 
        #Now LINESTYLE is directly supported... 
        plotMethod=request.get('PLOTMETHOD')
        if plotMethod:
            if not request.get('LINESTYLE'):
                #Only update if LINESTYLE is not defined...
                if plotMethod=='NonStepped':
                    request['LINESTYLE']='-'
                elif plotMethod=='Stepped':
                    request['LINESTYLE']='steps-post'
                else:
                    pass    #Defaults from GEAVars will be used.

        #Return the modified request... for convinence..
        return request
                    
    process=staticmethod(process)
                    
if __name__=='__main__':
    
    import sys
    
    GEAVars.environ['QUERY_STRING']='PREFIX=pre&SUFFIX=suff&PATTERN=pat1&CHANNELS=chan1 chan2&LAPSE=180'
    r=Request()
    print r
    
    
    GEAVars.environ['QUERY_STRING']='PREFIX_tag1=pre&SUFFIX_tag1=suff&PATTERN_tag1=pat1&CHANNELS_tag1=chan1 chan2&LAPSE_tag1=180'
    rc=RequestCollection()
    print rc
    
    
    GEAVars.environ['QUERY_STRING']='PREFIX_tag1=pweerre&PREFIX_tag2=paasssre&PREFIX_tag3=psfsdre&PREFIX_tag4=prfsde&'
    rc=RequestCollection()
    print rc
    
    

