#!/usr/bin/python

import GEAVars
from GEAHtml import HTMLTextBox, HTMLDynChanTable
from pages.systems.laserBasePage import LaserBasePage

gChannels="systems/laser/btoPage.channels"

class BtoPage(LaserBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        LaserBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        html.channels=HTMLDynChanTable(dataStr=gChannels)
        html.doc.append(html.channels.return_html())
        
def main(outStream=GEAVars.outStream, standAlone=False):

    BtoPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(sys.stdout, standAlone=True)
