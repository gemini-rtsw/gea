#!/usr/bin/python

from geaBasePage import GeaBasePage
import GEAVars

class InstruementsBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
def main(outStream=GEAVars.outStream, standAlone=False):

    InstrumentsBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
