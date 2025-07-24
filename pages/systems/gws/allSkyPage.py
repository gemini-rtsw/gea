#!/usr/bin/python
import os
from GEAGeneral import util, naming
from GEAHtml import HTMLTextBox, HTMLDynListTable
from GEATime import Time       
from GEARequest import RequestCollection, Request 
import GEAVars 
from pages.systems.gwsBasePage import GwsBasePage
from pages.geaBasePage import MkPage

class AllSkyPage(GwsBasePage, MkPage):
    """Core functionality is inherited from GEAPage.BasePage
    """        
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """ 
        GwsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        text1="""All-sky camera data coming from the TMT project."""
        html.textBox1=HTMLTextBox(vars={'text':text1})
        html.doc.append(html.textBox1)
         
        html.table=HTMLDynListTable(rows=0, cols=0)
        html.doc.append(html.table)
        
        html.doc.setReload(180)   # In seconds.
        
    def _processRequest(self, request, stream):

        table=self.html.table  #So don't have to write so much.

        descList=['Blue filter','Red filter','Z Filter','Y Filter']
        fileList=[GEAVars.path.web.tmtAllSkyImageBlue, GEAVars.path.web.tmtAllSkyImageRed, GEAVars.path.web.tmtAllSkyImageZ, GEAVars.path.web.tmtAllSkyImageY]

        for f, desc in zip(fileList, descList):
            table.add_array_after_last_row(['<img alt="[ TMT all-sky camera image  (UNAVAILABLE)" src="%s">' % (f,), desc])
            table.add_array_after_last_row(['&nbsp;'])  # Throw a separating row in...
                
    def _getLocalRequests(self):
        return RequestCollection({None:Request()})                   
                
def main(outStream=GEAVars.outStream, standAlone=False):

    AllSkyPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(sys.stdout, standAlone=True)


    
    
