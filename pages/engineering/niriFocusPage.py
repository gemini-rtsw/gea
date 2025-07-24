#!/usr/bin/python

import os  
from pages.engineeringBasePage import EngineeringBasePage
import GEAVars
from pages.geaBasePage import MkPage

gChannels="engineering/niriFocusPage.channels"

class NiriFocusPage(EngineeringBasePage, MkPage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        self.channels=gChannels
        
        EngineeringBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
                                        
def main(outStream=GEAVars.outStream, standAlone=False):

    NiriFocusPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
