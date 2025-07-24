#!/usr/bin/python

from GEAHtml import MenuItem, HTMLDynListTable 
from GEATime import Time   
from GEARequest import Request, RequestCollection
from GEADataHandler import RealTimeDataExtractor
import GEAVars
from geaBasePage import GeaBasePage

class RtBasePage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('Time Probe', GEAVars.dispatchScript+'/pages/rt/timeProbePage?'),
                  MenuItem('Health', GEAVars.dispatchScript+'/pages/rt/healthPage?'),
                 ]

    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
            
        GeaBasePage._assemblePage(self, topMenuList=[RtBasePage.menuItemList]+topMenuList)
        html=self.html
                
        html.table=HTMLDynListTable(rows=0, cols=0)
        html.doc.append(html.table)
        
        self.html=html
        
    def _processRequest(self, request, stream):
        """Process the request.
        
        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which 
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function assemblePage().
        """
        table=self.html.table  #So don't have to write so much.

        #Add the heading.
        table.setCellColSpan(0,0, 2) 
        table.setCellcontents(0,0, '<h3>Real time data probed at %s</h3>' % Time().string1, {'class':'heading'})
            
        for item in RealTimeDataExtractor(request).extract():
            for name, val in zip(item.x, item.y):
                table.add_array_after_last_row([name, val])
            
def main(outStream=GEAVars.outStream, standAlone=False):

    RtBasePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
