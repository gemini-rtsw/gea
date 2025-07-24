#!/usr/bin/python

from pages.geaBasePage import GeaBasePage
from GEARequest import RequestCollection, Request
from GEAHtml import StrDict, HtmlHelper, HTMLFormContEmpty
import GEAVars
import os
from watcher.watchershow import dumpWatcherConfig

class logWatcherPage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        
        html=self.html

    def _processRequest(self, request, stream):
        html = self.html

        dWC = dumpWatcherConfig()
        dWC.indent = 1
        dWC.altmargin = 4

        text = dWC.dumpconfig()

        html.doc.append(text)

    def _getLocalRequests(self):
        return RequestCollection({None:Request()})   
     
           
def main(outStream=GEAVars.outStream, standAlone=False):

    logWatcherPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
