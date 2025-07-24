#!/usr/bin/python

from GEAHtml import HTMLTextBox,  MenuItem    
from geaBasePage import GeaBasePage
import GEAVars

class HelpBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[  MenuItem('Browsers', GEAVars.dispatchScript+'/pages/helpPage?PAGE=geaDoc.html#Browsers', 0),
                    MenuItem('Getting Started', GEAVars.dispatchScript+'/pages/helpPage?PAGE=geaDoc.html#Getting_Started'),
                  ]
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
            
        GeaBasePage._assemblePage(self, topMenuList=[HelpBasePage.menuItemList]+topMenuList)
        html=self.html

        html.textbox=HTMLTextBox()    
        html.doc.append(html.textbox) 
        
def main(outStream=GEAVars.outStream, standAlone=False):

    HelpBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
