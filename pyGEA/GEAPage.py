#!/usr/bin/python

import sys, os, StringIO
    
from GEAGeneral import util, printExcept
from GEAException import RequestException, PlotException
from GEATime import Time
from GEAValidator import BooleanValidator
from GEARequest import RequestCollection, Request
from GEAHtml import HTMLDocCont, HTMLErrorPage, HTMLAnnouncement, HTMLNotice, HtmlHelper
import GEAVars
    
class BasePage(object):
    """Abstract base class. All GEA pages should inherit from it. 
    """
    def __init__(self, outStream=None, standAlone=True):
        """
        Attributes:
            html - This is a dictionary with handles to GEAHtml objects which make up the page. Each page should
            have at least a 'doc' handle so that something can be printed. If html also contains an 'infoitem' handle, 
            then all the error/eception information will be put there into a var 'info'. See self.run() and GEAHTML module
            for more information. 
    
        Arguements:
            outStream - Where the final webpage will be written to.
            standAlone - Determines whether to encapsulate the resulting page in all the 
            header and footer content (and things such as menus...)
        """
        self.outStream=outStream or GEAVars.outStream
            
        self.queryString=self._getQueryString()     #Either an empty string or QUERY_STRING with '?' prepended to it.
        
        #Need to distinguish between pathInfo and calledName. calledName includes the path of the dispatch script. 
        #These are used when calling non GEA pages; either for the old archivers, or pages from different servers all together.
        self.pathInfo=GEAVars.environ.get('PATH_INFO','')
        self.calledName=GEAVars.environ.get('SCRIPT_NAME', '')+self.pathInfo
   
        #This might be usefull if want to combine multiple pages together. Inside self._assemblePage(), one could use different 
        #HTML containers (from GEAHtml module) to hold the widgets depending whether a page is a standAlone or not. 
        #This might be used to for example eliminate multiple headers being added.
        self.standAlone=standAlone 

        self.serverAddr=GEAVars.environ.get('SERVER_ADDR',None)
        
        #Used when processing requests remotly on another host.
        
        #Perhaps the cookies should be part of a GEARequest... (something to think about)
        from Cookie import SimpleCookie
        self.cookie=SimpleCookie(os.environ.get('HTTP_COOKIE',None))
                    
        self.genTime=Time()
    
        self.html=util.Holder()  #This will store all the html handles to the objects from GEAHtml.  self._assemblePage() will populate this object.
    
    def _assemblePage(self):
        """Each inherited class should define this method. It will populate the self.html dictionary with
        objects from GEAHtml.
        """
        self.html.doc=HTMLDocCont()   #Default; empty page container
        self.html.doc.vars.update(pagetitle='GEAPage empty container.')
        
    def _processRequest(self, request, stream):
        """Each inherited class can define this method if some processing is required.
        """
        pass
        
    def _getLocalRequests(self):
        """This is called from self.run() when QUERY_STRING is empty  (RequestException generated in self.run()), but some
        default data should still be processed. Each child can override this method if there is 
        a need for a default requests. See self.run() how this is used.
        
        A RequestCollection of nameTag/request pairs (nameTag, request) should be returned. 
        """
        return None
        
    def _processException(self, stream, request=None): # html=None):

        if sys.exc_info()[0] == PlotException:
            stream.write(sys.exc_value)
            return

        import datetime

        stream.write("GEA has experienced an internal fault. Please file a fault report noting the time and date as %s.\n" % datetime.datetime.now().__str__())

        exch = open("/gemsoft/var/log/gea/exception.log", "a")
        exch.write("\nException raised at " + datetime.datetime.now().__str__() + "\n")
        exch.write(printExcept())
        exch.close()
        
    
    def _getQueryString(self):
        """If GEAVars.environ['QUERY_STRING'] is defined, its value is returned with a 
        question mark prepended. An empty string is returned otherwise.
        """
        try:
            queryString='?'+GEAVars.environ['QUERY_STRING']
        except:
            queryString=''
        
        return queryString
        
    def _getHeaderInfo(self):
        """Want this to be consistent between pages.
        """
        return self.__class__.__name__
               
    def _readAnnouncement(self, fileName=None):
        """Read an announcement from a file (default file name set in GEAVars). This is used to display 
        important announcements dynamically. Each child can override this method to extend its functionality;
        perhaps to include multiple announcements.
        
        Arguments:
            fileName - This is the file that is read to obtain the announcement. If not given, a default
            set in GEAVars is used instead.
        """
        if fileName is None:
            fileName=GEAVars.path.fileSys.announcementMessage
            
        try:
            content=file(fileName, 'r').read()
        except IOError:
            content=''

        return content
        
    def _addAnnouncement(self, htmlHolder=None, fileName=None, documentHandleName='doc', widgetHandleName='announcement'):
        """Adds an announcement section to the page.
        
        See self._readAnnouncement() defined in pyGEA.GEAPage for more information. 
        
        Arguments:
            htmlHolder - If given, the announcement box will be appended to it. If not given, it
                will be appened to self.html.
            fileName - The name of the file containing the announcement. GEAVars.announcementMessage
                contains the default.
            documentHandleName - The name of handle to an GEAHtml object inside self.html dictionary 
                that the announcement should be appened to. This is almost always 'doc' and there should 
                be no need to change it.
        """

        announce=self._readAnnouncement(fileName)

        if announce:           
    
            if htmlHolder is None:
                html=self.html
            else:
                html=htmlHolder

            html[widgetHandleName]=HTMLAnnouncement(vars={'announcement':announce})
            html[documentHandleName].header.append(html[widgetHandleName])
        
    def _setWidgetVars(sefl, widget, varsDict, notUpdateList, **otherVars):
        """Update widget.vars with all values from varsDict and then otherVars as long as the variable
        being updated is not in the notUpdateList.
        
        There are a few special cases that have to be taken into account. 
        For example when dealing with checkboxes and radio buttons, when the item (say a checkbox) is 
        unchecked, the QUERY_STRING string contains no corresponding key/value pair. Therefore the name
        corresponding to the chekcbox in question has a value None. For the checkbox to look unchecked
        in the widget, it needs a '' (empty string). Therefore we convert None to '' for all the 
        radio/checkboxes.
        
        """
        tmpDict={}
        
        for d in [varsDict, otherVars]:
            
            for key, value in d.iteritems():
                
                #All vars in a widget are lowercase
                key=key.lower()
                
                #Have to deal with chekcboxes as a special case. When they are unchecked QUERY_STRING does not contaian 
                #a corresponding key/value pair, but we need value be equal to an empty string  to have the checkbos unchecked.
                if key in ['gridlines', 'rateofchange'] and value is None:
                    value=''
                    
                if value is None or key in notUpdateList:
                    continue
                        
                #Only update vars wich the widget has.
                if widget.vars.has_key(key):
                    tmpDict[key]=value
        
        widget.vars.update(tmpDict)
            
    def run(self):
        """Assembles the page. Processes the requests if any. Updates the page contents based on the results. 
        Prints the page to self.outStream.
        """
        #Temporary...  Currently have some third party code that on error writes to stdout... therefore need to make sure that have a 
        #header written first so that the page can still be interpreted by the browsers.
        self.outStream.write("""Content-Type: text/html\n\n""")
    
        mainInfoStream=StringIO.StringIO()
        
        try:
        
            #This is a recent addition; may be used for any processing that should be made before assembling the html.
            #For example checking whether the page should be processed at a given site. 
            self.initPage()
        
            #Parse the query string.    Do this before we assemble the page, so that we can have a page be stand alone, 
            #based on the STANDALONE key/value from the queryString.
            requests=RequestCollection()

            #except RequestException:
            #    requests=RequestCollection(reqColDict={})  #Empty collection.
                
            if requests.isEmpty():
                #The QUERY_STRING was empty but check if self._getLocalRequests() returns non-empty data.
                localRequests=self._getLocalRequests()
                if localRequests is not None:
                    requests.update(localRequests)
       
            #It only makes sense to have one STANDALONE queryString variable per page, but since may have
            #many identical widgets, could have a case where have multiple STANDALONE keys of the form:
            #STANDALONE_widget1, STANDALONE_widget2, etc.... that were generated automatically.
            #In that case, go throgh the request collection, and use the first one we find; if none are found, leave the defaults. 
            for request in requests.values():
                standAlone=request.get('STANDALONE', None)
                if standAlone is not None:
                    #Update... 
                    self.standAlone=BooleanValidator(valueOnError=False, errorPreText='Validating %s... ' % 'STANDALONE',
                                                                        stream=mainInfoStream).validate(standAlone)
                    break
            
            self._assemblePage()
        
            for request in requests.values():
                #Check whether to show debug information (for example tracebacks on errors)
                GEAVars.debug=BooleanValidator(valueOnError=GEAVars.debug, errorPreText='Validating %s... ' % 'DEBUG',
                                               stream=mainInfoStream).validate(request.get('DEBUG',GEAVars.debug))
                #Revise...
                #...to store errors/info for each request. The html widget associated with this request (ie. with same nameTag)
                #is then updated with this information.  If self.html has no widget with the request name, the information is
                #appended to the header of html.doc.
                infoStream=StringIO.StringIO()
                
                try:
                    self._processRequest(request, infoStream)
                except:
                    self._processException(infoStream)

                info=self._processInfo(infoStream.getvalue())
                    
                if info:  #Check if there is something to display.
                    if request.nameTag:
                        #Dealing with a request wich has been tagged - this request therefore corresponds
                        #to a particular widget with a name defined in 'nameTag' variable.
                        #Add the infoStream information to the header of this particular widget.
                        self.html[request.nameTag].header.append(HTMLNotice(vars={'text':info}))
                    else:
                        #The request has not been tagged; add the infoStream information to the beginning of the container
                        #document.
                        self.html.doc.insert(0, HTMLNotice(vars={'text':info}))
                        
            if mainInfoStream.getvalue(): 
                self.html.doc.insert(0, HTMLNotice(vars={'text':mainInfoStream.getvalue()}))
        
            self.html.doc.write(self.outStream)
        
        except:  
            #If get in here, the exceptions which were generated inside were not handeled and/or were too critical  
            #to have a resolution; generate an error HTML page.  
            if not self.standAlone:
                errorPage=HTMLErrorPage(vars={'errormsg':str(sys.exc_value),
                   'traceback':printExcept(),
                   'otherinfo':'',
                   'environment': util.dictStr(GEAVars.environ)})
                errorPage.write(self.outStream)
            else:  
                self.outStream.write("<br><br><pre><div class=error1>%s</div></pre><br>" % printExcept())
        
       
    def _processInfo(self, info):
        """ info contains any text/exception stuff that was accumulated during execution. 
        A child might want to everwrite this method to reformat them.
        """
        return info
 
def main(outStream=None, standAlone=True):

    class testPage(BasePage):
        pass

    page=testPage(outStream, standAlone)
    page.run()
                
if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)

