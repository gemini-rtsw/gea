#!/usr/bin/env python

import sys
from GEATime import Time
    
class Data(list):
    """Hides the details of data representation. All data passed around should be of this type.
       Initially only x and y data is initialized (to empty) but more can be added at runtime via append.
       All methods (append, __str__, clearAll, __getitem__) support an arbitrary number data lists.
    """
    
    def __init__(self, dataList=None, name='', legendName='', interpolated=False):
        """dataLists should contain lists of data. So one could create a Data object with:
            
        More data lists can be appened after the object has been created via append().
        """
        list.__init__(self)
                
        if dataList:
            self+=dataList
        
        while len(self)<2:             #Maybe later will have more default elements. For now it's 2.
            self.append([])

        self.name=name
        self.legendName=legendName  #Sometimes may want to have a pretty legend name for the data.
        
        self.interpolated=interpolated
        
        #Inintially assume no discontinuities in the data.
        #self.discList holds the idecies of where data discontinuities have occured.
        self.discList=[] 
            
    def addComponents(self, newData):
        """Adds components of newData to self one by one. Concatinates names with a '+'
        character in between. 
  
        """
        diff=len(newData)-len(self)
        if diff > 0:
            self+=[[None]] * diff             #NOTE: Make sure this works.
            
        for i in range(len(newData)):
            try:
                self[i]+=newData[i]
            except IndexError:                  #Have to rewrite this to deal with a case  when self[i] is a Numeric array. 
                pass            #Done adding
                
        self.name+="+"+newData.name
               
        #Adjust the discontinuity list.
        discListLen=len(self.discList)
        self.discList+=map(lambda x: x+discListLen,  newData.discList)
        
        return self      
                  
    def _getX(self):
        return self[0]
    def _setX(self, value):
        self[0]=value
    x=property(_getX, _setX)   #seems like properties are really slow... might want to rething this.
         
    def _getY(self):
        return self[1]
    def _setY(self, value):
        self[1]=value
    y=property(_getY, _setY)  #seems like properties are really slow... might want to rething this.
         
    def isEmpty(self):
        """Returns True if any all items in self are empty.
        """
        for item in self:
            if item:
                return False
        return True
            
    def __str__(self, xAsTime=False, sep='\t'):
        """Returns a string representation of the data. Works for a general size of self
        """
        #All data may not have the same dimensions.
        maxSize=max(map(len, self))
    
        strData=[]
        if self.name:
            strData.append('%s\n' % self.name)
        
        if xAsTime:
            for i in xrange(maxSize):
                for j, item in enumerate(self):               
                    try:
                        if j==0:
                            strData+=[item[i],sep]
                        else:    
                            strData+=[str(item[i]),sep]
                    except IndexError:
                        strData+=["N/A",sep]
                
                strData+=["\n"]            
        else:
            for i in xrange(maxSize):
                for item in self:
                    try:
                        strData+=[str(item[i]),sep]
                    except IndexError:
                        strData+=["N/A", sep]
                
                strData+=["\n"]
            
        if self.discList:
            strData+=['\nDiscontinuity List:\n', str(self.discList)]
            
        return "".join(strData)


if __name__=='__main__':
    
    
    data=Data(name='empty')
    print data
    data2=Data([[32,4,6], [3,5, 3]], 'data2', '', None)
    print data2
    
    data3=Data([[7,8,9], [0,99,111]], 'ree', '', None )
    print data2
    print data3

    print "\n\n"
    data3.addComponents(data)
    print data3

    print "\n\nNEW"
    d=Data([[1,2,3], [10,11,12]],'', '',  None )
    d2=Data([[32,4,6], [3,5]], 'blah','',  None)
    print d.addComponents(d2)
    
    d.x=[1,23]
    print d.x, d.y, d    
    
    
    

