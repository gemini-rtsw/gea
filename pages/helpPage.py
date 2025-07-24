#!/usr/bin/python

import os
from pages.helpBasePage import HelpBasePage
import GEAVars

class HelpPage(HelpBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.UDF:
        """  
        HelpBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html  
        
        self.html.textbox.vars.update(text="")
        
    def _processRequest(self, request, stream):
        """Process the request.
        
        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which 
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function assemblePage().
        """
        pageName=request.get('PAGE', '')
        
        if pageName:
            pageName=pageName.lstrip('/')
            i=pageName.find('?')
            if i>-1:
                pageName=pageName[:i]
            try:
                page=file(os.path.join(GEAVars.path.fileSys.doc, pageName)).read()
            except IOError:
                page="""
You have requested help for the page '%s'. 

We are in the process of setting up guides which will make the GEA 
navigation easier. In the mean while please use the top menu to browse
currently available help pages or write to me <a href="mailto:pgroszko@gemini.edu">here</a>.
""" % pageName
            
            self.html.textbox.vars.update(text=page)
           

def main(outStream=GEAVars.outStream, standAlone=False):

    HelpPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
