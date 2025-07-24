#!/usr/bin/python

from GEAHtml import *       
from pages.rtBasePage import RtBasePage
from GEARequest import Request, RequestCollection
import GEAVars

class HealthPage(RtBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        RtBasePage._assemblePage(self, topMenuList=topMenuList)
    
        html=self.html
            
        #See _getLocalRequests() to see the requests that are processed even when QUERY_STRING is empty.
    
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A dictionary of nameTag/request pairs (nameTag, request) should be returned. This dictionary is 
        essentially a RequestCollection() object. 
        """
        channels="""
m2:health.VAL
ws:cfHealth.VAL
ec:health.VAL 
gis:mon:other:heartbeati.VAL
"""
        
        #Returning a RequestCollection object with one Request inside.
        request=Request(request={'CHANNELS':channels}, nameTag=None)
        
        return RequestCollection(reqColDict={request.nameTag:request})
   
def main(outStream=GEAVars.outStream, standAlone=False):

    HealthPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
