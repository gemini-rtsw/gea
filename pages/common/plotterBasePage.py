#!/usr/bin/python

from GEAHtml import HTMLCont, HTMLHorizontalMenu, MenuItem
from pages.geaBasePage import GeaBasePage
import GEAVars

class PlotterBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)

def main(outStream=GEAVars.outStream, standAlone=False):

    PlotterBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
