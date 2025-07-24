#!/usr/bin/python
        
from pages.instrumentsBasePage import InstruementsBasePage
from pages.geaBasePage import MkPage
from GEAHtml import HTMLDynChanTable
import GEAVars


gChannels="instruments/igrins2Page.channels"

class Igrins2Page(InstruementsBasePage, MkPage):
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

    Igrins2Page(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
