#!/usr/bin/python

import sys, os
    
from GEAGeneral import util, printExcept
from GEAException import RequestException
from GEATime import Time
from GEAValidator import BooleanValidator
from GEARequest import RequestCollection, Request
from GEAHtml import HTMLDocCont, HTMLErrorPage, HTMLAnnouncement, HTMLNotice, HtmlHelper
from GEAPage import BasePage
import GEAVars
    
class BasePlainPage(BasePage):
    """Abstract base class. All plain-text GEA pages should inherit from it. 
    """

    def run(self):
    
        self.body = "Content-Type: text/plain\n\n"

        try:
        
            requests = RequestCollection()

            if requests.isEmpty():

                localRequests=self._getLocalRequests()

                if localRequests is not None:
                    requests.update(localRequests)
       
            self._assemblePage()
        
            if len(requests) == 0:
                self._processRequest({})

            for request in requests.values():

                self._processRequest(request)

            self.outStream.write(self.body)
        
        except:  
            self.outStream.write("Content-Type: text/plain\n\n")
            self.outStream.write("Error\n%s" % printExcept())
