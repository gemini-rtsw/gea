#!/usr/bin/python

from pages.geaBasePage import GeaBasePage
from GEARequest import RequestCollection, Request
from GEAHtml import StrDict, HtmlHelper, HTMLFormContEmpty
import GEAVars
import os

class SysMonitor(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        
        html=self.html

    def _processRequest(self, request, stream):
        html=self.html

        text  = '<iframe src="http://%s:8080" ' % GEAVars.siteDomain
        text += 'style="width: 100%; height: 10000; background-color: transparent; border: 0px none transparent; padding: 0px; overflow: hidden; "'
        text += 'title="sysMonII">'
        text += 'Browser must support iframe'
        text += '</iframe>\n'
        html.doc.append(text)

    def _getLocalRequests(self):
        return RequestCollection({None:Request()})   
     
           
def main(outStream=GEAVars.outStream, standAlone=False):

    SysMonitor(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
