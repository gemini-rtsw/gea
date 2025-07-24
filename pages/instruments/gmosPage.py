#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLTextBox, HTMLDynChanTable
from pages.instrumentsBasePage import InstruementsBasePage

gChannels="instruments/gmosPage.channels"

class GmosPage(InstruementsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        InstruementsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)        
        
def main(outStream=GEAVars.outStream, standAlone=False):

    GmosPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
