#!/usr/bin/python

import os
from GEATime import Time
from GEAHtml import HTMLHorizontalMenu, MenuItem , HTMLTextBox2, HTMLDynChanTableWithPlots, HtmlHelper      
from geaBasePage import GeaBasePage
from GEARequest import Request, RequestCollection
from GEAGeneral import naming
import GEAVars

class EngineeringBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    if GEAVars.site=='MK':
        menuItemList=[
                      MenuItem('Environment', GEAVars.dispatchScript+'/pages/engineering/environmentPage?'),
                      MenuItem('Telescope', GEAVars.dispatchScript+'/pages/engineering/telescopePage?'),
                      MenuItem('|', None),
                      MenuItem('IQ', GEAVars.dispatchScript+'/pages/engineering/iqPage?'),
                      MenuItem('|', None),
                      MenuItem('Altair', GEAVars.dispatchScript+'/pages/engineering/altairPage?'),
                      MenuItem('Gmos', GEAVars.dispatchScript+'/pages/engineering/gmosPage?'),
                      MenuItem('Niri', GEAVars.dispatchScript+'/pages/engineering/niriPage?'),
                      MenuItem('Nifs', GEAVars.dispatchScript+'/pages/engineering/nifsPage?'),
                      MenuItem('Gnirs', GEAVars.dispatchScript+'/pages/engineering/gnirsPage?'),
                      ]  
    else:
        menuItemList=[
                      MenuItem('Environment', GEAVars.dispatchScript+'/pages/engineering/environmentPage?'),
                      MenuItem('Seeing Monitor', GEAVars.dispatchScript+'/pages/engineering/seeingMonitorPage?'),
                      MenuItem('Telescope', GEAVars.dispatchScript+'/pages/engineering/telescopePage?'),
                      MenuItem('|', None),
                      MenuItem('IQ', GEAVars.dispatchScript+'/pages/engineering/iqPage?'),
                    ]  

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
            
        GeaBasePage._assemblePage(self, topMenuList=[EngineeringBasePage.menuItemList]+topMenuList)
        html=self.html
                
        html.textBox=HTMLTextBox2(vars={'text':''})    
        html.doc.append(html.textBox) 
        
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A dictionary (or a RequestCollection) of nameTag/request pairs (nameTag, request) should be returned. 
        """
        #For now return a collection with one (empty) request.
        return RequestCollection({'None':{}})

    def _processRequest(self, request, stream):
        """Process the request.
        """ 
        html=self.html
        
        dateStr=request.get('DATESTR', '') 
        # AWE: problem here, no dateStr returned, but getLatestDailyDir doesn't work
        #if dateStr:
        #     dataDir=naming.getDailyDir(dateStr=dateStr, fromWeb=True)
        #else:
        #     dataDir=naming.getLatestDailyDir(fromWeb=True)
        dataDir=naming.getDailyDir(dateStr=dateStr, fromWeb=True)
        
        #IMPORTANT.. have to add the root of gea as to check of dir existance as 'dataDir' is relative to the apache root.
        fileSysDataDir=GEAVars.path.fileSys.geaRoot+dataDir
    
        if os.path.isdir(fileSysDataDir):
            #Need a pretty time string formatting.
            t=Time()
            try:
                t.string4=os.path.basename(fileSysDataDir)
                tBefore, tAfter=Time(t.seconds-Time.secPerDay), Time(t.seconds+Time.secPerDay)
                html.textBox.vars['text']+='\n%s<strong>&lt;&lt;     %s     &gt;&gt;</strong>%s\n' % ( 
                                                    HtmlHelper.createLink("%s" % tBefore.string9,
                                                                            self.calledName,
                                                                            DATESTR=tBefore.string4), 
                                                    t.string8, 
                                                    HtmlHelper.createLink("%s" % tAfter.string9,
                                                                            self.calledName,
                                                                            DATESTR=tAfter.string4))
            except ValueError:
                html.textBox.vars['text']+='\nCannot convert directory name to date.\n'
        
            html.dataTable=HTMLDynChanTableWithPlots(dataStr=self.channels, dataDir=dataDir)
            html.doc.append(html.dataTable)
        
        else:
            if request.get('LATEST', '').lower()=='true':
                #Already showed the link to probe for the latest data (see else below) but the dir could not be found; there must be 
                #no data to display.
                html.textBox.vars['text']+="""\nNo data is available.\n"""
            else:
                html.textBox.vars['text']+="""\nCannot find the requested data. 
Please click %s to get the latest that's available.\n""" %  (HtmlHelper.createLink("here", self.calledName, LATEST='True'),)

def main(outStream=GEAVars.outStream, standAlone=False):
    EngineeringBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
