#!/usr/bin/python
import os
from GEAGeneral import util, naming
from GEAHtml import HTMLTextBox 
from GEATime import Time        
import GEAVars
from pages.systems.gwsBasePage import GwsBasePage
from pages.geaBasePage import MkPage

class TmtPage(GwsBasePage, MkPage):
    """Core functionality is inherited from GEAPage.BasePage
    """        
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """ 
        GwsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        text1="""Seeing Data coming from TMT project. 
Empty plots represent nights when data was not available. """
        html.textBox1=HTMLTextBox(vars={'text':text1})
        html.doc.append(html.textBox1)
         
        imagesHtml="""
<pre>
<img alt="[ TMT CN2 Plot NOT AVAILABLE ]" src="%s">
<img alt="[ TMT Dimm Plot NOT AVAILABLE ]" src="%s">
<img alt="[ TMT Mass Plot NOT AVAILABLE ]" src="%s">
</pre>
""" % (GEAVars.path.web.tmtCn2Plot, GEAVars.path.web.tmtDimmPlot, GEAVars.path.web.tmtMassPlot)
          
        html.doc.append(imagesHtml)
                
        html.doc.setReload(900)   # In seconds.
                
def main(outStream=GEAVars.outStream, standAlone=False):

    TmtPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(sys.stdout, standAlone=True)


    
    
