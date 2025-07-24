#!/usr/bin/python

import os
from GEAGeneral import naming, util
from GEATime import Time
from GEAHtml import HTMLFormCont, HTMLOptionsDiq, HTMLTimeSelectorDiq, HTMLPlot, HTMLTextBox, MenuItem
from GEAData import Data
from GEADataHandler import RemedyDataExtractor
from GEAPlot import MatHistPlot              
import GEAVars
from pages.remedyBasePage import RemedyBasePage

class Constants:
    #Constants... used in normalization. Values in meters.
    lambdaNot=0.55e-6
    rNot=0.17
    strRep=r'$\lambda_0=0.55\mu m \hspace{0.5} r_0=17 cm$'    #String representation of the constants which will be added to the plots.
    
class DiqPage(RemedyBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    menuItemList=[MenuItem('IQ (Epics)', GEAVars.dispatchScript+'/pages/compilations/iqPage?'),
                            MenuItem('Delivered IQ (Remedy)', GEAVars.dispatchScript+'/pages/remedy/diqPage?'),  
                            ]
    
    def _assemblePage(self, topMenuList=None):
        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        topMenuList=topMenuList or []
        RemedyBasePage._assemblePage(self,  topMenuList=[DiqPage.menuItemList]+topMenuList)
        
        html=self.html
        
        text="""The plot is obtained using the data from the Remedy (NightLog) database.
Data points, which are not properly formatted will generate a warning.
"""
        html.textBox=HTMLTextBox(vars={'text':text})
        html.doc.append(html.textBox)
        
        html.form=HTMLFormCont() #Form container.
        #cgifile is of the form:   /run/dispatch.gea/some_directories/file_without_py_extenstion
        html.form.vars.update(cgifile=self.calledName)
        html.doc.append(html.form)    
    
        #Time selector widget.
        html.timeSelector=HTMLTimeSelectorDiq()
        html.timeSelector.vars.update(util.combineDict(Time(self.genTime.seconds-Time.secPerWeek).toStartTimeDict(),
                                                            self.genTime.toEndTimeDict()))  #Update the time vars (startday, startmonthr, etc..)
        html.form.append(html.timeSelector)
                
        html.options=HTMLOptionsDiq()
        html.options.vars.update(plottitle='',
                                               xlabel='Delivered IQ',
                                               xmin='',
                                               xmax='',
                                               ylabel='Counts',                               
                                               ymin='',
                                               ymax='',
                                               showmean='Yes',
                                               legend=GEAVars.plot.LEGEND,
                                               dpi=GEAVars.plot.DPI,
                                               bins='30',
                                               format='Plot',
                                               site='MK/CP'
                                                )
        html.form.append(html.options)    
            
    def _processRequest(self, request, stream):
        """Process the request.
        
        All requests can be subdivided into diffent groups (containing single plots, multiple, no plots.. etc).
        This function process each request depending on what type it is. The type is determined on which 
        'HTML widget' is used and what kind of options (shown in vars and tagged vars) it supports. To see the
        widgets in the current page see the function _assemblePage().
        
        In this case only dealing with one widget, hence the situation is simple.
        """   
        
        try:
            self._generatePlot(request, stream)                                    
        finally:
            #Want to make sure we update the html widget with old values. 
            for widget in (self.html.timeSelector, self.html.options):
                self._setWidgetVars(widget, request, [])
                    
    def _extractRemedyData(self, request, stream, dataFileName=None):
        """Extract, and manipulate data from Remedy.
        
        Right now keeping time of each seeing measurement... but for histograms there is no need.
        
        """

        #Need to know where to write our data to.
        if dataFileName is None:
            raise RuntimeError('No file name proveded; need to know where to write data to.')

        #By default plot normalized seeing data.
        format=request.get('FORMAT', 'Normalized')
        
        varKeys=['Wavelength', 'LocalTime', 'Airmass', 'FWHM','Notes']
        results=[]
        rKeys=['UT Date', 'Telescope']
        
        for i in (5,6,7,8,9):
            rKeys+=map(lambda x: x+str(i), varKeys) 
        
        rQuery=""
        extractor=RemedyDataExtractor(rQuery="" , request=request,  rKeys=rKeys, dBase='NL')
         
        timeData=[]
        seeingData=[]
        dataToWrite=[]
                       
        #We need to write data to a file. This could be done automatically when calling extractor.extract()
        #but we want to be selective in what we write, as well as need to be able to write 
        #normalized data which was not available at the time of extraction().              
        
        if format=='Normalized':
            rowFormat="%-20s\t%-3s\t%-18s\t%-14s\t%-14s\t%-14s\t%-14s"
            header=rowFormat % ('UT Time', 'Site', 'Normalized Seeing', 'FWHM', 'Wavelength', 'AirMass', 'Note')                    
        else: #format=='Raw'     
            rowFormat="%-20s\t%-3s\t%-14s\t%-14s\t%-14s\t%-14s"
            header=rowFormat % ('UT Time', 'Site', 'FWHM', 'Wavelength', 'AirMass', 'Note')                
            
        #Remember how many values we had to disregard.
        badValueCount=0     
                    
        for item in extractor.extract(dataFileName=None):
            
            #With the same request we could have data from both sites. To get the local time properly converted to the 
            #UT time, we need to know which site we're looking at.
            telSite={'North':'MK','South':'CP'}.get(item['Telescope'], 'MK')                     
                        
            for i in (5,6,7,8,9):
                              
                strNum=str(i)
                 
                if format=='Normalized':
                
                    lam=item.get('Wavelength'+strNum, None)        
                    theta=item.get('FWHM'+strNum, None)
                    airMass=item.get('Airmass'+strNum, None)
                    locTime=item.get('LocalTime'+strNum, None)
                    utDate=item.get('UT Date', None)
                    
                    if lam is None or theta is None or airMass is None or utDate is None or locTime is None:
                        #Skip these values
                        continue
                    
                    #A note does not have to exist, for us to still use the other values for plotting.
                    note=item.get('Notes'+strNum, '')                    
         
                    #Account for poor formatting.
                    theta=theta.replace('"', '').replace('~', '').replace('>', '')
                    lam=lam.replace('"', '')
                    airMass=airMass.replace(',', '.')
                    
                    #Could do all this in one go using Numeric....
                    try:
                        seeingData.append(float(theta)*((float(lam)*1e-6/(Constants.lambdaNot))**0.2)*(float(airMass)**(-0.6)))
                        timeData.append(self._utDate2Time(utDate, locTime, telSite).string1)     
                        #notes.append(note)                                
                        dataToWrite.append(rowFormat % (timeData[-1],telSite,seeingData[-1], theta, lam, airMass, note))
                    except  ZeroDivisionError:
                        pass
                    except (ValueError,), e:
                        badValueCount+=1                    
                    
                elif format=='Raw':
                    theta=item.get('FWHM'+strNum, None)
                    utDate=item.get('UT Date', None)
                    locTime=item.get('LocalTime'+strNum, None)                    
                                        
                    if theta is None or utDate is None or locTime is None:
                        continue
                    
                    #These guys are not necessery to show the value.
                    lam=item.get('Wavelength'+strNum, '')        
                    airMass=item.get('Airmass'+strNum, '')
                    note=item.get('Notes'+strNum, '')                    
                    
                    #Account for poor formatting.
                    theta=theta.replace('"', '').replace('~', '').replace('>', '')
                    
                    #Could do all this in one go using Numeric....
                    try:
                        seeingData.append(float(theta))
                        timeData.append(self._utDate2Time(utDate, locTime, telSite))
                        dataToWrite.append(rowFormat % (timeData[-1], telSite, theta, lam, airMass, note))
                    except  ZeroDivisionError:
                        pass
                    except (ValueError,), e:
                        badValueCount+=1

                else:
                    raise RunTimeException("Unsupported seeing data format '%s'. Expecting 'Raw' or 'Normalized'.\n" % format)
                                                                                                      
        if badValueCount>0:
            stream.write('Found <strong>%d</strong> badly formated values - <strong>disregarding them</strong>.\n' % badValueCount)                
                                      
        dataToWrite.sort()
        dataToWrite.reverse()
        
        f=file(os.path.join(GEAVars.path.fileSys.wwwData, dataFileName), "w")     
        f.write(header+'\n')      
        f.write('\n'.join(dataToWrite)) 
        f.close()
                                    
        #Return a tuple: ([Data], startTime, endTime)     
        return ([Data([timeData, seeingData], name="Remedy Delivered Image Quality\n[%s - %s]" % (format, request['SITE']))],
                extractor.startTime,
                extractor.endTime)
            
    def _utDate2Time(self, utDate, locTime, telSite):
        """Temporary helper function... have do deal with the badly formatted database.
        """
        #utDate here is going to be 00:00 UT of the night we're observing on.
        t=Time(seconds=utDate, site=None)  #Site==None implies UT time.
        
        #To account for the for local time given in locTime, switch to the current site time. Note that 
        #this is actually broken for CP times; we're not accounting for daylight saving times. 

        # Sucks too much to be true. Nukit and fix later. TCC

        # t.seconds-=GEAVars.siteTimeOffsetDict[telSite]      

        if locTime.find(':')>-1:
            #h:mm or hh:mm 
            locTime=locTime.split(':')
            hour=locTime[0]
            minute=locTime[1]
        elif locTime.find('.')>-1:
            #h.mm or hh.mm 
            locTime=locTime.split('.')
            hour=locTime[0]
            minute=locTime[1]
        elif len(locTime)==4:
            #hhmm
            hour=locTime[0:2]
            minute=locTime[2:-1]
        else:
            #hmm
            hour=locTime[0]
            minute=locTime[1:-1]        
            
        #If the hour is >17 then we're likely talking about last night. 
        #Lets role back the day so we can make an adjustement. If we don't do this and adjust hours to say 19, 
        #we'd skip to the next night.
        if int(hour)>17:
            t.seconds-=Time.secPerDay
            
        #Now set hour/minute
        t.hour=hour
        t.minute=minute

        #Now lets go back to the ut time.
        # ReHack for above TCC
        # t.seconds+=GEAVars.siteTimeOffsetDict[telSite]    
        
        return t
            
    def _generatePlot(self, request, stream):
        """Generate a plot. 
        """
        #Generate equevalent names for the data and image. They will be random generated, but have the same random 'stamp' and 
        #different prefix and suffix.
        imFileName, dataFileName=naming.genImDataNames()
        
        #Extract data
        (dataList, startTime, endTime)=self._extractRemedyData(request, stream, dataFileName=dataFileName)

        #Create a plot.
        p=MatHistPlot(dataList=dataList, fStream=stream, options=request)        
    
        p.plot()
                
        #Lets calculate the mean of the data.
        if request.get('SHOWMEAN','Yes')=='Yes':
            try:
                from matplotlib import numerix
                m=numerix.array(dataList[0].y).mean()
                p.axvline(m, linewidth=2, color='r')      
                
                ##p.text(0.69,0.80, r'$mean=%4f$' % float(m), transform=)
                p.text(0.67,0.82, r'$mean=%4f$' % float(m))

            except:
                pass                                                         
                
        #If the user did not specify a title, generate one based on the start/end time stamps.
        #If 'PLOTTITLE' is in the request then it will was added automatically during ploting (since request was passed as options).
        if not request.get('PLOTTITLE', None):
            p.title('Delivered IQ for %s - %s' % (startTime.string7, endTime.string7))

        if request.get('FORMAT','')=='Normalized':
            p.text(0.70,0.86, Constants.strRep)
        
        fName=request.get('SAVEIMAGE','') or imFileName
        
        #When writing the image, need to specify the tmp directory with respect to the file system path.
        p.write(os.path.join(GEAVars.path.fileSys.wwwData, fName))
                                              
        #Now that generated a plot, lets update self.html with a simple HTMLPlot object which will just show the image.
        self.html.plotImage=HTMLPlot()
        self.html.plotImage.vars.update(imagefilename=os.path.join(GEAVars.path.web.wwwData, fName),
                                        datafilename=os.path.join(GEAVars.path.web.wwwData, dataFileName))
        
        #Add at the beggining of the page (after the menu)
        self.html.doc.insert(0, self.html.plotImage)
        
    def _data2String(dataList, heading):
        """Helper. Used to get the raw data formatted into a table when written.        
        """
        heading=['UT Date', 'Airmass5', 'Airmass6', 'Airmass7', 'Airmass8', 'Airmass9', 'FWHM5', 
            'FWHM6', 'FWHM7', 'FWHM8', 'FWHM9', 'LocalTime5', 'LocalTime6', 'LocalTime7', 
            'LocalTime8', 'LocalTime9', 'Wavelength5', 'Wavelength6', 'Wavelength7', 
            'Wavelength8', 'Wavelength9']
        
        strList=["""
Raw data table. Total records: %d
------------------------------------------
""" % len(dataList)]

        format="%14s\t" * len(heading)
        
        strList.append(format % tuple(heading))
        
        strList+=map(lambda d: format % tuple([d[name] for name in heading]), dataList)
            
        return '\n'.join(strList)
        
    _data2String=staticmethod(_data2String)
        
          
def main(outStream=GEAVars.outStream, standAlone=False):

    DiqPage(outStream, standAlone).run()

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)
        
if GEAVars.usePsyco:
    import psyco
    psyco.bind(DiqPage, rec=2)
