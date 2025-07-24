#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLDynChanTable
from pages.systems.prBasePage import PrBasePage

gChannels="systems/prPage.channels"

class PrPage(PrBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        PrBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
        
def main(outStream=GEAVars.outStream, standAlone=False):

    PrPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
