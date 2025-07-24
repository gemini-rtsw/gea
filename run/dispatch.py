#!/usr/bin/python
# -*- encoding: utf-8 -*-

import os
import sys
import GEAVars
from GEAGeneral import util
# reload(sys)
# sys.setdefaultencoding('UTF8')

def main():

    sys.tracebacklimit = 99
         
    try:
        pathInfo=GEAVars.environ['PATH_INFO']
 
        #All GEA pages will have an url of the form:   <domain>/pages/<some_page>
        if pathInfo.startswith('/pages'):
        
            #First cleanup the path (making sure only have single '/', and 
            #then prepare for importing.
            modName=os.path.normpath(pathInfo).lstrip('/').replace('/', '.')
                        
            page = util.deepImport(modName)

        else:
            #... should be updated.... 
            raise RunTimeError('Page does not exist')

        page.main()
        
    except Exception, e:
        #Hope to never be here... 
        print "Content-Type:   text/html\n\n"
        print "Error: ", e

if __name__=='__main__':

    main()
    
