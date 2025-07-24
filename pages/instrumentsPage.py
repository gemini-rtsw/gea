#!/usr/bin/python
from GEAHtml import HTMLTextBox
from pages.instrumentsBasePage import InstruementsBasePage
import GEAVars

class InstruementsPage(InstruementsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        InstruementsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
        
        self.welcomeMessage="""
Welcome to the Insruments section.
"""
        html.textbox=HTMLTextBox()    
        html.doc.append(html.textbox) 
        html.textbox.vars.update(text=self.welcomeMessage)

def main(outStream=GEAVars.outStream, standAlone=False):

    InstruementsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
