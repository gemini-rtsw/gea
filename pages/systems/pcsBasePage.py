#!/usr/bin/python

from GEAHtml import HTMLTextBox,  MenuItem    
from pages.systemsBasePage import SystemsBasePage
import GEAVars

class PcsBasePage(SystemsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('m1 Animations', GEAVars.dispatchScript+'/pages/systems/pcs/m1AnimationsPage?'),
              MenuItem('m1 Surface', GEAVars.dispatchScript+'/pages/systems/pcs/m1SurfaceRTPage?'),
             ]

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        if topMenuList is None:
            topMenuList=[]
            
        SystemsBasePage._assemblePage(self, topMenuList=topMenuList+[PcsBasePage.menuItemList])
        html=self.html
        
def main(outStream=GEAVars.outStream, standAlone=False):

    PcsBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
