#!/usr/bin/python

from GEAHtml import HTMLTextBox, HTMLDynListTable   
from pages.rtBasePage import RtBasePage
from GEARequest import Request, RequestCollection
import GEAVars
import os

class TimeProbePage(RtBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        RtBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        #Prototype.. ideally want all this in _processRequest()
        command='GEMINI_TOP=/gemsoft /gemsoft/bin/timeProbe'
        try:
            lines=os.popen(command, 'r').readlines()
        except IOError:
            text='Error extracting time information'
            
        #html.doc.append(HTMLTextBox(vars={'text':lines}))
        html.doc.append(self._text2Html(lines))
        
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A dictionary of nameTag/request pairs (nameTag, request) should be returned. This dictionary is 
        essentially a RequestCollection() object. 
        """
        #Overwrite parents _getLocalRequests()
        return {}
        
    def _text2Html(self, lines):
        """Create pretty html from the raw text (lines)
        """
        if not lines: 
            return ''
        
        self.html.table=HTMLDynListTable(tableAttrs={'width':"100%",  'class':"tableList"})
        
        table=self.html.table

        #Start with the header.... lines[0] is just \n
        table.add_array_after_last_row(lines[1].split('|'), {'class':'heading'})        
        
        for line in lines[2:]:
            if line.startswith('\n') or line.startswith('--') or line.startswith('NOTE') or line.startswith('SINCE'):
                continue
                
            table.add_array_after_last_row(line.split())   
                            
        return table
        
   
def main(outStream=GEAVars.outStream, standAlone=False):

    TimeProbePage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
