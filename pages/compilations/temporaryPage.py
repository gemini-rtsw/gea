#!/usr/bin/python
        
from pages.compilationsBasePage import CompilationsBasePage
from GEAHtml import HTMLDynChanTable
import GEAVars

gChannels="compilations/temporaryPage.channels"

class TemporaryPage(CompilationsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        CompilationsBasePage._assemblePage(self, topMenuList=topMenuList)
        
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
        
def main(outStream=GEAVars.outStream, standAlone=False):

    TemporaryPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
