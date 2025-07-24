#!/usr/bin/python

import os

from GEAGeneral import util, naming
from GEATime import Time
from GEAHtml import HTMLFormCont, HTMLOptionsSurfacePlot, HtmlHelper, HTMLImage       
import GEAVars
from specialized.m1Surface import PlotToMake, Algorithms, makePlot
from pages.systems.pcsBasePage import PcsBasePage

class M1SurfaceRTPage(PcsBasePage):
    """Core functionality is inherited from GEAPage.BasePage
    """     
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """ 
        PcsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        #Main form
        html.form=HTMLFormCont() #Form container.
        #cgifile is of the form:   /run/dispatch.gea/some_directories/file_without_py_extenstion
        html.form.vars.update(cgifile=self.calledName)
        html.doc.append(html.form)    
    
        html.options=HTMLOptionsSurfacePlot()
        html.options.vars.update(plottitle='',
                                 min='',
                                 max='',
                                 source='Pneumatic/Hydraulic'
                                )
        html.form.append(html.options)

    def _processRequest(self, request, stream):

        source=request.get('SOURCE', '')
        
        if source=='Pneumatic':
            names=['axPnuLC']
        elif source=='Hydraulic':
            names=['axHydLC']
        elif source=='Pneumatic/Hydraulic':
            names=['axHydLC', 'axPnuLC']
        elif source=='PnuError':
            names=['axPnuError']
        else:
            names=[]
            
        for name in names:
            
            image, imageLarge=self._generatePlot(name)
                    
            self.html[name]=HTMLImage()
            self.html[name].vars.update(imagefilename=image, largeimagefilename=imageLarge)
            
            #Add at the beggining of the page.
            self.html.form.insert(0, self.html[name])
            
        #Want to update the options widget with latest choices
        self._setWidgetVars(self.html.options, request, [])
            
    def _generatePlot(self, name):
    
        #Generate the names of the images. 
        randName=naming.genName()
        
        image="%s%s%s" % (name, randName, '.png')
        imageLarge="%s%s%s" % (name, randName, '.Large.png')
    
        if name=='axPnuError':
            #Special case.
            plotsToMake=[PlotToMake((os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/axPnuDmd.channels'),
                                     os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/axPnuLC.channels')), 
                                    image, 
                                    imageLarge,
                                    name,
                                    dir=GEAVars.path.fileSys.wwwData,
                                    algorithm=Algorithms.diff12
                                    ),
                        ]
            
        else:
            plotsToMake=[PlotToMake((os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/%s.channels' % name),), 
                                    image, 
                                    imageLarge,
                                    name,
                                    dir=GEAVars.path.fileSys.wwwData,
                                    ),
                        ]

        for item in plotsToMake:
            item.title="%s Generated: %s" % (item.title, Time().string1)
            makePlot(item)
        
        return (os.path.join(GEAVars.path.web.wwwData, image), 
                os.path.join(GEAVars.path.web.wwwData, imageLarge), 
                )
                
def main(outStream=GEAVars.outStream, standAlone=False):

    M1SurfaceRTPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
