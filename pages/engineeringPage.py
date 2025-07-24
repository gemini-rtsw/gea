#!/usr/bin/python

from GEAHtml import HTMLTextBox      
from pages.engineeringBasePage import EngineeringBasePage
import GEAVars

gChannels=''

class EngineeringPage(EngineeringBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        self.channels=gChannels
        EngineeringBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
            
    def _processRequest(self, request, stream):
        html=self.html
        html.message=HTMLTextBox(vars={'text':"""
Welcome to the Daily Engineering Page. 
In the future this page will contain a summary of the systems which need engineering attention
based on the last nights performance. For now, please click on categories above to browse 
pregenerated plots."""})
        html.doc.append(html.message) 

def main(outStream=GEAVars.outStream, standAlone=False):

    EngineeringPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
