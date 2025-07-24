#!/usr/bin/python

from GEAHtml import HTMLTextBox,  MenuItem    
from pages.systemsBasePage import SystemsBasePage
import GEAVars

class EcsBasePage(SystemsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('Ecs Logger', GEAVars.dispatchScript+'/pages/systems/ecs/ecsLoggerPage?'),
                            ]   

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        if topMenuList is None:
            topMenuList=[]
            
        SystemsBasePage._assemblePage(self, topMenuList=topMenuList+[EcsBasePage.menuItemList])
        html=self.html
        
def main(outStream=GEAVars.outStream, standAlone=False):

    EcsBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
