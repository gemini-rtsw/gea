#!/usr/bin/python

from GEAHtml import HTMLTextBox,  MenuItem    
from pages.systemsBasePage import SystemsBasePage
import GEAVars

class LaserBasePage(SystemsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('Bto', GEAVars.dispatchScript+'/pages/systems/laser/btoPage?'),
              MenuItem('Lis', GEAVars.dispatchScript+'/pages/systems/laser/lisPage?'),
              MenuItem('Lse', GEAVars.dispatchScript+'/pages/systems/laser/lsePage?'),
             ]

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        if topMenuList is None:
            topMenuList=[]
            
        SystemsBasePage._assemblePage(self, topMenuList=topMenuList+[LaserBasePage.menuItemList])
        html=self.html
        
def main(outStream=GEAVars.outStream, standAlone=False):

    LaserBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
