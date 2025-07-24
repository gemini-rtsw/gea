#!/usr/bin/python

import GEAVars
from pages.instrumentsBasePage import InstruementsBasePage
from GEAHtml import HTMLDynChanTable
from pages.geaBasePage import CpPage

gChannels="./instruments/niciPage.channels"

class NiciPage(InstruementsBasePage, CpPage):
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

    NiciPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)

