#!/usr/bin/python

from pages.adminBasePage import AdminBasePage
import GEAVars

class AdminPage(AdminBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        AdminBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
        
        message="""
Welcome to the GEA Admin Page.
"""
        html.textbox.vars.update(text=message)
    
def main(outStream=GEAVars.outStream, standAlone=False):

    AdminPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
