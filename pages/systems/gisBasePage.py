#!/usr/bin/python

from GEAHtml import HTMLTextBox,  HTMLHorizontalMenu, MenuItem    
from pages.systemsBasePage import SystemsBasePage
import GEAVars

class GisBasePage(SystemsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """  
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html

def main(outStream=GEAVars.outStream, standAlone=False):

    SystemsBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
