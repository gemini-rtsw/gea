#!/usr/bin/python

"""
This file creates the java script code responsible for displaying the left side menu.
Currently  the javascript is just one function writeMenu().

"""
from GEAVars import dispatchScript, path, html, site
import os
import sys
            
depthOffset='&nbsp;&nbsp;&nbsp'   #String which each submenu is offset by.
menuFileName=os.path.join(path.fileSys.geaRoot, html.jsMenu.lstrip('/'))

class MenuItem(object):
    def __init__(self, name, link, depth=0):
        self.name=name
        self.link=link
        self.depth=depth
        
        if link is None:
            self.html=name
        else:
            if self.depth>0:
                self.html="""<a class="menuSubItem" href="%s">%s</a>""" % (link, name) 
            else:
                self.html="""<a class="menuItem" href="%s">%s</a>""" % (link, name) 
                
    def str(self):
        return self.html
        
class menusMK:
    dailyMenu=[MenuItem('Daily/Reports', None, 0),
               MenuItem('Engineering', dispatchScript+'/pages/engineeringPage?', 0),
               MenuItem('System Monitor', dispatchScript+'/pages/sysMonitorPage?', 0),
               MenuItem('Data Export', dispatchScript+'/pages/common/dataExportPage?', 0),
               MenuItem('Log Watcher', dispatchScript+'/pages/logWatcherPage?', 0),
               MenuItem('Weekly Plan', 'http://project.gemini.edu:2010/Plan/Overview.aspx', 0),      
               MenuItem('Fault Reports', dispatchScript+'/pages/remedy/frsPage?', 0),
               MenuItem('Ticket Search', dispatchScript+'/pages/remedy/frsPage?FORMAT=ticket', 1),
               MenuItem('User Search', dispatchScript+'/pages/remedy/frsPage?FORMAT=user', 1),
               MenuItem('Stats/Graphs', dispatchScript+'/pages/remedy/frsPage?FORMAT=stats', 1),
               MenuItem('Night Log', dispatchScript+'/pages/nightlog/nightLogPage?', 0),
	       MenuItem('Metrics', None, 0),
               MenuItem('EMM Report', dispatchScript+'/pages/metrics/nightLogPage?FORMAT=Report&SITE=MK', 1),
               MenuItem('Telescope', dispatchScript+'/pages/metrics/telMetricsPage?', 1),               
               MenuItem('Laser', dispatchScript+'/pages/metrics/laserMetricsPage?', 1),               
               MenuItem('GEA <i>labs</i>', '/labs', 0),               
              ]
                    
    systemsMenu=[MenuItem('Systems', None, 0),
               MenuItem('A&G', dispatchScript+'/pages/systems/agPage?', 0),
               MenuItem('Crcs', dispatchScript+'/pages/systems/crcsPage?', 0),
               MenuItem('Ecs', dispatchScript+'/pages/systems/ecsPage?', 0),
               MenuItem('Ecs Logger', dispatchScript+'/pages/systems/ecs/ecsLoggerPage?', 1),
               MenuItem('Gis', dispatchScript+'/pages/systems/gisPage?', 0),
               MenuItem('Gws (Weather)', dispatchScript+'/pages/systems/gwsPage?', 0),
               MenuItem('Laser', dispatchScript+'/pages/systems/laserPage?', 0),
               MenuItem('Bto', dispatchScript+'/pages/systems/laser/btoPage?', 1),
               MenuItem('Lis', dispatchScript+'/pages/systems/laser/lisPage?', 1),
               MenuItem('Lse', dispatchScript+'/pages/systems/laser/lsePage', 1),
               MenuItem('Mcs', dispatchScript+'/pages/systems/mcsPage?', 0),
               MenuItem('Pcs', dispatchScript+'/pages/systems/pcsPage?', 0),
               MenuItem('m1 Animation', dispatchScript+'/pages/systems/pcs/m1AnimationsPage', 1),
               MenuItem('m1 Surface', dispatchScript+'/pages/systems/pcs/m1SurfaceRTPage?', 1),
               MenuItem('Pr', dispatchScript+'/pages/systems/prPage?', 0),
               MenuItem('Scs', dispatchScript+'/pages/systems/scsPage?', 0),
               MenuItem('Tcs', dispatchScript+'/pages/systems/tcsPage?', 0),
               MenuItem('Wfs', dispatchScript+'/pages/systems/wfsPage?', 0),
              ]
    
    instrumentsMenu=[MenuItem('Instruments', None, 0),
               MenuItem('Altair', dispatchScript+'/pages/instruments/altairPage?', 0),
               MenuItem('Gmos', dispatchScript+'/pages/instruments/gmosPage?', 0),
               MenuItem('Gnirs', dispatchScript+'/pages/instruments/gnirsPage?', 0),
               MenuItem('Gpol/Gcal', dispatchScript+'/pages/instruments/gpolGcalPage?', 0),
	       MenuItem('Igrins-2', dispatchScript+'/pages/instruments/igrins2Page?', 0),
               MenuItem('Nifs', dispatchScript+'/pages/instruments/nifsPage?', 0),
               MenuItem('Niri', dispatchScript+'/pages/instruments/niriPage?', 0),
               MenuItem('Niri Focus', dispatchScript+'/pages/instruments/niri/niriFocusPage?', 1)
              ]

    compilationsMenu=[MenuItem('Compilations', None, 0),
               MenuItem('Calibrations', dispatchScript+'/pages/compilations/calPage?', 0),
               MenuItem('IQ', dispatchScript+'/pages/compilations/iqPage?', 0),
               MenuItem('Temporary', dispatchScript+'/pages/compilations/temporaryPage?', 0),
               MenuItem('Versions', dispatchScript+'/pages/compilations/versionsPage?', 0),
              ]
                
    rtMenu=[MenuItem('Real Time', None, 0),
               MenuItem('Time Probe', dispatchScript+'/pages/rt/timeProbePage?', 0),
               MenuItem('Health', dispatchScript+'/pages/rt/healthPage?',0)
              ]
          
    adminMenu=[MenuItem('Admin', None, 0),
               MenuItem('Archiver Status', 'http://geanorth.hi.gemini.edu:4800', 0)
              ]
                   
    linksMenu=[MenuItem('Links', None, 0),
               MenuItem('Queue Plan', 'http://internal.gemini.edu/science/GNqueue/qpt-plans/tonight.html', 0),
               MenuItem('Phone Numbers', 'http://internal.gemini.edu/sos/node/3204', 0),
               MenuItem('MKO Weather', 'http://internal.gemini.edu/telescope/tempdir/telMKWeather.html', 0),
               MenuItem('Gemini Home', 'http://www.gemini.edu', 0),
               MenuItem('Ops Wiki', 'http://opswiki.wikis.gemini.edu/index.php/Main_Page', 0),
               MenuItem('Swg Wiki', 'http://swg.wikis-internal.gemini.edu/index.php/Main_Page', 0),
              ]
                
    miniMenus=[dailyMenu, systemsMenu, instrumentsMenu, compilationsMenu, rtMenu, adminMenu, linksMenu]

class menusCP:
    dailyMenu=[MenuItem('Daily/Reports', None, 0),
               MenuItem('Engineering', dispatchScript+'/pages/engineeringPage?', 0), 
               MenuItem('Sys/Inst Monitor', dispatchScript+'/pages/sysMonitorPage?', 0),
               MenuItem('Data Export', dispatchScript+'/pages/common/dataExportPage?', 0),
               MenuItem('Weekly Plan', 'http://project.gemini.edu:2010/Plan/Overview.aspx', 0),
               MenuItem('Fault Reports', dispatchScript+'/pages/remedy/frsPage?', 0),
               MenuItem('Ticket Search', dispatchScript+'/pages/remedy/frsPage?FORMAT=ticket', 1),
               MenuItem('User Search', dispatchScript+'/pages/remedy/frsPage?FORMAT=user', 1),
               MenuItem('Stats/Graphs', dispatchScript+'/pages/remedy/frsPage?FORMAT=stats', 1),
               MenuItem('Night Log', dispatchScript+'/pages/nightlog/nightLogPage?', 0),
               MenuItem('Metrics', None, 0),
               MenuItem('EMM Report', dispatchScript+'/pages/metrics/nightLogPage?FORMAT=Report&SITE=MK', 1),
               MenuItem('Telescope', dispatchScript+'/pages/metrics/telMetricsPage?', 1),               
               MenuItem('Laser', dispatchScript+'/pages/metrics/laserMetricsPage?', 1),               
               MenuItem('GEA <i>labs</i>', '/labs', 0),               
              ]
                    
    systemsMenu=[MenuItem('Systems', None, 0),
               MenuItem('A&G', dispatchScript+'/pages/systems/agPage?', 0),
               MenuItem('Crcs', dispatchScript+'/pages/systems/crcsPage?', 0),
               MenuItem('Ecs', dispatchScript+'/pages/systems/ecsPage?', 0),
               MenuItem('Gis', dispatchScript+'/pages/systems/gisPage?', 0),
               MenuItem('Gws (Weather)', dispatchScript+'/pages/systems/gwsPage?', 0),
               MenuItem('Laser', dispatchScript+'/pages/systems/laserPage?', 0),
               MenuItem('Mcs', dispatchScript+'/pages/systems/mcsPage?', 0),
               MenuItem('Pcs', dispatchScript+'/pages/systems/pcsPage?', 0),
               MenuItem('Pr', dispatchScript+'/pages/systems/prPage?', 0),
               MenuItem('Bfo', dispatchScript+'/pages/systems/bfoPage?', 0),
               MenuItem('Scs', dispatchScript+'/pages/systems/scsPage?', 0),
               MenuItem('Tcs', dispatchScript+'/pages/systems/tcsPage?', 0),
               MenuItem('Wfs', dispatchScript+'/pages/systems/wfsPage?', 0),
               MenuItem('Canopus', dispatchScript+'/pages/systems/aomPage?', 0),
              ]
    
    instrumentsMenu=[MenuItem('Instruments', None, 0),
               MenuItem('Gpol/Gcal', dispatchScript+'/pages/instruments/gpolGcalPage?', 0),
               MenuItem('Gmos', dispatchScript+'/pages/instruments/gmosPage?', 0),
               MenuItem('Gsaoi', dispatchScript+'/pages/instruments/gsaoiPage?', 0),
               MenuItem('Flamingos2', dispatchScript+'/pages/instruments/flamingos2Page?', 0),
               MenuItem('Gpi', dispatchScript+'/pages/instruments/gpiPage?', 0),
              ]   
                    
    compilationsMenu=[MenuItem('Compilations', None, 0),
               MenuItem('Calibrations', dispatchScript+'/pages/compilations/calPage?', 0), 
               MenuItem('IQ', dispatchScript+'/pages/compilations/iqPage?', 0),
               MenuItem('Temporary', dispatchScript+'/pages/compilations/temporaryPage?', 0),
               MenuItem('Versions', dispatchScript+'/pages/compilations/versionsPage?', 0),
              ]
                
    rtMenu=   [MenuItem('Real Time', None, 0),
               MenuItem('Time Probe', dispatchScript+'/pages/rt/timeProbePage?', 0),
               MenuItem('Health', dispatchScript+'/pages/rt/healthPage?', 0)
              ]
          
    adminMenu=[MenuItem('Admin', None, 0),
               MenuItem('Archiver Status', 'http://geasouth.cl.gemini.edu:4800', 0)
              ]
                
    linksMenu=[MenuItem('Links', None, 0),
               MenuItem('Queue Plan', 'http://internal.gemini.edu/science/GSqueue/qpt-plans/tonight.html', 0),
               MenuItem('Phone Numbers', 'http://internal.gemini.edu/general/afg/administration/GS_Phone_List_CURRENT.pdf', 0),
               MenuItem('Gemini Home', 'http://www.gemini.edu', 0),
              ]
                
    miniMenus=[dailyMenu, systemsMenu, instrumentsMenu, compilationsMenu, rtMenu, adminMenu, linksMenu]


def createMenu(miniMenus):

    strList=[r'''<table class="menu" width="130" cellspacing="0" cellpadding="0"><tr><td>\n\
''']    
    strList+=[createMiniMenu(item) for item in miniMenus] 

    strList+=[r'''</td></tr></table>\n\
''']
        
    return ''.join(strList)
        
def createMiniMenu(menu):
    """Kind of messy with all the '\n\' characters. An alternative would be to use 
    javascript's document.write() method.
    """
    strList=[r'''<table class="miniMenu" width="130" cellspacing="0">\n\
''']            

    titleSet=0
    for menuItem in menu:
    
        #Take the first element to be the title.
        if not titleSet:
            strList+=[r'''<tr><td class="menuTitle">%s</td></tr> \n\
''' % menuItem.html]

            titleSet=1
        
        else:   #Now add the non-title elements.
            if menuItem.depth>0: 
                cssClass="menuSubItem" 
            else: 
                cssClass="menuItem"
            strList+=[r'''<tr><td class="%s">%s%s</td></tr> \n\
''' % (cssClass, depthOffset*menuItem.depth, menuItem.html)]
    
    #Have to account for the special case where only had one element; only the title.

    strList+=[r'''</table>\n\
''']
    #Testing....  need a small space between menus.
    strList+=[r'''<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
''']

    return ''.join(strList)
    
    
    
def main(argv=None):

    if site=='MK':
        miniMenus=menusMK.miniMenus
    else:
        miniMenus=menusCP.miniMenus

    scriptText="""
//File created by menuCreator.py
function writeMenu()
{
    var s='%s';
    document.write(s);
}
""" % createMenu(miniMenus)

    try:
        fileName=argv[1]  #First argument is the file name where the menu will be written to.
    except:
        fileName=menuFileName  #Use the default.

    f=file(fileName, 'w')
    f.write(scriptText)
    f.close()
        
        
        
if __name__=='__main__':
    
    main(sys.argv)

