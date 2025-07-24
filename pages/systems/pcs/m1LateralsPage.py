#!/usr/bin/python

import os

from GEAGeneral import util, naming
from GEATime import Time
from GEAHtml import HTMLFormCont, HTMLOptionsLateralsPlot, HtmlHelper, HTMLImage, HTMLTextBox      
import GEAVars
from specialized.m1Lateral import PlotToMake, Algorithms, makePlot
from pages.systems.pcsBasePage import PcsBasePage

class M1LateralsPage(PcsBasePage):
    """Core functionality is inherited from GEAPage.BasePage
    """     
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """ 
        PcsBasePage._assemblePage(self, topMenuList=topMenuList)
        html=self.html
        
        text1="""Pick the type of 'view' you want, and click on 'Update'.
You can click on the image to get a bigger version. If it seems distorted or the values are not very readable,
then your browser automatically rescaled the image. This feature can be turned off in the options. """
        html.textBox1=HTMLTextBox(vars={'text':text1})
        html.doc.append(html.textBox1)
        
        #Main form
        html.form=HTMLFormCont() #Form container.
        #cgifile is of the form:   /run/dispatch.gea/some_directories/file_without_py_extenstion
        html.form.vars.update(cgifile=self.calledName)
        html.doc.append(html.form)    
    
        html.options=HTMLOptionsLateralsPlot()
        html.options.vars.update(plottitle='', view='Symmetric')
        html.form.append(html.options)
        
        text2="""
The principle of action of the lateral actuators is such that there are 2
mirror symmetries in the distribution graph:
1. across the elevation (horizontal) axis, with the same amplitude but a sign
change, i.e.#45 = - #46... #31 = - #60...#30 = - #1...#16 = - #15.... etc.
2. across the vertical axis, with the same amplitude and sign, i.e. #31 =
#30... #45 = #16...#46 = #15...#60 = #1.... etc

Using the 'Symmetric' view, one can therefore directly compare the boxes in any
given column (i.e. 1st box of the 1st line, 1st box of the 2nd line, 1st box
of 3rd line, 1st box of 4th line): they should all have the same amplitude but
line 1 and 2 will be positive, whereas line 3 and 4 will be negative.

Below is an image showing the orientation of the actuators around the primary mirror.
"""
        html.textBox2=HTMLTextBox(vars={'text':text2})
        html.doc.append(html.textBox2)

        imageHtml="""
<img src="/pages/systems/pcs/lateralModel.png">

"""
        html.doc.append(imageHtml)

    def _processRequest(self, request, stream):
        """Following protocol from m1SurfaceRTPage.processRequest()
        """
        view=request.get('VIEW', '')
        
        name='lateralLC'
        if 1:    #source=='Laterals'     - for now only have source=Laterals..
   
            image, imageLarge=self._generatePlot(name, view)
                    
            self.html[name]=HTMLImage()
            self.html[name].vars.update(imagefilename=image, largeimagefilename=imageLarge)
            
            #Add at the beggining of the page.
            self.html.form.insert(0, self.html[name])
            
        #Want to update the options widget with latest choices
        self._setWidgetVars(self.html.options, request, [])
            
    def _generatePlot(self, name, view='DM_Screen'):
    
        #Generate the names of the images. 
        randName=naming.genName()
        
        image="%s%s%s" % (name, randName, '.png')
        imageLarge="%s%s%s" % (name, randName, '.Large.png')
    
        plotsToMake=[PlotToMake((os.path.join(GEAVars.path.fileSys.geaRoot, 'pyGEA/specialized/%s.channels' % name),), 
                                image, 
                                imageLarge,
                                name,
                                dir=GEAVars.path.fileSys.wwwData,
                                view=view
                                )]

        for item in plotsToMake:
            item.title="%s Generated: %s" % (item.title, Time().string1)
            makePlot(item)
        
        return (os.path.join(GEAVars.path.web.wwwData, image), 
                os.path.join(GEAVars.path.web.wwwData, imageLarge), 
                )
                
def main(outStream=GEAVars.outStream, standAlone=False):

    M1LateralsPage(outStream, standAlone).run()
        
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
