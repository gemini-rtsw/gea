#!/usr/bin/python

import os
from GEAHtml import  HTMLDocContWithSideMenu, HTMLHorizontalMenu, HTMLCont, HTMLSep , \
                                    HTMLHeaderLinks, HTMLHeaderLinks2, HtmlHelper, HTMLTextBox3
from GEAPage import BasePage
from GEAGeneral import util
from GEAException import SiteException
import GEAVars

class MkPage(object):
    pass
    
class CpPage(object):
    pass

class GeaBasePage(BasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    
    This page adds the header, side menu, footer and the announcement. 
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        html=util.Holder()    #At the end will do self.html=html. But declaring it as a local variable saves from typing self everywhere.
        html.sep=HTMLSep()
                
        if not self.standAlone:                            
            html.doc=HTMLDocContWithSideMenu()

            pagetitle='GEA[%s]-' % GEAVars.site+self.__class__.__name__
            html.doc.vars.update(pagetitle=pagetitle,
                                 mainfile=self.calledName,
                                 headerinfo=self._getHeaderInfo(),
                                 headerlinks=self._createHeaderLinks()
                                 )
                                 
            topMenuList=topMenuList or [[""]]   # If topMenuList is None, make it an empty menu
            html.topMenu=HTMLHorizontalMenu(topMenuList)
            html.doc.header.append(html.topMenu)

            #Adds an item named 'announcement' to the html dictionary if needed. See BasePage._readAnnouncement() for more information.
            self._addAnnouncement(htmlHolder=html)  
        else:
            html.doc=HTMLCont()
            
        self.html=html
        
        self._includeDailyPageLink()
        
    def _includeDailyPageLink(self):
        """Lets see if this works... want to automatically include a link at a top of the page to 
        the daily pregenrated plots if they exist. Lets assume that we are looking for a module 
        in pages.engineering with the same name as the page currently running.
        """
        if 'engineering' in self.calledName:
            #The current page already comes from engineering - hence don't want to link to itself.
            return 
        
        modName=self.__class__.__name__[0].lower()+self.__class__.__name__[1:]
        fileName=os.path.join(GEAVars.path.fileSys.pages, 'engineering', modName+'.py')
        
        if os.path.isfile(fileName):
            #module=util.deepImport(pages.engineering.modName)
            link=HtmlHelper.createLink('See pre-generated plots', 
                                       os.path.join(GEAVars.path.web.pages, 
                                                    'engineering', 
                                                     modName),
                                       cssClass='a1')
            self.html.doc.append(HTMLTextBox3(vars={'text':'[%s]' % link}))
            
    def initPage(self):
        """For any checks that may need to be done before start assembling html.
        """
        #Make sure we should be processing the request - may be attempting to look at a page on the wrong server.
        #For example altairPage should only be processed in the north.
        #Will raise an exception on Error
        self._siteCheck()
        
    def _siteCheck(self):
        if isinstance(self, MkPage) and GEAVars.site!='MK':
            raise SiteException('The requested page is only meant to be accessible from %s' % GEAVars.siteDomainDict['MK'])
        if isinstance(self, CpPage) and GEAVars.site!='CP':
            raise SiteException('The requested page is only meant to be accessible from %s' % GEAVars.siteDomainDict['CP'])
        
    def _createHeaderLinks(self):
        """These depend on whether this current page is only meant to be shown at one of the sites (ex. atlairPage only in the north)
        """
        if isinstance(self, MkPage) or isinstance(self, CpPage):
            return HTMLHeaderLinks(vars={'mainfile':self.calledName})
        else:
            return HTMLHeaderLinks2(vars={'mainfile':self.calledName+self.queryString})
        
    def _processInfo(self, info):
        """Determines how much information should be shown, based on whether in debug mode
        or not.
        """
        if GEAVars.debug:
            return info
        
        #Temporary; clean up Remedy error related to running out of licences.
        if  info.find('ARGetListField failed')>-1:
            return "GEA licences to log into Remedy are all being used. Please try again later."
        if  info.find('error: VerifyUser failed')>-1:
            return "Remedy access temporarily unavailable."
        
        #For some known error do not display the whole traceback, only the last line.
        for errStr in ('DataHandlerException', 'PlotException', 'DataExportException',
                           'IOError', 'RuntimeError', 'ValueError'):
            #Usually will have a whole traceback. Only display the text after 'SomeException:", which
            #shows only the user readable information.
            if errStr=='PlotException' and errStr.find('Min and Max for the y-axis are both')>-1:
                info="Exported data has some unplottable values (possibly 'inf' or 'nan'). You may want to look at a spreadsheet."
        
            index=info.rfind(errStr)
            if index>-1:
                #Accounting for ': ' after the name of the exception.
                info=info[index+len(errStr)+2:]
    
        return info
              

def main(outStream=GEAVars.outStream, standAlone=False):

    GeaBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
