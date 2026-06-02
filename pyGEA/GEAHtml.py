#!/usr/bin/python
# -*- encoding: utf-8 -*-

"""
Used for automatically generating html code. The main idea behind this design, is to be able to write most of the HTML code
(or use a WYSIWYG editor) for different components and then use python to wrap that code so it can be 
used in a more dynamic way. An alternate approach would be to use a library such as HTMLgen, and do all (or most) of the HTML
in python. 
"""

import os
import cgi                      #For escaping
import GEAVars 
import urllib
import random
from GEATime import Time
from GEAGeneral import util, naming

#import re          #Using string methods for now... 

import PyHtmlTable  #Third party module for creating dynamic html tables in python.

class HtmlHelper(object):
    
    def createLink(name, link, cssClass=None,  **queryStrPairs):
        """Helper method to create hyperlinks.
        """
        #Create a query string.
        queryString=HtmlHelper.dict2QueryString(queryStrPairs)
               
        #Want to make sure calledName end with a '?' character if queryStrPairs is non empty
        if len(queryStrPairs)>0:
            link=link.rstrip('?')+'?'

        if cssClass is not None:
            theClass='class="%s"' % cssClass
        else:
            theClass=''
            
        return '<a %s href="%s%s">%s</a>' % (theClass, link, cgi.escape(queryString), name)
        
    createLink=staticmethod(createLink)
    
    def dict2QueryString(d):
        """Creates a query string of type key1=val1&key2=val2... from the given dictionary.
        """        
        qp=urllib.quote_plus
        return '&'.join([qp(str(key))+'='+qp(str(value)) for key, value in d.items()])
        
    dict2QueryString=staticmethod(dict2QueryString)
      
    #Use string substitution; faster...  
    # escapeRegEx=re.compile(r'%(?!\()')
    def escapePercent(text):
        """Ugly... should try with RE and see whats faster... 
    
        Replaces all occurances of '%' with '%%' except cases when '%' is followed by '('. Used so that there
        is no need to manually escape the '%' characters in the html code. 
        """
        dummy="#@$4D#@$GT5E"
        text=text.replace('%(', dummy)
        text=text.replace('%', '%%')
       
        return text.replace(dummy, '%(')

    escapePercent=staticmethod(escapePercent)
    
class StrDict(dict):
    """Allows for partial string substitution and for extended update format.
    """
    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            return "%%(%s)s" % name 
                
    def update(self, newDict=None, **kwargs):
        """Allows for updates of the form "key=value".
        """        
        if newDict is None and kwargs=={}:
            dict.update(self) #This will raise an exception. 
        
        if not newDict is None:
            dict.update(self, newDict)         

        dict.update(self, kwargs)            
            
class PyHtmlTableGEA(PyHtmlTable.PyHtmlTable):
    """Wrapper of PyHtmlTable that provides extra functionality
    """
    def __getattribute__(self, name):
        return self.__dict__[name]
        
    def add_array_after_last_row(self, inarr, attrs=None):

        """Adds list of data specified by inarr to table object
          starting at row,col

          Optionally specify attributes to set on cells being added
          by defining the attrs dictionary

          Note: Cell attribute insertion can be additive or overwriting depending
                on calls to setReplaceCellattrs() or setAppendCellattrs()

                Default is to append new attributes
        """
        lastRow=self.maxRow
        
        arlen = len( inarr )
        
        for i in range( arlen ):
            self.setCellcontents(lastRow, i, inarr[i], attrs )
            
    def setCellattrs( self, row, col, indict, overwrite=None):
        """Added a flag to decide whether to overwrite or to add the given attributes.
        """
        #Need this because PyHtmlTable explicitelly checks for 1s and 0s.
        overwrite={True:1, False:0}.get(overwrite, overwrite)

        if overwrite is None:
            overwrite=self.overwriteattrs
            
        oldOverwrite=self.overwriteattrs
        self.overwriteattrs=overwrite
        PyHtmlTable.PyHtmlTable.setCellattrs(self, row, col, indict)
        self.overwriteattrs=oldOverwrite
        
class HTMLObject(list):
    """General base html generator class. All others should inherit from this. 
    
    The following is the order of components printed:
    
    contents of header
    contents of body
    contents of self
    contents of footer
    
    Each item inside header/body/footer has vars and taggedVars substituted into it. Contents of self do not. 
    Ideally the users of the objects which inherit from HTMLObject would add components via
    append method. Each compenent could be another object which inherited from HTMLObject, and 
    it would have its own vars and taggedVars.
    
    The defaults of most vars are set to "[varName]", where varName is a name of the variable in question.
    The exceptions to this rule are:
        wwwcssdir           #Set in HTMLObject constructor
        wwwimagesdir        #Set in HTMLObject constructor 
        wwwmediadir         #Set in HTMLObject constructor
        wwwscriptsdir       #Set in HTMLObject constructor
        mkurl               #Set in HTMLDocContWithSideMenu constructor
        cpurl               #Set in HTMLDocContWithSideMenu constructor
        site                #Set in HTMLDocContWithSideMenu/HTMLDocCont constructors
        jsgea               #Set in HTMLDocContWithSideMenu constructor
        jsmenu              #Set in HTMLDocContWithSideMenu constructor
        gealogo             #Set in HTMLDocContWithSideMenu/HTMLDocCont constructors
        geabanner           #Set in HTMLDocContWithSideMenu/HTMLDocCont constructors
        cssfile             #Set in HTMLDocContWithSideMenu constructor
    The defaults on these variables are set to their counterparts from GEAVars. 
    
    """
    def __init__(self, autoTaggedVars=False, **kwargs):    
        """
        Arguments/Attributes:
            body - Can be a list of any objects that have a string representation via str().
            vars - Dictionary with entries to be substituted into the html code.
            header - Printed before body.
            footer - Printed after body.
            taggedVars - 
            useTags -
            reSubList - 
            nameTag - 
            fStream - 
        """
        #Defaults
        self.fStream=GEAVars.errStream

        self.nameTag=None
        self.header=[]
        self.footer=[]
        self.body=[]
        
        self.useTags=True
        self.reSubList=[]  
        
        self.__dict__['vars']=StrDict()
        self.__dict__['taggedVars']=StrDict()
                
        #If taggedVars not passed on as a parameter, create it from vars.
        if autoTaggedVars and not kwargs.has_key('taggedVars'):
            try:
                for key in kwargs['vars'].keys():
                    upKey=key.upper()
                    self.__dict__['taggedVars'][upKey]=upKey
            except KeyError:
                #Dont have kwargs['vars'].. thats ok. Do nothing.
                pass
                       
        for key, value in kwargs.iteritems():
            self.__setattr__(key, value)
            
        #Setup default content locations. These just like any other vars can be overwritten when widgets are created.  
        #Things such as logos (and other NON-DATA images), css definitions and scripts are always looked for in these directories. 
        self.vars.update({'wwwmediadir':GEAVars.path.web.wwwMedia,
                          'wwwcssdir':GEAVars.path.web.wwwCss,
                          'wwwimagesdir':GEAVars.path.web.wwwImages,
                          'wwwscriptsdir':GEAVars.path.web.wwwScripts})
                          
        #This is a nice way of having javascript code unique to a widget. Each function/variable
        #that is meant to be unique should have a %(JS)s appended to its name. This is later
        #automatically transfored into JS<number> when the html is being prepared
        #to be sent back to the client.
        self.__dict__['taggedVars']['JS']='JS%s' % random.randrange(0, 9999)
                          
        
    def __setattr__(self, name, value):
        """Needed to make sure vars and taggedVars are of type StrDict.
        """
        if name=='vars' or name=='taggedVars':
            #Do not want to create a new StrDict - always update. This allows for users to pass only partially filled-in vars (or taggedVars) 
            #dictionary to the constractor of the HTML* object that they are creating without loss of the default values for keys that were not 
            #present in vars (or taggedVars). Also ensures that StrDict is always used as the
            #dictionary holding values for vars (or taggedVars).
            self.__dict__[name].update(value)
            
        else:
            object.__setattr__(self, name, value)
        
    def __str__(self):
        """Return the html representation of this object and all its components. 
        
        Only contents of self.body, self.header, and self.footer have self.vars and 
        self.taggedVars substitututed. Contents of self are assumed to be 
        other HTMLObjects and have their own self.vars and self.taggedVars which they
        use.
        """ 
        if self.useTags:
            self._addTags() 


        strList=map(str, self.header)+map(str, self.body)

        #Substitute self.vars and self.taggedVars into the items  of strList.
        strList=map(lambda item: 
                    HtmlHelper.escapePercent(HtmlHelper.escapePercent(item) % self.vars) % self.taggedVars, 
                    strList)                    
    
        #Add contents of self.
        strList+=(map(str, self))
        
        #Add the footer separately because contents of self (ie. the list) should not have self.vars and self.taggedVars substituted into them. 
        strList+=map(lambda item: HtmlHelper.escapePercent(HtmlHelper.escapePercent(str(item)) % self.vars) % self.taggedVars, 
                     self.footer)                    
    
        return ''.join(strList)
               
    def dataStr(self, escape=True):
        """Returns a nicely formatted information about the contents of 
        self's data (vars, taggedVars, etc). 
        """
        strList=['Class name:\n\t',self.__class__.__name__,'\n']
        
        for item in ['vars', 'taggedVars', 'nameTag', 'useTags', 'reSubList']:
            strList+=["Contents of ",item,':\n']
            try:
                keys=self.__dict__[item].keys()
                keys.sort()
                for key in keys:
                    strList+=['\t',str(key),':',str(self.__dict__[item][key]),'\n']
            except AttributeError:   #Dealing with a non-dictionary variable.
                strList+=['\t',str(self.__dict__[item]),'\n']
        
        text="".join(strList)
        
        if escape:
            text=cgi.escape(text)
        
        return text
        
    def _addTags(self):
                
        if self.nameTag is None:
            return 
            
        for key, value in self.taggedVars.items():
            if key in self.reSubList:
                self.taggedVars[key]=''.join(["%(",value,'_',self.nameTag,")s"])
            else:
                self.taggedVars[key]=''.join([value+'_',self.nameTag])

    def write(self, stream):
        
        stream.write(self.__str__())
        stream.flush()                      
                                
    def __eq__(self, x):
        """Need to implement this... 
        """
        raise RuntimeError('HTMLObject.__eq__() not implemented.')
        #return self==x

#Classes below are just wrappers of the one above with header, footer, and body, filled in. 
class HTMLErrorPage(HTMLObject):
    """Used for displaying errors. 

    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
          
        header="""Content-Type:   text/html\n\n
<html>
<head>
<title>GEA</title>
</head>
<body>
<table class="mainHeader" width="100%" cellspacing="0" cellpadding="5">
    <tr>
        <td><img align="center" src="%(geabanner)s"></td>
   </tr>
</table>

"""        
        footer="""
</body>
</html>"""        
        body="""
<br> 
<table border=0 cellpadding=4 cellspacing=0 bgcolor="#70bff4">
    <tr> 
        <td>
            <font face="Tahoma, Arial, Helvetica" color=white> <b> Error Message </b> </font>
        </td> 
    </tr> 
</table>
<table width=100% border=0 cellpadding=2 cellspacing=2 bgcolor=#F0F0F0>
<tr> 
    <td> <pre>%(errormsg)s</pre>
    </td>
</tr>
</table>

<br> 
<table border=0 cellpadding=4 cellspacing=0 bgcolor="#70bff4">
    <tr> 
        <td>
            <font face="Tahoma, Arial, Helvetica" color=white> <b> Traceback </b> </font>
        </td> 
    </tr> 
</table>
<table width=100% border=0 cellpadding=2 cellspacing=2 bgcolor=#F0F0F0>
<tr> 
    <td> <pre>%(traceback)s</pre>
    </td>
</tr>
</table>

<br> 
<table border=0 cellpadding=4 cellspacing=0 bgcolor="#70bff4">
    <tr> 
        <td>
            <font face="Tahoma, Arial, Helvetica" color=white> <b> Environment </b> </font>
        </td> 
    </tr> 
</table>
<table width=100% border=0 cellpadding=2 cellspacing=2 bgcolor=#F0F0F0>
<tr> 
    <td> <pre>%(environment)s</pre>
    </td>
</tr>
</table>

<br> 
<table border=0 cellpadding=4 cellspacing=0 bgcolor="#70bff4">
    <tr> 
        <td>
            <font face="Tahoma, Arial, Helvetica" color=white> <b> Other Info </b> </font>
        </td> 
    </tr> 
</table>
<table width=100% border=0 cellpadding=2 cellspacing=2 bgcolor=#F0F0F0>
<tr> 
    <td> <pre>%(otherinfo)s</pre>
    </td>
</tr>
</table>

"""        
        vars={'errormsg':'[errormsg]',
              'traceback':'[traceback]', 
              'environment':'[environment]',
              'otherinfo':'[otherinfo]',
              'gealogo':GEAVars.html.geaLogo,
              'geabanner':GEAVars.html.geaBanner,
              }

        HTMLObject.__init__(self, header=[header], footer=[footer], body=[body], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
        
class HTMLCont(HTMLObject):
    """Empty Container class. Similar to HTMLDocCont but does not contain the beginning and end html and body tags.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
                  
        HTMLObject.__init__(self, **kwargs)
      

class HTMLSimpleCont(HTMLObject):
    """Html Container class. Should be the main page object. 
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
          
        header="""
<html>
<head>
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="-1">
</head>
<body>
"""        
        footer="""   
</body>
</html>
"""        
        HTMLObject.__init__(self, header=[header], footer=[footer])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)


class HTMLDocCont(HTMLObject):
    """Html Container class. Should be the main page object. 
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
          
        header="""Content-Type:   text/html\n\n
<html>
<head>
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="-1">

<title>%(pagetitle)s</title>
</head>
<body background="%(background)s">
<img align="left" src="%(geabanner)s">
<br>
<br>
<br>
<br>
<br>
<div align="center"><h1><a href="%(mainfile)s">%(pageheading)s</a></h1>
</div>

<br>
<br>
"""        
        footer="""   
<br>
<hr>
<br>
        
<table class="mainFooter" width="100%" cellspacing="0" cellpadding="5">
<tr>
<td align="left">
<a href="http://www.gemini.edu/">
Gemini Observatory
</a>
<td width="100%">
<a href="http://www.python.org/">
<div align="right"><img src="%(wwwimagesdir)sPythonPoweredAnim.gif" align=right width=55
     height=22 alt="[Python Powered]" border=0>
</div>
</a>
</td>
</tr>
</table>

</body>
</html>"""        
        vars={'pagetilte':'[pagetilte]', 'mainfile':'[mainfile]',
              'pageheading':'[pageheading]','background':'[background]',
              'site':GEAVars.site,
              'geabanner':GEAVars.html.geaBanner,
              }

        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                    
class HTMLDocContWithSideMenu2(HTMLObject):
    """Html Container class. Should be the main page object. 
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
          
        #Content-Type:   text/html\n\n
        header="""
<html>
<head>

<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="-1">

<meta http-equiv="Content-Style-Type" content="text/css">

   <!-- external style sheet to control element properties -->
   <link rel="STYLESHEET" href="%(cssfile)s" media="screen" type="text/css">

<title>%(pagetitle)s</title>

<script language="JavaScript" type="text/javascript" src="%(jsmenu)s"> </script>
<script language="JavaScript" type="text/javascript" src="%(jsgea)s"> </script>
<script language="JavaScript" type="text/javascript" src="%(jssort)s"> </script>
<link rel="shortcut icon" href="%(wwwimagesdir)sfavicon.ico">
</head>
<body width="100%">

<div align=center>
<table align=center class="mainHeader" cellspacing="0" cellpadding="0">
    <tr>
        <td>
            <a href="%(homepage)s">
                <img src="%(geabanner)s">
            </a>
        </td>

    </tr>
</table>
</div>


<table class="secondaryHeader" width="100%" cellspacing="2" cellpadding="0">
    <tr>
        <td class="site" width="160" align="left">
               Current Site: %(site)s
        </td>  
        <td class="secondaryHeader" align="left">
            %(headerinfo)s
        </td> 
    
        <td class="secondaryHeader" align="right">
        
        %(headerlinks)s
        </td> 
    </tr>
</table>


<table width="100%" cellspacing="2" cellpadding="0">
    <tr> 
        <td valign="top" width="130">
<!-- Side menu -->      
<script language="JavaScript">
// <!--
writeMenu()
// -->
</script>
</td>
            
    <td valign="top" class="mainPage">
<!-- Browser check -->
<script type="text/javascript" src="/www_media/scripts/browser_detect.js">
</script>
<script language="JavaScript">
// <!--
if (!isBrowserSupported())
{
    document.write('<table width="100%" cellspacing="0" cellpadding="3"><tr><td class="browserWarning" align="center" colspan=3>');
    document.write('You are using an unsupported browser.');
    document.write('</td></tr></table>');
}
// -->
</script>    
                <!-- The main page contents come next -->
"""        
        footer="""   
        </td>
    </tr>
</table>

<br>
<table class="mainFooter" width="100%" cellspacing="2" cellpadding="1">
<tr>
    <td align=left class="mainFooter">
      GEA %(geaversion)s
    </td>

    <td align="right" class="mainFooter">
        <a href="http://www.python.org/">
            <img src="%(wwwimagesdir)sPythonPoweredAnim.gif" align=right width=55 height=22 alt="[Python Powered]" border=0>
        </a>
    </td>
</tr>
</table>

</body>
</html>"""        
        vars={'pagetitle':'[pagetitle]', 
              'mainfile':'[mainfile]',
              'pageheading':'[pageheading]',
              'background':'[background]', 
              'headerinfo':'[headerinfo]',
              'cpurl':'http://' + GEAVars.siteDomainDict['CP'],   
              'mkurl':'http://' + GEAVars.siteDomainDict['MK'],
              'homepage':'',
              'site':GEAVars.site,
              'jsgea':GEAVars.html.jsGEA,
              'jssort':GEAVars.html.jsSort,
              'jsmenu':GEAVars.html.jsMenu,
              'gealogo':GEAVars.html.geaLogo,
              'geabanner':GEAVars.html.geaBanner,
              'cssfile':GEAVars.html.cssFile,
              'geaversion':GEAVars.versionStr,
              'headerlinks':'[headerlinks]',
              }

        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                

class HTMLDocContWithSideMenu(HTMLObject):
    """Html Container class. Should be the main page object. 
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, reload=None, **kwargs):
          
        #Content-Type:   text/html\n\n
        header="""
<html>
<head>

<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<meta http-equiv="EXPIRES" content="Tue, 01 Jan 1980 1:00:00 GMT">
<meta http-equiv="Pragma" content="no-cache">

%(reload)s

   <!-- external style sheet to control element properties -->
   <link rel="STYLESHEET" href="%(cssfile)s" media="screen" type="text/css">

<title>%(pagetitle)s</title>

<script type="text/javascript" src="/www_media/scripts/browser_detect.js"> </script>
<script language="JavaScript" type="text/javascript" src="%(jsmenu)s"> </script>
<script language="JavaScript" type="text/javascript" src="%(jsgea)s"> </script>
<script language="JavaScript" type="text/javascript" src="%(jssort)s"> </script>
<link rel="shortcut icon" href="%(wwwimagesdir)sfavicon.ico">
</head>
<body width="100%">


<table width="100%" class="mainHeader"  cellspacing="1" cellpadding="0">
    <tr>
        <td align="left" rowspan="2" width="100" height="10">
                <img src="%(geabanner)s" alt="[GEA]">
        </td>
        <td colspan="2" valign="top" align="right">
            %(headerlinks)s  &nbsp; 
        </td>
    </tr>
    <tr>
        <td align="left" valign="bottom" >
            &nbsp; <strong> %(headerinfo)s </strong>
        </td> 
        <td align="right" valign="bottom" class="site">
            Current Site: %(site)s &nbsp; 
        </td>
    </tr>
</table>

<table width="100%" cellspacing="2" cellpadding="0">
    <tr> 
        <td valign="top" width="130">
<!-- Side menu -->      
<script language="JavaScript">
// <!--


writeMenu()
// -->
</script>
        </td>
        <td valign="top" class="mainPage">
		

<!-- Browser check -->
<script language="JavaScript">
// <!--
// Need to check how well Opera and Konqueror are supported.
if (!isBrowserSupported())
{
    document.write('<table width="100%" cellspacing="0" cellpadding="3"><tr><td class="browserWarning" align="center" colspan=3>');
    document.write('You are using an unsupported browser.');
    document.write('</td></tr></table>');
}
// -->

</script>		
		
        <!-- The main page contents come next -->
"""     
        footer="""   
        </td>
    </tr>
</table>

<br>
<table class="mainFooter" width="100%" cellspacing="2" cellpadding="1">
<tr>
    <td align=left class="mainFooter">
      GEA %(geaversion)s
    </td>

    <td align="right" class="mainFooter">
        <a href="http://www.python.org/">
            <img src="%(wwwimagesdir)sPythonPoweredAnim.gif" align=right width=55 height=22 alt="[Python Powered]" border=0>
        </a>
    </td>
</tr>
</table>

</body>
</html>
"""        
        vars={'pagetitle':'[pagetitle]', 
              'mainfile':'[mainfile]',
              'pageheading':'[pageheading]',
              'background':'[background]', 
              'headerinfo':'[headerinfo]',
              'cpurl':'http://' + GEAVars.siteDomainDict['CP'],   
              'mkurl':'http://' + GEAVars.siteDomainDict['MK'],
              'homepage':'',
              'site':GEAVars.site,
              'jsgea':GEAVars.html.jsGEA,
              'jssort':GEAVars.html.jsSort,
              'jsmenu':GEAVars.html.jsMenu,
              'gealogo':GEAVars.html.geaLogo,
              'geabanner':GEAVars.html.geaBanner,
              'cssfile':GEAVars.html.cssFile,
              'geaversion':GEAVars.versionStr,
              'headerlinks':'[headerlinks]',
              'reload':''
              }
                    
        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

        self.setReload(reload)
                
    def setReload(self, reload=None):
        
        if reload is None:
            self.vars['reload']=''
        else:
            self.vars['reload']='<meta http-equiv="REFRESH" content="%s">' % str(reload)
            
                                    
class HTMLHeaderLinks(HTMLObject):
    def __init__(self, **kwargs):

        body="""
        [<strong>Homes</strong>: <a href="%(mkurl)s">MK</a> | <a href="%(cpurl)s">CP</a>]
        """
        vars={'mainfile':'[mainfile]',
                    'cpurl':'http://' + GEAVars.siteDomainDict['CP'],   
                    'mkurl':'http://' + GEAVars.siteDomainDict['MK'],
                }
        
        HTMLObject.__init__(self, body=[body], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLHeaderLinks2(HTMLObject):
    def __init__(self, **kwargs):

        body="""
        [<strong>Current</strong>: <a href="%(mkurl)s%(mainfile)s">MK</a> | <a href="%(cpurl)s%(mainfile)s">CP</a>]
        &nbsp;
        [<strong>Homes</strong>: <a href="%(mkurl)s">MK</a> | <a href="%(cpurl)s">CP</a>]
        """
        vars={'mainfile':'[mainfile]',
                    'cpurl':'http://' + GEAVars.siteDomainDict['CP'],   
                    'mkurl':'http://' + GEAVars.siteDomainDict['MK'],
                }
        
        HTMLObject.__init__(self, body=[body], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLFormCont(HTMLObject):
    """Form container object. All form components should reside here.

    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
          
        header="""
<form METHOD="GET" ACTION="%(cgifile)s">

<script language="JavaScript">
var globalSubmitFunctions=new Array();

function globalSubmit()
{
     for (var i=0; i<globalSubmitFunctions.length; i++)
     {
        if (!globalSubmitFunctions[i]())
        {
            return false;
        }
     }
     return true;
}

</script>

<div align="center">
<input TYPE=submit VALUE="Update" onClick="return globalSubmit();">
<hr>
</div>       
"""
        footer="""
<div align="center">
<hr>
<input TYPE=submit VALUE="Update" onClick="return globalSubmit();">
</div>
</form>
"""
        vars={'cgifile':'[cgifile]'}
        
        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLFormCont2(HTMLObject):
    """Form container object. All form components should reside here.

    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
          
        header="""
<form METHOD="GET" ACTION="%(cgifile)s">

<script language="JavaScript">
var globalSubmitFunctions=new Array();

function globalSubmit()
{
     for (var i=0; i<globalSubmitFunctions.length; i++)
     {
        var result=globalSubmitFunctions[i]();
        
        if (!result)
        {
            return false;
        }
     }
     return true;
}
   
function setFixedTime(timestamp)
{
    setCookie('fixedTimeRange', (timestamp - 600) + "-" + (timestamp + 600), '/');
}

    
</script>
    
"""
        footer="""
<div align="center">
<input TYPE=submit VALUE="Update" onClick="return globalSubmit();">
</div>
</form>
"""
        vars={'cgifile':'[cgifile]'}
        
        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLFormContEmpty(HTMLObject):
    """Form container object. All form components should reside here.

    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    
    def __init__(self, **kwargs):
          
        header="""
<form METHOD="%(method)s" ACTION="%(cgifile)s">      
"""
        footer="""
</form>
"""
        vars={'cgifile':'[cgifile]', 'method':'GET'}
        
        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLFormContSideSubmit(HTMLObject):
    """Form container object. All form components should reside here.

    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
          
        header="""
<script language="JavaScript">
var globalSubmitFunctions=new Array();

function globalSubmit()
{
     for (var i=0; i<globalSubmitFunctions.length; i++)
     {
        var result=globalSubmitFunctions[i]();
        
        if (!result)
        {
            return false;
        }
     }
     return true;
}
</script>
        
<div align="center">
<form METHOD="GET" ACTION="%(cgifile)s">
<table cellpadding=0 cellspacing=0>
<tr>
<td>
"""
        footer="""
</td>
<td align="center" valign="middle">
    <input TYPE=submit VALUE="Update">
</td>
</td>
</table>
</form>
</div>"""
        
        vars={'cgifile':'[cgifile]'}
        
        HTMLObject.__init__(self, header=[header], footer=[footer], vars=vars)
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

 
 
class HTMLOptionsPlotExt(HTMLObject):
    """Extended plot options.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div class="OptionsPlotExt">
<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2"><table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="2"  align="center" valign="middle">Other Options</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="80" align="center" valign="middle">X Label</td>
          <td align="left" valign="middle" class="widgetOptionCell2"><input type=text align="left"  name="%(XLABEL)s" size=45 maxlength=45 value="%(xlabel)s"> 
          </td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="80" align="center" valign="middle">Plot Title</td>
          <td  align="left" valign="middle" class="widgetOptionCell2"><input type=text align="left"  name="%(PLOTTITLE)s" size=45 maxlength=45 value="%(plottitle)s"> 
          </td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="80" align="center" valign="middle">Plot Method</td>
            <td class="widgetOptionCell2"  colspan="2" align="left" valign="middle"><select NAME="%(PLOTMETHOD)s" SIZE=1>
                    <option selected> Stepped</option>
                    <option> NonStepped</option>
                  </select>            
            </td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="80" align="center" valign="middle">Interpolate</td>
          <td align="left" valign="middle" class="widgetOptionCell2"><input type=text align="right"  name="%(INTERPOLATE)s" size=10 maxlength=10 value="%(interpolate)s"> 
          &nbsp;&nbsp;&nbsp[Only used when creating a Spreadsheet - leave 0 (zero) for none]
          </td>
        </tr>
        <tr> 
          <td align="center" colspan="4">&nbsp;</td>
        </tr>
      </table>
      </td>
  </tr>  
</table>
</div>
</div>
<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(PLOTMETHOD)s'), '%(plotmethod)s');
// -->
</script>

"""
        vars={'xlabel':'[xlabel]', 
              'plottitle':'[plottitle]',
             'plotmethod':'[plotmethod]',
             'interpolate':'[interpolate]'
            }

        taggedVars={'XLABEL':'XLABEL',
                    'PLOTTITLE':'PLOTTITLE',
                    'PLOTMETHOD':'PLOTMETHOD',
                    'INTERPOLATE':'INTERPOLATE'
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

class HTMLOptionsPlot(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="700">
  <tr> 
    <td align="center">
        <table>
            <tr>
                <td>
                     <table>
                        <tr> 
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Min
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
                          </td>
                          <td align="center" valign="middle" width="68"  class="widgetLabel">
                              Y Max
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
                          </td>
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Label
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YLABEL)s" size=10 maxlength=30 value="%(ylabel)s"> 
                          </td>          
                        </tr>
                        <tr> 
                          <td class="widgetLabel" align="center" valign="middle">Format</td>
                            <td class="widgetOptionCell2" align="left" valign="middle"><select NAME="%(FORMAT)s" SIZE=1>
                                    <option> Plot</option>
                                    <option> Spreadsheet</option>
                                  </select>            
                            </td>
                             <td class="widgetLabel"  align="center" valign="middle">
                                 DPI 
                            </td>
                             <td align="left" valign="middle" class="widgetOptionCell2">
                                 <select NAME="%(DPI)s" SIZE=1>
                                    <option> 50</option>
                                    <option> 75</option>
                                    <option> 80</option>
                                    <option SELECTED> 85</option>
                                    <option> 90</option>
                                    <option> 95</option>                    
                                    <option> 100</option>
                                    <option> 125</option>
                                    <option> 150</option>
                                    <option> 175</option>
                                    <option> 200</option>
                                    <option> 225</option>
                                    <option> 250</option>
                                    <option> 275</option>
                                    <option> 300</option>
                                  </select>
                            </td>
                
                            <td class="widgetLabel"  align="center" valign="middle">
                                 Legend 
                            </td>
                             <td align="left" valign="middle" class="widgetOptionCell2">
                                 <select NAME="%(LEGEND)s" SIZE=1>
                                    <option> Outside</option>
                                    <option SELECTED> Inside</option>
                                    <option> Off</option>
                                  </select>
                            </td>
                        </tr>
                     </table>
                     </td>
                     <td>
                            <table class="widgetLabel">
                                <tr>
                                    <td align="left" valign="middle" >
                                       Plot Rate of
                                    </td>  
                                </tr>
                                <tr>
                                    <td align="center" valign="middle">Change:
                                      <input type=checkbox %(rateofchange)s name="%(RATEOFCHANGE)s" value="checked">
                                    </td>  
                                </tr>
                            </table>
                    </td>
        </tr>
            
      </table>
      </td>
  </tr>  
</table>

<input type=hidden name=%(GRIDLINES)s value="%(gridlines)s">

</div>

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(FORMAT)s'), '%(format)s');
selectSingleOptByText(gfo('%(LEGEND)s'), '%(legend)s');
// -->
</script>

"""
        vars={'imagefilename':'[imagefilename]', 
              'dataFileName':'[dataFileName]',
              'gridlines':'[gridlines]', 
              'rateofchange':'[rateofchange]',
              'legend':'[legend]', 
              'ymax':'[ymax]', 'ymin':'[ymin]','ylabel':'[ylabel]',
              'dpi':'[dpi]',
              'format':'[format]',
            }

        taggedVars={'DPI':'DPI', 
                    'GRIDLINES':'GRIDLINES', 
                    'LEGEND':'LEGEND',
                    'UPDATE':'UPDATE',
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'FORMAT':'FORMAT',
                    'RATEOFCHANGE':'RATEOFCHANGE',
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

class HTMLOptionsPlot2(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
<table width="700">
    <tr>
        <td colspan=3 valign="top" align="left">
            <table width="100%" >
                <tr>
                    <td class="heading"  align="center" colspan=2 valign="middle">
                        Options &nbsp;&nbsp;&nbsp;&nbsp;<a href="%(helplink)s">[Help]</a>
                    </td>
                    
                <td class="widgetLabel"  align="center" valign="middle">
                    Format
                </td>
                <td class="widgetOptionCell2" align="left" valign="middle">
                        <select NAME="%(FORMAT)s" SIZE=1>
                            <option> Plot</option>
                            <option> Spreadsheet</option>
                        </select>            
                </td>
                <td class="widgetLabel"   align="center" valign="middle">
                    Interpolate [S]
                </td>
                <td align="left" valign="middle" class="widgetOptionCell2">
                    <input type=text align="right"  name="%(INTERPOLATE)s" size=10 maxlength=10 value="%(interpolate)s"> 
                </td>
                <td class="widgetLabel"  align="center" valign="middle">
                    Fill [S]
                </td>
                <td class="widgetOptionCell2" align="left" valign="middle">
                        <select NAME="%(FILL)s" SIZE=1>
                            <option> No </option>
                            <option> Yes </option>
                        </select>            
                </td>


            </tr>
                <tr>
                            <td class="widgetLabel"  align="center" valign="middle">
                                 DPI 
                            </td>
                             <td align="left" valign="middle" class="widgetOptionCell2">
                                 <select NAME="%(DPI)s" SIZE=1>
                                    <option> 50</option>
                                    <option> 75</option>
                                    <option> 80</option>
                                    <option SELECTED> 85</option>
                                    <option> 90</option>
                                    <option> 95</option>                    
                                    <option> 100</option>
                                    <option> 125</option>
                                    <option> 150</option>
                                    <option> 175</option>
                                    <option> 200</option>
                                    <option> 225</option>
                                    <option> 250</option>
                                    <option> 275</option>
                                    <option> 300</option>
                                  </select>
                            </td>
                
                            <td class="widgetLabel"  align="center" valign="middle">
                                 Legend 
                            </td>
                             <td align="left" valign="middle" class="widgetOptionCell2">
                                 <select NAME="%(LEGEND)s" SIZE=1>
                                    <option> Outside</option>
                                    <option SELECTED> Inside</option>
                                    <option> Off</option>
                                  </select>
                            </td>
                              <td class="widgetLabel" width="80" align="center" valign="middle">Line Style</td>
                                <td class="widgetOptionCell2"  align="left" valign="middle">
                                <select NAME="%(LINESTYLE)s" SIZE=1>                                
                                    <option selected> steps </option>
                                    <option> steps-o </option>
                                    <option> o-o </option>
                                    <option> o </option>
                                    <option> - </option>
                                    <option> -- </option>
                                    <option> d-d </option>
                                    <option> d </option>
                                    <option> x-x </option>
                                    <option> x </option>
                                    <option> +-+ </option>
                                    <option> + </option>
                                      </select>            
                                </td>
                            <td align="center" valign="middle" class="widgetLabel" colspan="2">
                                Rate Of Change:<input type=checkbox %(rateofchange)s name="%(RATEOFCHANGE)s" value="checked">

                            </td>
                        </td>  
                </tr>
                <tr>
                                      <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Min
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
                          </td>
                          <td align="center" valign="middle" width="68"  class="widgetLabel">
                              Y Max
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
                          </td>
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Label
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YLABEL)s" size=10 maxlength=30 value="%(ylabel)s"> 
                          </td>     
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Scale
                          </td>                          
                          <td class="widgetOptionCell2"  align="left" valign="middle"><select NAME="%(YSCALE)s" SIZE=1>
                                        <option selected> linear </option>
                                        <option> log </option>
                                      </select>            
                          </td>                            
                </tr>
                <tr>
                        <td align="center" valign="middle" width="68" class="widgetLabel">
                              Title                          
                                   <tiny> [<a href="javascript:void(0)" onMouseDown="
                                     gfo('%(PLOTTITLE)s').value='';
                                     return false;"
                                     onClick="return false;">Clear</a>] </tiny>
                    </td>                                 
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2" colspan=3>
                              <input type=text align="left"  name="%(PLOTTITLE)s" size=32  maxlength=70 value="%(plottitle)s"> 
                          </td>
   
                    
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              X Label
                          </td>                                        
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(XLABEL)s" size=10 maxlength=30 value="%(xlabel)s"> 
                          </td>                               
                          
                          
                    <td align="center" valign="middle" class="widgetLabel">
                              Reduce
                    </td>
                    <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="right"  name="%(REDUCE)s" size=10 maxlength=20 value="%(reduce)s"> 
                    </td>                                                                          
                </tr>
                
            </table>
        </td>              
    </tr>
    
    
</table>
<input type=hidden name=%(GRIDLINES)s value="%(gridlines)s">

<!-- For now hidden... will provide this as user settable... -->
<input type=hidden name=%(XAXISCHANNEL)s value="%(xaxischannel)s">
</div>

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(FILL)s'), '%(fill)s');
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(FORMAT)s'), '%(format)s');
selectSingleOptByText(gfo('%(LEGEND)s'), '%(legend)s');
selectSingleOptByText(gfo('%(LINESTYLE)s'), '%(linestyle)s');
selectSingleOptByText(gfo('%(YSCALE)s'), '%(yscale)s');

// -->
</script>

"""
        vars={'imagefilename':'[imagefilename]', 
              'dataFileName':'[dataFileName]',
              'gridlines':'[gridlines]', 
              'rateofchange':'[rateofchange]',
              'legend':'[legend]', 
              'ymax':'[ymax]', 'ymin':'[ymin]','ylabel':'[ylabel]',
              'plottitle':'[plottitle]',
              'dpi':'[dpi]',
              'format':'[format]',
              'xlabel':'[xlabel]', 
              'plottitle':'[plottitle]',
              'linestyle':'[linestyle]',
              'interpolate':'[interpolate]',
              'helplink':'[helplink]',
              'reduce':'[reduce]',
              'fill':'[fill]',
              'xaxischannel':'[xaxischannel]',
              'yscale':'[yscale]',
            }

        taggedVars={'DPI':'DPI', 
                    'GRIDLINES':'GRIDLINES', 
                    'LEGEND':'LEGEND',
                    'UPDATE':'UPDATE',
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'PLOTTITLE':'PLOTTITLE',
                    'FORMAT':'FORMAT',
                    'RATEOFCHANGE':'RATEOFCHANGE',
                    'XLABEL':'XLABEL',
                    'LINESTYLE':'LINESTYLE',
                    'INTERPOLATE':'INTERPOLATE',
                    'REDUCE':'REDUCE',
                    'FILL':'FILL',
                    'XAXISCHANNEL':'XAXISCHANNEL',
                    'YSCALE':'YSCALE'
                    }
             
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLOptionsPlot3(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
<table width="700">
    <tr>
        <td colspan=3 valign="top" align="left">
            <table width="100%" >
                <tr>
                    <td class="heading"  align="center" colspan=2 valign="middle">
                        Options &nbsp;&nbsp;&nbsp;&nbsp;<a href="%(helplink)s">[Help]</a>
                    </td>
                    <td align="center" valign="middle" class="widgetLabel">
                              Reduce
                    </td>
                    <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="right"  name="%(REDUCE)s" size=10 maxlength=20 value="%(reduce)s"> 
                    </td>
                <td class="widgetLabel"  align="center" valign="middle">
                    Format
                </td>
                <td class="widgetOptionCell2" align="left" valign="middle">
                        <select NAME="%(FORMAT)s" SIZE=1>
                            <option> Plot</option>
                            <option> Spreadsheet</option>
                        </select>            
                </td>
                <td class="widgetLabel"   align="center" valign="middle">
                    Interpolate
                </td>
                <td align="left" valign="middle" class="widgetOptionCell2">
                    <input type=text align="right"  name="%(INTERPOLATE)s" size=10 maxlength=10 value="%(interpolate)s"> 
                </td>

            </tr>
                <tr>
                            <td class="widgetLabel"  align="center" valign="middle">
                                 DPI 
                            </td>
                             <td align="left" valign="middle" class="widgetOptionCell2">
                                 <select NAME="%(DPI)s" SIZE=1>
                                    <option> 50</option>
                                    <option> 75</option>
                                    <option> 80</option>
                                    <option SELECTED> 85</option>
                                    <option> 90</option>
                                    <option> 95</option>                    
                                    <option> 100</option>
                                    <option> 125</option>
                                    <option> 150</option>
                                    <option> 175</option>
                                    <option> 200</option>
                                    <option> 225</option>
                                    <option> 250</option>
                                    <option> 275</option>
                                    <option> 300</option>
                                  </select>
                            </td>
                
                            <td class="widgetLabel"  align="center" valign="middle">
                                 Legend 
                            </td>
                             <td align="left" valign="middle" class="widgetOptionCell2">
                                 <select NAME="%(LEGEND)s" SIZE=1>
                                    <option> Outside</option>
                                    <option SELECTED> Inside</option>
                                    <option> Off</option>
                                  </select>
                            </td>
                              <td class="widgetLabel" width="80" align="center" valign="middle">Plot Method</td>
                                <td class="widgetOptionCell2"  align="left" valign="middle"><select NAME="%(PLOTMETHOD)s" SIZE=1>
                                        <option selected> Stepped</option>
                                        <option> NonStepped</option>
                                      </select>            
                                </td>
                            <td align="center" valign="middle" class="widgetLabel" colspan="2">
                                Rate Of Change:<input type=checkbox %(rateofchange)s name="%(RATEOFCHANGE)s" value="checked">

                            </td>
                        </td>  
                </tr>
                <tr>
                                      <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Min
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
                          </td>
                          <td align="center" valign="middle" width="68"  class="widgetLabel">
                              Y Max
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
                          </td>
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              Y Label
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(YLABEL)s" size=10 maxlength=30 value="%(ylabel)s"> 
                          </td>     
                          <td align="center" valign="middle" width="68" class="widgetLabel">
                              X Label
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2">
                              <input type=text align="left"  name="%(XLABEL)s" size=10 maxlength=30 value="%(xlabel)s"> 
                          </td>     
                </tr>
                <tr>
                        <td align="center" valign="middle" width="68" class="widgetLabel">
                              Title
                          </td>
                          <td align="left" valign="middle" class="widgetOptionCell2" colspan=5>
                              <input type=text align="left"  name="%(PLOTTITLE)s" size=60  maxlength=70 value="%(plottitle)s"> 
                          </td>
                    <td align="left" colspan=2>
                            [<a href="javascript:void(0)" onMouseDown="
                            gfo('%(PLOTTITLE)s').value='';
                            return false;"
                            onClick="return false;">Clear Title</a>]
                    </td>                          
                          
                </tr>
                
            </table>
        </td>              
    </tr>
    
    
</table>
<input type=hidden name=%(GRIDLINES)s value="%(gridlines)s">

<!-- For now hidden... will provide this as user settable... -->
<input type=hidden name=%(XAXISCHANNEL)s value="%(xaxischannel)s">
</div>

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(FORMAT)s'), '%(format)s');
selectSingleOptByText(gfo('%(LEGEND)s'), '%(legend)s');
selectSingleOptByText(gfo('%(PLOTMETHOD)s'), '%(plotmethod)s');
// -->
</script>

"""
        vars={'imagefilename':'[imagefilename]', 
              'dataFileName':'[dataFileName]',
              'gridlines':'[gridlines]', 
              'rateofchange':'[rateofchange]',
              'legend':'[legend]', 
              'ymax':'[ymax]', 'ymin':'[ymin]','ylabel':'[ylabel]',
              'plottitle':'[plottitle]',
              'dpi':'[dpi]',
              'format':'[format]',
              'xlabel':'[xlabel]', 
              'plottitle':'[plottitle]',
              'plotmethod':'[plotmethod]',
              'interpolate':'[interpolate]',
              'helplink':'[helplink]',
              'reduce':'[reduce]',
              'xaxischannel':'[xaxischannel]'
            }

        taggedVars={'DPI':'DPI', 
                    'GRIDLINES':'GRIDLINES', 
                    'LEGEND':'LEGEND',
                    'UPDATE':'UPDATE',
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'PLOTTITLE':'PLOTTITLE',
                    'FORMAT':'FORMAT',
                    'RATEOFCHANGE':'RATEOFCHANGE',
                    'XLABEL':'XLABEL',
                    'PLOTMETHOD':'PLOTMETHOD',
                    'INTERPOLATE':'INTERPOLATE',
                    'REDUCE':'REDUCE',
                    'XAXISCHANNEL':'XAXISCHANNEL'
                    }
             
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                

class HTMLOptionsAdvPlot(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="700">
  <tr> 
    <td align="center">
     <table>
        <tr> 
          <td class="widgetLabel" align="center" valign="middle">Format</td>
            <td class="widgetOptionCell2" align="left" valign="middle"><select NAME="%(FORMAT)s" SIZE=1>
                    <option> Plot</option>
                    <option> Spreadsheet</option>
                  </select>            
            </td>
             <td class="widgetLabel"  align="center" valign="middle">
                 DPI 
            </td>
             <td align="left" valign="middle" class="widgetOptionCell2">
                 <select NAME="%(DPI)s" SIZE=1>
                    <option> 50</option>
                    <option> 75</option>
                    <option SELECTED> 100</option>
                    <option> 125</option>
                    <option> 150</option>
                    <option> 175</option>
                    <option> 200</option>
                    <option> 225</option>
                    <option> 250</option>
                    <option> 275</option>
                    <option> 300</option>
                  </select>
            </td>

            <td class="widgetLabel"  align="center" valign="middle">
                 Legend 
            </td>
             <td align="left" valign="middle" class="widgetOptionCell2">
                 <select NAME="%(LEGEND)s" SIZE=1>
                    <option> Outside</option>
                    <option SELECTED> Inside</option>
                    <option> Off</option>
                  </select>
            </td>
            
            <!--
            <td class="widgetLabel"  align="center" valign="middle">
                  Reduce
            </td>
             <td class="widgetOptionCell2"  colspan="" align="left" valign="middle">
            <input type=text align="left"  name="%(REDUCE)s" size=10 maxlength=20 value="%(reduce)s"> 
            </td>
            -->
            
      </table>
      </td>
  </tr>  
</table>

<input type=hidden name=%(GRIDLINES)s value="%(gridlines)s">

</div>

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(FORMAT)s'), '%(format)s');
selectSingleOptByText(gfo('%(LEGEND)s'), '%(legend)s');
// -->
</script>

"""
        vars={'imagefilename':'[imagefilename]', 
              'dataFileName':'[dataFileName]',
              'gridlines':'checked', 
              'legend':'[legend]', 
              'ymax':'[ymax]', 'ymin':'[ymin]','ylabel':'[ylabel]',
             'dpi':'[dpi]',
             'format':'[format]'
            }

        taggedVars={'DPI':'DPI', 
                    'GRIDLINES':'GRIDLINES', 
                    'LEGEND':'LEGEND',
                    'UPDATE':'UPDATE',
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'FORMAT':'FORMAT'
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
    
class HTMLOptionsLateralsPlot(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2"><table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="4"  align="center" valign="middle">Options</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">View</td>
            <td class="widgetOptionCell"  colspan="3" align="left" valign="middle"><select NAME="%(VIEW)s" SIZE=1>
                    <option selected> Symmetric</option>
                    <option> DM_Screen</option>
                  </select>            
            </td>
        </tr>
        <tr> 
          <td align="center" colspan="4">&nbsp;</td>
        </tr>
      </table>
      </td>
  </tr>  
</table>
</div>
<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(VIEW)s'), '%(view)s');
// -->
</script>

"""
        vars={'plottitle':'[plottitle]', 
             'view':'[view]'
            }

        taggedVars={
                    'PLOTTITLE':'PLOTTITLE',
                    'VIEW':'VIEW'
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                

  
class HTMLOptionsSurfacePlot(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2"><table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="4"  align="center" valign="middle">Options</td>
        </tr>
<!--
        <tr> 
          <td width="68" align="center" valign="middle" class="widgetLabel">Extrema</td>
          <td width="134" align="left" valign="middle" class="widgetOptionCell"><label>Min:</label> <input type=text align="right"  name="%(MIN)s" size=10 maxlength=20 value="%(min)s"> 
           &nbsp;&nbsp;&nbsp;&nbsp;  blank = auto-selection.
          </td>
          <td width="140" align="left" valign="middle" class="widgetOptionCell"><label>Max:</label> <input type=text align="right"  name="%(MAX)s" size=10 maxlength=20 value="%(max)s"> 
           &nbsp;&nbsp;&nbsp;&nbsp;  blank = auto-selection.
          </td>
        </tr>
        <tr> 
          <td width="68" align="center" valign="middle" class="widgetLabel">Plot Title</td>
          <td align="left" valign="middle" colspan="3" class="widgetOptionCell"><input type=text align="right"  name="%(PLOTTITLE)s" size=40 maxlength=40 value="%(plottitle)s"> 
             &nbsp;&nbsp;&nbsp;&nbsp; If field left empty, automatic title(s) will be generated  
          </td>  
        </tr>
-->
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Source</td>
            <td class="widgetOptionCell"  colspan="3" align="left" valign="middle"><select NAME="%(SOURCE)s" SIZE=1>
                    <option> Pneumatic</option>
                    <option> PnuError</option>
                    <option> Hydraulic</option>
                    <option> Pneumatic/Hydraulic</option>
                  </select>            
            </td>
        </tr>
        <tr> 
          <td align="center" colspan="4">&nbsp;</td>
        </tr>
      </table>
      </td>
  </tr>  
</table>
</div>
<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(SOURCE)s'), '%(source)s');
// -->
</script>

"""
        vars={'plottitle':'[plottitle]', 
             'min':'[min]',
             'max':'[max]', 
             'source':'[source]'
            }

        taggedVars={'MIN':'MIN',
                    'MAX':'MAX',
                    'PLOTTITLE':'PLOTTITLE',
                    'SOURCE':'SOURCE'
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLOptionsOverloads(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2"><table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="4"  align="center" valign="middle">Options</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Source</td>
            <td class="widgetOptionCell"  colspan="3" align="left" valign="middle"><select NAME="%(SOURCE)s" SIZE=1>
                    <option> Pneumatic</option>
                    <option> Hydraulic</option>
                  </select>            
            </td>
        </tr>
        <tr> 
          <td align="center" colspan="4">&nbsp;</td>
        </tr>
      </table>
      </td>
  </tr>  
</table>
</div>
<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(SOURCE)s'), '%(source)s');
// -->
</script>

"""
        vars={'source':'[source]'}

        taggedVars={'SOURCE':'SOURCE'}
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                

class HTMLOptionsNLNightly(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
        
<!-- ****************************
HTMLOptionsNLNightly 
******************************-->
<input type=hidden name="%(FORMAT)s" value="Nightly">
 <!-- No need for the user to midify hour/minute/second. Take noon. -->
<input type=hidden name=%(STARTHOUR)s   value="12">
<input type=hidden name=%(STARTMINUTE)s value="00">
<input type=hidden name=%(STARTSECOND)s value="00">

<div align="center">
 <table>

 <tr> 
           <td class="widgetLabel" width="68" align="center" valign="middle">Telescope</td>
            <td class="widgetOptionCell" align="left" valign="middle"><select NAME="%(SITE)s" SIZE=1>
                    <option selected> MK</option>
                    <option> CP</option>
                  </select>
            </td>
 
        <td class="widgetTimeLabel" align="center">Night of: (M/D/Y)</td>
        <td width="250"> 
        <select NAME=%(STARTMONTH)s SIZE=1>
                <option> Jan</option>
                <option> Feb</option>
                <option> Mar</option>
                <option> Apr</option>
                <option> May</option>
                <option> Jun</option>
                <option> Jul</option>
                <option> Aug</option>
                <option> Sep</option>
                <option> Oct</option>
                <option> Nov</option>
                <option> Dec</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1>
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
            </td>
            
            
      </tr>
</table>
</div>


<script language="JavaScript">
// <!--
//////
// Initial setup.
/////
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');

//Set up default time.
setStartTimeOptions('0', "None", 
                    '0', "None", 
                    '0', "None",  
                    '%(startday)s', gfo('%(STARTDAY)s'), 
                    '%(startmonth)s', gfo('%(STARTMONTH)s'), 
                    '%(startyear)s', gfo('%(STARTYEAR)s')); 
// -->
</script>
"""
        vars={'site':'[site]',
             'startyear':'[startyear]', 
             'startmonth':'[startmonth]', 
             'startday':'[startday]',
            }

        taggedVars={
                    'SITE':'SITE', 
                    'STARTDAY':'STARTDAY',
                    'STARTMONTH':'STARTMONTH', 
                    'STARTYEAR':'STARTYEAR',
                    'STARTSECOND':'STARTSECOND', 
                    'STARTMINUTE':'STARTMINUTE', 
                    'STARTHOUR':'STARTHOUR',
                    'FORMAT':'FORMAT',
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
                

class HTMLOptionsNLReport(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
        
<!-- ****************************
HTMLOptionsNLReport 
******************************-->
<input type=hidden name="%(FORMAT)s" value="Report">

<div align="center">
 <table>

 <tr> 
           <td class="widgetLabel" width="68" align="center" valign="middle">Telescope</td>
            <td class="widgetOptionCell" colspan="3" align="left" valign="middle">
                <select NAME="%(SITE)s" SIZE=1>
                    <option selected> MK</option>
                    <option> CP</option>
                  </select>            
            </td>
           <td class="widgetLabel" width="68" align="center" valign="middle">Include Plot</td>
            <td class="widgetOptionCell" colspan="3" align="left" valign="middle">
                <select NAME="%(INCLUDEPLOT)s" SIZE=1>
                    <option> Yes</option>
                    <option selected> No</option>
                  </select>                        
            </td>            
           <td class="widgetLabel" width="68" align="center" valign="middle">
                For Printing
           </td>
            <td class="widgetOptionCell" align="left" valign="middle">
                <input type=checkbox %(forprinting)s name=%(FORPRINTING)s value="Checked">
            </td>
</tr>
</table>
</div>


<script language="JavaScript">
// <!--
//////
// Initial setup.
/////
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');
selectSingleOptByText(gfo('%(INCLUDEPLOT)s'), '%(includeplot)s');

                    
// -->
</script>
"""
        vars={'site':'[site]','forprinting':'[forprinting]', 'includeplot':'[includeplot]' }

        taggedVars={
                    'SITE':'SITE', 
                    'FORMAT':'FORMAT',
                    'FORPRINTING':'FORPRINTING',
                    'INCLUDEPLOT':'INCLUDEPLOT'
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
                

                
class HTMLOptionsFrs(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<!-- ****************************
HTMLOptionsFrs 
******************************-->
    
<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2">
        <table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="8"  align="center" valign="middle">Options</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Telescope</td>
            <td class="widgetOptionCell" colspan="3" align="left" valign="middle"><select NAME="%(SITE)s" SIZE=1>
                    <option selected> MK</option>
                    <option> CP</option>
                  </select>
            </td>
            <td class="widgetLabel" width="68" align="center" valign="middle">Format</td>
            <td class="widgetOptionCell" colspan="3" align="left" valign="middle"><select NAME="%(FORMAT)s" SIZE=1>
                    <option selected> night</option>    
                  </select>
            </td>
        </tr>
      </table>
      </td>
  </tr>  
</table>
<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(FORMAT)s'), '%(format)s');
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');

// -->
</script>
</div>
"""
        vars={'site':'[site]',
             'format':'[format]',
             'cgifile':'[cgifile]'
            }

        taggedVars={'FORMAT':'FORMAT',
                    'SITE':'SITE',
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
        
class HTMLOptionsFrsUser(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""

<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2">
        <table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="4"  align="center" valign="middle">Options</td>
        </tr>
        <tr> 
          <td align="center" class="widgetLabel" width="68" valign="middle">
            User
           </td>
          <td class="widgetOptionCell">
            <input type=text name="%(USER)s" size=20 maxlength=256 value="%(user)s"></td>
          </td>
        
          <td class="widgetLabel" width="68" align="center" valign="middle">Filter</td>
            <td class="widgetOptionCell" colspan="3" align="left" valign="middle"><select NAME="%(FILTER)s" SIZE=1>
                    <option selected> Work in progress</option>
                    <option> Closed</option>
                    <option> All</option>
                  </select>
            </td>
        </tr>
      </table>
      </td>
  </tr>  
</table>

<input type=hidden name=%(FORMAT)s value="%(format)s">

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(FILTER)s'), '%(filter)s');
// -->
</script>
</div>
"""
        #Maybe should set default format to 'user' since technically thats the only case when this widget should be used...
        vars={'filter':'[filter]', 'user':'[user]', 'format':'[format]'}
        taggedVars={'FILTER':'FILTER', 'USER':'USER', 'FORMAT':'FORMAT'}
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
    
class HTMLOptionsFrsTicket(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="600">
  <tr> 
    <td colspan="2">
        <table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="4"  align="center" valign="middle">Options</td>
        </tr>
        <tr> 
          <td align="center" class="widgetLabel" width="68" valign="middle">
            Ticket
           </td>
          <td class="widgetOptionCell">
            <input type=text name="%(CASEID)s" size=20 maxlength=256 value="%(caseid)s"></td>
          </td>
        </tr>
      </table>
      </td>
  </tr>  
</table>

<input type=hidden name=%(FORMAT)s value="%(format)s">
</div>
"""
        #Maybe should set default format to 'ticket' since technically thats the only case when this widget should be used...
        vars={'caseid':'[caseid]', 'format':'[format]'}
        taggedVars={'CASEID':'CASEID', 'FORMAT':'FORMAT'}
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
    
    
class HTMLOptionsFrsStats(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="400" border=0>
  <tr> 
    <td colspan="2">
      <table width="100%" border=0>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">View</td>
          <td class="widgetOptionCell" align="left" valign="middle">
            <select NAME="%(VIEW)s" SIZE=1>
             <option selected> StatsTable</option>
             <option> Plot</option>
            </select>
            &nbsp;&nbsp;&nbsp;&nbsp;
          </td>
          <td colspan="4" class="widgetOptionCell" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
           <center>
           <a id="HTMLOptionsFrsStats_plottingOptionsShowLink%(JS)s" href="javascript:void(0)" onMouseDown="
                hideEl('HTMLOptionsFrsStats_plottingOptionsShowLink%(JS)s');
                showEl('HTMLOptionsFrsStats_plottingOptionsHideLink%(JS)s');
                showEl('HTMLOptionsFrsStats_plottingOptions%(JS)s');
                return false;"
                onClick="return false;">[Show Plotting Options...]</a>
                <a id="HTMLOptionsFrsStats_plottingOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                hideEl('HTMLOptionsFrsStats_plottingOptionsHideLink%(JS)s');
                showEl('HTMLOptionsFrsStats_plottingOptionsShowLink%(JS)s');
                hideEl('HTMLOptionsFrsStats_plottingOptions%(JS)s');
                return false;"
                onClick="return false;">[Hide Plotting Options...]</a>
           </center>
          </td>
         </tr>
        </tr>
        <tr><td colspan=4>
        
        <div id="HTMLOptionsFrsStats_plottingOptions%(JS)s">
        <table width="100%">
        <tr> 
              <td align="center" valign="middle" width="68" class="widgetLabel">
                  Y Min
              </td>
              <td align="left" valign="middle" class="widgetOptionCell">
                  <input type=text align="left"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
              </td>
              <td align="center" valign="middle" width="68"  class="widgetLabel">
                  Y Max
              </td>
              <td align="left" valign="middle" class="widgetOptionCell">
                  <input type=text align="left"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
              </td>      
        </tr>  
        </table>
        </div>
    
        </td></tr>
      </table>
      </td>
  </tr>  
</table>
<input type=hidden name=%(FORMAT)s value="%(format)s">

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////
// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(VIEW)s'), '%(view)s');
selectSingleOptByText(gfo('%(SHOW)s'), '%(show)s');

hideEl('HTMLOptionsFrsStats_plottingOptionsHideLink%(JS)s');
showEl('HTMLOptionsFrsStats_plottingOptionsShowLink%(JS)s');
hideEl('HTMLOptionsFrsStats_plottingOptions%(JS)s');

// -->
</script>
</div>
"""
        vars={'site':'[site]',
             'format':'[format]',
             'view':'[view]',
             'show':'[show]',
             'ymin':'[ymin]',
             'ymax':'[ymax]'
            }

        taggedVars={'FORMAT':'FORMAT',
                    'VIEW':'VIEW',   
                    'SHOW':'SHOW',    
                    'SITE':'SITE',
                    'JS':'JS',
                    'YMIN':'YMIN',
                    'YMAX':'YMAX'
                    }
                    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
        
class HTMLFormFrs(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<form METHOD="GET" ACTION="%(cgifile)s">  
<input type=hidden name=%(STARTHOUR)s value="07">
<input type=hidden name=%(STARTMINUTE)s value="30">
<input type=hidden name=%(STARTSECOND)s value="00">

<div align="center">

 <table width="100%" cellpadding=1 cellspacing=1>
        <tr> 
           <td class="widgetOptionCell2" align="center" valign="middle">
              <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=last24Hours">Last 24 Hours (MK)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=last7Days">Last 7 Days (MK)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=last30Days">Last 30 Days (MK)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=last3Months">Last 3 Months (MK)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=thistwoWeeks">Last 2 Weeks (MK)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=thisWeek">This week (MK)</a>
            </td>
        </tr>
        <tr> 
           <td class="widgetOptionCell2" align="center" valign="middle">        
              <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=last24Hours">Last 24 Hours (CP)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=last7Days">Last 7 Days (CP)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=last30Days">Last 30 Days (CP)</a>
            <strong>|</strong>
            <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=last3Months">Last 3 Months (CP)</a>
            <strong>|</strong>            
            <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=thistwoWeeks">Last 2 Weeks (CP)</a>
            <strong>|</strong>            
            <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=thisWeek">This week (CP)</a>
            </td>            
        </tr>        
</table>
      
<table width="600" cellpadding=1 cellspacing=1>
  <tr> 
    <td>
        <table width="100%" cellpadding=1 cellspacing=1>
        <tr> 
            <td class="widgetLabel" align="center" valign="middle">
              Telescope
            </td>
            <td class="widgetOptionCell2" align="left" valign="middle">
                 <select NAME="%(SITE)s" SIZE=1>
                    <option selected> MK</option>
                    <option> CP</option>
                  </select>
            </td>
        <td class="widgetTimeLabel" align="center" valign="middle"> Night of: (M/D/Y)</td>
        <td align="left" class="widgetOptionCell2"> <select NAME=%(STARTMONTH)s SIZE=1 >
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1>
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>

              <input TYPE=submit VALUE="Update">
                <!--
                    When submitting using the "update" button, want the format to be "night"
                -->
              <input type=hidden name=%(FORMAT)s value="night">
            </td>
        </tr>
      </table>
      </td>
  </tr>  
</table>

</form>
<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');

//Set up default time for the time selection widget.. 
setStartTimeOptions('0', "None", 
                    '0', "None", 
                    '0', "None",  
                    '%(startday)s', gfo('%(STARTDAY)s'), 
                    '%(startmonth)s', gfo('%(STARTMONTH)s'), 
                    '%(startyear)s', gfo('%(STARTYEAR)s')); 

// -->
</script>
</div>
"""
        vars={'site':'[site]',
            'startyear':'[startyear]', 
            'startmonth':'[startmonth]', 
            'startday':'[startday]',
            }

        taggedVars={'FORMAT':'FORMAT',
                    'SITE':'SITE',
                    'STARTSECOND':'STARTSECOND', 
                    'STARTMINUTE':'STARTMINUTE', 
                    'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY',
                    'STARTMONTH':'STARTMONTH', 
                    'STARTYEAR':'STARTYEAR',
                    }

        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)        
                

class HTMLFormFrsOLD(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<form METHOD="GET" ACTION="%(cgifile)s">  
<input type=hidden name=%(STARTHOUR)s   value="07">
<input type=hidden name=%(STARTMINUTE)s value="30">
<input type=hidden name=%(STARTSECOND)s value="00">

<div align="center">
<table width="600" cellpadding=1 cellspacing=0>
  <tr> 
    <td>
        <table width="100%" cellpadding=0 cellspacing=0>
        <tr> 
          <td class="widgetLabel" colspan="4" align="center" valign="middle">Quick Links... faults for:</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">
              MK
          </td>
           <td class="widgetOptionCell2" align="center" valign="middle">
              <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=last24Hours">Last 24 hours</a>
    </td>
   <td class="widgetOptionCell2" align="center" valign="middle">
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=last7Days">Last 7 days</a>
    </td>
   <td class="widgetOptionCell2" align="center" valign="middle">
            <a href="/pages/remedy/frsPage?SITE=MK&FORMAT=thisWeek">This week</a>
          </td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">
              CP
          </td>
           <td class="widgetOptionCell2" align="center" valign="middle">
              <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=last24Hours">Last 24 hours</a>
    </td>
   <td class="widgetOptionCell2" align="center" valign="middle">
              <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=last7Days">Last 7 days</a>
    </td>
   <td class="widgetOptionCell2" align="center" valign="middle">
              <a href="/pages/remedy/frsPage?SITE=CP&FORMAT=thisWeek">This week</a>
          </td>
        </tr>
      </table>
      </td>
  </tr>  
</table>
<table width="600" cellpadding=1 cellspacing=0>
  <tr> 
    <td colspan="5">
        <table width="100%" cellpadding=0 cellspacing=0>
        <tr> 
          <td class="widgetLabel" colspan="5"  align="center" valign="middle">Arbitrary site/time selection</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">
              Telescope
          </td>
         <td class="widgetOptionCell2" align="center" valign="middle">
                 <select NAME="%(SITE)s" SIZE=1>
                    <option selected> MK</option>
                    <option> CP</option>
                  </select>
        </td>
      <td class="widgetTimeLabel" align="center" width="125"> Night of: (M/D/Y)</td>
        <td align="center" class="widgetOptionCell2"> <select NAME=%(STARTMONTH)s SIZE=1 >
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1>
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
        
              <input TYPE=submit VALUE="Update">
                <!--
                    When submitting using the "update" button, want the format to be "night"
                -->
              <input type=hidden name=%(FORMAT)s value="night">
            </td>
        </tr>
      </table>
      </td>
  </tr>  
</table>

</form>

<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');

//Set up default time for the time selection widget.. 
setStartTimeOptions('0', "None", 
                    '0', "None", 
                    '0', "None",  
                    '%(startday)s', gfo('%(STARTDAY)s'), 
                    '%(startmonth)s', gfo('%(STARTMONTH)s'), 
                    '%(startyear)s', gfo('%(STARTYEAR)s')); 

// -->
</script>
</div>
"""
        vars={'site':'[site]',
            'startyear':'[startyear]', 
            'startmonth':'[startmonth]', 
            'startday':'[startday]',
            }

        taggedVars={'FORMAT':'FORMAT',
                    'SITE':'SITE',
                    'STARTSECOND':'STARTSECOND', 
                    'STARTMINUTE':'STARTMINUTE', 
                    'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY',
                    'STARTMONTH':'STARTMONTH', 
                    'STARTYEAR':'STARTYEAR',
                    }

        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)        
                

                
class HTMLOptionsDiq(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="600">
   <tr> 
    <td colspan="2"><table width="100%">
        <tr> 
          <td class="widgetLabel" colspan="4"  align="center" valign="middle">Options</td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">X</td>
          <td align="left" valign="middle" class="widgetOptionCell"><label>Label:</label> <input type=text align="right"  name="%(XLABEL)s" size=15 maxlength=20 value="%(xlabel)s"> 
          </td>        
          <td width="134" align="left" valign="middle" class="widgetOptionCell"><label>Min:</label> <input type=text align="right"  name="%(XMIN)s" size=10 maxlength=20 value="%(xmin)s"> 
          </td>
          <td width="140" align="left" valign="middle" class="widgetOptionCell"><label>Max:</label> <input type=text align="right"  name="%(XMAX)s" size=10 maxlength=20 value="%(xmax)s"> 
          </td>
         </td>
        </tr>
        
        <tr> 
          <td width="68" align="center" valign="middle" class="widgetLabel">Y</td>
          <td width="207" align="left" valign="middle" class="widgetOptionCell"><label>Label:</label> <input type=text align="right"  name="%(YLABEL)s" size=15 maxlength=20 value="%(ylabel)s"> 
          </td>
        
          <td width="134" align="left" valign="middle" class="widgetOptionCell"><label>Min:</label> <input type=text align="right"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
          </td>
          <td width="140" align="left" valign="middle" class="widgetOptionCell"><label>Max:</label> <input type=text align="right"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
          </td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Plot Title</td>
          <td align="left" valign="middle" colspan="3" class="widgetOptionCell"><input type=text align="right"  name="%(PLOTTITLE)s" size=40 maxlength=40 value="%(plottitle)s"> 
             &nbsp;&nbsp;&nbsp;&nbsp; If field left empty, automatic title will be generated  
          </td>        
         </td>
        </tr>        
        <tr> 
          <td align="center" colspan="4" > <table width="100%" height="100%" class="widgetOptionCell">
              <tr> 
              
              <td align="left" valign="middle" ><label>Show Mean</label> 
                 <select NAME="%(SHOWMEAN)s" SIZE=1>
                    <option> Yes</option>
                    <option SELECTED> No</option>
                  </select>
              </td>
                
                <td width="50%" align="left" valign="middle"><label>Bins:</label> 
                  <input type=text align="right"  name="%(BINS)s" size=10 maxlength=20 value="%(bins)s"> 
                </td>
              </tr>
              <tr> 
              <td align="left" valign="middle" ><label>Legend</label> 
                 <select NAME="%(LEGEND)s" SIZE=1>
                    <option> Outside</option>
                    <option SELECTED> Inside</option>
                    <option> Off</option>
                  </select>
              </td>
                <td align="left" valign="middle"><label>DPI</label> 
                <select NAME="%(DPI)s" SIZE=1>
                    <option> 50</option>
                    <option> 75</option>
                    <option> 80</option>
                    <option SELECTED> 85</option>
                    <option> 90</option>
                    <option> 95</option>                    
                    <option> 100</option>
                    <option> 125</option>
                    <option> 150</option>
                    <option> 175</option>
                    <option> 200</option>
                    <option> 225</option>
                    <option> 250</option>
                    <option> 275</option>
                    <option> 300</option>
                  </select>
                </td>
              </tr>
            </table></td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Telescope</td>
            <td class="widgetOptionCell" colspan="3" align="left" valign="middle"><select NAME="%(SITE)s" SIZE=1>
                    <option> MK</option>
                    <option> CP</option>
                    <option SELECTED> MK/CP</option>
                  </select>
            </td>
        </tr>
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Format</td>
            <td class="widgetOptionCell"  colspan="3" align="left" valign="middle"><select NAME="%(FORMAT)s" SIZE=1>
                    <option> Normalized</option>
                    <option> Raw</option>
                  </select>            
            </td>
        </tr>
        
        <tr> 
          <td align="center">&nbsp;</td>
        </tr>
      </table>
      </td>
  </tr>
</table>
<script language="JavaScript">
// <!--

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(LEGEND)s'), '%(legend)s');
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');
selectSingleOptByText(gfo('%(FORMAT)s'), '%(format)s');
selectSingleOptByText(gfo('%(SHOWMEAN)s'), '%(showmean)s');

// -->
</script>
"""
        vars={'title':'[title]', 'reduce':'[reduce]',
              'xmax':'[xmax]', 'xmin':'[xmin]','xlabel':'[xlabel]', 'ymax':'[ymax]', 
              'ymin':'[ymin]','ylabel':'[ylabel]',  
              'dpi':'[dpi]',
              'showmean':'[showmean]',              
              'format':'[format]',
              'site':'site'
              }

        taggedVars={'DPI':'DPI', 
                    'SITE':'SITE',
                    'BINS':'BINS', 
                    'SHOWMEAN':'SHOWMEAN',
                    'LEGEND':'LEGEND',
                    'REDUCE':'REDUCE', 
                    'XMIN':'XMIN','XMAX':'XMAX',
                    'XLABEL':'XLABEL', 
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'PLOTTITLE':'PLOTTITLE',
                    'FORMAT':'FORMAT'
                    }
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLOptionsTelMetrics(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
            
        body="""
<div align="center">

<script language="JavaScript">
// <!--
                                                           
function HTMLOptionsTelMetrics_updateHorizGoalLines%(JS)s(obj)  {
                                                                      
    switch (obj.text) {
        case 'Science Availability [ % Sci / (Night - Weather) ]' :
            HTMLOptionsTelMetrics_updateLines%(JS)s('90', '', '', '');                       
            break;
        case 'Time Loss [ % Faults / Obs ]' :
            HTMLOptionsTelMetrics_updateLines%(JS)s('4', '5', '', '');   
            break;                                                     
        default :
            HTMLOptionsTelMetrics_updateLines%(JS)s('', '', '', '');   
            break;
    
        return false;               
    }                                                              
}

function HTMLOptionsTelMetrics_updateLines%(JS)s(l1, l2, l3, l4) {
    gfo('%(LINE1)s').value=l1;    
    gfo('%(LINE2)s').value=l2; 
    gfo('%(LINE3)s').value=l3; 
    gfo('%(LINE4)s')=l4; 
                                                                
} 

// -->
</script>


 <table width="700">
   <tr>      
          <td class="widgetLabel" width="68" align="center" valign="middle">Plot Type</td>
            <td class="widgetOptionCell" colspan="5" align="left" valign="middle">
                    <select NAME="%(PLOTTYPE)s" SIZE=1    onChange="return HTMLOptionsTelMetrics_updateHorizGoalLines%(JS)s(gfo('%(PLOTTYPE)s')[gfo('%(PLOTTYPE)s').selectedIndex]);">         
            <!--
            <option> Non-Science Overheads [ % (Faults + Comm + Eng) / Sci ] </option>
            <option> Non-Science Overheads [ Hours ] </option>          
            -->

            <option> Science Availability [ % Sci / (Night - Weather) ]</option>
            
            <!--
            <option> Science Availability [ Hours ] </option>
            -->
            
            <option SELECTED> Time Loss [ % Faults / Obs ] </option>
            <option> Time Loss [ Hours ] </option>
            <option> Time Usage [ % (Faults, Weather, Eng, Comm, Sci) / Avail ] </option>
            <option> Time Usage [ Hours ] </option>
            <option> Weather Loss [ % Weather / Avail ] </option>
            <option> Weather Loss [ Hours ] </option>                                          
                  </select>
            </td>
    
    </tr>   
    <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">
              Data Source
          </td>
          <td class="widgetOptionCell" colspan="1" align="left" valign="middle">
                    <select NAME="%(SITE)s" SIZE=1>
                    <option> MK</option>
                    <option> CP</option>
                    <option> MK_and_CP</option>
                  <!--  <option> ave(MK,CP)</option> -->
                  </select>
           </td>
            
          <td class="widgetLabel" width="68" align="center" valign="middle">
              Averaging
          </td>
          <td class="widgetOptionCell" colspan="1" align="left" valign="middle">
                    <select NAME="%(TIME2AVE)s" SIZE=1>
                    <option SELECTED> Daily</option>
                    <option> Weekly</option>
                    <option> Monthly</option>
                  </select>
           </td>            
            
            <td class="widgetLabel" width="68" align="center" valign="middle">
                DPI
            </td>
            <td class="widgetOptionCell" colspan="1" align="left" valign="middle">
                    <select NAME="%(DPI)s" SIZE=1>
                    <option> 50</option>
                    <option> 75</option>
                    <option> 80</option>
                    <option > 85</option>
                    <option> 90</option>
                    <option> 95</option>                    
                    <option SELECTED> 100</option>
                    <option> 125</option>
                    <option> 150</option>
                    <option> 175</option>
                    <option> 200</option>
                    <option> 225</option>
                    <option> 250</option>
                    <option> 275</option>
                    <option> 300</option>
                  </select>
            </td>            
    </tr>     
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Plot Title</td>
          <td align="left" valign="middle" colspan="5" class="widgetOptionCell"><input type=text align="left"  name="%(PLOTTITLE)s" size=40 maxlength=40 value="%(plottitle)s"> 
             &nbsp;&nbsp;&nbsp;&nbsp;
          </td>        
        </tr>    
   <tr> 
      <td width="68" align="center" valign="middle" class="widgetLabel">
          Y Label
      </td>
      <td width="207" align="left" valign="middle" class="widgetOptionCell">
              <input type=text align="left"  name="%(YLABEL)s" size=15 maxlength=20 value="%(ylabel)s"> 
      </td>  
      
       <td width="68" align="center" valign="middle" class="widgetLabel">
          Y Min
      </td>           
      <td width="134" align="left" valign="middle" class="widgetOptionCell">
                <input type=text align="right"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
      </td>
          
      <td width="68" align="center" valign="middle" class="widgetLabel">
          Y Max
      </td>  
      <td width="140" align="left" valign="middle" class="widgetOptionCell">
            <input type=text align="right"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
      </td>
  </tr>       
   <tr> 
      <td colspan="2" align="center" valign="middle" class="widgetLabel">
          Horizontal Goal Lines
      </td>
      <td  colspan="4"  align="center" valign="middle" class="widgetOptionCell">
         <input type=text align="right"  name="%(LINE1)s" size=10 maxlength=20 value="%(line1)s"> 
         &nbsp; &nbsp;
         <input type=text align="right"  name="%(LINE2)s" size=10 maxlength=20 value="%(line2)s"> 
         &nbsp; &nbsp;
         <input type=text align="right"  name="%(LINE3)s" size=10 maxlength=20 value="%(line3)s">  
         &nbsp; &nbsp;                     
         <input type=text align="right"  name="%(LINE4)s" size=10 maxlength=20 value="%(line4)s">                          
      </td>      
            
  </tr>      
     
</td>
</tr>
</table>
<script language="JavaScript">
// <!--

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');
selectSingleOptByText(gfo('%(PLOTTYPE)s'), '%(plottype)s');
selectSingleOptByText(gfo('%(TIME2AVE)s'), '%(time2ave)s')        
// -->
</script>
"""
        vars={'plottitle':'[plottitle]',
              'ymax':'[ymax]', 
              'ymin':'[ymin]','ylabel':'[ylabel]',  
              'dpi':'[dpi]',
              'plottype':'[plottype]',
              'site':'site',
              'time2ave':'[time2ave]', 
              'line1':'[line1]',
              'line2':'[line2]',
              'line3':'[line3]',  
              'line4':'[line4]',                          
              }

        taggedVars={'DPI':'DPI', 
                    'SITE':'SITE',
                    'PLOTTYPE':'PLOTTYPE', 
                    'GRIDLINES':'GRIDLINES', 
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'PLOTTITLE':'PLOTTITLE',
                    'TIME2AVE':'TIME2AVE',
                    'LINE1':'LINE1',
                    'LINE2':'LINE2',
                    'LINE3':'LINE3',
                    'LINE4':'LINE4',                    
                    }
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                


class HTMLOptionsLaserMetrics(HTMLObject):
    """Detailed plot with option to name the image file.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
            
        body="""
<div align="center">

 <table width="700">
   <tr>      
          <td class="widgetLabel" width="68" align="center" valign="middle">Plot Type</td>
            <td class="widgetOptionCell" colspan="5" align="left" valign="middle">
              <select NAME="%(PLOTTYPE)s" SIZE=1;">         
               <option SELECTED> Both [ hours ]</option>
               <option> Shuttered [ hours ]</option>
               <option> Blanket Closure [ hours ]</option>
               <option> Both %</option>
               <option> Shuttered %</option>
               <option> Blanket Closure %</option>
              </select>
            </td>
    
    </tr>   
    <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">
              Data Source
          </td>
          <td class="widgetOptionCell" colspan="1" align="left" valign="middle">
                    <select NAME="%(SITE)s" SIZE=1>
                    <option> MK</option>
                    <option> CP</option>
                    <option> MK_and_CP</option>
                  </select>
           </td>
            
          <td class="widgetLabel" width="68" align="center" valign="middle">
              Averaging
          </td>
          <td class="widgetOptionCell" colspan="1" align="left" valign="middle">
                    <select NAME="%(TIME2AVE)s" SIZE=1>
                    <option SELECTED> Daily</option>
                    <option> Weekly</option>
                    <option> Monthly</option>
                  </select>
           </td>            
            
            <td class="widgetLabel" width="68" align="center" valign="middle">
                DPI
            </td>
            <td class="widgetOptionCell" colspan="1" align="left" valign="middle">
                    <select NAME="%(DPI)s" SIZE=1>
                    <option> 50</option>
                    <option> 75</option>
                    <option> 80</option>
                    <option> 85</option>
                    <option> 90</option>
                    <option> 95</option>                    
                    <option SELECTED> 100</option>
                    <option> 125</option>
                    <option> 150</option>
                    <option> 175</option>
                    <option> 200</option>
                    <option> 225</option>
                    <option> 250</option>
                    <option> 275</option>
                    <option> 300</option>
                  </select>
            </td>            
    </tr>     
        <tr> 
          <td class="widgetLabel" width="68" align="center" valign="middle">Plot Title</td>
          <td align="left" valign="middle" colspan="5" class="widgetOptionCell"><input type=text align="left"  name="%(PLOTTITLE)s" size=40 maxlength=40 value="%(plottitle)s"> 
             &nbsp;&nbsp;&nbsp;&nbsp;
          </td>        
        </tr>    
   <tr> 
      <td width="68" align="center" valign="middle" class="widgetLabel">
          Y Label
      </td>
      <td width="207" align="left" valign="middle" class="widgetOptionCell">
              <input type=text align="left"  name="%(YLABEL)s" size=15 maxlength=20 value="%(ylabel)s"> 
      </td>  
      
       <td width="68" align="center" valign="middle" class="widgetLabel">
          Y Min
      </td>           
      <td width="134" align="left" valign="middle" class="widgetOptionCell">
                <input type=text align="right"  name="%(YMIN)s" size=10 maxlength=20 value="%(ymin)s"> 
      </td>
          
      <td width="68" align="center" valign="middle" class="widgetLabel">
          Y Max
      </td>  
      <td width="140" align="left" valign="middle" class="widgetOptionCell">
            <input type=text align="right"  name="%(YMAX)s" size=10 maxlength=20 value="%(ymax)s"> 
      </td>
  </tr>       
   <tr> 
      <td colspan="2" align="center" valign="middle" class="widgetLabel">
          Horizontal Goal Lines
      </td>
      <td  colspan="4"  align="center" valign="middle" class="widgetOptionCell">
         <input type=text align="right"  name="%(LINE1)s" size=10 maxlength=20 value="%(line1)s"> 
         &nbsp; &nbsp;
         <input type=text align="right"  name="%(LINE2)s" size=10 maxlength=20 value="%(line2)s"> 
         &nbsp; &nbsp;
         <input type=text align="right"  name="%(LINE3)s" size=10 maxlength=20 value="%(line3)s">  
         &nbsp; &nbsp;                     
         <input type=text align="right"  name="%(LINE4)s" size=10 maxlength=20 value="%(line4)s">                          
      </td>      
            
  </tr>      
     
</td>
</tr>
</table>
<script language="JavaScript">
// <!--

// Select appropriate items in all the <select> tags.
selectSingleOptByText(gfo('%(DPI)s'), '%(dpi)s');
selectSingleOptByText(gfo('%(SITE)s'), '%(site)s');
selectSingleOptByText(gfo('%(PLOTTYPE)s'), '%(plottype)s');
selectSingleOptByText(gfo('%(TIME2AVE)s'), '%(time2ave)s')        
// -->
</script>
"""
        vars={'plottitle':'[plottitle]',
              'ymax':'[ymax]', 
              'ymin':'[ymin]','ylabel':'[ylabel]',  
              'dpi':'[dpi]',
              'plottype':'[plottype]',
              'site':'site',
              'time2ave':'[time2ave]', 
              'line1':'[line1]',
              'line2':'[line2]',
              'line3':'[line3]',  
              'line4':'[line4]',                          
              }

        taggedVars={'DPI':'DPI', 
                    'SITE':'SITE',
                    'PLOTTYPE':'PLOTTYPE', 
                    'GRIDLINES':'GRIDLINES', 
                    'YMIN':'YMIN','YMAX':'YMAX',
                    'YLABEL':'YLABEL',
                    'PLOTTITLE':'PLOTTITLE',
                    'TIME2AVE':'TIME2AVE',
                    'LINE1':'LINE1',
                    'LINE2':'LINE2',
                    'LINE3':'LINE3',
                    'LINE4':'LINE4',                    
                    }
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                


class HTMLTimeSelector(HTMLObject):
    """Start/End time selector.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
            
        body="""
<!-- HTMLTimeSelector -->
        
<div align="center">
 <table width="800" >
  <tr> 
    <td><div align="center">
        <table width="100%" border="0">
          <tr> 
            <td class="widgetTimeLabel" align="center" width="80"> Start: </td>
            <td width="175"> <select NAME=%(STARTMONTH)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;"> 
                <option> Jan</option>
                <option> Feb</option>
                <option> Mar</option>
                <option> Apr</option>
                <option> May</option>
                <option> Jun</option>
                <option> Jul</option>
                <option> Aug</option>
                <option> Sep</option>
                <option> Oct</option>
                <option> Nov</option>
                <option> Dec</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>                
                <option> 2011</option>                
                <option> 2012</option>                
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
            </td>
            <td>
              <select NAME=%(STARTHOUR)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
              </select><strong>:</strong>
            </td>
            <td>
              <select NAME=%(STARTMINUTE)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select><strong>:</strong>
            </td>
            <td>
              <select NAME=%(STARTSECOND)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> </td>
              <td> 
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.sub(1440); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                        24h 
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.add(1440); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>
                    &nbsp; &nbsp;
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.sub(60); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                        1h 
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.add(60); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>
                    &nbsp; &nbsp;
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.sub(10); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                        10min 
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.add(10); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>  
                    &nbsp; &nbsp;
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.sub(1); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                       1min 
                    <a href="javascript:void(0)" onMouseDown="startTimeSelector%(JS)s.add(1); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>  
              </td>
              
        
          </tr>
          <tr> 
            <td class="widgetTimeLabel" align="center" width="70"> End: </td>
            <td> <select NAME=%(ENDMONTH)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> Jan</option>
                <option> Feb</option>
                <option> Mar</option>
                <option> Apr</option>
                <option> May</option>
                <option> Jun</option>
                <option> Jul</option>
                <option> Aug</option>
                <option> Sep</option>
                <option> Oct</option>
                <option> Nov</option>
                <option> Dec</option>
              </select>
              <select NAME=%(ENDDAY)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;" >
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(ENDYEAR)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;" >
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
            </td>
            <td><select NAME=%(ENDHOUR)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
              </select><strong>:</strong>
            </td>
            <td>
              <select NAME=%(ENDMINUTE)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select><strong>:</strong>
            </td>
            <td>
              <select NAME=%(ENDSECOND)s SIZE=1 onChange="HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;" >
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> </td>
              <td> 
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.sub(1440); HTMLTimeSelector_onChangeUpdate%(JS)s(); return false;"onClick="return false;">&lt;&lt;</a> 
                        24h 
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.add(1440); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>
                    &nbsp; &nbsp;
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.sub(60); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                        1h 
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.add(60); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>
                    &nbsp; &nbsp;
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.sub(10); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                        10min 
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.add(10); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>  
                    &nbsp; &nbsp;
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.sub(1); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&lt;&lt;</a> 
                       1min 
                    <a href="javascript:void(0)" onMouseDown="endTimeSelector%(JS)s.add(1); HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">&gt;&gt;</a>  
              </td>
              
              
          </tr>
          <tr>
          <td colspan="2"></td>
          <td align="left" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
[<a href="javascript:void(0)" onMouseDown="selectSingleOptByText(startTimeSelector%(JS)s.h,'00'); selectSingleOptByText(endTimeSelector%(JS)s.h,'00');HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">Zero</a>] 
         </td>
          <td align="left" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
[<a  href="javascript:void(0)" onMouseDown="selectSingleOptByText(startTimeSelector%(JS)s.min,'00'); selectSingleOptByText(endTimeSelector%(JS)s.min,'00');HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">Zero</a>] 
         </td>
          <td align="left" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
[<a href="javascript:void(0)" onMouseDown="selectSingleOptByText(startTimeSelector%(JS)s.s,'00'); selectSingleOptByText(endTimeSelector%(JS)s.s,'00');HTMLTimeSelector_onChangeUpdate%(JS)s();return false;"onClick="return false;">Zero</a>] 
          </td>
          </tr>
      </table>
    </div></td>
  </tr>    
</table>
</div>    


<script language="JavaScript">
// <!--
//////
// Initial setup.
/////

var HTMLTimeSelector_onChangeArray%(JS)s=new Array();
function HTMLTimeSelector_addToOnChangeArray%(JS)s(fun)
{
	HTMLTimeSelector_onChangeArray%(JS)s[HTMLTimeSelector_onChangeArray%(JS)s.length]=fun;
}

function HTMLTimeSelector_onChangeUpdate%(JS)s()
{
	for (var i=0; i<HTMLTimeSelector_onChangeArray%(JS)s.length; i++)
	{
		HTMLTimeSelector_onChangeArray%(JS)s[i]();
	}
}

startTimeSelector%(JS)s=new TimeSelector(gfo('%(STARTYEAR)s'),
                                                                  gfo('%(STARTMONTH)s'),
                                                                  gfo('%(STARTDAY)s'),
                                                                  gfo('%(STARTHOUR)s'),
                                                                  gfo('%(STARTMINUTE)s'),
                                                                  gfo('%(STARTSECOND)s'));
 
	
endTimeSelector%(JS)s=new TimeSelector(gfo('%(ENDYEAR)s'),
                                                                  gfo('%(ENDMONTH)s'),
                                                                  gfo('%(ENDDAY)s'),
                                                                  gfo('%(ENDHOUR)s'),
                                                                  gfo('%(ENDMINUTE)s'),
                                                                  gfo('%(ENDSECOND)s'));

startTimeSelector%(JS)s.updateFromVars('%(startyear)s', '%(startmonth)s', '%(startday)s',   '%(starthour)s',  '%(startminute)s', '%(startsecond)s');
endTimeSelector%(JS)s.updateFromVars('%(endyear)s', '%(endmonth)s', '%(endday)s',   '%(endhour)s',  '%(endminute)s', '%(endsecond)s');
    
startEndTimeSelector%(JS)s=new StartEndTimeSelector(startTimeSelector%(JS)s, endTimeSelector%(JS)s);
 
// -->
</script>

"""
        vars={'startyear':'[startyear]', 'startmonth':'[startmonth]', 'startday':'[startday]','starthour':'[starthour]', 
            'startminute':'[startminute]', 'startsecond':'[startsecond]', 
            'endyear':'[endyear]', 'endmonth':'[endmonth]', 'endday':'[endday]','endhour':'[endhour]', 
            'endminute':'[endminute]', 'endsecond':'[endsecond]', 
            }

        taggedVars={'STARTSECOND':'STARTSECOND', 'STARTMINUTE':'STARTMINUTE', 'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY','STARTMONTH':'STARTMONTH', 'STARTYEAR':'STARTYEAR',
                    'ENDSECOND':'ENDSECOND', 'ENDMINUTE':'ENDMINUTE', 'ENDHOUR':'ENDHOUR',
                    'ENDDAY':'ENDDAY','ENDMONTH':'ENDMONTH', 'ENDYEAR':'ENDYEAR',
                    'QUICKTIMESELECTOR':'QUICKTIMESELECTOR',
                    'JS':'JS'
                    }
        
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, 
                                        body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)


class HTMLTimeSelectorSimple(HTMLObject):
    """Start/End time selector.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):

        utc = ''
        if 'utc' in kwargs: utc = '(UTC)'
            
        body="""
<!-- HTMLTimeSelectorSimple -->
        
<div align="center">
 <table>
  <tr> 
    <td align="center">
        <table border="0">
          <tr> 
            <td class="widgetTimeLabel" align="center"> Start %(UTC)s: </td>
            <td> <select NAME=%(STARTMONTH)s SIZE=1 onChange=>
                <option> Jan</option>
                <option> Feb</option>
                <option> Mar</option>
                <option> Apr</option>
                <option> May</option>
                <option> Jun</option>
                <option> Jul</option>
                <option> Aug</option>
                <option> Sep</option>
                <option> Oct</option>
                <option> Nov</option>
                <option> Dec</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1 >
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1 >
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>                  
                <option> 2011</option>                  
                <option> 2012</option>                  
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
            </td>
            <td class="widgetTimeLabel" align="center"> End %(UTC)s: </td>
            <td> <select NAME=%(ENDMONTH)s SIZE=1 >
                <option> Jan</option>
                <option> Feb</option>
                <option> Mar</option>
                <option> Apr</option>
                <option> May</option>
                <option> Jun</option>
                <option> Jul</option>
                <option> Aug</option>
                <option> Sep</option>
                <option> Oct</option>
                <option> Nov</option>
                <option> Dec</option>
              </select>
              <select NAME=%(ENDDAY)s SIZE=1 >
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(ENDYEAR)s SIZE=1 >
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
                </select>
            </td>
          </tr>
      </table>
      </td>
  </tr>    
</table>
</div>    

<input type=hidden name=%(STARTHOUR)s   value="00">
<input type=hidden name=%(STARTMINUTE)s value="00">
<input type=hidden name=%(STARTSECOND)s value="00">

<input type=hidden name=%(ENDHOUR)s     value="23">
<input type=hidden name=%(ENDMINUTE)s   value="59">
<input type=hidden name=%(ENDSECOND)s   value="59">

<script language="JavaScript">
// <!--
//////
// Initial setup.
/////
startTimeSelector%(JS)s=new TimeSelector(gfo('%(STARTYEAR)s'),
                                                                  gfo('%(STARTMONTH)s'),
                                                                  gfo('%(STARTDAY)s'),
                                                                  gfo('%(STARTHOUR)s'),
                                                                  gfo('%(STARTMINUTE)s'),
                                                                  gfo('%(STARTSECOND)s'))
 
endTimeSelector%(JS)s=new TimeSelector(gfo('%(ENDYEAR)s'),
                                                                  gfo('%(ENDMONTH)s'),
                                                                  gfo('%(ENDDAY)s'),
                                                                  gfo('%(ENDHOUR)s'),
                                                                  gfo('%(ENDMINUTE)s'),
                                                                  gfo('%(ENDSECOND)s'));
                                                            
startTimeSelector%(JS)s.updateFromVars('%(startyear)s', '%(startmonth)s', '%(startday)s',   '%(starthour)s',  '%(startminute)s', '%(startsecond)s');
endTimeSelector%(JS)s.updateFromVars('%(endyear)s', '%(endmonth)s', '%(endday)s',   '%(endhour)s',  '%(endminute)s', '%(endsecond)s');
    
startEndTimeSelector%(JS)s=new StartEndTimeSelector(startTimeSelector%(JS)s, endTimeSelector%(JS)s);

A = 0; B = 1;
function getSemester(year,semester){
  if (semester == A){
    startEndTimeSelector%(JS)s.updateFromDate(new Date('Feb 1, '+year+' 00:00:00'),new Date('Jul 31, '+year+' 23:59:59') ); 
  }else{
    startEndTimeSelector%(JS)s.updateFromDate(new Date('Aug 1, '+year+' 00:00:00'),new Date('Jan 31, '+(year+1)+' 23:59:59') ); 
  }
  return false;
}
 
// -->
</script>

"""

        vars={'startyear':'[startyear]', 'startmonth':'[startmonth]', 'startday':'[startday]','starthour':'[starthour]', 
            'startminute':'[startminute]', 'startsecond':'[startsecond]', 
            'endyear':'[endyear]', 'endmonth':'[endmonth]', 'endday':'[endday]','endhour':'[endhour]', 
            'endminute':'[endminute]', 'endsecond':'[endsecond]', 
            }

        taggedVars={'UTC':utc,'STARTSECOND':'STARTSECOND', 'STARTMINUTE':'STARTMINUTE', 'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY','STARTMONTH':'STARTMONTH', 'STARTYEAR':'STARTYEAR',
                    'ENDSECOND':'ENDSECOND', 'ENDMINUTE':'ENDMINUTE', 'ENDHOUR':'ENDHOUR',
                    'ENDDAY':'ENDDAY','ENDMONTH':'ENDMONTH', 'ENDYEAR':'ENDYEAR',
                    'QUICKTIMESELECTOR':'QUICKTIMESELECTOR',
                    'JS':'JS'
                    }
        
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

class HTMLTimeSelectorPlotting(HTMLTimeSelector):
    """Start/End time selector with quick selectors.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        quickSelectionHtml="""
<div align="center">
<table>
<tr>
<td>
[<a href="javascript:void(0)" onMouseDown="
// A 'night' is taken to be between 6pm and 6am. If it is before 6pm, update start/end times to last night, 
// if right now it's past 6pm, then look at tonight.
var d=new Date();
if (d.getHours()<18)
{
    d=adjustDate(d, -1440);            // Go to yesterday this time (-24h).
}
d.setHours(18);                 
d.setSeconds(0);
d.setMinutes(0);
// Setup the start time.
startEndTimeSelector%(JS)s.start.updateFromDate(d);
// Setup the end time.
d=adjustDate(d, +720);             // Add 12h 
startEndTimeSelector%(JS)s.end.updateFromDate(d);
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;
">Last/Current_Night</a>]

 &nbsp; <strong></strong> &nbsp;
 
[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(1440);
startEndTimeSelector%(JS)s.end.now();
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Last_24h</a>]
 
[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(720);
startEndTimeSelector%(JS)s.end.now();
updateFixedTimeRange%(JS)s();
return false;"onClick="return false;">Last_12h</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(360);
startEndTimeSelector%(JS)s.end.now();
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Last_6h</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(180);
startEndTimeSelector%(JS)s.end.now();
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Last_3h</a>] 

&nbsp; <strong></strong> &nbsp;

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 180));
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Start+3h</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 60));
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Start+1h</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 30));
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Start+30m</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 10));
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Start+10m</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 5));
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Start+5min</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 1));
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Start+1min</a>] 

</td>
</tr>
</table>
</div>
"""
        
        quickSelectionJavaScript="""
<script language="JavaScript">
// <!--

// Moved everything inline...


// -->
</script>
"""
        timeRangeHtml="""
<script language="JavaScript">
// <!--

function setupFixedTimeRange%(JS)s(v, sd, ed)
{
    var exd=new Date();    

    exd.setDate(exd.getDate() + 90);
    
    if (v=='Yes')
    {
        setCookie('fixedTimeRange', (sd.getTime()/1000.0)+"-"+(ed.getTime()/1000.0), '/', exd);
    }
    else
    {
        // Seems like can't guarantee that the cookie always gets properly deleted. 
        //deleteCookie('fixedTimeRange', '/', "localhost");
    
        // Value of -1 implies the fixed time range should not be used.
        setCookie('fixedTimeRange', -1, '/', exd);
    }

}
                                                       
function updateFixedTimeRange%(JS)s()
{
    var so=gfo('%(FIXTIMERANGE)s').options[gfo('%(FIXTIMERANGE)s').options.selectedIndex].text;
    var sd=startEndTimeSelector%(JS)s.start.toDate();
    var ed=startEndTimeSelector%(JS)s.end.toDate();
    setupFixedTimeRange%(JS)s(so, sd, ed);
    return true;
}

// Want to make sure that we update the cookie with the latest time range values.
globalSubmitFunctions.push(updateFixedTimeRange%(JS)s);

// And call it each time one of the selectors update. 
HTMLTimeSelector_addToOnChangeArray%(JS)s(updateFixedTimeRange%(JS)s);

// -->
</script>

<div align="center">
 Fix time selection?
<select NAME=%(FIXTIMERANGE)s SIZE=1 onChange="
updateFixedTimeRange%(JS)s();
return false;
">
    <option SELECTED> No</option>
    <option> Yes</option>
</select> 

</div>

<div align="center">

</div>

<script language="JavaScript">
// <!--

// Here we check the cookie to see whether we should settle on the time selection to be
// fixed or not.
var c=getCookie("fixedTimeRange");
if (c==null || c=='-1')
{ 
    selectSingleOptByText(gfo('%(FIXTIMERANGE)s'), 'No');
}
else
{
    selectSingleOptByText(gfo('%(FIXTIMERANGE)s'), 'Yes');
}
// -->
</script>



<script language="JavaScript">
// <!--

function updateTimeRangesListCookie%(JS)s(obj)
{
    var exd=new Date();    

    exd.setDate(exd.getDate() + 90);

    setCookie('timeRangesList', selectionToString(obj, '|'), '/', exd);    
}

// -->
</script>

<div align="center">

<table>
<tr>
<td valign="middle">
[<a href="javascript:void(0)" onMouseDown="
var c=getCookie('timeRangesList');
if (c!=null)
{
    removeAllOptions(gfo('%(TIMERANGESTORE)s'));
    addTextOptions(gfo('%(TIMERANGESTORE)s'), c, /\|/);
}
return false;"
onClick="return false;">Update Entries</a>]   
</td>
<td>
    <select NAME="%(TIMERANGESTORE)s"  size="5">                                          
    </select>
</td>
<td>
    <table>
    <tr>
    <td>
[<a href="javascript:void(0)" onMouseDown="
var tag=gfo('%(TIMERANGETAG)s').value;
if (tag!='')
{
    var re=/\;/g;
    tag=tag.replace(re, '_');  // don't allow the ';' character in tags - use it as a separator.
    tag+=' ;   ';
    gfo('%(TIMERANGETAG)s').value='';
}
else
{
tag='';
}
var s=tag+startEndTimeSelector%(JS)s.toString();
if (!isTextInOptions(s, gfo('%(TIMERANGESTORE)s')))
{
    var sep='|';
    addTextOptions(gfo('%(TIMERANGESTORE)s'), stripStr(s), sep);
    sortSelect(gfo('%(TIMERANGESTORE)s'));
    updateTimeRangesListCookie%(JS)s(gfo('%(TIMERANGESTORE)s'));
}
return false;"
onClick="return false;">Add current time range to list with a tag </a> <input type="text" name="%(TIMERANGETAG)s" value="" size="8">]    
    </tr>
     
     <tr>
    <td>
[<a href="javascript:void(0)" onMouseDown="
var s=getSelectedText(gfo('%(TIMERANGESTORE)s'));
if (s==null) return false; // Need this for IE.
// In case have a tag, need to get rid of it before we pass the string to the time selector.
var si=s.indexOf(';');
if (si>-1)
{
    s=stripStr(s.substring(si+2));  
}
startEndTimeSelector%(JS)s.fromString(s);
updateFixedTimeRange%(JS)s();
return false;"
onClick="return false;">Use selected entry</a>]     
    </tr>
     
     <tr>
    <td>
[<a href="javascript:void(0)" onMouseDown="
removeSelectedOptions(gfo('%(TIMERANGESTORE)s'))
sortSelect(gfo('%(TIMERANGESTORE)s'));
updateTimeRangesListCookie%(JS)s(gfo('%(TIMERANGESTORE)s'));
return false;"
onClick="return false;">Delete selected entry</a>]    
    </tr>
     
     <tr>
    <td>
 [<a href="javascript:void(0)" onMouseDown="
removeAllOptions(gfo('%(TIMERANGESTORE)s'))
updateTimeRangesListCookie%(JS)s(gfo('%(TIMERANGESTORE)s'));
return false;"
onClick="return false;">Delete all entries</a>]     
    </tr>
    
    </table>
</td>
</tr>
</table>

</div>

<script language="JavaScript">
// <!--

//Initialize the list of time ranges based on the current value of a cookie.
var c%(JS)s=getCookie("timeRangesList");
if (c%(JS)s != null)
{
    addTextOptions(gfo('%(TIMERANGESTORE)s'), c%(JS)s, /\|/);
}
// -->
</script>


"""
        vars={'fixtimerange':'[fixtimerange]', 
            }

        taggedVars={'FIXTIMERANGE':'FIXTIMERANGE',
                    'TIMERANGESTORE':'TIMERANGESTORE',
                    }

        HTMLTimeSelector.__init__(self, vars=vars, taggedVars=taggedVars)
                    
        self.body.insert(0, quickSelectionHtml)
        self.body.append(quickSelectionJavaScript)
        self.body.append(timeRangeHtml)
        
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
    


class HTMLTimeSelectorPlottingORG(HTMLTimeSelector):
    """Start/End time selector with quick selectors.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        quickSelectionHtml="""
<div align="center">
<table>
<tr>
<td>
[<a href="javascript:void(0)" onMouseDown="
// A 'night' is taken to be between 6pm and 6am. If it is before 6pm, update start/end times to last night, 
// if right now it's past 6pm, then look at tonight.
var d=new Date();
if (d.getHours()<18)
{
    d=adjustDate(d, -1440);            // Go to yesterday this time (-24h).
}
d.setHours(18);                 
d.setSeconds(0);
d.setMinutes(0);
// Setup the start time.
startEndTimeSelector%(JS)s.start.updateFromDate(d);
// Setup the end time.
d=adjustDate(d, +720);             // Add 12h 
startEndTimeSelector%(JS)s.end.updateFromDate(d);
return false;"
onClick="return false;
">Last/Current_Night</a>]

 &nbsp; <strong></strong> &nbsp;
 
[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(1440);
startEndTimeSelector%(JS)s.end.now();
return false;"
onClick="return false;">Last_24h</a>]
 
[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(720);
startEndTimeSelector%(JS)s.end.now();
return false;"onClick="return false;">Last_12h</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(360);
startEndTimeSelector%(JS)s.end.now();
return false;"
onClick="return false;">Last_6h</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(180);
startEndTimeSelector%(JS)s.end.now();
return false;"
onClick="return false;">Last_3h</a>] 

&nbsp; <strong></strong> &nbsp;

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 180));
return false;"
onClick="return false;">Start+3h</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 60));
return false;"
onClick="return false;">Start+1h</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 30));
return false;"
onClick="return false;">Start+30m</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 10));
return false;"
onClick="return false;">Start+10m</a>] 

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), 5));
return false;"
onClick="return false;">Start+5min</a>] 

</td>
</tr>
</table>
</div>
"""
        
        quickSelectionJavaScript="""
<script language="JavaScript">
// <!--

// Moved everything inline...

// -->
</script>
"""
        HTMLTimeSelector.__init__(self)
                    
        self.body.insert(0, quickSelectionHtml)
        self.body.append(quickSelectionJavaScript)
        
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
    
class HTMLTimeSelectorNLReport(HTMLTimeSelectorSimple):
    """Start/End time selector with quick selectors.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        quickSelectionHtml="""
<div align="center">
<table>
<tr>
<td>

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), -global_minPerWeek));
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.end.toDate(), -global_minPerWeek));
return false;"
onClick="return false;"> Week Back<< </a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
d.setHours(12); d.setMinutes(0); d.setSeconds(0);
d=adjustDate(d, -global_minPerDay*(d.getDay()+2));
startEndTimeSelector%(JS)s.start.updateFromDate(d);
d=adjustDate(d, global_minPerWeek);       
startEndTimeSelector%(JS)s.end.updateFromDate(d);
return false;"
onClick="return false;">Current_Week</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(),global_minPerWeek));
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.end.toDate(),global_minPerWeek));
return false;"
onClick="return false;"> >>Week Ahead </a>]


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -global_minPerWeek);       // Week;
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_7_Days</a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -30*1440);       // Month
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_Month</a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -3*30*1440);       // Month
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_3_Months</a>]

</td>
</tr>
</table>
</div>
"""
        
        quickSelectionJavaScript="""
<script language="JavaScript">
// <!--
 //Set the times to noon.
var d=startEndTimeSelector%(JS)s.start.toDate();
d.setHours(12); d.setMinutes(0); d.setSeconds(0);
startEndTimeSelector%(JS)s.start.updateFromDate(d);

d=startEndTimeSelector%(JS)s.end.toDate();
d.setHours(12); d.setMinutes(0); d.setSeconds(0);
startEndTimeSelector%(JS)s.end.updateFromDate(d);

// -->
</script>
"""
        HTMLTimeSelectorSimple.__init__(self)
                    
        self.body.insert(0, quickSelectionHtml)
        self.body.append(quickSelectionJavaScript)
        
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
    
class HTMLTimeSelectorFrsStats(HTMLTimeSelectorSimple):
    """Start/End time selector with quick selectors.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        quickSelectionHtml="""
<div align="center">
<table>
<tr>
<td>

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), -global_minPerWeek));
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.end.toDate(), -global_minPerWeek));
return false;"
onClick="return false;"> Week Back<< </a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
d.setHours(12); d.setMinutes(0); d.setSeconds(0);
d=adjustDate(d, -global_minPerDay*(d.getDay()+2));
startEndTimeSelector%(JS)s.start.updateFromDate(d);
d=adjustDate(d, global_minPerWeek);       
startEndTimeSelector%(JS)s.end.updateFromDate(d);
return false;"
onClick="return false;">Current_Week</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(),global_minPerWeek));
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.end.toDate(),global_minPerWeek));
return false;"
onClick="return false;"> >>Week Ahead </a>]

&nbsp;&nbsp;&nbsp;

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
//d.setHours(0); d.setMinutes(0); d.setSeconds(1);
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -7*1440);       // Week;
//d.setHours(23); d.setMinutes(59); d.setSeconds(59);
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_7_Days</a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
//d.setHours(0); d.setMinutes(0); d.setSeconds(1);
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -30*1440);       // Month
//d.setHours(23); d.setMinutes(59); d.setSeconds(59);
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_Month</a>]

&nbsp;&nbsp;&nbsp;
 
[<a href="javascript:void(0)" onMouseDown="getSemester(2017,A);"
onClick="return false;">2017A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2017,B);"
onClick="return false;">2017B</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2018,A);"
onClick="return false;">2018A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2018,B);"
onClick="return false;">2018B</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2019,A);"
onClick="return false;">2019A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2019,B);"
onClick="return false;">2019B</a>]

-----
[<a href="javascript:void(0)" onMouseDown="getSemester(2020,A);"
onClick="return false;">2020A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2020,B);"
onClick="return false;">2020B</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2021,A);"
onClick="return false;">2021A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2021,B);"
onClick="return false;">2021B</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2022,A);"
onClick="return false;">2022A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2022,B);"
onClick="return false;">2022B</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2023,A);"
onClick="return false;">2023A</a>]

[<a href="javascript:void(0)" onMouseDown="getSemester(2023,B);"
onClick="return false;">2023B</a>]
</td>
</td>
</tr>
</table>
</div>
"""
        
        quickSelectionJavaScript="""
<script language="JavaScript">
// <!--

// -->
</script>
"""
        HTMLTimeSelectorSimple.__init__(self)
                    
        self.body.insert(0, quickSelectionHtml)
        self.body.append(quickSelectionJavaScript)
        
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
   
   
class HTMLTimeSelectorTelMetrics(HTMLTimeSelectorSimple):
    """Start/End time selector with quick selectors.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        quickSelectionHtml="""
<div align="center">
<table>
<tr>
<td>

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(), -global_minPerWeek));
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.end.toDate(), -global_minPerWeek));
return false;"
onClick="return false;"> Week Back<< </a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
d.setHours(12); d.setMinutes(0); d.setSeconds(0);
d=adjustDate(d, -global_minPerDay*(d.getDay()+2));
startEndTimeSelector%(JS)s.start.updateFromDate(d);
d=adjustDate(d, global_minPerWeek);       
startEndTimeSelector%(JS)s.end.updateFromDate(d);
return false;"
onClick="return false;">Current_Week</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.start.toDate(),global_minPerWeek));
startEndTimeSelector%(JS)s.end.updateFromDate(adjustDate(startEndTimeSelector%(JS)s.end.toDate(),global_minPerWeek));
return false;"
onClick="return false;"> >>Week Ahead </a>]

&nbsp;&nbsp;&nbsp;

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
//d.setHours(0); d.setMinutes(0); d.setSeconds(1);
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -7*1440);       // Week;
//d.setHours(23); d.setMinutes(59); d.setSeconds(59);
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_7_Days</a>]

[<a href="javascript:void(0)" onMouseDown="
var d=new Date();
//d.setHours(0); d.setMinutes(0); d.setSeconds(1);
startEndTimeSelector%(JS)s.end.updateFromDate(d);
d=adjustDate(d, -30*1440);       // Month
//d.setHours(23); d.setMinutes(59); d.setSeconds(59);
startEndTimeSelector%(JS)s.start.updateFromDate(d);
return false;"
onClick="return false;">Last_Month</a>]

</td>
</tr>
</table>
</div>
"""
        
        quickSelectionJavaScript="""
<script language="JavaScript">
// <!--

// -->
</script>
"""
        HTMLTimeSelectorSimple.__init__(self, utc=True)
                    
        self.body.insert(0, quickSelectionHtml)
        self.body.append(quickSelectionJavaScript)
        
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
     
                
class HTMLTimeSelector2(HTMLObject):

    """Start/End time selector.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<input type="text" name="%(DATESTR)s" value="%(datestr)s" size="25">
"""
                
        vars={'datestr':'[datestr]'}

        taggedVars={'DATESTR':'DATESTR'}           
        
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
                
class HTMLTimeSelectorNL(HTMLObject):

    """Start/End time selector.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table>

<!--
  <tr> 
    <td colspan="2"><div align="center">
    <table width="100%">
      <tr>
          <td class="widgetTimeLabel" align="center" width="180">Quick Selector; see last...</td>
         <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="180" onClick="updateTimeFromQuickSelector(this.value);">
             3h</td>
       <td width="70" class="widgetOptionCell" ><input type="radio" name="%(QUICKTIMESELECTOR)s" value="360" onClick="updateTimeFromQuickSelector(this.value);">
             6h</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="720" onClick="updateTimeFromQuickSelector(this.value);">
             12h</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="1080" onClick="updateTimeFromQuickSelector(this.value);">
             18h</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="1440" onClick="updateTimeFromQuickSelector(this.value);">
             24h</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="2160" onClick="updateTimeFromQuickSelector(this.value);">
             36h</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="2880" onClick="updateTimeFromQuickSelector(this.value);">
             48h</td>
       </tr>
    </table>
    </td>
  </tr>
-->
 <tr> 
        <td class="widgetTimeLabel" align="center" width="125">Night of: (M/D/Y)</td>
        <td> <select NAME=%(STARTMONTH)s SIZE=1>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
            </td>
      </tr>
</table>
<!--
No need for the user to midify hour/minute/second. Take noon.
-->
<input type=hidden name=%(STARTHOUR)s   value="12">
<input type=hidden name=%(STARTMINUTE)s value="00">
<input type=hidden name=%(STARTSECOND)s value="00">
</div> 


<script language="JavaScript">
// <!--

//////
// Initial setup.
/////

//Set up default time.
setStartTimeOptions('0', "None", 
                    '0', "None", 
                    '0', "None",  
                    '%(startday)s', gfo('%(STARTDAY)s'), 
                    '%(startmonth)s', gfo('%(STARTMONTH)s'), 
                    '%(startyear)s', gfo('%(STARTYEAR)s')); 
    
//Initially time is setup using the above; want QUICKTIMESELECTOR radio buttons all 
//unselected.
//clearButtons(gfo('%(QUICKTIMESELECTOR)s'));
                    
// -->
</script>

"""
        vars={'startyear':'[startyear]', 'startmonth':'[startmonth]', 'startday':'[startday]',
            
            #Should be constant... 
            #'starthour':'[starthour]', 'startminute':'[startminute]', 'startsecond':'[startsecond]', 
            }

        taggedVars={
                    'STARTSECOND':'STARTSECOND', 'STARTMINUTE':'STARTMINUTE', 'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY','STARTMONTH':'STARTMONTH', 'STARTYEAR':'STARTYEAR',
                    'QUICKTIMESELECTOR':'QUICKTIMESELECTOR',
                    }
        
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
        
class HTMLTimeSelectorFrsStatsOLD(HTMLObject):
    """Start/End time selector.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="700"  cellpadding="0" cellspacing="0">
  <tr> 
    <td colspan="2"><div align="center">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
          <td class="widgetLabel" align="center" width="120">Quick Selector; see last...</td>
         <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="1440" onClick="updateTimeFromQuickSelector(this.value);">
             1 day</td>
       <td width="70" class="widgetOptionCell" ><input type="radio" name="%(QUICKTIMESELECTOR)s" value="10080" onClick="updateTimeFromQuickSelector(this.value);">
             1 week</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="20160" onClick="updateTimeFromQuickSelector(this.value);">
             2 weeks</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="30240" onClick="updateTimeFromQuickSelector(this.value);">
             3 weeks</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="40320" onClick="updateTimeFromQuickSelector(this.value);">
             4 weeks</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="89280" onClick="updateTimeFromQuickSelector(this.value);">
             2 months</td>
            <!--
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="-1" onClick="updateTimeFromQuickSelector(this.value);">
             All</td>
             -->
       </tr>
    </table>
    </td>
  </tr>
  <tr>
    <td colspan="2"><div align="center">
        <table border="0" width="100%" cellpadding="0" cellspacing="1">
          <tr> 
            <td class="widgetLabel" align="center" width="70"> Start: </td>
            <td align="center"> Day (m/d/y) </td>
            <td width="180" >
             <select NAME=%(STARTMONTH)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>                  
                <option> 2011</option>                  
                <option> 2012</option>                  
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select>
            </td>
            <td align="center"> Time (h:m:s) </td>
            <td width="175">
              <select NAME=%(STARTHOUR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
              </select>
              <select NAME=%(STARTMINUTE)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> <select NAME=%(STARTSECOND)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> </td>
          </tr>
          <tr> 
            <td class="widgetLabel" align="center" width="70" > End: </td>
            <td align="center"> Day (m/d/y) </td>
            <td>
              <select NAME=%(ENDMONTH)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option > 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(ENDDAY)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(ENDYEAR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select> </td>
            <td align="center"> Time (h:m:s) </td>
            <td>
              <select NAME=%(ENDHOUR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
              </select>
              <select NAME=%(ENDMINUTE)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select>
              <select NAME=%(ENDSECOND)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> </td>
          </tr>
        </table>
      </div></td>
  </tr>
</table>
</div>
<script language="JavaScript">
// <!--
//Update the time selection based on the radio button clicked.        
function updateTimeFromQuickSelector(quickLapseValue)
{
    var endTime = new Date();                // Get current time.

    //Special case, want the start date to be Jan 1, 2002
    if (quickLapseValue=="-1")
    {
        //var startTime = new Date(2002, 0, 1,0,0,0);    // Does not work in IE
        var startTime = new Date("Jan 1, 2002 00:00:00");
    }
    else
    {
        // quickLapseValue in minutes, but want milliseconds
        var startTime = new Date(endTime.getTime()-quickLapseValue*60.0*1000.0); 
    }

    //TESTING
    //gfo('%(XLABEL)s').value=startTime.toLocaleString();
    //gfo('%(YLABEL)s').value=endTime.toLocaleString(); 
    
    setStartTimeOptions(startTime.getSeconds(), gfo('%(STARTSECOND)s'), 
                    startTime.getMinutes(), gfo('%(STARTMINUTE)s'), 
                    startTime.getHours(), gfo('%(STARTHOUR)s'), 
                    startTime.getDate(), gfo('%(STARTDAY)s'), 
                    startTime.getMonth()+1, gfo('%(STARTMONTH)s'), 
                    startTime.getFullYear(), gfo('%(STARTYEAR)s'));

    setEndTimeOptions(endTime.getSeconds(), gfo('%(ENDSECOND)s'), 
                    endTime.getMinutes(), gfo('%(ENDMINUTE)s'), 
                    endTime.getHours(), gfo('%(ENDHOUR)s'), 
                    endTime.getDate(), gfo('%(ENDDAY)s'), 
                    endTime.getMonth()+1, gfo('%(ENDMONTH)s'), 
                    endTime.getFullYear(), gfo('%(ENDYEAR)s'));
                    
}

//////
// Initial setup.
/////

//Set up start/end times.
setStartTimeOptions('%(startsecond)s', gfo('%(STARTSECOND)s'), 
                    '%(startminute)s', gfo('%(STARTMINUTE)s'), 
                    '%(starthour)s', gfo('%(STARTHOUR)s'), 
                    '%(startday)s', gfo('%(STARTDAY)s'), 
                    '%(startmonth)s', gfo('%(STARTMONTH)s'), 
                    '%(startyear)s', gfo('%(STARTYEAR)s'));

setEndTimeOptions('%(endsecond)s', gfo('%(ENDSECOND)s'), 
                    '%(endminute)s', gfo('%(ENDMINUTE)s'), 
                    '%(endhour)s', gfo('%(ENDHOUR)s'), 
                    '%(endday)s', gfo('%(ENDDAY)s'), 
                    '%(endmonth)s', gfo('%(ENDMONTH)s'), 
                    '%(endyear)s', gfo('%(ENDYEAR)s'));      

//Initially time is setup using the above; want QUICKTIMESELECTOR radio buttons all 
//unselected.
clearButtons(gfo('%(QUICKTIMESELECTOR)s'));
                    
// -->
</script>


"""
        vars={'startyear':'[startyear]', 'startmonth':'[startmonth]', 'startday':'[startday]','starthour':'[starthour]', 
            'startminute':'[startminute]', 'startsecond':'[startsecond]', 
            'endyear':'[endyear]', 'endmonth':'[endmonth]', 'endday':'[endday]','endhour':'[endhour]', 
            'endminute':'[endminute]', 'endsecond':'[endsecond]', 
            }

        taggedVars={'STARTSECOND':'STARTSECOND', 'STARTMINUTE':'STARTMINUTE', 'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY','STARTMONTH':'STARTMONTH', 'STARTYEAR':'STARTYEAR',
                    'ENDSECOND':'ENDSECOND', 'ENDMINUTE':'ENDMINUTE', 'ENDHOUR':'ENDHOUR',
                    'ENDDAY':'ENDDAY','ENDMONTH':'ENDMONTH', 'ENDYEAR':'ENDYEAR',
                    'QUICKTIMESELECTOR':'QUICKTIMESELECTOR',
                    }
        
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

class HTMLTimeSelectorDiq(HTMLObject):
    """Start/End time selector.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        body="""
<div align="center">
 <table width="700">
  <tr> 
    <td colspan="2"><div align="center">
    <table width="100%">
      <tr>
          <td class="widgetLabel" align="center" width="180">Quick Selector; see last...</td>
         <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="1440" onClick="updateTimeFromQuickSelector(this.value);">
             1 day</td>
       <td width="70" class="widgetOptionCell" ><input type="radio" name="%(QUICKTIMESELECTOR)s" value="10080" onClick="updateTimeFromQuickSelector(this.value);">
             1 week</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="20160" onClick="updateTimeFromQuickSelector(this.value);">
             2 weeks</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="30240" onClick="updateTimeFromQuickSelector(this.value);">
             3 weeks</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="40320" onClick="updateTimeFromQuickSelector(this.value);">
             4 weeks</td>
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="89280" onClick="updateTimeFromQuickSelector(this.value);">
             2 months</td>
            <!--
           <td width="70" class="widgetOptionCell"><input type="radio" name="%(QUICKTIMESELECTOR)s" value="-1" onClick="updateTimeFromQuickSelector(this.value);">
             All</td>
             -->
       </tr>
    </table>
    </td>
  </tr>
  <tr>
    <td colspan="2"><div align="center">
        <table border="0" width="100%">
          <tr> 
            <td class="widgetLabel" align="center" width="70"> Start: </td>
            <td align="center"> Day (m/d/y) </td>
            <td width="180" > <select NAME=%(STARTMONTH)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(STARTDAY)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(STARTYEAR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 2002</option>
                <option> 2003</option>
                <option> 2004</option>
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>                  
                <option> 2011</option>                  
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select> </td>
            <td align="center"> Time (h:m:s) </td>
            <td width="175">
              <select NAME=%(STARTHOUR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
              </select>
              <select NAME=%(STARTMINUTE)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select>
              <select NAME=%(STARTSECOND)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> </td>
          </tr>
          <tr> 
            <td class="widgetLabel" align="center" width="70" > End: </td>
            <td align="center"> Day (m/d/y) </td>
            <td>
              <select NAME=%(ENDMONTH)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
              </select>
              <select NAME=%(ENDDAY)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
              </select>
              <select NAME=%(ENDYEAR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 2005</option>
                <option> 2006</option>
                <option> 2007</option>
                <option> 2008</option>
                <option> 2009</option>
                <option> 2010</option>
                <option> 2011</option>
                <option> 2012</option>
                <option> 2013</option>
                <option> 2014</option>
                <option> 2015</option>
                <option> 2016</option>
                <option> 2017</option>
                <option> 2018</option>
                <option> 2019</option>
                <option> 2020</option>
                <option> 2021</option>
                <option> 2022</option>
                <option> 2023</option>
                <option> 2024</option>
                <option> 2025</option>
                <option> 2026</option>
                <option> 2027</option>
                <option> 2028</option>
                <option> 2029</option>
                <option> 2030</option>
              </select> </td>
            <td align="center"> Time (h:m:s) </td>
            <td> <select NAME=%(ENDHOUR)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
              </select>
              <select NAME=%(ENDMINUTE)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select>
              <select NAME=%(ENDSECOND)s SIZE=1 onChange="clearButtons(gfo('%(QUICKTIMESELECTOR)s'));">
                <option> 00</option>
                <option> 01</option>
                <option> 02</option>
                <option> 03</option>
                <option> 04</option>
                <option> 05</option>
                <option> 06</option>
                <option> 07</option>
                <option> 08</option>
                <option> 09</option>
                <option> 10</option>
                <option> 11</option>
                <option> 12</option>
                <option> 13</option>
                <option> 14</option>
                <option> 15</option>
                <option> 16</option>
                <option> 17</option>
                <option> 18</option>
                <option> 19</option>
                <option> 20</option>
                <option> 21</option>
                <option> 22</option>
                <option> 23</option>
                <option> 24</option>
                <option> 25</option>
                <option> 26</option>
                <option> 27</option>
                <option> 28</option>
                <option> 29</option>
                <option> 30</option>
                <option> 31</option>
                <option> 32</option>
                <option> 33</option>
                <option> 34</option>
                <option> 35</option>
                <option> 36</option>
                <option> 37</option>
                <option> 38</option>
                <option> 39</option>
                <option> 40</option>
                <option> 41</option>
                <option> 42</option>
                <option> 43</option>
                <option> 44</option>
                <option> 45</option>
                <option> 46</option>
                <option> 47</option>
                <option> 48</option>
                <option> 49</option>
                <option> 50</option>
                <option> 51</option>
                <option> 52</option>
                <option> 53</option>
                <option> 54</option>
                <option> 55</option>
                <option> 56</option>
                <option> 57</option>
                <option> 58</option>
                <option> 59</option>
              </select> </td>
          </tr>
        </table>
      </div></td>
  </tr>
</table>
</div>
<script language="JavaScript">
// <!--
//Update the time selection based on the radio button clicked.        
function updateTimeFromQuickSelector(quickLapseValue)
{
    var endTime = new Date();                // Get current time.

    //Special case, want the start date to be Jan 1, 2002
    if (quickLapseValue=="-1")
    {
        //var startTime = new Date(2002, 0, 1,0,0,0);    // Does not work in IE
        var startTime = new Date("Jan 1, 2002 00:00:00");
    }
    else
    {
        // quickLapseValue in minutes, but want milliseconds
        var startTime = new Date(endTime.getTime()-quickLapseValue*60.0*1000.0); 
    }

    //TESTING
    //gfo('%(XLABEL)s').value=startTime.toLocaleString();
    //gfo('%(YLABEL)s').value=endTime.toLocaleString(); 
    
    setStartTimeOptions(startTime.getSeconds(), gfo('%(STARTSECOND)s'), 
                    startTime.getMinutes(), gfo('%(STARTMINUTE)s'), 
                    startTime.getHours(), gfo('%(STARTHOUR)s'), 
                    startTime.getDate(), gfo('%(STARTDAY)s'), 
                    startTime.getMonth()+1, gfo('%(STARTMONTH)s'), 
                    startTime.getFullYear(), gfo('%(STARTYEAR)s'));

    setEndTimeOptions(endTime.getSeconds(), gfo('%(ENDSECOND)s'), 
                    endTime.getMinutes(), gfo('%(ENDMINUTE)s'), 
                    endTime.getHours(), gfo('%(ENDHOUR)s'), 
                    endTime.getDate(), gfo('%(ENDDAY)s'), 
                    endTime.getMonth()+1, gfo('%(ENDMONTH)s'), 
                    endTime.getFullYear(), gfo('%(ENDYEAR)s'));
                    
}

//////
// Initial setup.
/////

//Set up start/end times.
setStartTimeOptions('%(startsecond)s', gfo('%(STARTSECOND)s'), 
                    '%(startminute)s', gfo('%(STARTMINUTE)s'), 
                    '%(starthour)s', gfo('%(STARTHOUR)s'), 
                    '%(startday)s', gfo('%(STARTDAY)s'), 
                    '%(startmonth)s', gfo('%(STARTMONTH)s'), 
                    '%(startyear)s', gfo('%(STARTYEAR)s'));

setEndTimeOptions('%(endsecond)s', gfo('%(ENDSECOND)s'), 
                    '%(endminute)s', gfo('%(ENDMINUTE)s'), 
                    '%(endhour)s', gfo('%(ENDHOUR)s'), 
                    '%(endday)s', gfo('%(ENDDAY)s'), 
                    '%(endmonth)s', gfo('%(ENDMONTH)s'), 
                    '%(endyear)s', gfo('%(ENDYEAR)s'));      

//Initially time is setup using the above; want QUICKTIMESELECTOR radio buttons all 
//unselected.
clearButtons(gfo('%(QUICKTIMESELECTOR)s'));
                    
// -->
</script>


"""
        vars={'startyear':'[startyear]', 'startmonth':'[startmonth]', 'startday':'[startday]','starthour':'[starthour]', 
            'startminute':'[startminute]', 'startsecond':'[startsecond]', 
            'endyear':'[endyear]', 'endmonth':'[endmonth]', 'endday':'[endday]','endhour':'[endhour]', 
            'endminute':'[endminute]', 'endsecond':'[endsecond]', 
            }

        taggedVars={'STARTSECOND':'STARTSECOND', 'STARTMINUTE':'STARTMINUTE', 'STARTHOUR':'STARTHOUR',
                    'STARTDAY':'STARTDAY','STARTMONTH':'STARTMONTH', 'STARTYEAR':'STARTYEAR',
                    'ENDSECOND':'ENDSECOND', 'ENDMINUTE':'ENDMINUTE', 'ENDHOUR':'ENDHOUR',
                    'ENDDAY':'ENDDAY','ENDMONTH':'ENDMONTH', 'ENDYEAR':'ENDYEAR',
                    'QUICKTIMESELECTOR':'QUICKTIMESELECTOR',
                    }
        
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

                
        
#TEMPORARY... to be deleted... once iq page gets updated..
class HTMLItemC4(HTMLObject):
    """Two images.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
 
    def __init__(self, **kwargs):
 
        body="""  
<div align="center">
<table border="0" cellpadding="0" cellspacing="0">
    <tr>
        <th colspan="2" class="siteHead1"><pre>%(header)s</pre></th>
    </tr>
</table>
<br>
<table border="0" cellpadding="0" cellspacing="0">
    <tr>
      <td><table border="0" cellpadding="0" cellspacing="0">
          <tr> 
      <td><a href="%(imagelarge1)s"><img alt="<%(image1)s>" src="%(image1)s" align="middle"></a></td>
   
          </tr>
        </table></td>
      <td><table border="0" cellpadding="0" cellspacing="0">
          <tr> 
       <td><a href="%(imagelarge2)s"><img alt="<%(image2)s>" src="%(image2)s" align="middle"></a></td>
   
          </tr>
        </table></td>
    </tr>
  </table>
</div>
"""
        vars={'image1':'[image1]','image2':'[image2]',
              'imagelarge1':'[imagelarge1]','imagelarge2':'[imagelarge2]',
              'header':'[header]'}
 
        HTMLObject.__init__(self, vars=vars, body=[body])
 
 
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
 

class HTMLTimeSelectorOverloads(HTMLTimeSelector):
    """Start/End time selector with quick selectors.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """
    def __init__(self, **kwargs):
        
        quickSelectionHtml="""
<div align="center">
<table>
<tr>
<td>

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(7*1440);
startEndTimeSelector%(JS)s.end.now();
return false;"
onClick="return false;">Last_7_Days</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(14*1440);
startEndTimeSelector%(JS)s.end.now();
return false;"
onClick="return false;">Last_2_Weeks</a>]

[<a href="javascript:void(0)" onMouseDown="
startEndTimeSelector%(JS)s.start.now();
startEndTimeSelector%(JS)s.start.sub(91*1440);    // ~91 days in 3 months.
startEndTimeSelector%(JS)s.end.now();
return false;"
onClick="return false;">Last_3_Months</a>]

</td>
</tr>
</table>
</div>
"""
        
        quickSelectionJavaScript="""
<script language="JavaScript">
// <!--
 
// -->
</script>
"""
        HTMLTimeSelector.__init__(self)
                    
        self.body.insert(0, quickSelectionHtml)
        self.body.append(quickSelectionJavaScript)
        
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLPlot(HTMLObject):
    """Single plot.
    """

    def __init__(self, **kwargs):

        body="""  
<div align="center">
<br>
<table border="0" cellpadding="0" cellspacing="0">
     <tr> 
        <td> <a href="%(datafilename)s"><img src="%(imagefilename)s"></a> </td>
    </tr>
    <tr>
        <td>
            &nbsp;
        </td>
    </tr>
</table>
</div>
"""
        vars={'imagefilename':'[imagefilename]', 
              'dataFileName':'[dataFileName]',
              }
    
        HTMLObject.__init__(self, vars=vars, body=[body])
              

        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

class HTMLImage(HTMLObject):
    """Single plot.
    """
    def __init__(self, **kwargs):

        body="""  
<div align="center">
<br>
<table border="0" cellpadding="0" cellspacing="0">
     <tr> 
        <td> <a href="%(largeimagefilename)s"><img src="%(imagefilename)s"></a> </td>
    </tr>
    <tr>
        <td>
            &nbsp;
        </td>
    </tr>
</table>
</div>
"""
        vars={'imagefilename':'[imagefilename]', 
              'largeimagefilename':'[largeimagefilename]',
              }
    
        HTMLObject.__init__(self, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
 
class HTMLScalingOptions(HTMLObject):
    
    def __init__(self, **kwargs):

        body="""  
<script language="JavaScript">
// <!--
if (!isBrowserSupported())
{
    document.write('<div align=center><strong>Channel scaling is supported in Firefox, Mozilla 1.6+ and IE5.5+. Please switch to a newer browser.</strong></div>');
    document.ids.ScalingSelector%(JS)s.display='none';
}
 
// -->
</script>

        
<div align="center">
<table width="700">
    <tr>
        <td colspan="2" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
            <a id="ScalingSelectorShowLink%(JS)s" href="javascript:void(0)" onMouseDown="
            hideEl('ScalingSelectorShowLink%(JS)s');
            showEl('ScalingSelectorHideLink%(JS)s');
            showEl('ScalingSelector%(JS)s');
            return false;"
            onClick="return false;">[Show Scaling Options...]</a>
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
            hideEl('ScalingSelectorHideLink%(JS)s');
            showEl('ScalingSelectorShowLink%(JS)s');
            hideEl('ScalingSelector%(JS)s');
            return false;"
            onClick="return false;">[Hide Scaling Options...]</a>
        </td>
    </tr>
</table>
<div align="center" id="ScalingSelector%(JS)s" >
<table border="0"  cellpadding="0" width="700">
    <tr> 
        <td colspan=4 align="left">
                Scaling *only* affects plotted data
        </td>
    </tr>
    <tr> 
        <td width="400" align="center" class="widgetChanSelLabel">
                Channel Name
        </td>
        <td align="center" colspan="1" class="widgetChanSelLabel">
                Scaling Factor (mult.)
        </td>
        <td align="center" colspan="1" class="widgetChanSelLabel">
                Offset (add)
        </td>
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan1%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale1%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset1%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(1);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan2%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale2%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset2%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(2);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan3%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale3%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset3%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(3);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan4%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale4%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset4%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(4);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan5%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale5%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset5%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(5);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan6%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale6%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset6%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(6);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan7%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale7%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset7%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(7);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan8%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale8%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset8%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(8);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan9%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale9%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset9%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(9);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan10%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale10%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset10%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(10);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan11%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale11%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset11%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(11);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan12%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale12%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset12%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(12);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan13%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale13%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset13%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(13);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan14%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale14%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset14%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(14);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan15%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale15%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset15%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(15);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td>
            <input id="ScalingSelectorChan16%(JS)s" type=text " size=55 maxlength=100 value="">
        </td>
        <td >
            <input id="ScalingSelectorScale16%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td >
             <input id="ScalingSelectorOffset16%(JS)s" type=text  size=10 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(16);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>
    <tr>
        <td colspan="3">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearAllChanScaleInput%(JS)s();
                parseChanToScaleQuery%(JS)s('%(chantoscale)s');
                return false;"
                onClick="return false;">[Fill with plotted channels]
            </a>    
        </td>
        <td align="center">
            <a id="ScalingSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearAllChanScaleInput%(JS)s();
                return false;"
                onClick="return false;">[Clear All]
            </a>        
        </td> 
    </tr>
<!-- Not implemented handling of these yet...
    <tr> 
        <td align="center" class="widgetChanSelLabel">
                Reg Exp Pattern
        </td>
        <td align="center" class="widgetChanSelLabel">
                Scaling Factor (mult. data by...)
        </td>
    </tr>
    <tr>
        <td>
            <input name="%(PATTERNTOSCALE)s" type=text " size=55 maxlength=100 value="%(patterntoscale)s">
        </td>
        <td >
            <input id="%(PATTERNTOSCALEFACTOR)s" type=text  size=20 maxlength=20 value="%(patterntoscalefactor)s">
        </td>
    </tr>
-->
    
</table>
</div>

<input type=hidden name=%(CHANTOSCALE)s value="">

<script language="JavaScript">
hideEl('ScalingSelectorHideLink%(JS)s');
showEl('ScalingSelectorShowLink%(JS)s');
hideEl('ScalingSelector%(JS)s');

ScalingOptions_chanInputNum%(JS)s=16;

function createChanToScaleQuery%(JS)s()
{
    var str='';
    var temp='';
    
    for (var i=0; i<ScalingOptions_chanInputNum%(JS)s; i++) 
    {
        // Have limited number of input options...
        if (i>=ScalingOptions_chanInputNum%(JS)s) 
            break;
        
        temp=gebid('ScalingSelectorChan'+(i+1)+'%(JS)s').value;
        if (temp!='')
        {   
            if (str!='')
                str+='|';
                
            str+=temp+','+gebid('ScalingSelectorScale'+(i+1)+'%(JS)s').value+','+gebid('ScalingSelectorOffset'+(i+1)+'%(JS)s').value;
        }
    }
    gfo('%(CHANTOSCALE)s').value=str;
    
    // Want to return true, as this is called before submitting the form.
    return true;
}

function parseChanToScaleQuery%(JS)s (chanToScale)
{
    if (chanToScale=='')
        return;
        
    var chanAndScale=chanToScale.split('|');
    for (var i=0; i<chanAndScale.length; i++) 
    {
        // Have limited number of input options...
        if (i>=ScalingOptions_chanInputNum%(JS)s) 
            break;
        
        var s=chanAndScale[i].split(',');
        
        //document.write('<br>'+s.join('')+'<br>');
        gebid('ScalingSelectorChan'+(i+1)+'%(JS)s').value=s[0];
        gebid('ScalingSelectorScale'+(i+1)+'%(JS)s').value=s[1];
        gebid('ScalingSelectorOffset'+(i+1)+'%(JS)s').value=s[2];
    }
}

function clearChanInput%(JS)s(num)
{
    gebid('ScalingSelectorChan'+num+'%(JS)s').value='';
    gebid('ScalingSelectorScale'+num+'%(JS)s').value='';
    gebid('ScalingSelectorOffset'+num+'%(JS)s').value='';
}

function clearAllChanScaleInput%(JS)s()
{
    for (var i=1; i<=ScalingOptions_chanInputNum%(JS)s; i++) 
    {
        clearChanInput%(JS)s(i);
    }
}

// Want to make sure we do some processing before the form is submitted.
globalSubmitFunctions.push(createChanToScaleQuery%(JS)s);

parseChanToScaleQuery%(JS)s('%(chantoscale)s');

</script>
</div>
"""
        vars={'chantoscale':'[chantoscale]', 'patterntoscale':'[patterntoscale]', 'patterntoscalefactor':'[patterntoscalefactor]'}
        taggedVars={'JS':'JS', 'CHANTOSCALE':'CHANTOSCALE', 
        'PATTERNTOSCALE':'PATTERNTOSCALE',
        'PATTERNTOSCALEFACTOR':'PATTERNTOSCALEFACTOR'
        }
    
        HTMLObject.__init__(self, vars=vars, taggedVars=taggedVars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
                
class HTMLChannelConfigOptions(HTMLObject):
    
    def __init__(self, **kwargs):

        body=self._createBody(numEntries=10)
                   
        vars={'chanconfig':'[chanconfig]'}
    
        HTMLObject.__init__(self, autoTaggedVars=True, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)                
 
    def _createBody(self, numEntries=10):
        
        html=['''
<script language="JavaScript">
// <!--
if (!isBrowserSupported())
{
    document.write('<div align=center><strong>Changing channel options is supported in Firefox, Mozilla 1.6+ and IE5.5+. Please switch to a newer browser.</strong></div>');
    document.ids.ChanConfigOptions%(JS)s.display='none';
}
 
// A global to keep in track of how many entries we have. 
ChannelConfigOptions_chanInputNum%(JS)s=%(numEntries)s; 

// -->
</script>
        
<div align="center">
<table width="700">
    <tr>
        <td colspan="2" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
            <!-- <img src="%(wwwimagesdir)s/new.gif"> -->
            <a id="ChanConfigOptionsShowLink%(JS)s" href="javascript:void(0)" onMouseDown="
            hideEl('ChanConfigOptionsShowLink%(JS)s');
            showEl('ChanConfigOptionsHideLink%(JS)s');
            showEl('ChanConfigOptions%(JS)s');
            return false;"
            onClick="return false;">[Show <strong>Channel</strong> Configuration Options...] </a>
            <a id="ChanConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
            hideEl('ChanConfigOptionsHideLink%(JS)s');
            showEl('ChanConfigOptionsShowLink%(JS)s');
            hideEl('ChanConfigOptions%(JS)s');
            return false;"
            onClick="return false;">[Hide <strong>Channel</strong> Configuration Options...] </a> 
        </td>
    </tr>
</table>      

<div align="center" id="ChanConfigOptions%(JS)s" >



<table border="0"  cellpadding="0" width="700">  

    <tr> 
        <td colspan=6 align="left">
<pre>These optoins *only* affects plotted data</pre>          
        </td>
    </tr>
    <tr> 
    
        <td width="10" align="center" class="widgetChanSelLabel">
                Id
        </td>    
        <td width="150" align="center" class="widgetChanSelLabel">
                Channel Name
        </td>
        <td width="250" align="center" class="widgetChanSelLabel">
                Legend Name
        </td>        
        <td align="center" colspan="1" class="widgetChanSelLabel">
                Scaling (mult.)
        </td>
        <td align="center" colspan="1" class="widgetChanSelLabel">
                Offset (add)
        </td>
    </tr>        
'''  % StrDict({'numEntries':str(numEntries)})]

        for i in range(1, numEntries+1):
            #Go in the look and add new entires for channels; one per row.
            
            #Here we're only string-replacing the 'i's. The other 'JS's get replaced later on
            #automatically when the html is being created. See HTMLObject.__str__() how this is done.
            html.append("""            
    <tr>
        <td>
            <strong>%(i)s</strong>
        </td>    
        <td>
            <input id="ChanConfigOptionsChan%(i)s%(JS)s" type=text " size=45 maxlength=250 value="">
        </td>
        <td>
            <input id="ChanConfigOptionsName%(i)s%(JS)s" type=text " size=25 maxlength=150 value="">
        </td>        
        <td >
            <input id="ChanConfigOptionsScale%(i)s%(JS)s" type=text  size=4 maxlength=20 value="">
        </td>
        <td >
             <input id="ChanConfigOptionsOffset%(i)s%(JS)s" type=text  size=4 maxlength=20 value="">
        </td>
        <td align="center">
            <a id="ChanConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearChanInput%(JS)s(%(i)s);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>            
""" % StrDict({'i':str(i)}))
                                    
        html.append("""
    <tr>
        <td colspan="5">
            <a id="ChanConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearAllChanInput%(JS)s();
                parseQuery%(JS)s('%(chanconfig)s');
                return false;"
                onClick="return false;">[Fill with plotted channels]
            </a>    
        </td>
        <td align="center">
            <a id="ChanConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearAllChanInput%(JS)s();
                return false;"
                onClick="return false;">[Clear All]
            </a>        
        </td> 
    </tr>
    
</table>
</div>

<input type=hidden name=%(CHANCONFIG)s value="">

<script language="JavaScript">
hideEl('ChanConfigOptionsHideLink%(JS)s');
showEl('ChanConfigOptionsShowLink%(JS)s');
hideEl('ChanConfigOptions%(JS)s');

ChannelConfigOptions_recSep%(JS)s="|||";
ChannelConfigOptions_fieldSep%(JS)s=",,,";

function createQuery%(JS)s()
{
    var str='';
    var temp='';
    
    for (var i=0; i<ChannelConfigOptions_chanInputNum%(JS)s; i++) 
    {
        // Have limited number of input options...
        if (i>=ChannelConfigOptions_chanInputNum%(JS)s) 
            break;
        
        temp=gebid('ChanConfigOptionsChan'+(i+1)+'%(JS)s').value;
        if (temp!='')
        {   
            if (str!='')
                str+=ChannelConfigOptions_recSep%(JS)s;
                
            str+=temp+ChannelConfigOptions_fieldSep%(JS)s+gebid('ChanConfigOptionsName'+(i+1)+'%(JS)s').value+ChannelConfigOptions_fieldSep%(JS)s+gebid('ChanConfigOptionsScale'+(i+1)+'%(JS)s').value+ChannelConfigOptions_fieldSep%(JS)s+gebid('ChanConfigOptionsOffset'+(i+1)+'%(JS)s').value;
        }
    }
    gfo('%(CHANCONFIG)s').value=str;
    
    // Want to return true, as this is called before submitting the form.
    return true;
}


function parseQuery%(JS)s (chanConfig)
{
    if (chanConfig=='')
        return;
        
    var chanConfig=chanConfig.split(ChannelConfigOptions_recSep%(JS)s);
    for (var i=0; i<chanConfig.length; i++) 
    {
        // Have limited number of input options...
        if (i>=ChannelConfigOptions_chanInputNum%(JS)s) 
            break;
                
        var s=chanConfig[i].split(ChannelConfigOptions_fieldSep%(JS)s);
        
        if (s.length==2)
        {
            //Only have data for the legendName of the channel, set default scaling and offset
            gebid('ChanConfigOptionsChan'+(i+1)+'%(JS)s').value=s[0];
            gebid('ChanConfigOptionsName'+(i+1)+'%(JS)s').value=s[1];       
            gebid('ChanConfigOptionsScale'+(i+1)+'%(JS)s').value="1";
            gebid('ChanConfigOptionsOffset'+(i+1)+'%(JS)s').value="0";                         
        }
        else
        {
            // Now have all the data (name, scaling factor, offset)
            gebid('ChanConfigOptionsChan'+(i+1)+'%(JS)s').value=s[0];
            gebid('ChanConfigOptionsName'+(i+1)+'%(JS)s').value=s[1];
            gebid('ChanConfigOptionsScale'+(i+1)+'%(JS)s').value=s[2];
            gebid('ChanConfigOptionsOffset'+(i+1)+'%(JS)s').value=s[3];
        }
    }
}

function clearChanInput%(JS)s(num)
{
    gebid('ChanConfigOptionsChan'+num+'%(JS)s').value='';
    gebid('ChanConfigOptionsName'+num+'%(JS)s').value='';    
    gebid('ChanConfigOptionsScale'+num+'%(JS)s').value='';
    gebid('ChanConfigOptionsOffset'+num+'%(JS)s').value='';
}

function clearAllChanInput%(JS)s()
{
    for (var i=1; i<=ChannelConfigOptions_chanInputNum%(JS)s; i++) 
    {
        clearChanInput%(JS)s(i);
    }
}

// Want to make sure we do some processing before the form is submitted.
globalSubmitFunctions.push(createQuery%(JS)s);

parseQuery%(JS)s('%(chanconfig)s');

</script>
</div> """)
            
        return ''.join(html) 


class HTMLEquationConfigOptions(HTMLObject):
    
    def __init__(self, **kwargs):

        body=self._createBody(numEntries=10)
                   
        vars={'equationconfig':'[equationconfig]', 'plotoperands':'[plotoperands]',
              'eqinterpolate':'[eqinterpolate]'}
    
        HTMLObject.__init__(self, autoTaggedVars=True, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)                
 
    def _createBody(self, numEntries=10):
        
        html=['''
<script language="JavaScript">
// <!--
if (!isBrowserSupported())
{
    document.write('<div align=center><strong>Changing equation options is supported in Firefox, Mozilla 1.6+ and IE5.5+.. Please switch to a newer browser.</strong></div>');
    document.ids.EquationConfigOptions%(JS)s.display='none';
}
 
// A global to keep in track of how many entries we have. 
EquationConfigOptions_InputNum%(JS)s=%(numEntries)s; 

// -->
</script>
        
<div align="center">
<table width="700">
    <tr>
        <td colspan="2" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
            <!-- <img src="%(wwwimagesdir)s/new.gif"> -->
            <a id="EquationConfigOptionsShowLink%(JS)s" href="javascript:void(0)" onMouseDown="
            hideEl('EquationConfigOptionsShowLink%(JS)s');
            showEl('EquationConfigOptionsHideLink%(JS)s');
            showEl('EquationConfigOptions%(JS)s');
            return false;"
            onClick="return false;">[Show <strong>Equation</strong> Configuration Options...] </a> 
            <a id="EquationConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
            hideEl('EquationConfigOptionsHideLink%(JS)s');
            showEl('EquationConfigOptionsShowLink%(JS)s');
            hideEl('EquationConfigOptions%(JS)s');
            return false;"
            onClick="return false;">[Hide <strong>Equation</strong> Configuration Options...] </a>  
        </td>
    </tr>
</table>      

<div align="center" id="EquationConfigOptions%(JS)s" >



<table border="0"  cellpadding="0" width="700">  

    <tr> 
        <td colspan=4 align="left">
<pre style="font-family:verdana, arial, sans-serif; font-size: small;">
Please read <a href="/pages/helpPage?PAGE=geaDoc.html#Equation_Editor">this</a> before using the equation editor.
Currently equation data is not exported as text (and visable when the plot is clicked), but this feature
will be implemented shortly.
</pre>          
        </td>
    </tr>
    <tr>
        <td colspan="4">
            <table width="700">
                <tr>
                <td class="widgetLabel"   align="center" valign="middle">
                    Plot operands
                </td>    
                <td class="widgetOptionCell2" align="left" valign="middle">
                        <select NAME="%(PLOTOPERANDS)s" SIZE=1>
                            <option selected> No</option>
                            <option> Yes</option>
                        </select>            
                </td>
                <td class="widgetLabel"   align="center" valign="middle">
                    Interpolate [S]
                </td>
                <td align="left" valign="middle" class="widgetOptionCell2">
                    <input type=text align="right"  name="%(EQINTERPOLATE)s" size=10 maxlength=10 value="%(eqinterpolate)s"> 
                </td> 
                </tr> 
            </table>                
         </td>
    
    </tr>
    <tr> 
    
        <td width="10" align="center" class="widgetChanSelLabel">
                Id
        </td>    
        <td width="150" align="center" class="widgetChanSelLabel">
                Equation
        </td>
        <td width="250" align="center" class="widgetChanSelLabel">
                Legend Name
        </td>        
    </tr>        
'''  % StrDict({'numEntries':str(numEntries)})]

        for i in range(1, numEntries+1):
            #Go in the look and add new entires for channels; one per row.
            
            #Here we're only string-replacing the 'i's. The other 'JS's get replaced later on
            #automatically when the html is being created. See HTMLObject.__str__() how this is done.
            html.append("""            
    <tr>
        <td>
            <strong>%(i)s</strong>
        </td>    
        <td>
            <input id="EquationConfigOptionsEq%(i)s%(JS)s" type=text " size=65 maxlength=250 value="">
        </td>
        <td>
            <input id="EquationConfigOptionsName%(i)s%(JS)s" type=text " size=25 maxlength=150 value="">
        </td>
        <td align="center">
            <a id="EquationConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearInput%(JS)s(%(i)s);
                return false;"
                onClick="return false;">[Clear]
            </a>        
        </td> 
    </tr>            
""" % StrDict({'i':str(i)}))
                                    
        html.append("""
    <tr>
        <td colspan="3">
            <a id="EquationConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearAllInput%(JS)s();
                parseQuery%(JS)s('%(equationconfig)s');
                return false;"
                onClick="return false;">[Fill with plotted equations]
            </a>    
        </td>
        <td align="center">
            <a id="EquationConfigOptionsHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
                clearAllInput%(JS)s();
                return false;"
                onClick="return false;">[Clear All]
            </a>        
        </td> 
    </tr>
    
</table>
</div>

<input type=hidden name=%(EQUATIONCONFIG)s value="">

<script language="JavaScript">
hideEl('EquationConfigOptionsHideLink%(JS)s');
showEl('EquationConfigOptionsShowLink%(JS)s');
hideEl('EquationConfigOptions%(JS)s');

EquationConfigOptions_recSep%(JS)s="|||";
EquationConfigOptions_fieldSep%(JS)s=",,,";

function createQuery%(JS)s()
{
    var str='';
    var temp='';
    
    for (var i=0; i<EquationConfigOptions_InputNum%(JS)s; i++) 
    {
        // Have limited number of input options...
        if (i>=EquationConfigOptions_InputNum%(JS)s) 
            break;
        
        temp=gebid('EquationConfigOptionsEq'+(i+1)+'%(JS)s').value;
        if (temp!='')
        {   
            if (str!='')
                str+=EquationConfigOptions_recSep%(JS)s;
                
            str+=temp+EquationConfigOptions_fieldSep%(JS)s+gebid('EquationConfigOptionsName'+(i+1)+'%(JS)s').value;
        }
    }
    gfo('%(EQUATIONCONFIG)s').value=str;
    
    // Want to return true, as this is called before submitting the form.
    return true;
}

function parseQuery%(JS)s (equationConfig)
{
    if (equationConfig=='')
        return;
        
    var equationConfigList=equationConfig.split(EquationConfigOptions_recSep%(JS)s);
    for (var i=0; i<equationConfigList.length; i++) 
    {
        // Have limited number of input options...
        if (i>=EquationConfigOptions_InputNum%(JS)s) 
            break;
                
        var s=equationConfigList[i].split(EquationConfigOptions_fieldSep%(JS)s);
        
        gebid('EquationConfigOptionsEq'+(i+1)+'%(JS)s').value=s[0];
        gebid('EquationConfigOptionsName'+(i+1)+'%(JS)s').value=s[1];                              
    }
}

function clearInput%(JS)s(num)
{
    gebid('EquationConfigOptionsEq'+num+'%(JS)s').value='';
    gebid('EquationConfigOptionsName'+num+'%(JS)s').value='';    
}

function clearAllInput%(JS)s()
{
    for (var i=1; i<=EquationConfigOptions_InputNum%(JS)s; i++) 
    {
        clearInput%(JS)s(i);
    }
}

// Want to make sure we do some processing before the form is submitted.
globalSubmitFunctions.push(createQuery%(JS)s);

parseQuery%(JS)s('%(equationconfig)s');

selectSingleOptByText(gfo('%(PLOTOPERANDS)s'), '%(plotoperands)s');

</script>
</div> """)
            
        return ''.join(html) 

class HTMLDynChanSelector(HTMLObject):
    """Dynamically creates a selection hierarchy, starting with a system through categories, 
    down to channels.
    
    This is kind of 'proof-of-concept' code... Should clean it up a a little and reorganize - probably
    put the parsing somewhere else.
  
    ---- temp info ----
    example of some data:
    
        data=[
        N('gws',
        [
            N("pressure", 
            [
                N('b1', None, system='b1Systems'), N('b2', None), N('b3', None)
            ]),
            N('wind', 
            [
                N('c1', None), N('c2', None), N('c3', None)
            ])
        ]),
        N('gwsfds',
        [
            N("pressfdsure", 
            [
                N('b1fs', None), N('bfs2', None), N('bfds3', None),N('bfddsss2', None), N('bfdddsss3', None)
            ]),
            N('windsdd', 
            [
                N('c1', None), N('c2', None), N('c3', None)
            ])
        ])
        ]
    --- temp info end ---
    
    """
    class N(object):
        """Node.
        """
        def __init__(self, name, tree, **kwargs):
            self.name=name
            self.tree=tree

            self.__dict__.update(kwargs)
            
        def getNames(self):
            """
            Returns a list of children's names.
            """
            return [item.name for item in self.tree]
            
        def getTrees(self):
            """
            Returns a list of children's trees (nodes).
            """
            return [item for item in self.tree]
            
        def isLeaf(self):
            return self.tree is None
            
        def toConfig(self, indent=0, parentArch=''):
            """
            Here indent==0 -> CAT1, indent==2 -> CAT2, etc..
            
            NOTE: Broken...Needs some work to properly display archivers. 
            """
            #Only list the archiver if defined. 
            archiver=self.__dict__.get('archiver', None)
            if archiver and archiver!=parentArch:
                archiverStr='# %s' % archiver
            else:
                archiverStr=''
            strList=[]
            
            if self.isLeaf():
                strList.append('%s\t\t%s\n' % (self.name, archiverStr))
                
            else:
                category='CAT%s' % str(indent+1)
                
                strList.append('#[%s] %s %s\n' % (category, self.name, archiverStr))
                
                for item in self.tree:
                    strList.append(item.toConfig(indent=indent+1, parentArch=archiver))

            return ''.join(strList)
                        
        def __str__(self, indent=0):
            """
            """
            ind=indent*'\t'
            
            if indent>0:
                if self.isLeaf():
                    strList=[ind, '\n', ind, 'Name: %s'% self.name,]
                else:
                    strList=[ind, '\n', ind, 'Name: %s\n'% self.name,]
            else:
                strList=[ind, 'Name: %s\n'% self.name,]
            
            if not self.isLeaf():
            
                strList+=[ ind, '[' ]
                for item in self.tree:
                    strList+=[item.__str__(indent=indent+1)]
                
                strList+=['\n', ind, ']']
            
            return ''.join(strList)
            
        def __cmp__(self, other):
            return cmp(self.name, other.name)
         
        def sort(self, cmpfunct=None):
            """Assume balanced tree...
            """
            if not self.isLeaf():
                map(lambda x: x.sort(cmpfunct), self.tree)
                self.tree.sort(cmpfunct)
    
            return self
    
    def __init__(self, chanHierFile='', **kwargs):

        self.dataList=self._parseDataFile(chanHierFile)
        
        if 1:  #Sort...
            self.dataList=map(lambda x: x.sort(),  self.dataList)
            self.dataList.sort()
        
##~         print '<pre>'
##~         for item in self.dataList:
##~             print item.toConfig()
##~         print '</pre>'
        
        
        body="""
<div align="center">

<table width="700">
    <tr> 
        <td >
            <table width="100%">
                <tr> 
                  <td width="13%" align="center" class="widgetChanSelLabel">Archivers:</td>
                  <td width="87%"><input type=text name="%(SYSTEMS)s" size=32 maxlength=100 value="%(systems)s"></td>
                </tr>
            </table>
        </td>
        <td>
            <table  width="100%">
                    <tr> 
                      <td width="13%" align="center" class="widgetChanSelLabel">Pattern:</td>
                      <td width="87%"><input type=text name="%(PATTERN)s" size=40 maxlength=256 value="%(pattern)s"></td>
                    </tr>
                </table>
        </td>
    </tr>
</table>

<table width="700">
    <tr>
        <td colspan="2" style="font-family:verdana, arial, sans-serif; font-size: x-small;">
            <a id="ChannelSelectorShowLink%(JS)s" href="javascript:void(0)" onMouseDown="
            hideEl('ChannelSelectorShowLink%(JS)s');
            showEl('ChannelSelectorHideLink%(JS)s');
            showEl('ChannelSelector%(JS)s');
            return false;"
            onClick="return false;">[Show Detailed...]</a>
            <a id="ChannelSelectorHideLink%(JS)s"href="javascript:void(0)" onMouseDown="
            hideEl('ChannelSelectorHideLink%(JS)s');
            showEl('ChannelSelectorShowLink%(JS)s');
            hideEl('ChannelSelector%(JS)s');
            return false;"
            onClick="return false;">[Hide Detailed...]</a>
            <script language="JavaScript">
            showEl('ChannelSelectorHideLink%(JS)s');
            hideEl('ChannelSelectorShowLink%(JS)s');
            </script>
        </td>
    </tr>
</table>
<div id="ChannelSelector%(JS)s">
<table width="700">
    <tr>
        <td colspan="2">
            <table width="100%">
                    <tr>  
                            <td  width="200" align="center" class="widgetChanSelLabel">Top Component Selection</td>
                            <td align="center" class="widgetChanSelLabel">Component Selection</td>
                               
                    </tr>
                    <tr>
                            <td VALGN="top">
                                <select NAME="%(CAT1SELECTION)s" MULTIPLE size="15">
                                    
"""+self._getSystemOptionsHTML()+"""
                            
                                </select>
                            </td>
                            <td VALIGN="top">
                                 <select NAME="%(CAT2SELECTION)s" MULTIPLE size="15">
                                </select>
                            </td>
                    </tr>
                    <tr> 
                            <td colspan="2">
                                 <table width="100%" height="100%" align="center">
                                             <tr>
                                                 <td width="13%" align="center" class="widgetChanSelLabel">Channel Selection</td>
                                                 <td width="13%" align="center">&nbsp;</td>
                                                 <td width="13%" align="center" class="widgetChanSelLabel"> CHANNELS TO PLOT</td>
                                             </tr>
                                             
                                               <td width="28%">
                                                    <select width="25" NAME="%(SELECTION)s" MULTIPLE size="8">
                                                    </select>
                                                
                                                </td>
                                               <td width="20%"><table width="70%" height="100%" align="center" cellpadding="1">
                                                    <tr>
                                                     <td align="center" valign="middle"><input name="button1" type=button onClick="copySelectedOptions(gfo('%(SELECTION)s'),gfo('%(CHANNELS)s'),false); return false;" value=">> (Add Highlighted)"></td>
                                                   </tr>
                                                    <tr>
                                                     <td align="center" valign="middle"><input name="button2" type=button  onClick="copyAllOptions(gfo('%(SELECTION)s'),gfo('%(CHANNELS)s'),false);return false;" value="&gt;&gt (Add All)"></td>
                                                   </tr>
                                                    <tr>
                                                     <td align="center" valign="middle">&nbsp;</td>
                                                   </tr>
                                                  <tr>
                                                     <td align="center" valign="middle"> <input name="button5" type=button  onClick="selectAllOptions(gfo('%(CHANNELS)s'));return false;" value="Highlight All"></td>
                                                   </tr>
                                                   <tr>
                                                     <td align="center" valigns="middle"><input name="button3" type=button  onClick="removeSelectedOptions(gfo('%(CHANNELS)s'));return false;" value="Clear Highlighted"></td>
                                                   </tr>
                                                   <tr>
                                                     <td align="center" valign="middle"> <input name="button4" type=button  onClick="removeAllOptions(gfo('%(CHANNELS)s'));return false;" value="Clear All"></td>
                                                   </tr>
                                                 </table></td>
                                                    <td width="35%">
                                                   <select width="25" NAME="%(CHANNELS)s" MULTIPLE size="8">
                                                    </select>
                                                </td>
                                             </tr>
                                        </table>
                                           
                                    </td>
                    </tr>
            </table>
         </td>
    </tr>
</table>

<input type=hidden name=%(SYSTEMS2)s value="%(systems2)s">

<script language="JavaScript">

"""+self._getInitJS()+"""

/////////////
//Other inits
///////////
// Remember the chennels selection from call to call.  
addTextOptions(gfo('%(CHANNELS)s'), "%(channels)s");
//selectAllOptions(gfo('%(CHANNELS)s'));

</script>
</div>
</div>

"""
        vars={'systems':'[systems]',
              'systems2':'[systems2]',
              'pattern':'[pattern]',
              'channels':'[channels]',
              'legend':'[legend]',
            
              'cat1selection':'[cat1selection]',
              'cat2selection':'[cat2selection]',
              }
        
        taggedVars={'SYSTEMS':'SYSTEMS',
                    'SYSTEMS2':'SYSTEMS2',
                    'PATTERN':'PATTERN',
                    'CHANNELS':'CHANNELS',   
                    'SELECTION':'SELECTION',
                    
                    'CAT1SELECTION':'CAT1SELECTION',
                    'CAT2SELECTION':'CAT2SELECTION',
                    
                    'JS':'JS',
                    }
    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
         
    def _procCat1(self, dataStr):
        """
        Should optimize...
        """
        def pop():
            try:
                return lines.pop()
            except:
                return None
                        
        def getNameAndArchiver(str):
            i=str.find('#')
                
            if i> -1:
                name=str[0:i].strip()
                archiver=str[i:].lstrip('#').strip()
            else:
                name=str.strip()
                archiver=''
                        
            return name, archiver
    
        N=HTMLDynChanSelector.N
        
        lines=dataStr.split('\n')
        lines.reverse()
        
        archiverCat1=''  
        cat2List=[] 
        
        while 1:
            line=pop()
            if line is None:
                return      #Reached end of file... 
            elif line.startswith('[CAT1]'):
                
                #Check whether the category should be added based on what site we're running on.
                for s in ('[MK]', '[CP]'):
                    if line.find(s)>-1:
                        if s[1:3]!=GEAVars.site:
                            #Do not add this section.. 
                            return 
                        line=line.replace(s,'')
                   
                cat1, archiverCat1=getNameAndArchiver(line[7:].strip())
                if archiverCat1=='':
                    archiverCat1=cat1

                break #Now have the top category...
                
        while 1:
            archiverCat2=''
            line=pop()
            if line is None:
                break      #Reached end of file... 
            elif line.startswith('[CAT2]'):
            
                needToContinue=0
                for s in ('[MK]', '[CP]'):
                    if line.find(s)>-1:
                        if s[1:3]!=GEAVars.site:
                            needToContinue=1      #Do not add this section.. 
                            break
                        line=line.replace(s,'')
                if needToContinue:
                    continue
                
                cat2, archiverCat2=getNameAndArchiver(line[7:].strip())
                if archiverCat2=='':
                    archiverCat2=archiverCat1
                
                selections=[]
                
                while 1:
                    line=pop()
                    if line is None:
                        break      #Reached end of file... 
    
                    if line.startswith('[CAT2]'):
                        lines.append(line)
                        break   #New category... 
    
                    if line.startswith('#') or line=='' or line.startswith(' '):
                        continue

                    channel, archiverChan=getNameAndArchiver(line)
                    if archiverChan=='':
                        archiverChan=archiverCat2

                    selections.append(N(name=channel, tree=None, archiver=archiverChan))

                            
                cat2List.append(N(name=cat2, tree=selections, archiver=archiverCat2))
        
        #Find the name of the top category 
              
        return N(name=cat1, tree=cat2List, archiver=archiverCat1)
         
         
    def _parseDataFile(self, dataStr):
        return self._parseDataStr(open(GEAVars.path.fileSys.geaConf + "/pages/" + dataStr).read())

    def _parseDataStr(self, dataStr):
        
        dataList=[]
        cat1Segments=dataStr.split('[CAT1]')
              
        for cat1 in cat1Segments[1:]:
            d=self._procCat1("[CAT1]"+cat1)
            if d is not None:
                dataList.append(d)
        
        return dataList
        
    def _getSystemOptionsHTML(self):
        """
        Returns a line a string containing lines with <option>system</optoin> 
        for each system in self.dataList
        """
        return '\n'.join(map(lambda x: '<option>%s</option>' % x.name, self.dataList))
        
    def _getInitJS(self):
        """
        Returns the javascript needed to initialize data from self.dataList.
        
        ... some messy naming.. 'systems' are really archivers.. 
        """
        #Setup the dictionary which will hold the name of the system each channel is from.
        strList=['var HTMLDynChanSelector_makeModel%(JS)s = new DynamicOptionList("%(CAT1SELECTION)s","%(CAT2SELECTION)s","%(SELECTION)s");',
                 'var HTMLDynChanSelector_chan2ArchDict%(JS)s = new Array(); // So we know a which archiver the channels are from.\n']
        
        for cat1 in self.dataList:
            strList.append("//Setup '%s'" % cat1.name)
         
            cat2Names=cat1.getNames()
            strList.append('HTMLDynChanSelector_makeModel%%(JS)s.forText("%s").addOptions("%s");' % (cat1.name, '", "'.join(cat2Names)))
            
            #Go throught the categories and add channel names.
            for cat2 in cat1.getTrees():
                
                channels=cat2.getTrees()

                strList.append('HTMLDynChanSelector_makeModel%%(JS)s.forText("%s").forText("%s").addOptions("%s");' % (cat1.name, cat2.name, '", "'.join(cat2.getNames())))
            
                #Finally need to remember which of the archivers each of the channels resides in. 
  
                for channelNode in channels:
                    strList.append('HTMLDynChanSelector_chan2ArchDict%%(JS)s["%s"]="%s";' % (channelNode.name, channelNode.archiver))
                    
        strList+=['initDynamicOptionLists();',]
 
        strList+=["""
// 'archivers' and 'systems' here mean the same thing.... 
// Should be called before the form is submitted. 
// A bit of a hack.... 
function HTMLDynChanSelector_updateArchivers%(JS)s()
{
    var archivers=new Array();   //This will contain all the archivers with no duplicates.
    
    for (var i=0; i<gfo('%(CHANNELS)s').options.length; i++)
    {
        chanOpt=gfo('%(CHANNELS)s').options[i]
    
        //Only consider thes selected channels. 
        if (chanOpt.selected)
        {
            archivers[HTMLDynChanSelector_chan2ArchDict%(JS)s[chanOpt.text]]="";
        }
        
    }

    //Finally update the value of the input field.
    var newArchiversArray=new Array();
    for (var i in archivers)
    {
        if (i != 'undefined')
        {
            newArchiversArray.push(i);
        }
    }
    //document.forms[0]['debug'].value=newArchiversArray.join(" ");
    gfo('%(SYSTEMS2)s').value=newArchiversArray.join(" ");
    
    return true;
}

function HTMLDynChanSelector_selectChannels%(JS)s()
{
    selectAllOptions(gfo('%(CHANNELS)s'));
    return true;
}

//Add functions to run on submit. 
//ORDER VERY IMPORTANT HERE...
globalSubmitFunctions.push(HTMLDynChanSelector_selectChannels%(JS)s);
globalSubmitFunctions.push(HTMLDynChanSelector_updateArchivers%(JS)s);

"""]        

        return '\n'.join(strList)
    
class HTMLAnnouncement(HTMLObject):
    """Announcement.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """

    def __init__(self, **kwargs):
        
        body="""<fieldset class="announcement"><legend>Announcement</legend> 
<pre>%(announcement)s</pre>
</fieldset>
"""
        vars={'announcement':'[announcement]'}
        
        HTMLObject.__init__(self, vars=vars, body=[body])
              

        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLTextBox(HTMLObject):
    """Text box.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """

    def __init__(self, **kwargs):
        
        body="""<pre class="textbox">%(text)s</pre>"""
        
        vars={'text':'[text]'}
        
        HTMLObject.__init__(self, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLTextBox2(HTMLObject):
    """Text box.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """

    def __init__(self, **kwargs):
        
        body="""
<table class="textBox2">
<tr>
    <td class="textBox2">
        <pre class="textBox2">%(text)s</pre>
    </td>
</tr>
</table>
"""
        vars={'text':'[text]'}
        
        HTMLObject.__init__(self, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
class HTMLTextBox3(HTMLObject):
    """Text box.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """

    def __init__(self, **kwargs):
        
        body="""
<table class="textBox3" width=650>
<tr>
    <td align="right" class="textBox3">
        %(text)s
    </td>
</tr>
</table>
"""
        
        vars={'text':'[text]'}
        
        HTMLObject.__init__(self, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)                

class HTMLNotice(HTMLObject):
    """Notice.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """

    def __init__(self, **kwargs):
        
        body="""<fieldset class="notice"><legend>Notice</legend> 
<pre>%(text)s</pre>
</fieldset>"""
        
        vars={'text':'[text]'}
        
        HTMLObject.__init__(self, vars=vars, body=[body])
              

        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
        
class HTMLError(HTMLObject):
    """Error.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """

    def __init__(self, **kwargs):
        
        body="""<fieldset class="error"><legend>Error:</legend> 
<pre>%(text)s</pre>
</fieldset>"""
        
        vars={'text':'[text]'}
        
        HTMLObject.__init__(self, vars=vars, body=[body])
              

        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
        
class HTMLSep(HTMLObject):
    """Seperator.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """ 
    def __init__(self, **kwargs):
          
        body='<br><table width="100%"><tr><td><div align="center"><img src="%(wwwimagesdir)s%(himage)s" align="middle"></div></tr></td></table><br>'

        vars={'himage':'hrule.png'}
 
        HTMLObject.__init__(self, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

                
class HTMLPopupLink(HTMLObject):
    """
    """
    def __init__(self, **kwargs):
          
        body="""
<table border=0>
<tr>
<td>
    <a href="%(popupPage)s" onclick="javascript:popupPage('%(popupPage)s', '<pre>%(text)s</pre>'); return false;" target="newWin">
    %(name)s
    </a>
</td>
</tr>
</table>
"""
        vars={'text':'[text]', 
              'name':'[name]', 
              'popupPage':GEAVars.dispatchScript+'/pages/common/popupPage'}
 
        HTMLObject.__init__(self, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
      
class HTMLDynTable(HTMLObject):
    """Dynamic Html Table. 
    
    See PyHtmlTableGEA  for how to use it.
    
    Arguments/Attributes:
        body - Can be a list of any objects that have a string representation via str().
        vars - Dictionary with entries to be substituted into the html code.
        header - Printed before body.
        footer - Printed after body.
        taggedVars - 
        useTags -
        reSubList - 
        nameTag - 
        fStream - 
    """ 
    def __init__(self, rows=0, columns=0, tableAttrs=None, **kwargs):
        
        self._table=PyHtmlTableGEA(rows, columns, tableAttrs)
        
        HTMLObject.__init__(self, body=[self._table])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)
                
    def __getattr__(self, name):
        """Only get here when the attribute is not in self.__dict__. Look for it in self._table.
        
        No need to do this for setattr because, all attributes in PyHtmlTableGEA are set through
        methods.
        """
        return getattr(self._table, name)

    def add_array_after_last_row(self, inarr, attrs=None):
        """Overwrite for speed... 
        """
        return self._table.add_array_after_last_row(inarr, attrs)
            
    def setCellattrs( self, row, col, indict, overwrite=None):
        """Overwrite for speed... 
        """
        return self._table.setCellattrs(row, col, indict, overwrite)
        
        
class HTMLDynListTable(HTMLDynTable):
    """
    """
    def __init__(self, rows=1, columns=1, tableAttrs=None,  **kwargs):
        """
        See PyHtmlTableGEA for how to use it.
        """
        header=['<div align="left">']
        footer=['</div>']
        
        kwargs['header']=kwargs.get('header', [])+header
        kwargs['footer']=footer+kwargs.get('footer', [])
    
        if tableAttrs is None:
            tableAttrs={'class':'tableList', 'width':650}
    
        HTMLDynTable.__init__(self, rows=0, columns=0, tableAttrs=tableAttrs, **kwargs)
            
    def add_array_after_last_row(self, inarr, attrs=None):
        """Distinguish between rows...
        """

        # Hack alert. Only do even/odd rows in tables that have class, "tableList"
        # No other easy way to do this...

        if 'class="tableList"' not in self._table.tabattr:
            return self._table.add_array_after_last_row(inarr, attrs)

        if self._table.getmaxRow() % 2:
            defAttr={'class':'even'}
        else:
            defAttr={}
            
        if attrs is not None:
            defAttr.update(attrs)
        
        return self._table.add_array_after_last_row(inarr, defAttr)
        
            
class HTMLDynImageTable(HTMLDynTable):
    """
    """
    def __init__(self, imageList, imagesPerRow, title=None, tableAttrs=None, **kwargs):
        """
        See PyHtmlTableGEA for how to use it.
        """
        header=['<div align="center">']
        footer=['</div>']
        
        kwargs['header']=kwargs.get('header', [])+header
        kwargs['footer']=footer+kwargs.get('footer', [])
    
        if tableAttrs is None:
            tableAttrs={'class':'hMenu'}
    
        HTMLDynTable.__init__(self, rows=0, columns=0, tableAttrs=tableAttrs, **kwargs)
        
        self._addImages(imageList, imagesPerRow)
    
        #Add the title
        if title is not None:
            self._table.add_row(-1)   #First row
            self._table.setCellColSpan(0,0, self._table.getmaxCol()+1) # Span cell at index row 1,col 0, make 2 high
            self._table.setCellcontents(0,0, str(title), {'align':'center', 'class':'dynImTable'})
                
    def _addImages(self, imageList, imagesPerRow):
    
        #Create html with links.
        imageList=map(lambda imTup: '<a href="%s"><img src="%s" align="middle"></a>' % (imTup[1], imTup[0]), imageList)    

        imNum=len(imageList)
        
        first=0
        last=imagesPerRow
        
        while 1:            
            self._table.add_array_after_last_row(imageList[first:last])            
            
            if last>imNum:
                break
            
            first=last
            last+=imagesPerRow
    
class HTMLHorizontalMenu(HTMLDynTable):
    """
    """
    def __init__(self, menus, tableAttrs=None, selected=None, **kwargs):
        """
        See PyHtmlTableGEA for how to use it.
        
        Arguments:
        menus - list of lists of menus.
        """
##~         header=['<div align="center">']
##~         footer=['</div>']
##~         
##~         kwargs['header']=kwargs.get('header', [])+header
##~         kwargs['footer']=footer+kwargs.get('footer', [])
    
        if tableAttrs is None:
            tableAttrs={'class':'hMenu', 'cellpadding':0, 'cellspacing':0}
    
        HTMLDynTable.__init__(self, rows=0, columns=0, tableAttrs=tableAttrs, **kwargs)
        
        self.menus=menus
    
    def __str__(self):
        #Want to create the menus only at the time of 'string-ing' the object. This allowes to modify them multiple times
        #until the html is actually created.
        self._createMenus(self.menus)
        
        return HTMLDynTable.__str__(self)
        
    def _createMenus(self, menus):
    
        for miniMenu in menus:            
            #Each miniMenu is shown as a table row.
            #Each miniMenu can may have its own attributes.
            try:
                attrs=miniMenu.attrs
            except AttributeError:
                attrs={'class':'hMenu'}
                
            menuTable=PyHtmlTableGEA(0,0)
            menuTable.add_array_after_last_row(map(str, miniMenu), attrs=attrs)        
            
            self._table.add_array_after_last_row([str(menuTable)])
                
#SHOULD COMBINE THIS WITH /bin/menuCreator.py... bit of an overhead to create a new object for each item...
class MenuItem(object):
    def __init__(self, name, link, depth=0, selected=False, cssClass=None):
        self.name=name
        self.link=link
        self.depth=depth
        self.cssClass=cssClass
        
        if link is None:
            if self.cssClass:
                self.html='<div class="%s">%s</div>' % (cssClass, name)
            else:
                self.html=name
        else:   
            if self.cssClass:
                self.html="""<a class="%s" href="%s">%s</a>""" % (cssClass, link, name)
            else:
                self.html="""<a href="%s">%s</a>""" % (link, name) 
                
    def __str__(self):
        return self.html
  
class MenuItemSep(MenuItem):
    def __init__(self, name, link, depth=0, selected=False, cssClass='hMenuSep'):
        MenuItem.__init__(self, name, link, depth, selected, cssClass)
  
class HTMLDynChanTable(HTMLDynTable):
    """
    Currently the html table is created during the parsing. Would be nice to separate parsing from creating 
    the html. 
    
    Attributes:
    parsedDataList - Holds tuples of type (name, query). It stores all the queries that are contained in the 
    table.  This is used for daily plots. It's a bit of an overhead, and at one point need to seperate 
    the parsing of config data from creating the html table. This way daily plots generation would not 
    waste processing on creating tables.. 
    """
    def __init__(self, dataStr, useSubTables=False, itemsPerRow=1, secTitleCssClass='section', 
                script='/pages/common/plotterPage', autoTitle=True, queryStrPairs=None, title=None, tableAttrs=None,  
                **kwargs):
        """
        Arguments:
        useSubTables - Determines whether to have a seperate table for each section; allows for more freedom in terms
            of table dimensions.
        """
        self.parsedDataList=[]
        self._allColSpanIndex=[]  #Remember what rows the section (or non section) titles are. These need to span all columns
        
        #Remember the defaults.
        self._secTitleCssClass=secTitleCssClass
        self._itemsPerRow=itemsPerRow
        self._script=script
        self._queryStrPairs=queryStrPairs or {}
        self._useSubTables=useSubTables
        self._autoTitle=autoTitle    #Determines whether to create a titile plot  based on the section/chan name automatically.
        self._pageFile=dataStr       #Remember the page .channels filename, so per-section edit controls know which page they act on.

        # dataStr that comes in is actually the filename of the real data. Replace it with the file's contents.

        #General GEAHtml object init stuff.
        header=['<div align="left">']
        header+=['''    		 
	   	
        <div id="FixedTime"></div>

<script language="JavaScript">
// <!--    
function updateFixedTimeRange()
{
	var c=getCookie("fixedTimeRange");
	if (c!=null && c!='-1')
	{ 
		var da=timeRangeToDate(c);
		fixedMsg  = 'Plotting time range is FIXED at ' + dateToString(da[0]) + ' - ' + dateToString(da[1]);  				
                fixedMsg += '.&nbsp;<input type=\"button\" value=\"Remove\" onClick=\"setCookie(\\'fixedTimeRange\\', -1, \\'/\\');\">' 
		gebid('FixedTime').innerHTML=fixedMsg
	}
	else
	{
		gebid('FixedTime').innerHTML='';  				
	}
	
	setTimeout("updateFixedTimeRange()",2000);
}

updateFixedTimeRange();

// -->
</script>
                
        ''']
        
        footer=['</div>']
        
        kwargs['header']=kwargs.get('header', [])+header
        kwargs['footer']=footer+kwargs.get('footer', [])
    
        if tableAttrs is None:
            tableAttrs={'class':'dynChanTable'}
    
        HTMLDynTable.__init__(self, tableAttrs=tableAttrs, **kwargs)
        
        #Fill the table with sections.
        self._parseDataFile(dataStr)
        
        #Add the title
        if title is not None:
            self._table.add_row(-1)   #First row
            self._table.setCellColSpan(0,0, self._table.getmaxCol()+1) # Span cell at index row 1,col 0, make 2 high
            self._table.setCellcontents(0,0, title, {'class':'sectionMain'})
                         
    def _parseOption(self, line):
        """Returns True when an option has been parsed, False otherwise
        """
        parsed=False
    
        if line.startswith('#'):
            #Check whether to update the defauls
            if line.startswith('#[ITEMSPERROW]'):
                self._itemsPerRow=int(line[14:])
                parsed=True
            elif line.startswith('#[SCRIPT]'):
                self._script=line[9:].strip()
                parsed=True
            elif line.startswith('#[QUERYSTRPAIRS]'):
                self._queryStrPairs.update(eval(line[16:].strip()))
                parsed=True
            elif line.startswith('#[CSSCLASS]'):
                self._secTitleCssClass.update(eval(line[11:].strip()))
                parsed=True
            elif line.startswith('#[AUTOTITLE]'):
                autoTitle=self._validateAUTOTITLE(line[12:].strip())
                parsed=True
            elif line.startswith('#[SUBTABLE]'):
                self._useSubTables=self._validateSUBTABLE(line[11:].strip())
                parsed=True

        return parsed
            
    def _parseDataFile(self, dataStr):
        self._parseDataStr(open(GEAVars.path.fileSys.geaConf + "/pages/" + dataStr).read())

    def _parseDataStr(self, dataStr):
    
        #Check dataStr for some default settings. 
        #All the defaults should be set before the first '#SECTION' statement
        i=dataStr.find('#[SECTION]')
        if i>-1:
            for line in dataStr[:i].split('\n'):
                self._parseOption(line)
        else:
            i=0     #Start at the beginning.
        
        #Separate the string into SECTIONS, and parse each one by one.
        for section in dataStr[i:].strip().split('#[SECTION]'):
            if section:
                self._parseSectionStr(section) 
                
        #Have to deal with the tricky business of setting the column span of different tables.
        #This needs to be done *after* all the parsing has been done, so that we know the
        #max number of columns that the table has.
        if self._allColSpanIndex:
            colNumber=self._table.getmaxCol()+1
            #Want all rows indexed in self._allColSpanIndex to span over all the columns.
            for index in self._allColSpanIndex:
                self._table.setCellColSpan(index ,0,  colNumber)  #Set the span of the title 

    def _parseSectionStr(self, sectionStr):
        """Do all the parsing....
        
        NOTE: Should probably use REs.. bit of a mess
        NOTE: Some extra error checking and ability to escape characters should probably be included here...
        """
        #For speed so don't have to look this up each time.
        telSite=GEAVars.site
        
        #Start with these as defaults.
        secTitleCssClass=self._secTitleCssClass
        itemsPerRow=self._itemsPerRow
        script=self._script
        queryStrPairs=dict(self._queryStrPairs)
        useSubTables=self._useSubTables
        autoTitle=self._autoTitle
        
        htmlItemList=[]         #Each item here will be a cell in an html table.

        lines=sectionStr.split('\n')
        try:
            #The first line is the section info.
            line=lines[0]
            #First check if section should be shown at current site.
            for s in ('[MK]', '[CP]'):
                if line.find(s)>-1:
                    if s[1:3]!=GEAVars.site:
                        return      #Do not add this section.. 
                    line=line.replace(s,'')
            #Check if section should be treated as standard html.
            if line.find('[HTML]')>-1:
                #Dealing with an html section. Want to add the whole section as a row in the table and make sure its span 
                #is later adjusted to span over all the colums.
                del(lines[0])
                self._table.add_array_after_last_row([''.join(lines)])
                self._allColSpanIndex.append(self._table.getmaxRow())
                return 
            
            sectionName=line.strip()  #The first line is the name of the section. 
            del(lines[0])
        except IndexError:
            sectionName=''
        
        #Now go throgh all the data in this SECTION, and parse it. 
        #Usually a  line with channel data would look like (without starting hash):
        #<chanName1>     [OPTION]  [OPTION]    #  <Human redeable name (link)>
        for line in lines:
            if line.strip()=='':
                continue
            
            #Line that start with # can be comments, or options that are processed.
            if line.startswith('#'):
            
                #These options apply to the whole section - perhaps should only allow to define them at the 
                #beginning.
                #Check whether to update the defauls
                if line.startswith('#[ITEMSPERROW]'):
                    itemsPerRow=int(line[14:])
                elif line.startswith('#[SCRIPT]'):
                    script=line[9:].strip()
                elif line.startswith('#[CSSCLASS]'):
                    secTitleCssClass=line[11:].strip()
                elif line.startswith('#[SUBTABLE]'):
                    useSubTables=self._validateSUBTABLE(line[11:].strip(), useSubTables)
                    
                #These only apply to entries 'from now on' - ie. until the end of the current section.
                elif line.startswith('#[AUTOTITLE]'):
                    autoTitle=self._validateAUTOTITLE(line[12:].strip())
                elif line.startswith('#[QUERYSTRPAIRS]'):  
                    #QUERYSTRPAIRS is special in that the originals defined at the beginning of the section get
                    #updated not replaced.
                    queryStrPairs.update(eval(line[16:].strip()))
                    
                #These only apply to the contents of this given line. (cell)
                elif line.startswith('#[CELL]'):
                    #Just have a regular cell - no link.
                    htmlItemList.append(line[7:].strip())
                    
                #Now go to the next line.
                continue
            
            #From now all the options that are processed only apply to the current line (cell)
            goNext=False
            for s in ('[MK]', '[CP]'):
                if line.find(s)>-1:
                    if s[1:3]!=GEAVars.site:
                        goNext=True      #Do not add this line (cell) 
                        break
                    line=line.replace(s,'')
            if goNext:
                continue

            #Check if we need to add some formatting... 
            i=line.find('[FORMAT1]')
            if i> 0: 
                nameFormat='<div class="format1">%s</div>'
                line=line.replace('[FORMAT1]', "")
            else:
                nameFormat='%s'
                    
            #Check if dealing with a CHANNEL or a PATTERN
            chanOrPattern='PATTERN' #By default treat  as a PATTERN.
            i=line.find('[C]')
            if i>-1:
                line=line.replace('[C]', "")
                chanOrPattern='CHANNELS'
                        
            lineQuery={}
            #Look for some query string pairs that should only apply to this line (cell)
            #Might want to use re here.. also do some checking that don't have a # inside the pairs dict {....}... 
            beg, end=line.find('{'), line.find('}')
            if  -1<beg<end:
                lineQuery.update(eval(line[beg:end+1]))
                line=line[:beg]+line[end+1:]
            
            #Now look for human readable name:
            i=line.find('#')  
            if i> 0:
                #Have a name 
                try:
                    value=line[0:i]                        
                    name=line[i:].lstrip('#')
                except IndexError:
                    value=name=line
            else:
                value=name=line.strip()
                
            #Setup the query.
            query=dict(queryStrPairs)
            query.update({chanOrPattern:value.strip()})
            #Finally update with the values local to the cell (line)
            query.update(lineQuery)
                            
            #If have no titile, then use name.
            if autoTitle:
                query['PLOTTITLE']=query.get('PLOTTITLE', '')
                if query['PLOTTITLE']=='':
                    if sectionName:
                        query['PLOTTITLE']= '%s: %s' % (sectionName, name)
                    else:
                        query['PLOTTITLE']= name
                
            htmlItemList.append(self._createCellsHtml(name=nameFormat % name, chanOrPat=value.strip(), script=script, **query))
                
            #This parsed data can be used by other tools (ex. daily plotting).
            self.parsedDataList.append(util.Holder(queryStrPairs=query, humanName=name, chanOrPat=value.strip()))
        
        #Add the section titile, and make sure it spans all columns.
        #Append a small per-section "edit" control so a user can add/delete
        #channels in exactly this section straight from the page.
        titleHtml=sectionName
        if sectionName:
            editUrl='%s/pages/common/editChannelsPage?PAGE=%s&SECTION=%s' % (
                GEAVars.dispatchScript,
                urllib.quote(self._pageFile),
                urllib.quote(sectionName))
            titleHtml=('%s &nbsp;<a class="editchan" href="#" '
                       'onclick="window.open(\'%s\',\'editchan\','
                       '\'width=900,height=600,scrollbars=yes,resizable=yes,'
                       'location=no,toolbar=no,menubar=no,status=no\');'
                       'return false;" '
                       'title="Add or remove channels in this section">[edit]</a>'
                       % (sectionName, editUrl))
        self._table.add_array_after_last_row([titleHtml], {'class':secTitleCssClass})
        self._allColSpanIndex.append(self._table.getmaxRow())
            
        #Create an HTML table with the all the items. 
        if useSubTables:
            sectionTable=HTMLDynTable(tableAttrs={'class':'dynChanSubTable'})
        else:
            sectionTable=self._table  #Add rows to the main table.
            #Remember where the section title is, so that later can set its colum span properly
            self._allColSpanIndex.append(self._table.getmaxRow())

        imNum=len(htmlItemList)
            
        first=0
        last=itemsPerRow
        
        while 1:            
            sectionTable.add_array_after_last_row(htmlItemList[first:last])            
            
            if last>imNum:
                break
            
            first=last
            last+=itemsPerRow

        if useSubTables:
            #Now need to append the new table to the main one
            self._table.add_array_after_last_row([sectionTable])
            self._allColSpanIndex.append(self._table.getmaxRow())

    def _validateSUBTABLE(self, text, onError=None):
        if text=='True' or text=='true' or text=='1':
            return True
        if text=='False' or text=='false' or text=='0':
            return False
        if onError is None:
            return self._useSubTables
        return onError
                
    def _validateAUTOTITLE(self, text, onError=None):
        if text=='True' or text=='true' or text=='1':
            return True
        if text=='False' or text=='false' or text=='0':
            return False
        if onError is None:
            return self._autoTitle
        return onError
                      
    def _createCellsHtml(self, name, chanOrPat, script, **query):
        return HtmlHelper.createLink(name, script, **query)
        
class HTMLDynChanTableWithPlots(HTMLDynChanTable):
    """
    Each cell should have a plot, and a link.
    
    Currently the html table is created during the parsing. Would be nice to separate parsing from creating 
    the html. 
    """
    def __init__(self, dataStr, useSubTables=False, itemsPerRow=1, secTitleCssClass='section', 
                script='/pages/common/plotterPage', autoTitle=True, queryStrPairs=None, title=None, tableAttrs=None,  
                dataDir=None,    #Path to where the data should be.
                **kwargs):
                
        self._dataDir=dataDir or GEAVars.path.web.wwwData
        HTMLDynChanTable.__init__(self, dataStr, useSubTables, itemsPerRow, secTitleCssClass, 
                                  script, queryStrPairs, title, tableAttrs,  **kwargs)
    
    def _createCellsHtml(self, name, chanOrPat, script, **query):
    
        imageName=os.path.join(self._dataDir, naming.genDailyName(chanOrPat, prefix=naming.imPrefix))
        dataName=os.path.join(self._dataDir, naming.genDailyName(chanOrPat, prefix=naming.dataPrefix))

        return """
<table cellpadding="0" cellspacing="0">
    <tr>
        <td colspan="2" align="center" >
            %s
        </td>
    </tr>
    <tr>
        <td colspan="2" align="center" >
            <a href="%s"><img src="%s" alt="Plot not available"></a>
        </td>
    </tr>
    <tr>
        <td align="center">
            %s
        </td>
        <td align="center">
            <a href="%s">[Data]</a>
        <td>
    </tr>
</table>""" % (name,
               imageName+'.Large.png',
               imageName+'.Small.png',
               HtmlHelper.createLink('[Re-plot]', script, **query),
               dataName)
   
def main():

    welcome="""<h2 align=center>GEAHtml.py</h2>
<p>
This page shows the different types of available html components.
<p>
<p>
"""
    #Temporary...
    #print """Content-Type:   text/html\n\n"""
  
    doc=HTMLDocCont()
    doc.vars.update(pageheading='', pagetitle='GEAHtml.py contents')

    sep=HTMLSep()
    
    doc.append(welcome)
    doc.append(sep)
    
    #Form types
    items=[#HTMLDocContWithSideMenu1(),
            HTMLErrorPage(), 
            HTMLDocCont(), 
            HTMLFormCont(),
            #HTMLHorizontalMenu(),
            HTMLTimeSelector(),           
            #HTMLTimeSelectorFRS(),
            HTMLTimeSelectorNL(),       
            HTMLTimeSelectorOverloads(),        
            HTMLTimeSelectorDiq(),
            HTMLOptionsPlot(),
            #HTMLOptionsFRS(),
            #HTMLOptionsNL(),
            HTMLOptionsOverloads(),
            HTMLOptionsDiq(),
            HTMLOptionsSurfacePlot(),
            HTMLDynChanSelector(),
            HTMLDynImageTable(['dumm1','dummy2'], 2),
            HTMLPlot(),
            HTMLImage(),
            HTMLNotice(),
            HTMLTextBox(),

          ]
    
    for item in items:
        doc.append(item)
        doc.append("<h4>Default properties:</h4>")
        doc.append("<pre>"+item.dataStr()+"</pre>")
        doc.append(sep)
        
    print doc
    
def main2():

    dList=HTMLDynChanSelector().dataList
    dList.sort()
    
    for item in dList:
        print '\n\n', str(item)
    
    
if __name__=='__main__':

    main()

