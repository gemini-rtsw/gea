#!/usr/bin/python
    
from pages.rtBasePage import RtBasePage
from GEAHtml import HTMLTextBox
import GEAVars

class RtPage(RtBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        RtBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
        
        html.textBox=HTMLTextBox()
        html.doc.append(html.textBox)
        
        text="""
Welcome to the GEA RT section.

These pages provide real-time access to the epics channels from all
of Gemini's systems. 
"""
        html.textBox.vars.update(text=text)
    
def main(outStream=GEAVars.outStream, standAlone=False):

    RtPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
