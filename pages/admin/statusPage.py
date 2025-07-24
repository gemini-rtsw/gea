#!/usr/bin/python

import os
import re
from GEARequest import Request,RequestCollection
from GEAHtml import  HtmlHelper
from pages.adminBasePage import AdminBasePage
import GEAVars

class StatusPage(AdminBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self,topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        AdminBasePage._assemblePage(self,topMenuList=topMenuList)
        html=self.html  
        table=html.table
        
    def _getLocalRequests(self):
        nameTag=None            #Do not need a nameTag,  because do not have multiple objects (widgets) of the same type on this page.
        r=Request(request={'VIEW':'status',},nameTag=nameTag)
        return RequestCollection({nameTag:r})
        
    def _processRequest(self,request,stream):

        self.__getattribute__('_view_'+request.get('VIEW','status'))(request=request,stream=stream) 
        
    def _view_status(self,request,stream,**options):
        
        table=self.html.table
        
        regExp=re.compile(r"^System (\w*):(.*)$")  
        command=os.path.join(GEAVars.path.fileSys.bin,'archstatus all 2>&1')

        """ FIXME:

            This code formerly took the output of "archstatus all" (above). archstatus
            hasn't been ported yet, so this function doesn't work.

        table.add_array_after_last_row(['Archiver','Status'],{'align':'center','class':'heading'})
 
        try:
            lines=os.popen(command,'r').readlines()
        except IOError:
            lines=[]
            
        for line in lines:
            #Each line of the form: 
            #System ecs:            UP - 43/52 (connected/total)
            result=regExp.search(line)
            table.add_array_after_last_row([result.group(1),result.group(2)])
        """
        table.add_array_after_last_row(["Sorry, status page down."])
            
    def _view_archLinks(self,request,stream,**options):
        
        table=self.html.table
        
        try:
            f=file(GEAVars.path.fileSys.portConf,'r')
        except IOError:
            stream.write('Cannot open port configuration file %s' % GEAVars.path.fileSys.portConf)
            return 
        
        table.add_array_after_last_row(['Archiver','Port'],{'align':'center','class':'heading'})
 
        for line in f.readlines():
            if line.startswith('#') or line.startswith(' '):
                continue
            
            arch,port=line.split()
            if int(port)>0:
                table.add_array_after_last_row([arch,HtmlHelper.createLink(port,
                                                GEAVars.siteDomain+':%s' % port)])
    
def main(outStream=GEAVars.outStream,standAlone=False):

    StatusPage(outStream,standAlone).run()
        
if __name__=='__main__':

    main(sys.stdout,standAlone=True)


    
    
