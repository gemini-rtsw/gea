#!/usr/bin/python
        
from pages.compilationsBasePage import CompilationsBasePage
from GEAHtml import HTMLDynChanTable, MenuItem, HTMLTextBox
import GEAVars

gChannels="compilations/versionsPage.channels"

class VersionsPage(CompilationsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
        CompilationsBasePage._assemblePage(self,  topMenuList=topMenuList)
        
        html=self.html
        
        html.doc.append('<strong>This is a first draft of this page. Lots more to come...</strong>')        
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
             
def main(outStream=GEAVars.outStream, standAlone=False):

    VersionsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
