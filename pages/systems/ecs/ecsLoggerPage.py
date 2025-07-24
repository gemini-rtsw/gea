#!/usr/bin/python

import os
import glob
import GEAVars
from GEARequest import Request
from GEAHtml import HTMLTextBox
from pages.systems.ecsBasePage import EcsBasePage

class EcsLoggerPage(EcsBasePage):
    """Core functionality is inherited from GEAPage.BasePage.
    """
    def _assemblePage(self, topMenuList=None):

        """Populates the self.html dictionary with objects from GEAHtml.
        """  
        EcsBasePage._assemblePage(self, topMenuList=topMenuList)

    def _getLocalRequests(self):
        nameTag = None
        return {nameTag:Request(request={'year':'error.log'}, nameTag=None) }

    def _processRequest(self, request, stream):

        fn = 'ecs/logger/' + request.get('year', None)

        command='ps ax | grep "ecsLogger.csh" | grep -v -P "grep|nedit"'

        try:
            text=os.popen(command, 'r').read()
            if text:
                msg = '*** Ecs Logger is <strong>RUNNING</strong> ***'
            else:
                msg = '*** Ecs Logger is <strong>NOT RUNNING</strong> ***'
                
        except IOError:
            msg = 'Information on status of the logger is unavailable'
                
        try:
            f = file(os.path.join(GEAVars.path.fileSys.geaData, fn), 'r')
            text=f.read()
        except IOError:
            text='Cannot open file containing the log...'
            
        msg  = '<p>' + msg + '</p>'
        msg += '<p> Historical ecs logs: ' 
        for fn in glob.glob(os.path.join(GEAVars.path.fileSys.geaData, 'ecs/logger/20[0-9][0-9]')):
            y = fn.split("/")[-1]
            msg += '<a href="/pages/systems/ecs/ecsLoggerPage?year=%s">%s</a>&nbsp;' % (y, y)
        msg += '<a href="/pages/systems/ecs/ecsLoggerPage?">current</a>' 
        msg += '</p>'

        # '<a href="geanorth">gea</a>'

            # f=file(os.path.join(GEAVars.path.fileSys.geaData, 'ecs/logger/error.log'), 'r')
        self.html.doc.append(msg)

        self.html.doc.append(HTMLTextBox(vars={'text':text}))
        
def main(outStream=None, standAlone=False):

    EcsLoggerPage(outStream, standAlone).run()

if __name__=='__main__':

    main(GEAVars.outStream, standAlone=True)

