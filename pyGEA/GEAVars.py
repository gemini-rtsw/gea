#!/usr/bin/python

"""This file contains all the default GEA variables. Classes here are only used to
differentiate namespaces.
"""
import sys
import os

pathJoin=os.path.join

#Enviroment... might have to be redefined when start using mod_python.
environ=os.environ

###########
#This is the only variable that needs to be set for the system to know if it is running on MK or CP.
site=environ['GEMINI_SITE']    #Should be either  MK or CP   (for  'Mauna Kea' or 'Cerro Pachon')
version=environ['GEA_VERSION']
revision=environ['GEA_RELEASE']
if site not in ['MK', 'CP']:
    raise RuntimeError("Site '%s' unrecognized\n" % str(site))
###########

#This may be non-blank if apache is not used for link rewriting.
dispatchScript=''

debug=False    #Can be overwridden by a 'DEBUG=On' addition to a QUERY_STRING in any page.

siteDomainDict={'MK':'geanorth.hi.gemini.edu',  
                'CP':'geasouth.cl.gemini.edu'}  

JiraHost={'MK':'https://osc.hi.gemini.edu',  
          'CP':'https://osc.cl.gemini.edu'}  
siteDomain = siteDomainDict[site]
            
#Time offsets from UTC time... in seconds 
#
# Don't use b/c CP has std/dst time. Better to let the OS handle it instead of changing it here!
#
# siteTimeOffsetDict={'MK': + 36000, 
#                   'CP': + 10800} #std time
#                   'CP': + 14400} #dst time

# siteTimeOffset=siteTimeOffsetDict[site]
                 
#Default streams.
outStream=sys.stdout            #Default output stream
errStream=sys.stderr            #Default error stream

#Flag that determines whether to use psyco optimization.
usePsyco=False

defaultTimeRange=86400  #24*60*60=Day - Default time range over which the plots are shown if this info is not in the QUERY_STRING.  In seconds.
defaultTimeRangeRemedy=604800 #24*60*60*7=Week
      
#This is used to separate multiple values of in the QUERY_STRING when building a string from them.  
#A space character might have to be changed when if/when have to deal with multiple words in queries. 
#This variable is also used to separate different entries in html <select> statement entries; see GEAHtml and jsGEA.js
#for more info.
queryStrSep=' '

#Mostly used when generating html/javascript and need to separate records/fields
recSep="|||"
fieldSep=",,,"

#Locations

class path:
    """All variables in path represent directories and should end with a slash.
    """
    class web:   
        """Paths relative to the apache's root.
        """
        geaRoot='/'
        pages=pathJoin(geaRoot, 'pages/')
        doc=pathJoin(geaRoot, 'doc/')
        
        #Default content locations (Should have a final slash)
        wwwMedia='/www_media/'
        wwwCss=pathJoin(wwwMedia, 'css/')
        wwwImages=pathJoin(wwwMedia, 'images/')
        wwwScripts=pathJoin(wwwMedia, 'scripts/')

        wwwData='/wwwdata/'	# This is a symlink from DocumentRoot to $GEA_DATA/geadata for generated documents.
        m1SurfacePlots=pathJoin(wwwData, 'm1SurfacePlots')    #Where the surface plots should go into 
        daily=pathJoin(wwwData, 'daily')

#        niriVacFileNameDict={'MK':pathJoin(wwwData ,'niriData/niriVac.txt')}

        dataServer='http://localhost/run/ArchiveDataServer.cgi'
    
        sysMonHtml=pathJoin(wwwData, 'sysMon/html/')
        sysMonReport=pathJoin(sysMonHtml, 'sysMonReport.html')                
            
    class fileSys:
        """Paths relative to linux's root (/).
        """
        geaConf=environ['GEA_CONF']
        geaRoot=environ['GEA_BASE']
        geaData=environ['GEA_DATA']
        geaTmp =environ['GEA_TMP']
        pages=pathJoin(geaRoot, 'pages/')
        doc=pathJoin(geaRoot, 'doc/')
        wwwData=pathJoin(environ['GEA_DATA'], 'wwwdata/')		# filesystem path to where wwwData url path above.
        epicsbin=pathJoin(environ['EPICS_BASE'], 'bin/linux-x86_64/')	# Path to epics programs
        
        #Default content locations (Should have a final slash)
        wwwMedia=pathJoin(geaRoot, 'www_media/')
        wwwCss=pathJoin(wwwMedia, 'css/')
        wwwImages=pathJoin(wwwMedia, 'images/')
        wwwScripts=pathJoin(wwwMedia, 'scripts/')
        
        bin=pathJoin(geaRoot, 'bin/')
        m1SurfacePlots=pathJoin(wwwData, 'm1SurfacePlots/')  #Where the surface plots should go into 
        daily=pathJoin(wwwData, 'daily/')
    
        niriVacFileNameDict={'MK':pathJoin(wwwData ,'niriData/niriVac.txt')}
        
        calDataDirNameDict={'MK':geaData + '/../caldata',
                            'CP':'/net/josie.cl.gemini.edu/staging/dataproc/data/gea'}
    
        calDataDirNameDict=calDataDirNameDict[site]
                
        sysMonHtml=pathJoin(wwwData, 'sysMon/html/')
        sysMonLog=pathJoin(wwwData, 'sysMon/status/info.log')
        sysMonReport=pathJoin(sysMonHtml, 'sysMonReport.html')         
        sysMonConfig=pathJoin(geaConf, 'sysMon/')   
        sysMonStatus=pathJoin(wwwData, 'sysMon/status/')       
             
        announcementMessage = pathJoin(geaConf, 'announce.html')
        homeMessage         = pathJoin(geaConf, 'home.html')
  
class html:
    """These are used in pyGEA.GEAHtml.py for defaults of some vars.
    """
    jsGEA=pathJoin(path.web.wwwScripts, 'jsGEA.js') 
    jsMenu=pathJoin(path.web.wwwScripts, 'sideMenu.js')
    jsSort=pathJoin(path.web.wwwScripts, 'sorttable.js')

    geaBannerDict={'MK':'GEABannerSmall.MK.gif', 'CP':'GEABannerSmall.CP.gif'}
    geaBanner=pathJoin(path.web.wwwImages, geaBannerDict[site]) 
        
    geaLogoDict={'MK':'GEALogo.MK.png', 'CP':'GEALogo.CP.png'}
    geaLogo=pathJoin(path.web.wwwImages, geaLogoDict[site]) 
    
    cssFile=pathJoin(path.web.wwwCss, 'GEAStyle.css')
      
class dataEx:
    """Data exporting/extracting related.
    """
    freqDirFile='master_index'   #Name of the freq directory file used by ArchiveEngine to archive data
    
    #Determines whether should automatically write extracted data in ascii to disk.
    autoWriteData=True  
    
    TEXTDATA=False          #Determines how to extract EPICS data; as text or as value. 

    #Used when exporting data in a spreadsheet.Determines whether to fill columns with repeated values.
    FILL=False               

    INTERPOLATE=0          #Only used when creating spreadsheets. A value of 0 implies no interpalation is done.
    
    #Used when creating meta archivers. Controls how many days should be added to the time range over which extracting the data. 
    #The days are added both at the beginning and at the end.
    metaArchDayOffset=20     
    
    #If an archive name is found in these lists, it is considered an sql archie and a sql database is used as the data source 
    #not the binary ChannelArchiver archives.
    sqlArchDict={'MK':[],   # 'MK':['nifs'],
                 'CP':[]}
    sqlArchList=sqlArchDict[site]
    
    sqlDataBaseName='sysMon'
    
    
    metaArchDict={'MK':{'all':'ag crcs ecs gis gws mcs pcs pcsact scs tcs wfs altair igrins2 gmos michelle niri bto lis nirifocus',
                         'iq':'wfs scs tcs pcs pcsact',
                         'lis':'laser',
                         'oldiq':'iq',
                                     },
                         'CP':{'all':'ag crcs ecs gis gws mcs pcs scs tcs wfs gmos gnirs gpi trecs',
                               'iq':'wfs scs tcs pcs',
                              'oldiq':'iq'
                                    }
                            }
    metaArch=metaArchDict[site]
    
#Plotting - default values.
class plot:
    """Variables related to plotting.
    """
    backend='Agg'       #Used for matplotlib plotting. Could be GD or Agg (see http://matplotlib.sourceforge.net/ for info).
    
    MAXDELTAX=2000      #MAXDELTAX==-1 means always join points NOT USED
   
    LEGEND='Inside'     #'Inside', 'Outside' or 'Off'
    
    DPI=85
    
    AA=True
    BINS=30            #For use with histograms.
    GRIDLINES=True

    LINESTYLE='steps-post'  #See matplotlib for available linestyles.
    
    PLOTMETHOD='Stepped' #'Stepped' or 'NonStepped'. This is related to LINESTYLE above.
        
    XLABEL=''
    YLABEL='' 
    PLOTTITLE=''
    XMIN=''
    XMAX=''
    YMIN=''
    YMAX=''
    YSCALE='linear'    # linear or log
    
    DISCRETEDATA=10         #When have fewer data points than this, add a 'mark' on each point
    
    #Used during data extraction.
    REDUCE=1
    HANDLEDISCON=True   #Flag; used to decide whether to check every extracted value for additional info (for example state of the archive).
    

#Admin stuff.
versionStr=version + "-" + revision
author="Peter Groszkowski (pgroszko@gemini.edu)"
organization="Gemini Observatory"
