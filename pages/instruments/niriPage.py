#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLDynChanTable, HTMLDynListTable
from pages.instruments.niriBasePage import NiriBasePage
from pages.geaBasePage import MkPage

gChannels="./instruments/niriPage.channels"

class NiriPage(NiriBasePage, MkPage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """          
        NiriBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
        
    def _getNiriVacuum(self):
        try:
            str=file(GEAVars.path.fileSys.niriVacFileNameDict['MK'], 'r').read()            
        except:
            str='Niri vacuum data not available...'
        
        return str

def main(outStream=GEAVars.outStream, standAlone=False):

    NiriPage(outStream, standAlone).run()
        
if  __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
