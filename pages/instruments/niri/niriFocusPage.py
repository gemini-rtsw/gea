#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLDynChanTable
from pages.instruments.niriBasePage import NiriBasePage
from pages.geaBasePage import MkPage

gChannels="instruments/niri/niriFocusPage.channels"

class NiriFocusPage(NiriBasePage, MkPage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        NiriBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)

def main(outStream=GEAVars.outStream, standAlone=False):

    NiriFocusPage(outStream, standAlone).run()
        
if  __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
