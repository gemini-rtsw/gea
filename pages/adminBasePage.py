#!/usr/bin/python

from GEAHtml import HTMLCont, HTMLDynListTable, MenuItem
from geaBasePage import GeaBasePage
import GEAVars

class AdminBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('Status', GEAVars.dispatchScript+'/pages/admin/statusPage?'),
               ]
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
            
        GeaBasePage._assemblePage(self, topMenuList=[AdminBasePage.menuItemList]+topMenuList)
        html=self.html
        
        html.table=HTMLDynListTable(rows=0, cols=0)
        html.doc.append(html.table) 
        
def main(outStream=GEAVars.outStream, standAlone=False):

    AdminBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
