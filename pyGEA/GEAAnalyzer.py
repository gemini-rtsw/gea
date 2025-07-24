#!/usr/bin/env python

"""GEAAnalyzer.py

Contains all the common Analyzer classes. 
Ones that are specific to particular data (and/or system) are located the system's page module.
"""
import os
import sys
import math
# from Numeric import * 
from GEAData import Data
import GEAVars

class Stats(dict):
    """Helper class.
    
    Each entry should be of the form:
    key:<list>
    
    NOTE:.. should just use Numeric here.
    """    
    def sum(self, *keys):
        sum=0
        for key in keys:
            for item in self[key]:
                sum+=item
        return sum
       
    def numEntries(self, *keys):
        num=0
        for key in keys:
            num+=len(self[key])
        return num
       
    def average(self, *keys):
        return self.mean(*keys)
       
    def mean(self, *keys):
        return float(self.sum(*keys))/float(self.numEntries(*keys))
        
class BaseAnalyzer(object):
    """All analyzer classes should inherit from it.
    """
    def __init__(self, dataList=None, dataFileName=None, **kwargs):
        
        if dataList is None:
            self.dataList=[Data([])]
        else:
            self.dataList=dataList
    
        self.dataFileName=dataFileName
    
        self.__dict__.update(kwargs)
    
    def _process(self, data):
        """Each subclass should inherit override this mthod.
        """
        raise NotImplemented("process() not implemented.")
            
    def process(self):
        """Returns analyzed dataList
        """
        self.processedList=map(self._process, self.dataList)
        self.writeData(self.processedList)
        
        return self.processedList
        
    def writeData(self, dataList=None):
        
        if not self.dataFileName:
            return False
                   
        if dataList is None:
            dataList=self.dataList    
        
        f=file(os.path.join(GEAVars.path.fileSys.wwwData, self.dataFileName), "w")        
        map(lambda item: f.write('%s\n' % item), dataList) 

        return True
        
class RateOfChangeAnalyzer(BaseAnalyzer):
     
    def _process(self, data):
        """Right now do not account for discontinuities in the data... should update... 
        """
        x=data.x
        y=data.y
        
        #Special cases
        if len(x)==0 and len(y)==0:
            der=[] 
        elif len(x)==1 and len(y)==1:
            der=[0]             # Not quite a valid concept to find a derivative *of* a point ... 
        else:
            #In case seld.data.x or self.data.y are not Numeric arrays...
            xPadded=concatenate((array([x[0]]), array(x), array([x[-1]])), 1)
            yPadded=concatenate((array([y[0]]), array(y), array([y[-1]])), 1)
            
            xi=xPadded[:-2]
            xf=xPadded[2:]
            
            yi=yPadded[:-2]
            yf=yPadded[2:]
            
            der=(yf-yi)/(xf-xi) 
        
        if data.name:
            name='[RoC] %s' % data.name
        else:
            name='Rate of change'
            
        if data.legendName!='':
            legendName='[RoC] %s' % data.legendName
        else:
            legendName=''
                        
        d=Data([array(x), der], name=name, legendName=legendName)
        return d
        
class ScalerAnalyzer(BaseAnalyzer):
     
    def _process(self, data):
        pass

def main():

    x=arange(0,10,1)
    y=sin(x)

    d=Data([x, y],'data1')
    
    a=RateOfChangeAnalyzer([d])
    
    print d
    print 'rate of change:'
    for item in  a.process():
        print item
    
if __name__=='__main__':
    
    main()
    

