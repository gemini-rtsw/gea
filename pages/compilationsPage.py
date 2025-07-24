#!/usr/bin/python

from GEAHtml import HTMLTextBox
from pages.compilationsBasePage import CompliationsBasePage
import GEAVars

class CompliationsPage(CompliationsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        CompliationsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
        
        self.welcomeMessage="""
Welcome to the Compilations section.
"""
        html.textbox=HTMLTextBox()    
        html.doc.append(html.textbox) 
        html.textbox.vars.update(text=self.welcomeMessage)

def main(outStream=GEAVars.outStream, standAlone=False):

    CompliationsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
