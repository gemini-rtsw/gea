#!/usr/bin/python

from geaBasePage import GeaBasePage
import GEAVars

class HomePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        try:
            contents = file(GEAVars.path.fileSys.homeMessage, 'r').read()
        except:
            contents="""
<div class="boxed1">
<br>
<div style="text-align: center;"><h1>Welcome to the Gemini Engineering Archive.</h1> </div>
<br>
"""
        html.doc.append(contents)
        
def main(outStream=GEAVars.outStream, standAlone=False):

    HomePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)


