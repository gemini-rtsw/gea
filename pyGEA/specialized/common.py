#!/usr/bin/python

import sys
from GEATime import Time
import GEAVars        

gDiskWrite=1             # Boolean used to decide whether the image is to be written to disk or shown via show().
gUseImshow=0             # If true, use imshow() for plotting, else use pcolor(). imshow() is faster and uses interpolation.
gDataDir=GEAVars.path.fileSys.wwwData

class PlotToMake(object):
    """Wrapper class to keep track of the data associated with each plot.

    Arguments:
    chanFileNameTup - Tuple containing a list of file names. Each of these files contains
        a list of channels for which data is extracted via 'caGet'. 
    algorithm - a funcition (could be from the Algorithms class) which is called 
        on the data obtianed via caGet.
    
    """
    def __init__(self, chanFileNameTup, name, nameLarge=None, title='', 
                 dpi=100, dpiLarge=175, dir=gDataDir, minMax=None, algorithm=None, **kwargs):
        self.chanFileNameTup=chanFileNameTup  #Tuple with names of files where channel names are located.
        self.name=name                  #Used when writing to disk.
        self.nameLarge=nameLarge        #Used when writing to disk.
        self.title=title
        self.dpi=dpi
        self.dpiLarge=dpiLarge
        self.dir=dir        #Directory where the image(s) will be written to.
        self.minMax=minMax  #Should be either None or  a tuple representing the min/max values of the particular plot. 
        self.algorithm=algorithm        #Funtion to be called on the data. 
            
        self.__dict__.update(kwargs)
            
class Algorithms:
    """Container class holding functions with algorithms that can be performed on the data.
    """
    def diff12(data1, data2):
        """Take the difference betweek the two data sets; used in plotting errors.
        """
        return data1-data2
        
    diff12=staticmethod(diff12)

#
# chanFileName is a file containing a single column that is a list of channel names
# to get values from. caGet returns a list of values for each channel.
#
# The following will return a list of lists containing channel name and it's value.
# data = [ item.split() for item in pipe.readlines() ]

def caGet(chanFileName):
    """Gets data from the EPICS database.
    
    Expect data of the form:
    channelName  value
    """

    import os
    import ca

    try:
        data = [ ca.pv(i.rstrip(), syncT=1).get() for i in file(chanFileName).readlines() if not (i.startswith(' ') or i.startswith('\n')) ]
    except:
        raise IOError("Can't read data from " + chanFileName)

    return data  #Now data is a list of values.
