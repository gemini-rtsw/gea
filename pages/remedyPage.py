#!/usr/bin/python

from GEAHtml import HTMLTextBox       
from pages.remedyBasePage import RemedyBasePage
import GEAVars

class RemedyPage(RemedyBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        RemedyBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
        
        message="""
Welcome to the GEA Remedy Pages.

These pages provide interfaces to the NightLog and FRS.
"""
        html.textbox=HTMLTextBox(vars={'text':message})    
        html.doc.append(html.textbox) 
        
def main(outStream=GEAVars.outStream, standAlone=False):

    RemedyPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
