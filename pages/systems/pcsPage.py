#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLTextBox, HTMLDynChanTable
from pages.systems.pcsBasePage import PcsBasePage

gChannels="systems/pcsPage.channels"

class PcsPage(PcsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        PcsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
        
def main(outStream=GEAVars.outStream, standAlone=False):

    PcsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
