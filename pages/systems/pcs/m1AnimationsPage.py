#!/usr/bin/python

import os
import re
import glob
from GEAGeneral import util
from GEATime import Time
from GEAHtml import HTMLTextBox, HTMLDynListTable,  HtmlHelper
from GEARequest import Request, RequestCollection        
import GEAVars
from pages.systems.pcsBasePage import PcsBasePage

class M1AnimationsPage(PcsBasePage):
    """Core functionality is inherited from GEAPage.BasePage
    """        
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """ 
        PcsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        message="""
Please note that currently the animations cannot be played on some computers.
This is mainly due to the different codecs that users have installed. Updating to 
the latest movie/media player might help. 
Within the next little while we hope to provide a guide explaining how to install
the necessary codes. 
"""
        message2="""
Animations from the past two weeks are currently being created.
Please come back later.
"""
        html.textbox=HTMLTextBox(vars={'text':message})    
        html.doc.append(html.textbox) 
        
        html.table=HTMLDynListTable()
                                
        html.doc.append(html.table)

    def _processRequest(self, request, stream):
        """Process the request.
        
        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which 
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function _assemblePage().
        """ 
        
        self._fetchAnimations(request, stream)
        
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self
.run()), but some
        default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A dictionary (or a RequestCollection) of nameTag/request pairs (nameTag, request) should be retur
ned. 
        """
        #Being very explicit, so that it is clear what is being done.
        
        #Do not need a nameTag,  because do not have multiple objects (widgets) of the same type on this page.
        nameTag=None            
        request={'FORMAT':'list'} 
                
        r=Request(request=request, nameTag=nameTag)

        return RequestCollection({nameTag:r})

    def _fetchAnimations(self, request, stream):
        
        table=self.html.table  #So don't have to write so much.
        
        heading=['axHydLC', 'axPnuLC', 'axPnuError']
        
        #Add the heading.
        table.add_array_after_last_row(["Night of: "]+heading, {'class':'heading'})
        
        dateDirList=glob.glob(os.path.join(GEAVars.path.fileSys.m1SurfacePlots, '*'))

        dateDirList.sort()
        dateDirList.reverse()
        
        for dir in dateDirList :
    
            dateDirName=os.path.split(dir)[-1]
            
            lastRow=table.getmaxRow()
            lastCol=table.getmaxCol()
    
            columns=[[],[],[]]
            
            for item, col in zip(heading, columns):
                files=glob.glob(os.path.join(dir, item, '*.mpeg')) + glob.glob(os.path.join(dir, item, '*.mp4'))
                
                #Only want the files names.. no path.
                files=map(lambda x: os.path.split(x)[-1], files)

                for f in files:
                    #Strip the name a little, and only show the date part
                    name=re.sub('.*Animation', '', re.sub('\.(mpeg|mp4)$', '', f))
                    link=HtmlHelper.createLink(name,os.path.join(GEAVars.path.web.m1SurfacePlots, 
                                                                dateDirName, 
                                                                item, 
                                                                f))
                    col.append(link)
                                                        
            lastRow=table.getmaxRow()
                
            table.setCellcontents(lastRow+1,0, 
                                  dateDirName,
                                  {'class':'heading'})
                
            for index, col in zip(range(1, len(columns)+1), columns):
                table.add_array_to_col(lastRow+1, index, col)
                
                
def main(outStream=GEAVars.outStream, standAlone=False):

    M1AnimationsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)

#Optimizing using psyco
if GEAVars.usePsyco:
    import psyco
    psyco.bind(M1AnimationsPage, rec=3)
    
