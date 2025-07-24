#!/usr/bin/python

import GEAVars
from GEAHtml import MenuItem
from pages.instrumentsBasePage import InstruementsBasePage
from pages.geaBasePage import MkPage

class NiriBasePage(InstruementsBasePage, MkPage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('Niri Focus', GEAVars.dispatchScript+'/pages/instruments/niri/niriFocusPage?'),
             ]
    
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        if topMenuList is None:
            topMenuList=[]
            
        InstruementsBasePage._assemblePage(self, topMenuList=topMenuList+[NiriBasePage.menuItemList])
        html=self.html

def main(outStream=GEAVars.outStream, standAlone=False):

    NiriBasePage(outStream, standAlone).run()
        
if  __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
