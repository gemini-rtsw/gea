#!/bin/python

from __future__ import generators

from GEAHtml import HTMLObject
import GEAVars

class HTMLDynChanSelector2(HTMLObject):
    """Dynamically creates a selection hierarchy, starting with a system through categories, 
    down to channels.
    
    TODO... REWRITE THIS SO *IT IS* DYNAMIC... want to get info from a config file.
    
    """
    def __init__(self, dataTree, **kwargs):
    
    
        data=[
        N('gws',
        [
            N("pressure", 
            [
                N('b1', None), N('b2', None), N('b3', None)
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
    
    
        #self.dataTree=dataTree
        self.dataTree=data
        
        body="""
<div align="center">
<table>
<tr>  
    <td  align="center" class="widgetChanSelLabel"><strong>System Selection</strong></strong></td>
    <td align="center" class="widgetChanSelLabel"><strong>Category Selection</strong></td>
       
</tr>
<tr>
    <td VALGN="top">
    <select NAME="%(SYSSELECTION)s" MULTIPLE size="5">
    
"""+self._getSystemOptionsHTML()+"""

    </select>
    </td>
    <td VALIGN="top">
    <select NAME="%(CAT1SELECTION)s" MULTIPLE size="5">
    </select>
    </td>
</tr>

<!--
<tr>
    <td COLSPAN="3" ALIGN="center">
    <input type="button" value="Reset This Form" onClick="this.form.reset(); resetDynamicOptionLists(this.form);">
    </td>
</tr>
-->
  <tr> 
    <td colspan="2"><table width="100%" height="100%" align="center">
                 <tr>
                     <td width="13%" align="center" class="widgetChanSelLabel"><strong>Channel Selection</strong></strong></td>
                     <td width="13%" align="center"><strong>&nbsp;</strong></td>
                     <td width="13%" align="center" class="widgetChanSelLabel"><strong> CHANNELS TO PLOT</strong></td>
                 </tr>
                 
                   <td width="28%">
                        <select width="25" NAME="%(SELECTION)s" MULTIPLE size="8">
                        </select>
                    
                    </td>
                   <td width="20%"><table width="70%" height="100%" align="center" cellpadding="1">
                        <tr>
                         <td align="center" valign="middle"><input name="button1" type=button onClick="copySelectedOptions(document.forms[0]['%(SELECTION)s'],document.forms[0]['%(CHANNELS)s'],false);selectAllOptions(document.forms[0]['%(CHANNELS)s']); updateSystems%(JS)s(document.forms[0]['%(SELECTION)s']);return false;" value=">> (Add Highlighted)"></td>
                       </tr>
                        <tr>
                         <td align="center" valign="middle"><input name="button2" type=button  onClick="copyAllOptions(document.forms[0]['%(SELECTION)s'],document.forms[0]['%(CHANNELS)s'],false);selectAllOptions(document.forms[0]['%(CHANNELS)s']);return false;" value="&gt;&gt (Add All)"></td>
                       </tr>
                       <tr>
                         <td align="center" valign="middle"><input name="button3" type=button  onClick="removeSelectedOptions(document.forms[0]['%(CHANNELS)s']);return false;" value="Clear Highlighted"></td>
                       </tr>
                       <tr>
                         <td align="center" valign="middle"> <input name="button4" type=button  onClick="removeAllOptions(document.forms[0]['%(CHANNELS)s']);return false;" value="Clear All"></td>
                       </tr>
                      <tr>
                         <td align="center" valign="middle"> <input name="button5" type=button  onClick="selectAllOptions(document.forms[0]['%(CHANNELS)s']);return false;" value="Highlight All"></td>
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
  <tr>
      <td colspan="2"><strong>Currently 'Systems' need to be added manually.</strong>
          
      </td>
  </tr>
  <tr> 
    <td><table  width="100%">
        <tr> 
          <td width="13%" align="center" class="widgetChanSelLabel"><strong>Systems:</strong></td>
          <td width="87%"><input type=text name="%(SYSTEMS)s" size=40 maxlength=100 value="%(systems)s"></td>
        </tr>
      </table></td>
    <td><table  width="100%">
        <tr> 
          <td width="13%" align="center" class="widgetChanSelLabel"><strong>Pattern:</strong></td>
          <td width="87%"><input type=text name="%(PATTERN)s" size=40 maxlength=256 value="%(pattern)s"></td>
        </tr>
      </table></td>
  </tr>

</table>
</div>

<script language="JavaScript">
////////////
//Widged-specific functions/variables - marked with %(JS)s appened:
///////////
//Keep track of what systems each channel belongs. Entries of the form {channel:system}
//Start with niri:
systemsArray%(JS)s=createSystemsArray("niri:dc:footRef niri:dc:footLGain niri:dc:mntLGain", "niri");
//Add gws:
//var tempArray=createSystemsArray("ws:cfTemp ws:cfPress ws:cfHumid ws:cfWindSpeed", "gws");
//systemsArray%(JS)s.concat(tempArray);

//var a=createSystemsArray("ws:cfTemp ws:cfPress ws:cfHumid ws:cfWindSpeed", "gws");
//var tempArray=systemsArray%(JS)s.concat(a);
//systemsArray=tempArray;
//var systemsArray%(JS)s=createSystemsArray("ws:cfTemp ws:cfPress ws:cfHumid ws:cfWindSpeed", "gws");

//Start with niri:
//var niriArray=createSystemsArray("niri:dc:footRef niri:dc:footLGain niri:dc:mntLGain", "niri");
//and gws:
//var gwsArray=createSystemsArray("ws:cfTemp ws:cfPress ws:cfHumid ws:cfWindSpeed", "gws");

//Add the two
//systemsArray%(JS)s=niriArray.concat(gwsArray);

//TESTING
//document.forms[0]["%(SYSTEMS)s"].value=systemsArray%(JS)s.join("--");

//systemsArray%(JS)s=systemsArray%(JS)s.concat(createSystemsArray("ws:cfTemp ws:cfPress ws:cfHumid ws:cfWindSpeed", "gws"));

//for (var i=0; i<systemsArray%(JS)s.length; i++) 
//{
//    document.write("<br>" + systemsArray%(JS)s[i]);
//}

//Updates the value of the SYSTEMS input to make sure it contains the actual system that selections in 
//selectionObj belong to.
function updateSystems%(JS)s(selectionObj)
{
    for (var i=0; i<selectionObj.options.length; i++)
    {
        updateSystemsValue(document.forms[0]['%(SYSTEMS)s'], systemsArray%(JS)s[selectionObj.options[i].text]);
    }
}

/////////////////
// Selection boxes setup
///////////////////
var makeModel = new DynamicOptionList("%(SYSSELECTION)s","%(CAT1SELECTION)s","%(SELECTION)s");

//makeModel.forText("%(SYSSELECTION)s").setText("niri", "gws");
//makeModel.forF("%(SYSSELECTION)s").setText("niri", "gws");

//Setup niri.
makeModel.forText("niri").addOptions("CC Temps", "DC Temps");
makeModel.forText("niri").forText("DC Temps").addOptions("niri:dc:footRef", "niri:dc:footLGain", "niri:dc:mntLGain");
makeModel.forText("niri").forText("CC Temps").addOptions("niri:eng:tmpS1Tmp1", "niri:eng:tmpS1Tmp2", "niri:eng:tmpC2Tmp", "niri:cc:tmpS1Tmp4");

//Setup gws.
makeModel.forText("gws").addOptions("Temp", "Pressure", "Pressure", "Wind Speed" );
makeModel.forText("gws").forText("Temp").addOptions("ws:cfTemp");
makeModel.forText("gws").forText("Pressure").addOptions("ws:cfPress");
makeModel.forText("gws").forText("Humidity").addOptions("ws:cfHumid");
makeModel.forText("gws").forText("Wind Speed").addOptions("ws:cfWindSpeed");

"""+self._getInitJS()+"""

initDynamicOptionLists();

/////////////
//Other inits
///////////
// Remember the chennels selection from call to call.
addTextOptions(document.forms[0]['%(CHANNELS)s'], "%(channels)s");
selectAllOptions(document.forms[0]['%(CHANNELS)s']);

</script>

"""
        vars={'systems':'[systems]',
              'pattern':'[pattern]',
              'channels':'[channels]',
            
              'sysselection':'[sysselection]',
              'cat1selection':'[cat1selection]',
              }
        
        taggedVars={'SYSTEMS':'SYSTEMS',
                    'PATTERN':'PATTERN',
                    'CHANNELS':'CHANNELS',   
                    'SELECTION':'SELECTION',
                    
                    'SYSSELECTION':'SYSSELECTION',
                    'CAT1SELECTION':'CAT1SELECTION',
                    
                    'JS':'JS',
                    }
    
    
        HTMLObject.__init__(self, taggedVars=taggedVars, vars=vars, body=[body])
              
        #Now update the defaults from the variables passed at run time.
        if kwargs:
            for key, value in kwargs.iteritems():
                self.__setattr__(key, value)

                
    def _getSystemOptionsHTML(self):
        """
        Returns a line a string containing lines with <option>system</optoin> 
        for each system in self.dataTree
        """
        return '\n'.join(map(lambda x: '<option>%s</option>' % x.name, self.dataTree))
        
    def _getInitJS(self):
        """
        Returns the javascript needed to initialize data from self.dataTree.
        """
        strList=[]
        for system in self.dataTree:
            strList.append("//Setup '%s'" % system.name)
         
            categoryNames=system.getNames()
            strList.append('makeModel.forText("%s").addOptions("%s");' % (system.name, '", "'.join(categoryNames)))
            
            #Go throught the categories and add channel names.
            for category in system.getTrees():
                
                chanNames=category.getNames()
                      
                strList.append('makeModel.forText("%s").forText("%s").addOptions("%s");' % (system.name, category.name, '", "'.join(chanNames)))
            
        return '\n'.join(strList)
                
    class N(object):
        """Node.
        """
        def __init__(self, name, tree):
            self.name=name
            self.tree=tree
            
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
            
        def __str__(self):
            return 'Name:%s\n%s\n' % (self.name, str(self.tree))

    def _parseDataStr(dataStr):
        """Returns a 'tree' representation of dataStr. 
        """
        sysDict={}
        
        lines=dataStr.split('\n')
        lines.reverse()
         
        while 1:
        
            line=lines.pop()
            
            if line.startswith('#SYSTEM'):
                system=line[7:].strip()
    
            elif line.startswith('#CATEGORY'):
                category=line[9:].strip()
        
        #Skip blank lines and lines that start with '#'
        for line in lines:
        
            if line.startswith('#') or line=='' or line.startswith(' '):
                continue
            
            i=line.find('#')
            
            if i> -1:
                    #Have a name provided.
                try:
                    chan=line[0:i].strip()
                    name=line[i:].lstrip('#')
                except IndexError:
                    chan=name=line
            else:
                chan=name=line
            
            itemList.append((chan, name))
            
        return itemList
            
        
        
        
def main():

    N=HTMLDynChanSelector2.N

    data=[
        N('gws',
        [
            N("pressure", 
            [
                N('b1', None), N('b2', None), N('b3', None)
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


    print HTMLDynChanSelector2(dataTree=data)
        
if __name__=='__main__':
    
    main()
    
