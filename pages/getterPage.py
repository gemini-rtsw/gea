#!/usr/bin/python

#Needs to be updated.
import urllib
import os
    
from GEAHtml import HTMLError            
from geaBasePage import GeaBasePage
import GEAVars

class GetterPage(GeaBasePage):
    """Core functionality is inherited from GEAPage.BasePage
    
    Fetches non GEA pages from either the current system or other servers. 
    It is called by the dispatch script (by default /run/dispatch.gea).
    """        
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """          
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        try:        
            #Pages could be local, or on remote servers
            if self.pathInfo.startswith('/http:'):   #Page on the remote server.
            
                #Need to strip the leading '/' and add another '/' after the colin; since apache got rid of it automatically.
                link=pathInfo.replace('/http:/', 'http://', 1)+self.queryString

                #page=urllib.urlopen(urllib.quote(link)).read()
                page=urllib.urlopen(link).read()
                   
                self.html.doc.append(page)
    
            elif self.pathInfo.startswith('/pages/html'):
            
                pass
##~                 #Need to strip the leading '/'.
##~                 link=''.join([GEAVars.siteDomain, '/pyGEA', self.pathInfo[1:], self.queryString])
##~                 page=urllib.urlopen(link).read()
##~                 self.html.doc.append(page)
                
            else:
                raise NameError("Page does not exist")
            
        except (NameError, IOError), e:   
            self.html.error=HTMLError()
            self.html.error.vars.update(text='Page requested cannot be displayed.\nThe following error occured:\n'+str(e))
            self.html.doc.append(self.html.error)
                
def main(outStream=GEAVars.outStream, standAlone=True):

    GetterPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(sys.stdout, standAlone=True)
