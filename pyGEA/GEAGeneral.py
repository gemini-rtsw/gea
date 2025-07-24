#!/usr/bin/env python
"""
Should clean up the code here...
"""
import sys
import  os
import  traceback
import  random
import textwrap
import StringIO
from GEATime import Time
import GEAVars

class util:
    """Collection of general utility helper functions and classes.
    """
    class Holder(dict):
        """Helper class. Inherits all from a standard dictionary, but has __getitem__/__setitem__ 
        overridden to always store all data in self.__dict__.
        
        It is meant to hold all the html widgets (objects from GEAHtml.py). 
        
        It allows to access them via the attribute notation, or as a key in a dictionary.
        This simplifies access to attributes when one has dynamically generated strings. 
        So for example one can do this:
        
        ----
        html=Holder()
        
        html.someWidget=HTMLItemA1()            #Setting an attribute the regular way                        
        html['anotherWidget']=HTMLItemB2()        #Setting another attribute but using dictionary notation    
        
        function1(html.anotherWidget)           #Accessing an html attribute in a usual fashion
        
        nameAsString='someWidget'
        
        function1(html[nameAsString])           #Or using the dictionary notation.
        
        ----
        Essentially in the example above, html.someWidget is equivalent to html['someWidget']
        
        """
        def __init__(self, initfrom=(), **kw):
            dict.__init__(self, initfrom)
            self.update(kw)
            self.__dict__ = self
    
    def getOtherSite(current=GEAVars.site):
        #Sometimes helpful...
        if current=='MK': 
            return 'CP'
        else:   
            return 'MK'
    getOtherSite=staticmethod(getOtherSite)
    
    def deepImport(modName):
        """Ensures we import the whole module named by 'modName', not just the 
        top level (ie: so that when doing mod=_import('x.y.z') we can use mod.something_in_z.
        """
        mod=__import__(modName)
        items=modName.split('.')[1:]
        for item in items:
            mod=getattr(mod, item)
        return mod
        
    deepImport=staticmethod(deepImport)
    
    def combineDict(*arg, **kwargs):
        """The new dictionary is updated with kwargs last, so that 
        contents of *arg, can actually be changed using kwargs.
        """
        newDict={}
        for item in arg:
            newDict.update(item)
        
        newDict.update(kwargs)
        return newDict
        
    combineDict=staticmethod(combineDict)
        
    def isStrLike(obj):
        """From Python Cookbook.
        """
        try:
            obj+''
        except (TypeError, ValueError):
            return 0
        return 1
    
    isStrLike=staticmethod(isStrLike)
    
    def invertDict(d):
        """Assumes 1to1"""
        newD={}
        for key, value in d.items():
            newD[value]=key
        return newD
    invertDict=staticmethod(invertDict)
    
    def makeDict(**kwargs):
        """Takes arguments in the form  key1=val1, key2=val2, etc... and returns a dictionary {'key1':val1, 'key2':val2, ....}.
        In python > 2.2, can use dict() to do the same thing.
        """
        return kwargs

    makeDict=staticmethod(makeDict)    
    
    def iterable(obj):
        try: 
            len(obj)            
        except: 
            return False
        return True
    
    iterable=staticmethod(iterable)
    
    def dictStr(d):
        """Returns a string with representation of a dictionary.
        """
        cont=[]
        for key, value in d.items():
            cont.append("%s:%s\n" % (key, value))
        
        return ''.join(cont)

    dictStr=staticmethod(dictStr)
        
    def htmlPrint(*items):
        for item in items:
            print '<pre>', item, '</pre>'
    htmlPrint=staticmethod(htmlPrint)
        
    def wordWrap2(text, width = 120):
    
        return '\n'.join(textwrap.wrap(text, width))
        
    def wordWrap(text, width = 120):
        """
        Taken from Python Cookbook.
        
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        
        """
        return reduce(lambda line, word, width=width: '%s%s%s' %
                        (line,
                       ' \n'[(len(line)-line.rfind('\n')-1
                        + len(word.split('\n',1)[0]
                        ) >= width)],
                        word),
                        text.split(' ')
                      )
    wordWrap=staticmethod(wordWrap)
                     
##~     def wordWrap2(s,length=76):
##~         offset = 0
##~         while offset+length < len(s):
##~             if s[offset] in ' \n':
##~                 offset += 1
##~                 continue
##~             
##~             endOfLine = s[offset:offset+length].find('\n')
##~             if endOfLine < 0:
##~                 endOfLine = s[offset:offset+length].rfind(' ')
##~             
##~             if endOfLine < 0:
##~                 endOfLine = length
##~                 newOffset = offset + endOfLine
##~             else:
##~                 newOffset = offset + endOfLine + 1
##~             
##~             yield s[offset:offset+endOfLine].rstrip()
##~             
##~             offset = newOffset
##~         
##~         if offset < len(s):
##~             yield s[offset:].strip()
##~            
##~     wordWrap2=staticmethod(wordWrap2)         

    def formatNum(num, digits=3, showSign=False):
        if showSign:
            flag='+'
        else:
            flag=''
        if num%1==0:                        # Whole number
            format='%%%sd' % (flag)
            return format % num
        else:
            format='%%%s.%df' % (flag, digits)
            return format % num
        
    formatNum=staticmethod(formatNum)
    
    def getSemesterRange(t=None, site=GEAVars.site):  
        '''Return the start and end times of the semester in which t is.
        
        Our semseters are like this (with years varying of course):
        2002/02/01 00:00:01 - 2002/07/31 23:59:59
        and this:
        2002/07/01 00:00:01 - 2003/01/31 23:59:59
        
        '''
        if t is None:
            #take t to be right now.
            t=Time()

        #We'll adjust months and years later..
        st=Time(site=site, fromAttr='string1', attrVal='2002/02/01 00:00:01')
        et=Time(site=site, fromAttr='string1', attrVal='2002/07/31 23:59:59')              

        
        if '02/01 00:00:01'<=t.string15<='07/31 23:59:59':
            st.year=t.year
            et.year=t.year
        elif t.string15<'02/01 00:00:01':
            st.year, et.year=t.year-1,t.year
            st.month, et.month=8, 1            
        else:
            st.year, et.year=t.year,t.year+1
            st.month, et.month=8, 1      
               
        return st, et
    
    getSemesterRange=staticmethod(getSemesterRange)
        
       
class naming(object):
    """Generates random names.
    """
    imPrefix='image.'    #Prefix that should be added to temporary image file names.
    dataPrefix='data.'   #Prefix added to all the temporary data file names.
    exportPrefix='export.'
        
    def genDailyName(name, prefix='', suffix=''):
        return "%s%s%s" % (prefix, name.replace(' ', '_').replace('|', '_PIPE_').replace(':', '_COLON_').replace('.', '_PERIOD_').replace('*', '_STAR_'), suffix)
    genDailyName=staticmethod(genDailyName)
    
    def createDailyDir(fromWeb=False):
        if fromWeb:
            dailyDir=GEAVars.path.web.daily
        else:
            dailyDir=GEAVars.path.fileSys.daily
            
        dirName=os.path.join(dailyDir, Time().string4)
        if not os.path.isdir(dirName):
            os.makedirs(dirName, mode=0777)
        return dirName
    createDailyDir=staticmethod(createDailyDir)
    
    def getLatestDailyDir(dayLimit=10, fromWeb=False):
        """
        Arguments:
        dayLimit - How many days back to search. 
        fromWeb - 
        fullPath - If set to False, only the basename is returned.
        """     
        try:
            #Attempt to return a name from the 'naming' namespace. If not yet created, then exception will be raised.
            if fromWeb:
                dailyDir=GEAVars.path.web.daily
                return naming.latestDailyWebDir
            else:
                dailyDir=GEAVars.path.fileSys.daily
                return naming.latestDailyFileSysDir
        except AttributeError:
            pass
                
        found=True
        t=Time()
        dirName=os.path.join(dailyDir, t.string4)
        for i in range(0, dayLimit):
            if os.path.isdir(dirName):
                found=True
                break #done.
            found=False
            t.seconds-=Time.secPerDay
            dirName=os.path.join(dailyDir, t.string4)
        if not found:
            dirName=dailyDir
            
        if fromWeb:
            naming.latestDailyWebDir=dirName
        else:
            naming.latestDailyFileSysDir=dirName
            
        return dirName        
    getLatestDailyDir=staticmethod(getLatestDailyDir)

    def getDailyDir(dateStr=None, fromWeb=False):
        """
        Arguments:
        dayStr - Should be of the format YYYY_MM_DD. 
        """ 
        dateStr=dateStr or Time().string4
        if fromWeb:
            dailyPath=GEAVars.path.web.daily
        else:
            dailyPath=GEAVars.path.fileSys.daily
        return  os.path.join(dailyPath, dateStr)
    getDailyDir=staticmethod(getDailyDir)
    
    #Code below generates 'random' names based on the date.
    def genName(prefix='', suffix=''):
        return "%s%s.%08d%s" % (prefix, Time().string2, naming.genRand(8), suffix)
    genName=staticmethod(genName)

    def genRand(digits):
        """Not doing any format/error checking. Will raise an exception if can't generate a number.
        """
        return random.randrange(0, int('9'*digits))
    genRand=staticmethod(genRand)
        
    def genImDataNames():
        """ To be used when want the same date stamp on both the image and data file names. 
            
        Returns a tuple: (tempImageName, tempDataName)
        """
        stamp=Time().string2+".%08d" % naming.genRand(8)
        return naming.imPrefix+stamp+".png", naming.dataPrefix+stamp
    genImDataNames=staticmethod(genImDataNames)
        
    def genDataName():
        """Used to generate temporary file names.
        NOTE: Should maybe add seconds.. or a randon number to the end, to deal with multiple requests per second.. 
        """
        return "%s%s.%08d" % (naming.dataPrefix, Time().string2, naming.genRand(8))
    genDataName=staticmethod(genDataName)
        
    def genImName():
        """Used to generate temporary file names.
        NOTE: Should maybe add seconds.. or a randon number to the end, to deal with multiple requests per second.. 
        """
        return "%s%s.%08d.png" % (naming.imPrefix, Time().string2, naming.genRand(8))
    genImName=staticmethod(genImName)
        
   
#Should clean up all the error printing functions below...         
def printError(data="Error\n", stream=GEAVars.errStream):
    stream.write(str(data))

def print_exc_plus(stream=GEAVars.errStream):
    """Based on a recipe from the Python Cookbook... Needs fixing.. 
    """
    tb=sys.exc_info()[2]
    
    while 1:
        if not tb.tb_next:
            break
        tb=tb.tb_next
    
    stack=[]
    f=tb.tb_frame
    
    while f:
        stack.append(f)
        f=f.f_back
    
    stack.reverse()
    traceback.print_exc(file=stream)     
    stream.write("\nLocals by frame, innermost last:")
    
    for frame in stack:
        stream.write("\nFrame %s in %s at line %s" % (frame.f_code.co_name, frame.f_code.co_filename, frame.f_lineno))
        for key, value in frame.f_locals.items():
            stream.write("\n\t%20s = " % key)
            try:
                stream.write(str(value))
            except:
                stream.write("<ERROR WHILE PRINTING VALUE>")
    
    stream.write("\n")
        
import cgi

def printExcept(stream=GEAVars.errStream):
    """Based on a Python Cookbook recipe.
    
    Writes the exception trace to the stream and returns it as a string.
    
    Arguments:
        stream - 
        html - Determines whether the output should be wrapped in HTML.
    """
    limit=None
    type, value, tb=sys.exc_info()
    list=traceback.format_tb(tb, limit)+traceback.format_exception_only(type, value)
    body= "Traceback (innermost last):\n" + "%-20s %s" % ("".join(list[:-1]), list[-1])
    body = cgi.escape(body)

    stream.write(body)
    return body
    
def printExcept2(stream=GEAVars.errStream):
    """Print the exception stack and extra debug information.
    """
    stream.write("".join(["Exception generated... TYPE:", str(sys.exc_type), "\tVALUE:", str(sys.exc_value), "\n"]))
    stream.write("TRACEBACK:\n")
    
    traceback.print_exc(file=stream)
    
#########
#All the validator classes below will be replaced with the contents of GEAValidator.py.  once GEAPlot.py gets updated... 
#########
class ValidatorBase(object):
                 
    def __init__(self):
        """Each type of validator should overwrite this class.
        """
        pass
                 
    def _handleError(self, errorText, stream, valueOnError, errorPreText=None):
        """If stream or velueOnError is None, raise an exception.
        Otherwise, write error to the stream, and return valueOnError.
        """
        errorPreText=errorPreText or ''
    
        if stream is None or valueOnError is None:
            raise ValueError(errorText)
        else:
            #Show something when dealing with an empty string.
            if valueOnError=='':
                strValueOnError="''"
            else:
                strValueOnError=valueOnError
                
            stream.write(errorPreText+errorText)
            stream.write('\nSetting default value: %s\n' % strValueOnError)
            return valueOnError

class Validator(dict):
    """DEPRICATED.... should use stuff from GEAValidator.
    """

    trueChoices=['on', 'On', 'ON', 'true', 'True', 'TRUE', 
                 'checked', 'yes', 'Yes', '1', True, 1]
    falseChoices=['off', 'Off', 'OFF', 'false', 'False', 'FALSE', 
                 'no', 'No', '0', False, 0]

    def validateBoolean(option, choiceTrue=True, choiceFalse=False, 
                        choicesTrue=None, choicesFalse=None, stream=None, 
                        valueOnError=None, errorPreText=None):
        """
        Arguments:
        ...
        stream - If provided, error text which is passed to an Exception object is also written here.
        valueOnError - If provided, when an exception during conversion is raised and stream is defined, 
        this value is returened. The error is written to the stream. 
        """
        if choicesTrue is None:
            choicesTrue=Validator.trueChoices
      
        if choicesFalse is None:
            choicesFalse=Validator.falseChoices  
  
        if option in choicesTrue:
            return choiceTrue
        elif option in choicesFalse:
            return choiceFalse
        else:
            return Validator._handleError('Could not convert "%s" to boolean' % option, 
                                          stream, valueOnError, errorPreText)    
        
    validateBoolean=staticmethod(validateBoolean)
            
    def validateFloat(option, minVal=None, maxVal=None, stream=None, valueOnError=None, errorPreText=None):
        """
        Arguments:
        ...
        stream - If provided, error text which is passed to an Exception object is also written here.
        valueOnError - If provided, when an exception during conversion is raised and stream is defined, 
        this value is returened. The error is written to the stream. 
        """
        try: 
            val=float(option)
        except ValueError:
            return Validator._handleError('Could not convert "%s" to float' % option, 
                                    stream, valueOnError, errorPreText)                
             
        if minVal is not None:
            if minVal>val:
                return Validator._handleError('Value %f is smaller than minimum %f' % (val, minVal), 
                                       stream, valueOnError, errorPreText)
        if maxVal is not None:
            if maxVal<val:
                return Validator._handleError('Value %f is larger than maximum %f' % (val, maxVal), 
                                       stream, valueOnError, errorPreText)                
        return val
                    
    validateFloat=staticmethod(validateFloat)
    
    def validateInt(option, minVal=None, maxVal=None, stream=None, valueOnError=None, errorPreText=None):
        """
        Arguments:
        ...
        stream - If provided, error text which is passed to an Exception object is also written here.
        valueOnError - If provided, when an exception during conversion is raised and stream is defined, 
        this value is returened. The error is written to the stream. 
        """

        try: 
            val=int(option)
        except ValueError:
            return Validator._handleError('Could not convert "%s" to int' % option, 
                                       stream, valueOnError, errorPreText)   

        if minVal is not None:
            if minVal>val:
                return Validator._handleError('Value %d is smaller than minimum %d' % (val, minVal), 
                                       stream, valueOnError, errorPreText)   

        if maxVal is not None:
            if maxVal<val:
                return Validator._handleError('Value %d is larger than maximum %d' % (val, maxVal), 
                                       stream, valueOnError, errorPreText)   
        return val
   
    validateInt=staticmethod(validateInt)

    def _handleError(errorText, stream, valueOnError, errorPreText=None):
        """If stream or velueOnError is None, raise an exception.
        Otherwise, write error to the stream, and return valueOnError.
        """
        errorPreText=errorPreText or ''
    
        if stream is None or valueOnError is None:
            raise ValueError(errorText)
        else:
            #Show something when dealing with an empty string.
            if valueOnError=='':
                strValueOnError="''"
            else:
                strValueOnError=valueOnError
                
            stream.write(errorPreText+errorText)
            stream.write('\nSetting default value: %s\n' % strValueOnError)
            return valueOnError

    _handleError=staticmethod(_handleError)
    
if __name__=='__main__':

    pass
