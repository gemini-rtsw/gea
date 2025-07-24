#!/usr/bin/python

from geaBasePage import GeaBasePage
from GEARequest import Request, RequestCollection
import GEAVars
import os

class WeeklyPlanPage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)

    def _processRequest(self, request, stream):
        """Process the request.
        """   
        top="""
<table width="100%">
<tr>
<td align="center">
<a href=/pages/weeklyPlanPage?SITE=MK><strong>Plan for MK</strong></a> &nbsp;&nbsp;&nbsp <strong>|</strong>
&nbsp;&nbsp;&nbsp; <a href=/pages/weeklyPlanPage?SITE=CP><strong>Plan for CP</strong></a>
</td>
</tr>
</table>
"""
        site=request['SITE'] or GEAVars.site

        try:
            f=file(GEAVars.path.fileSys.weeklyPlanFileNameDict[site], 'r')
            text=f.read()
        except IOError:
            text="Weekly Plan not available"
            
        self.html.doc.append(top+text)
        
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), 
        but some default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A dictionary of nameTag/request pairs should be returned. This dictionary is 
        essentially a RequestCollection() object. 
        """
        #Overwrite parents _getLocalRequests()
        return RequestCollection({None:Request({'SITE':GEAVars.site})})
   
def main(outStream=GEAVars.outStream, standAlone=False):

    WeeklyPlanPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
