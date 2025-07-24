#!/usr/bin/python
        
from pages.compilationsBasePage import CompilationsBasePage
from GEAHtml import HTMLDynChanTable, MenuItem, HTMLTextBox
import GEAVars

gChannels="compilations/iqPage.channels"

class IqPage(CompilationsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('IQ (Epics)', GEAVars.dispatchScript+'/pages/compilations/iqPage?'),
                  MenuItem('Delivered IQ (Remedy)', GEAVars.dispatchScript+'/pages/remedy/diqPage?'),  
                ]
    
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
        CompilationsBasePage._assemblePage(self,  topMenuList=[IqPage.menuItemList]+topMenuList)
        
        html=self.html
     
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
             
def main(outStream=GEAVars.outStream, standAlone=False):

    IqPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
