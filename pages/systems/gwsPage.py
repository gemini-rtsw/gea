#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLTextBox, HTMLDynChanTable, HtmlHelper, HTMLTextBox3
from pages.systems.gwsBasePage import GwsBasePage
import os

gChannels="systems/gwsPage.channels"

class GwsPage(GwsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GwsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
      
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels)
        
    def _includeDailyPageLink(self):
        """Want to override the standard method here... this is because the page with daily pregenerated
        weather plots has a different name in the /pages/engineering directory than GwsPage.py.
        """
        link=HtmlHelper.createLink('See pre-generated plots', 
                os.path.join(GEAVars.path.web.pages, 'engineering', 'environmentPage'), cssClass='a1')
        self.html.doc.append(HTMLTextBox3(vars={'text':'[%s]' % link}))
        
def main(outStream=GEAVars.outStream, standAlone=False):

    GwsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
