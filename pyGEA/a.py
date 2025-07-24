#!/usr/bin/env python

import sys
import os
import re
import commands
import casi
import casiTools
import time
import glob
import xmlrpclib
                        
from GEAGeneral import naming, util
from GEATime import Time
from GEAException import DataHandlerException
from GEAData import Data
from GEARemedy import Remedy
from GEAValidator import IntValidator, BooleanValidator
import GEAVars

import MySQLdb

# connect to the ArchiveDataServer
dataServer=xmlrpclib.Server(GEAVars.path.web.dataServer)

#from matplotlib.pylab import num2epoch

####################
# DataHandlerBase
####################
class DataHandlerBase(object):
    """Base class... all dataHandlers/extractors/exporters should inherit from this.
    """
    def __init__(self, request, fStream=GEAVars.errStream, startTime=None, endTime=None, **options):

        self.fStream=fStream
        
        self._initValidators()  

        #self._options are set based on the options variable passed to the constructor.
        #They are then updated from the request (after being validated)
        self._options=options or {}
        if request is not None:
            self.updateAndValidateOptions(**request)

            #Also want to parse the request for any other (non-option type) data that each child might need.
            self._parseRequest(request)
            
        #Set up start and end times.
        self._setupTimeParams(startTime, endTime, request)
    
    def _parseRequest(self, request):
        """Each child should overwrite this method and extract any info it needs from the request.
        """
        pass
        
    def _overwriteAttr(self, attr, value):
        """Helper... if value is not None, overwrite attr with value.
        """
        if value is not None:
            self.__dict__[attr]=value
            
    def _setupTimeParams(self, startTime, endTime, request):
        """Each child should overwrite this method if it needs start/end times setup.
        """
        pass
        
    def _initValidators(self): 
        """Each child should overwrite this method, and define all the option validators that are needed.
        """
        self._validators={}
        
    def _validate(self, key, value):
        if self._validators.has_key(key):
            #Only validate if a validator for this option has been created.
            return self._validators[key].validate(value)
        return  value
        
    def updateAndValidateOptions(self, **newOpt):
        """Updates options, from a dictionary. This method calls _convertOptionType(), 
        which disregards keys it does not "know".
        
        When a value for a particular key is None, that key is not processed. Empty values which are to 
        be processed should be set to '' (empty string).
        """
        for key, val in newOpt.items():
        
            if val is None:                   #Don't process None values. Those are GEARequest blanks
                continue
        
            if self._options.has_key(key):              #Only modify values for keys which are already present.
                self._options[key]=self._validate(key, val)
        
####################
# RealTimeDataExtractor
####################
class RealTimeDataExtractor(DataHandlerBase):
    """Extracts EPCIS data in real time via.
    """
    def __init__(self, request, fStream=GEAVars.errStream,  **options):
        """
        """
        DataHandlerBase.__init__(self, request, fStream=fStream, **options)
                    
    def _parseRequest(self, request):
           
        self.chanList=request.get('CHANNELS','').split()
        if not  self.chanList:
            raise DataHandlerException("No channels provided.\n")
        

    def extract(self):
    
        import ca

        tmpName=os.path.join(GEAVars.path.fileSys.geaTmp, naming.genName(prefix='chanList', suffix=''))
        chanFile=file(tmpName, 'a')
   
        x, y = [], [] 
        for item in self.chanList:
            x.append(item)
            try:
                y.append(ca.pv(item, syncT=1).get())
            except ca.error, e:
                print pv.name, e

        self.dataList=[Data([x, y], name=tmpName)]
        
        return self.dataList
        
        
class Db(object):
    """Wrapper for some db communications"""
    def __init__(self,user='gea',passwd='gea99',hostname='localhost',db=''):        
        self.db=MySQLdb.connect(hostname,user=user,passwd=passwd,db=db)    
        self.c=self.db.cursor()                    
                    
    def __del__(self):                
        if self.c:
            self.c.close()
        if self.db:
            self.db.close()
            
            
    def getColList(self, table, disregard=['ts', 'id']):
        """
        """
        #There has got to be a prettier way to just grab column names and not the whole table with everything else?!?
        q='show columns from %s;' % table
        self.c.execute(q)     
        result=self.c.fetchall()     
        #First item in each tuple is the name of a column... only grab those.
        if result:
            return [name for name in zip(*result)[0] if name not in disregard]
        else:
            return []
                                
####################
# MysqlDataExtractor
####################
class MysqlDataExtractor(DataHandlerBase):
    '''Extracts data from a mysql database...
    We map tables<->archives, channels<->columns, channelData<->rows. This extractor should be almost identical to use 
    as the Epics one by the outside users.
    
    In the future we might want to extract data by arbitrary queries. This should be really easy to implement.  
    
    A few conditions for using MysqlDataExtractor:
    * each table should have a time stamp column. By default called 'ts', but can have a different
    name - passed into the constractor under the 'timeStampColumn' variable.
    * see _createQuery() for how the timestamp is used, and its format.
        
    '''
    dataTypes={'float':float, 'string':str, 'int':int}  #What functions to use for different data types conversion.

    def __init__(self, request, fStream=GEAVars.errStream, db=GEAVars.dataEx.sqlDataBaseName, timeStampColumn='ts', 
                 dataFileName=None, archNames=None, startTime=None, endTime=None, **options):
        """
        """
        #Define options for this object and update it with anything passed in to the constructor.
        # Options setup.
        _options={'SKIPBAD':True,    #If True, data points that are not the right type, are just skipped.
                  'DATATYPE':'float'
                  }      #Defaults.
        _options.update(options)

        self._tableColDict={}
        self._allTableColDict={}
        self._timeStampColumn=timeStampColumn
        
        self._db=Db(db=db)
        
        self._archNames=archNames

        self._dataFileName=dataFileName

        DataHandlerBase.__init__(self, request, fStream=fStream, startTime=startTime, endTime=endTime, **_options)
                                                
    def _parseRequest(self, request):
    
        #We map systems/archivers to tables.
        
        tableList=self._archNames
        if tableList is None:
            tableList=(' %s %s' % (request.get('SYSTEMS',''), request.get('SYSTEMS2', ''))).split()
            
        set={}
        self._tableList=[set.setdefault(e,e) for e in tableList if e not in set]         #Get rid of duplicates.               
            
        if len(self._tableList)<1:
            raise DataHandlerException("No archivers (systems) provided.\n")
           
        #We map channel names to column names.
        self._channels=request.get('CHANNELS','').split()
        self._pattern=request.get('PATTERN', '')
                
        if not (self._channels or self._pattern):
            raise DataHandlerException("No channels or pattern provided.\n")          

        self._findAllTableColumns()
        
    def _initValidators(self):
        """Used by updateAndValidateOptions()
        
        Allows for automatic conversion of certain values to proper types (ie. str->int, str->float, etc...). 
        """
        DataHandlerBase._initValidators(self)
                                                                   
        self._validators['SKIPBAD']=BooleanValidator(valueOnError=True,stream=self.fStream,
                                                     errorPreText="Validating 'SKIPBAD'... ")
                    
    def _findAllTableColumns(self):
        '''This could be static.... maybe no need to poke the database each time.
        '''
        self._allTableColDict={}
        
        for t in self._tableList:
            self._allTableColDict[t]=self._db.getColList(t)
              
    def _globPatternToRe(self, glob):
        '''Convert a glob pattern to a re.
        Stolen from the ChannelArchiver c++ src (src/Tools/RegularExpression.cpp), with a modification to handle the '|' char.
        '''
        pattern="^"; 
        for i in glob:
            if i=='*':
                pattern+='.*'
            elif i=='?':
                pattern+='.'
            elif i=='|':
                pattern+=i
            else:  #Do we really want this??
                pattern+='['   # 'x' -> "[xX]"
                pattern+=i.lower()
                pattern+=i.upper()
                pattern+=']'
        pattern+='$'
    
        return pattern;
          
    def _matchTableColumns(self, source='all'):
        '''Look at the requested channels/columns in the form of a channel list or a glob pattern, 
        and match against what's available. 
        '''    
    
        self._tableColDict={}
    
        if self._channels and (source=='all' or source=='channel'):       
            cDict={}            
            for chan in self._channels:
                found=False
                for table, columns in self._allTableColDict.iteritems():
                    for col in columns:
                        if col==chan:
                            if not cDict.has_key(table): 
                                cDict[table]=[]                       
                            cDict[table].append(chan)                                                        
                            found=True                            
                            break
                    
                if not found:
                    #With channels, we want to find every channel we're asked for; raise exception otherwise.
                    raise DataHandlerException("Cannot find channel '%s'.\nYou might be trying to look at data for channel that does not exist at %s." % (chan, GEAVars.site))
                             
            self._tableColDict.update(cDict)            
                        
        if self._pattern and (source=='all' or source=='pattern'):
            regExp=re.compile(self._globPatternToRe(self._pattern)) 
            pDict={}
        
            for table, columns in self._allTableColDict.iteritems():
                #Check if each column matches the pattern.
                for c in columns:                        
                    if regExp.match(c):       
                        if not pDict.has_key(table): 
                            pDict[table]=[]                       
                        pDict[table].append(c)
                                    
            if len(pDict)==0:
                raise DataHandlerException("Cannot find channels corresponding to pattern '%s'.\nYou might be trying to look at data for channel that does not exist at %s." % (self._pattern, GEAVars.site))
                        
            #We don't want to override already existing entries obtained by going through self._channels. We need to add the new
            #columns we found in self._pattern and make sure that the columns requested for each table dont have repeats.
                         
            toMakeUnique=[]            
            for t, cList in pDict.iteritems():
                if self._tableColDict.has_key(t):
                    self._tableColDict[t]+=cList
                    toMakeUnique.append(t)
                else:
                    self._tableColDict[t]=cList   
                    
            for t in toMakeUnique:
                set={}
                self._tableColDict[t]=[set.setdefault(e,e) for e in self._tableColDict[t] if e not in set]
                                                                                   
    def _setupTimeParams(self, startTime, endTime, request):
        '''Want to override the standard way of setting up a default time.
        When exceptions are raised, instead of setting up a default time, set it to None.
        This allows for queries to be made without a specific time range given.
        '''
        if endTime is not None:
            self.endTime=endTime
        else:
            try:
                self.endTime=Time().fromEndTimeDict(request)
            except KeyError:
                self.endTime=None
                
        if startTime is not None:
            self.startTime=startTime
        else:
            try:
                self.startTime=Time().fromStartTimeDict(request)
            except KeyError:
                self.startTime=None

               
    def _createQuery(self, table, columns):
        
        timeQ=''
        if self.startTime and self.endTime:
            timeQ+='where %s<ts and %s>ts' % (self.startTime.string14, self.endTime.string14)
        elif self.startTime:
            timeQ+='where %s<ts' % (self.startTime,)
        elif self.endTime: 
            timeQ+='where %s>ts' % (self.endTime,)              

        #We're assuming the database has a time stamp column
        return '''select %s,`%s` from %s %s;''' % (self._timeStampColumn, 
                                                    "`,`".join(columns), 
                                                    table, 
                                                    timeQ)
        
    def _fetchData(self):
        
        #dataConv will be used to turn string data coming from the db into an appropriate type.
        dataConv=MysqlDataExtractor.dataTypes[self._options.get('DATATYPE', 'float')]
                    
        skipped=0
        for t, cList in self._tableColDict.iteritems():
            
            self._db.c.execute(self._createQuery(table=t, columns=cList))
            
            #The result will be a tuple of tuples such as:
            #((datetime.datetime(2006, 9, 15, 15, 12, 5), '65.00', '23.12'),
            #(datetime.datetime(2006, 9, 15, 15, 16, 59), '65.00', '322.32')...)         
            result=self._db.c.fetchall()          

            if not result:
                return self.dataList          
                           
            if self._options['SKIPBAD']:                
                #We go through each item, and check the validity of the data (i.e. if can use dataConv on it), only append if ok.
                #We can be potentially processing multiple datasets (from different columns), but they share a timestamp.
                #This method is useful in a case where have float data with possibly a few strings in it... the strings (that cannot
                #be converted to floats) will be disregarded.
                #TODO: Maybe a faster way todo it with numeric/numarray/numpy??
                        
                dataDict={}
                for name in cList:
                    dataDict[name]=Data([], name=name)   #Start with empty Data.

                for tup in result:
                    #tup is a tuple of tuples with data
                    
                    tStamp=float(time.mktime(tup[0].timetuple()))
                    
                    for name, data in zip(cList, tup[1:]):
                        try:
                            data=dataConv(data)                                                
                        except (TypeError, ValueError), e:
                            skipped+=1                            
                            continue  # Lets skip this one.
                        
                        dataDict[name].x.append(tStamp)
                        dataDict[name].y.append(data)
                  
                self.dataList+=dataDict.values()
          
            else:    
                #Here we assume that dataConv will properly convert all the data. If it fails even once, an exception 
                #is raised and further data conversion aborted.        
                resultZip=zip(*result)                                            
                ts=[float(time.mktime(t.timetuple())) for t in resultZip[0]]  #The first row will be timestamps                                    
                for n, d in zip(cList, resultZip[1:]):
                    self.dataList.append(Data([ts , map(lambda x: dataConv(x), d)], name=n))
                
            
        if skipped:
            self.fStream.write('Skipped %d values from the database.\n' % skipped) 
            
    def extract(self, source='all'):   #source can be 'all', 'channel', 'pattern' 
                
        self.dataList=[]                  
        
        self._matchTableColumns(source=source)  # We need to define which table/column combination we'll be fetching data from/for.
        
        self._fetchData()
        
        if self._dataFileName:
            f=file(self._dataFileName, 'a')
            for item in self.dataList:
                f.write(item.__str__(xAsTime=True, sep='\t\t'))
            f.close()
        
        return self.dataList     
     
     
####################
# EpicsDataInserter
####################
class EpicsDataInserter(DataHandlerBase):
    '''Imports data into an epics archive.

    Probably don't need the whole class wrapper.  Could be a couple of regular functions... 
    '''
    def __init__(self, request=None, fStream=GEAVars.errStream, dataRe=None, **options):

        if request is None:
            request={}    
              
        DataHandlerBase.__init__(self, request=request, fStream=fStream, **options)
            
        if dataRe is None:
            dataRe=r'^(\d{4}/[01]\d/[0-3]\d)\s*([012]\d:\d\d:\d\d)\s*([\S]*)\s*(.*)$'
            
        self._dataRe=re.compile(dataRe)
            
        self._archive=casi.archive()
         
    def _insertData(self, timeStamp, chanName, data):
        """Assume archive already open.
        """
        channel=casi.channel()
        value=casi.value()
        ctrlInfo=casi.ctrlinfo()
    
        if not self._archive.findChannelByName(chanName, channel):
            #Try adding the channel to the archive
            if not self._archive.addChannel (chanName, channel):
                raise IOError("Can't find/add channel '%s' in/to the archive" % chanName)
    
        #Do a quick check to make sure our data is not from the past...
        # if channel.getLastTime() > timeStamp:
        #     raise ValueError("Old time stamp (%s) is greater than %s on channel %s data... skipping." %
        #                      (channel.getLastTime(), timeStamp, chanName))
        if channel.getLastTime() > timeStamp:
            print ("Old time stamp (%.19s) is greater than %.19s on channel %s data... wierd..." %
                              (channel.getLastTime(), timeStamp, chanName))
    
        try: 
            data=float(data)
            theType=casi.DBR_TIME_DOUBLE
            self._archive.newValue(theType, 1, value)
            #(prec, units, disp_low, disp_high, low_alarm, low_warn, high_warn, high_alarm)
            ctrlInfo.setNumeric(5, '', 0, 0, 0, 0, 0, 0)
    
        except ValueError:
            theType=casi.DBR_TIME_STRING
            self._archive.newValue(theType, 1, value)
            ctrlInfo.setEnumerated()        
        
        value.setCtrlInfo(ctrlInfo)    
    
        value.setStat(0,0)
        value.setStatus('')
        
        value.setTime(timeStamp)    
    
        if theType==casi.DBR_TIME_DOUBLE:
            value.set(data)
            print 'Adding: ', value.time(), value.get()
        else:   # theType==casi.DBR_TIME_STRING:
            value.parse(data)
            print 'Adding: ', value.time(), value.text()
    
        if not channel.addValue(value):
            channel.addBuffer(value.determineChunk(self._archive.nextFileTime(value.time())))
            
            if not channel.addValue(value):
                raise IOError("Can't add value %s to channel %s"  % (data, chanName))
                
        channel.releaseBuffer()        
        
    def _getFreqDir(self, archiveName, t):
            
        if t is None:
            t=Time()
            
        d = os.path.join(GEAVars.path.fileSys.geaData + "/data", archiveName, t.string17)
        if not os.path.isdir(d):
            print 'Creating ', d
            os.makedirs(d)              
        
        return os.path.join(d, 'freq_directory')
        
    def insert(self, inputFileName, archiveName=None, freq_directory=None, aTime=None):
        
        if archiveName and freq_directory:
            raise RuntimeError('Should either provide a name of the archvie, or a full freq_directory file - not both.\n')
        
        if archiveName:      
            freq_directory=self._getFreqDir(archiveName, aTime)
        
        if not freq_directory:
            raise RuntimeError('Need to specify an archive name, or a freq_directory file where the data should go.\n')        
                
        if not self._archive.write(freq_directory, 24):
            raise IOError("Can't open archive '%s'." % freq_directory)           
           
        f=file(inputFileName, 'r')
        
        for line in map(lambda x: x.strip(), f.readlines()):   #Not pretty for big files...
    
            if line.startswith('#') or line=='':
                continue
            
            res=self._dataRe.search(line)
    
            if res:                
                #Here we want to put the data into the right section... d                
                d, t, n, v=res.groups()
                
                try:                                    
                    self._insertData('%s %s.000000000' % (d, t), n, v.strip())
                    
                except ValueError, e:
                    #Do nothing on these... just go to the next value.
                    print str(e)
                    
            else:
                print 'Error parsing. Skipping line:', line
                
        f.close()
        

def insertData(files, archiveName=None, freq_directory=None, aTime=None):    
    inserter=EpicsDataInserter()
    for f in files:
        print 'Processing file ', f
        inserter.insert(f, archiveName=archiveName, freq_directory=freq_directory, aTime=aTime)


####################
# EpicsDataHandlerBase
####################
class EpicsDataHandlerBase(DataHandlerBase):
    """Epics data extractors/exporters should inherit from this class.
    """
    def __init__(self, request, fStream=GEAVars.errStream, archNames=None, startTime=None, endTime=None, **options):

        #We need to setup self._archNames *before* we call DataHandlerBase, because we need it for _parseRequest which is 
        #done from the DataHandlerBase's constractor.
        #If archNames is provided via a variable passed to the object constactor (and is not None), its contents will be used instead 
        #of what's in the request. See EpicsDataHandlerBase._parseRequest() how this is done.
        self._archNames=archNames

        DataHandlerBase.__init__(self, request=request, fStream=fStream, startTime=startTime, endTime=endTime, **options)

        self.dataList=[]  #Will store the extracted data in an array of GEAData.Data objects            
        self._archIndeces=self._getArchiveIndex()
	self._archName=self._getArchiveName()		# No, archName is not the same as archNames above.

               
    def _setupTimeParams(self, startTime, endTime, request, defaultTimeRange=GEAVars.defaultTimeRange):
    
        if endTime is not None:
            self.endTime=endTime
        else:
            try:
                self.endTime=Time().fromEndTimeDict(request)
            except KeyError:
                #Missing a key (such as ENDYEAR or ENDMONTH, etc). Default the end time to now
                self.endTime=Time()

                
        if startTime is not None:
            self.startTime=startTime
        else:
            try:
                self.startTime=Time().fromStartTimeDict(request)
            except KeyError:
                #Dont have a proper startTime in the request. 
                self.startTime=Time(self.endTime.seconds-defaultTimeRange)

    def _parseRequest(self, request):
        if self._archNames is None:
            archivers=' %s %s' % (request.get('SYSTEMS',''), request.get('SYSTEMS2', ''))
            self._archNames = archivers
        else:
            archivers=' '.join(self._archNames)
            
        self.createArchList(archivers=archivers)
        if len(self.archList)<1:
            raise DataHandlerException("No archivers (systems) provided.\n")
           
        self.chanList=request.get('CHANNELS','').split()
        self.chanPattern=request.get('PATTERN', '')
            
        if not (self.chanPattern or self.chanList):
            raise DataHandlerException("No channels or pattern provided.\n")
            
    def createArchList(self, archivers):
        """Method "public" (no underscore) - can be called after object created, to redefine the archivers.
        systems - returns a list of archiver keys
        """
        aList=[]
        for arch in archivers.split():
            if GEAVars.dataEx.metaArch.has_key(arch):
                aList+=GEAVars.dataEx.metaArch[arch].split()
            else:
                aList.append(arch)
                
        alist = list(set(aList))

	self.archList=[x['key'] for item in aList for x in dataServer.archiver.archives() if x['name']==item]
        
    def _getArchiveName(self):
        """This method returns a name of a master_index file for the old ArchiveExport command
        """        
        # return the path for the master_index file
       
 	return [x['path'] for x in dataServer.archiver.archives() if x['name']==''][0]

    def _getArchiveIndex(self):
        """This method returns the index keys of archivers in _archNames
        """

	return [x['key'] for x in dataServer.archiver.archives() if x['name'] in self._archNames]

####################
# EpicsDataExtractor
####################
class EpicsDataExtractor(EpicsDataHandlerBase):

    def __init__(self, request, dataFileName, fStream=GEAVars.errStream, archNames=None, startTime=None, endTime=None, **options):

        #Define options for this object and update it with anything passed in to the constructor.
        # Options setup.
        _options={'REDUCE':GEAVars.plot.REDUCE,
                  'HANDLEDISCON':GEAVars.plot.HANDLEDISCON,  #Determines wheter should check the status of archived data.
                  'TEXTDATA':GEAVars.dataEx.TEXTDATA}      #Defaults.
        _options.update(options)

        EpicsDataHandlerBase.__init__(self, request=request, fStream=fStream, archNames=archNames, startTime=startTime, endTime=endTime, **_options)
                     
        self.dataFileName=dataFileName #With full path... or None
    
    def extract(self, source='all'):   #source can be 'all', 'channel', 'pattern'

        self.dataList=[]
        
        self._dataFile=file(self.dataFileName, 'a')

        try:
            if source=='channel' or source=='all':
            	self._fetchDataFromChanList()
                
            if source=='pattern' or source=='all':
                self._fetchDataFromChanPattern() 
        finally:
            self._dataFile.close()
            # Do not need to close self._arch. Could just call self._arch.open(<diff Archive>) to get other data.
            
        #Now self.dataList should be filled in. Return it for convenience.
        return self.dataList
    
    def _fetchDataFromChanPattern(self):
        """Looks in the archive and gets a list of channels which satisfy the RE pattern.
        Assumes that self._arch is open.
        """
        if not self.chanPattern:
            return                                  #Nothing to do.
	# match pattern against each archiver in archIndeces and build a chan dict with 'name' and 'key'
	self._chan=[]
	for key in self._archIndeces:
            #create a list of name and key dicts that match pattern
	    matches=dataServer.archiver.names(key, self.chanPattern)
	    for match in matches:
		self._chan.append(dict(name=match.items()[4][1],key=key))
	if len(self._chan)==0:
                raise DataHandlerException("Cannot find channels corresponding to pattern '%s'.\nYou might be trying to look at data for channel that does not exist at %s in archivers: %s" % (self.chanPattern, GEAVars.site, self._archNames))      
        #Iterate throught all the channels that match the pattern and are not in self.chanList

	for i in range(len(self._chan)):
        	if self._chan[i]['name'] not in self.chanList: 
        		self._fetchChannelData(index=i)


    def _fetchDataFromChanList(self):
        """Looks at the dataServer and confirms that there is data for channels in the list
        """
        for channel in self.chanList:

	    self._chan=[]
	    for key in self._archIndeces:
        	#create a list of name and key dicts that match pattern
		matches=dataServer.archiver.names(key, channel)
		for match in matches:
		    self._chan.append(dict(name=match.items()[4][1],key=key))


	    if len(self._chan) == 0:
		raise DataHandlerException("Cannot find channel '%s'.\n" % channel)
	    self._fetchChannelData(index=0)
       

    def _initValidators(self):
        """Used by updateAndValidateOptions()
        
        Allows for automatic conversion of certain values to proper types (ie. str->int, str->float, etc...). 
        """
        EpicsDataHandlerBase._initValidators(self)
        
        self._validators['REDUCE']=IntValidator(valueOnError=GEAVars.plot.REDUCE, 
                                                              minVal=1,
                                                              maxVal=5000, 
                                                              stream=self.fStream, 
                                                              errorPreText="Validating 'REDUCE'... ")
                                                                    
        self._validators['HANDLEDISCON']=BooleanValidator(valueOnError=True, stream=self.fStream,
                                                              errorPreText="Validating 'HANDLEDISCON'... ")
            
        self._validators['TEXTDATA']=BooleanValidator(valueOnError=GEAVars.dataEx.TEXTDATA,
                                                              stream=self.fStream,
                                                              errorPreText="Validating 'TEXTDATA'... ")

    def _fetchChannelData(self,index):
        """Grab all the channel data from channel self._chan and put it in x/y lists (inside a GEAData object). 
        """
	#retrieve the data values from the dataServer
	#count is rediculously high to get all data in a given search
	# it would be nice to use some binning functionality to improve the speed
	# of searches for long time periods.

	data=dataServer.archiver.values(self._chan[index]['key'], [self._chan[index]['name']], 
		int(self.startTime.seconds),
		int((self.startTime.seconds-int(self.startTime.seconds))*1000000000), 
		int(self.endTime.seconds),
		int((self.endTime.seconds-int(self.endTime.seconds))*1000000000), 
		3000, 0)[0]

	#if we max out on the number of data points, switch to a sampling method to cover desired time range
	if len(data['values']) == 3000:
	    data=dataServer.archiver.values(self._chan[index]['key'], [self._chan[index]['name']], 
		int(self.startTime.seconds),
		int((self.startTime.seconds-int(self.startTime.seconds))*1000000000), 
		int(self.endTime.seconds),
		int((self.endTime.seconds-int(self.endTime.seconds))*1000000000), 
		3000, 2)[0]
	    newname = "%s (averaged)" %(self._chan[index]['name'])
	    tempData=Data([], name=newname)    #Put all the pairs here.       
            self._dataFile.write("Channel: %s (averaged)\n" % self._chan[index]['name'])
	else:
	    tempData=Data([], name=self._chan[index]['name'])    #Put all the pairs here.       
            self._dataFile.write("Channel: %s\n" % self._chan[index]['name'])

        if self._options['HANDLEDISCON']:
            discAppend=tempData.discList.append
        else:   
            #Don't want to keep track where the discontinuities occur
            def dummy(x): pass
            discAppend=dummy
        
        #For speed... lots of lookups here.
        x, y=tempData.x, tempData.y
        xAppend, yAppend=x.append, y.append
        valTextOrGet="data['values'][val]['value'][0]"
	valGetDoubleTime="data['values'][val]['secs']+(float(data['values'][val]['nano'])/1000000000)"

        # Get the time as a floating point number into a string in the
        # form of "2011/04/12 10:32:43.599999904".

        def _mungeEpoch(val):
            import datetime

            secs = data['values'][val]['secs']
            nano = float(data['values'][val]['nano'])

            d = datetime.datetime.fromtimestamp(secs)
            tmsg  = d.strftime('%Y/%m/%d %H:%M:%S') + "." + ("%.2f" % (nano / 1000000000.0)).split('.')[1]

            # tmsg  = d.strftime('%Y/%m/%d %H:%M:%S') + ("%.2f" % ((nano / 1000000000.0) - .005))[1:]
            # tmsg  = d.strftime('%Y/%m/%d %H:%M:%S')
            # tmsg += (".%09d" % nano)[:3]
            d = datetime.datetime.utcfromtimestamp(secs)
            tmsg += d.strftime(' (%d %H)') 
            return tmsg

	valTime="_mungeEpoch(val)"
        valStatus="data['values'][val]['stat']"
        valIsInfo="data['values'][val]['sevr'] in (3904, 3872, 3848)"
	valIsRepeat="data['values'][val]['sevr'] in (3968, 3856)"

	for val in range(len(data['values'])):
	    #For some reason, the search always returns data earlier than startTime
	    if eval(valGetDoubleTime)<self.startTime.seconds:
		continue
	    #Only take every nth value depending on self._options['REDUCE']
	    if divmod(val,self._options['REDUCE'])[1] != 0:
		continue

	    if eval(valIsInfo): #have a discontinuity
                #Remember where the discontinuity occured.
		discAppend(len(x))
		if data['values'][val]['sevr'] == 3904:
		    statString = "Disconnected"
		elif data['values'][val]['sevr'] == 3872:
		    statString = "Archive Off"
		elif data['values'][val]['sevr'] == 3848:
		    statString = "Archive Disabled"
		txt="\n#%-35s%25s\n\n" % (eval(valTime), statString)
            else:                  
                v=eval(valTextOrGet)
                xAppend(eval(valGetDoubleTime))
                yAppend(v)
		if eval(valIsRepeat):
		    txt="%-35s%20s%20s%-7s\n" % (eval(valTime), v, 'Repeat ', eval(valStatus))
		else:
                    txt="%-35s%20s\n" % (eval(valTime), v)
                
            self._dataFile.write(txt)
                
        self.dataList.append(tempData)   
      
####################
# EpicsDataSpreadsheetExporter
####################
class EpicsDataSpreadsheetExporter(EpicsDataHandlerBase):

    def __init__(self, request, exportFileName, fStream=GEAVars.errStream, archNames=None, startTime=None, endTime=None, **options):
    
        #Define options for this object and update it with anything passed in to the constructor.
        _options={'INTERPOLATE':GEAVars.dataEx.INTERPOLATE, 'FILL':GEAVars.dataEx.FILL
                     }
        _options.update(options)

        EpicsDataHandlerBase.__init__(self, request=request, fStream=fStream, archNames=archNames, startTime=startTime, endTime=endTime, **_options)
                     
        self.exportFileName=exportFileName
        
    def _initValidators(self):
        """Used by updateAndValidateOptions()
        
        Allows for automatic conversion of certain values to proper types (ie. str->int, str->float, etc...). 
        """
        EpicsDataHandlerBase._initValidators(self)
        
        self._validators['INTERPOLATE']=IntValidator(valueOnError=0, 
                                                                                minVal=0,
                                                                                maxVal=86400,
                                                                                stream=self.fStream,
                                                                                errorPreText="Validating 'INTERPOLATE'...")        
        self._validators['FILL']=BooleanValidator(valueOnError=GEAVars.dataEx.FILL,
                                                                                stream=self.fStream,
                                                                                errorPreText="Validating 'FILL'... ")


    def _getChanPattern(self):
        """Combines self.chanList with self.chanPattern and returns a pattern which can 
        be used to extract channels.
        """
        if not (self.chanList or self.chanPattern):
            raise DataHandlerException("No channels or pattern provided.\n")
            
        patternList=[self.chanPattern or '']  #self.chanPattern could be None
            
        for channel in self.chanList:
            if patternList[0]=='':
                patternList.append(channel)
            else:
                patternList.append('|(%s)' % channel)
        
        return ''.join(patternList)
        
    def export(self):
        
        opt=''
        if self._options['INTERPOLATE']>0:
            opt+='-interpolate %s' % self._options['INTERPOLATE']
	#The fill option no longer exists in the new ArchiveExport command
        #if self._options['FILL']:
        #    opt+=' -fill '
        #other...
        #if blah...
	opt+=' -precision "8" '

        cmnd='%s/run/ArchiveExport %s -start "%s" -end "%s" -output "%s" -match "%s" %s' % (
                GEAVars.path.fileSys.geaRoot, 
                opt,
                self.startTime.string16, 
                self.endTime.string16, 
                self.exportFileName, 
                self._getChanPattern(),
		self._archName)        

        (exitstatus, output) = commands.getstatusoutput(cmnd)
        
        tempFileName=os.path.join(GEAVars.path.fileSys.wwwData, "tempFileName")
        fdH = open(tempFileName, "w")
        fdH.write(self._getChanPattern())
        fdH.close()

        fdB = open(self.exportFileName, "a")
        bufB = fdB.read()
        fdH = open(tempFileName, "a")
        fdH.write(bufB)
        fdH.close()

        os.remove(self.exportFileName)
        os.rename(tempFileName, self.exportFileName)

        if exitstatus:
            raise DataHandlerException("%s.\n" % output)
                
####################
# RemedyDataExtractor
####################
class RemedyDataExtractor(DataHandlerBase):

    def __init__(self, rQuery=None, 
                    rKeys=None, 
                    site=None, 
                    request=None, 
                    startTime=None, 
                    endTime=None, 
                    dBase='', 
                    fStream=GEAVars.errStream,
                    **options):
                    
        DataHandlerBase.__init__(self, request=request, fStream=fStream, startTime=startTime, endTime=endTime, **options)
               
        self._overwriteAttr('rQuery', rQuery)
        self._overwriteAttr('rKeys',  rKeys)
        self._overwriteAttr('site', site)
        
        self.dBase=dBase
        self.dataList=[]
        
    def _parseRequest(self, request):
        """Called from DataHandler.__init__()
        """
        self.rQuery=request.get('RQUERY', None)
        self.rKeys=request.get('RKEYS', None)
        self.site=request.get('SITE', None)
                    
    def extract(self, dataFileName=naming.genDataName(), data2StringFunc=None):
    
        self.dataList=Remedy(site=self.site, dBase=self.dBase).query(self.rQuery, self.rKeys, self.startTime, self.endTime) 
            
        return self.dataList
        
    def _setupTimeParams(self, startTime, endTime, request):
        """Want to override the standard way of setting up a default time.
        When exceptions are raised, instead of setting up a default time, set it to None.
        This allows for queries to be made without a specific time range ginven.
        """
        if endTime is not None:
            self.endTime=endTime
        else:
            try:
                self.endTime=Time().fromEndTimeDict(request)
            except KeyError:
                self.endTime=None
                
        if startTime is not None:
            self.startTime=startTime
        else:
            try:
                self.startTime=Time().fromStartTimeDict(request)
            except KeyError:
                self.startTime=None


def splitArchives(aList):
    '''Return two lists; one containing ChannelArchiver's names, other mysql tables.
    '''
    sqlList=[]
    chanArchList=[]
    
    for a in aList:
        if a in GEAVars.dataEx.sqlArchList:
            sqlList.append(a)
        else:
            chanArchList.append(a)   
        
    return [chanArchList, sqlList]

def autoHandleData(request, stream, dataFileName=None, *kwargs):
    '''Extract or export data based on information in the request. Should be clever enought to know where
    the data should be coming from (epics archive, mysql) and what needs to be done (data returned, or exported to a file).    
    '''    
    dataList=[]
    format=request.get('FORMAT', '')

    chanArchList,sqlList=splitArchives(request.get('SYSTEMS','').split()+request.get('SYSTEMS2','').split())
    
    if not chanArchList and not sqlList:
        raise DataHandlerException("No archivers (systems) provided.\n")
       
    #Quick check to see that we actually have some channels/patter to look for
    chanOrPatt=request.get('PATTERN','')+request.get('CHANNELS','')
    if not chanOrPatt.strip():
        raise DataHandlerException("No channels or pattern provided.\n")
        
    if format=='Spreadsheet':
        #TODO: Should implement merging of the sql data with the stuff coming from the epics archives.
        if sqlList:
            stream.write("Data from archives '%s' comes from a non-epics database, and currently\ncannot be exported as spreadsheet. Omitting it and only exporting epics data." % ",".join(sqlList))
 
        if chanArchList:
            EpicsDataSpreadsheetExporter(request=request, archNames=chanArchList,
                                     exportFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName),
                                     fStream=stream).export()                 
        else:
            raise DataHandlerException("Currently exporting spreadsheet data is only available for epics archives.\nNo epics archives were provided, so no data has been exported as a spreadsheet.\n")
                                 
    else: # format=='Plot' or format=='Histogram':        
                        
        #When extracting the data, we pass in a list of archiver names (for example: archNames=chanArchList) into the data extractors. 
        #Normally they can be obtained from request object, but here we want each extractor only try to process data only 
        #for specific ones (ie.MysqlDataExtractor should only look at the mysql archives). 
                
        if chanArchList and sqlList:
                        
            epics=EpicsDataExtractor(request=request, archNames=chanArchList,
                                dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName), 
                                fStream=stream)
            
            mysql=MysqlDataExtractor(request=request, archNames=sqlList,
                                    dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName),  
                                    fStream=stream)
            
            #This bit is a little tricky... we want to raise an exceptions *only* when data cannot be extracted at all by 
            #any of the extractors... So need to try grab it by channel first, then by pattern.
            #
            #Start with trying to grab the channels... raise if can't find the requested 
            exceptions=[]
            try:
                dataList+=epics.extract(source='channel')
            except DataHandlerException, e:
                exceptions.append(e)
                
            try:
                dataList+=mysql.extract(source='channel')
            except DataHandlerException, e:
                exceptions.append(e)
                
            if len(exceptions)>1:   #Something went wrong (at least in one of the extractions - raise)
                raise exceptions[0]  
                                 
            exceptions=[]
            try:
                dataList+=epics.extract(source='pattern')
            except DataHandlerException, e:
                exceptions.append(e)
                
            try:
                dataList+=mysql.extract(source='pattern')
            except DataHandlerException, e:
                exceptions.append(e)
            
            if len(exceptions)>1:    #Something went wrong (at least in one of the extractions - raise)
                raise exceptions[0]
            
        elif chanArchList:
            dataList=EpicsDataExtractor(request=request, archNames=chanArchList,
                                    dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName),  #Want full path..
                                    fStream=stream).extract() 
                                    
        elif sqlList:
            dataList=MysqlDataExtractor(request=request, archNames=sqlList,
                                    dataFileName=os.path.join(GEAVars.path.fileSys.wwwData, dataFileName),  #Want full path..
                                    fStream=stream).extract()             
                                                                                                    
    return dataList


########################################################
########################################################

def insertCalibrationsData(archiveName='cal', aTime=None):
    t=Time()  #today...      
    
    #Grab data files depending on what aTime we got... if got a None, insert everything available. 
    if aTime is None:          
        dataDirs=[os.path.basename(f) for f in glob.glob("%s/20?[0-9]????" %  (GEAVars.path.fileSys.calDataDirNameDict))]            
    else:
        dataDirs=[str(aTime.string12)]
            
    for d in dataDirs:
        t.string12=d
        files=glob.glob("%s/%s/*.dat" %  (GEAVars.path.fileSys.calDataDirNameDict, t.string12)) 
        insertData(files, archiveName=archiveName, freq_directory=None, aTime=t)


if __name__=='__main__':
    
    endTime=Time()
    startTime=Time(endTime.seconds-Time.secPerWeek)
    
    rQuery="('UT Date'>=\"%d\") AND ('UT Date'>=\"%d\")" % (startTime.seconds, endTime.seconds)
    rQuery=''
    rKeys=('UT Date','UT Date')  #Cannot have keys with length=1.. gotta fix this in remedyWrapper...!
    
    extractor=RemedyDataExtractor(rQuery=rQuery, startTime=startTime, endTime=endTime, rKeys=rKeys, site='MK', dBase='NL')
    extractor.extract()
    
    print extractor.dataList

