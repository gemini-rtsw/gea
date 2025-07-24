#!/usr/bin/python

from GEAHtml import  MenuItem    
from pages.systemsBasePage import SystemsBasePage
import GEAVars

class BfoBasePage(SystemsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """

    menuItemList=None

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        if topMenuList is None:
            topMenuList=[]
        
        if BfoBasePage.menuItemList:
            topMenuList+=[BfoBasePage.menuItemList]
        
        SystemsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
def main(outStream=GEAVars.outStream, standAlone=False):

    BfoBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
