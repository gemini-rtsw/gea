#!/usr/bin/python

import urllib
from GEAHtml import MenuItem, HTMLTextBox, HtmlHelper, HTMLCont      
from geaBasePage import GeaBasePage
from GEAGeneral import util
import GEAVars


class RemedyBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
            
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
               
def main(outStream=GEAVars.outStream, standAlone=False):

    RemedyBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
