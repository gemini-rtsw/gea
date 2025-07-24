// NEED TO CLEAN THIS FILE UP.... 
// at the bottom attached an external library.. 

/////////////////////////////
// General
/////////////////////////////

function gfo(s) { return document.forms[0][s];}
function gebid(s) { return document.getElementById(s);}

function gebc(searchClass,node,tag) {
	var classElements = new Array();
	if ( node == null )
		node = document;
	if ( tag == null )
		tag = '*';
	var els = node.getElementsByTagName(tag);
	var elsLen = els.length;
	var pattern = new RegExp('(^|\\s)'+searchClass+'(\\s|$)');
	for (i = 0, j = 0; i < elsLen; i++) {
		if ( pattern.test(els[i].className) ) {
			classElements[j] = els[i];
			j++;
		}
	}
	return classElements;
}

function addLoadEvent(func) {
	var oldonload = window.onload;
	if (typeof window.onload != 'function') {
		window.onload = func;
	}
	else {
		window.onload = function() {
			oldonload();
			func();
		}
	}
}


/////////////////////////////
// Time Selection tools.
/////////////////////////////
var global_month2Num={"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}; 
var global_num2Month={1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"};

var global_minPerHour=60;
var global_minPerDay=1440;
var global_minPerWeek=10080;

// Helper...
// date is a Date() instance.
function adjustDate(date, offset)
{    
    // Need to pass a value in milliseconds... offset is in minutes. 
    date.setTime(date.getTime()+(offset*60000.0));       // 60sec/min*1000millisec/sec=60000millisec/min
    return date
}

function timeRangeToDate(s)
{
	//Expect <num>-<num>
	var strArray=s.split('-');  
	return new Array(new Date(parseFloat(strArray[0])*1000), new Date(parseFloat(strArray[1])*1000));
}

function dateToString(d)
{
	//Want a different format than what the default toString gives.
    return global_num2Month[d.getMonth()+1] + " " +  d.getDate() + ", " + d.getFullYear() + " " +
                                    d.getHours() + ":" +  d.getMinutes() + ":" + d.getSeconds(); 

}

// TimeSelector class.
function TimeSelector(y, m, d, h, min, s)
{
    // Each _<x> variable is either a selection object or one that has a 'value' field (ex. <input type=hidden> tag type object)
    this.y=y;
    this.m=m;
    this.d=d;
    this.h=h;
    this.min=min;
    this.s=s;
    
	// Method mappings
	this.updateFromVars = TimeSelector_updateFromVars;
    this.updateFromDate = TimeSelector_updateFromDate;
    this.add = TimeSelector_add;
    this.sub = TimeSelector_sub;
    this.now = TimeSelector_now;  
	this.toString=TimeSelector_toString;
    this.fromString=TimeSelector_fromString;
	
    // If all _<x> are selectors can optimize a little...
    if (this.s.options && this.min.options && this.h.options && this.d.options && this.m.options && this.y.options)
    {
        this.toDate=TimeSelector_toDateAllSelectors;
    }
    else
    {
        this.toDate=TimeSelector_toDateGeneral;
    }
    
    // Meant to be "private".
    this._operation = TimeSelector_operation;
    
}


function TimeSelector_toString()
{
	var d=this.toDate();
    return global_num2Month[d.getMonth()+1] + " " +  d.getDate() + ", " + d.getFullYear() + " " +
                                    d.getHours() + ":" +  d.getMinutes() + ":" + d.getSeconds(); 

}

function TimeSelector_fromString(s)
{
	if (s==null)
	{
		return;
	}						
	this.updateFromDate(new Date(s));									

}

function TimeSelector_toDateAllSelectors()
{
    var a=new Array(this.m.options[this.m.options.selectedIndex].text," ",
                    this.d.options[this.d.options.selectedIndex].text,", ",
                    this.y.options[this.y.options.selectedIndex].text, " " , 
                    this.h.options[this.h.options.selectedIndex].text,":",
                    this.min.options[this.min.options.selectedIndex].text, ":" ,
                    this.s.options[this.s.options.selectedIndex].text);
    
    return new Date(a.join(''));
}

function TimeSelector_toDateGeneral()
{
    s=new Array();
    
    (this.m.options)? s.push(this.m.options[this.m.options.selectedIndex].text): s.push(this.m.value);
    s.push(" ");
    (this.d.options)? s.push(this.d.options[this.d.options.selectedIndex].text): s.push(this.d.value);
    s.push(", ");
    (this.y.options)? s.push(this.y.options[this.y.options.selectedIndex].text): y.push(this.y.value);
    s.push(" ");
    (this.h.options)? s.push(this.h.options[this.h.options.selectedIndex].text): s.push(this.h.value);
    s.push(":");
    (this.min.options)? s.push(this.min.options[this.min.options.selectedIndex].text): s.push(this.min.value);
    s.push(":");
    (this.s.options)? s.push(this.s.options[this.s.options.selectedIndex].text): s.push(this.s.value);
    
    return new Date(s.join(''));
    
}

function TimeSelector_updateFromDate(d)
{
    this.updateFromVars(d.getFullYear(), global_num2Month[d.getMonth()+1], d.getDate(),  
                                    d.getHours(), d.getMinutes(), d.getSeconds());      
}

function TimeSelector_updateFromVars(y, m, d, h, min, s)
{
    selectSingleOptByText(this.s, s);
    selectSingleOptByText(this.min, min);
    selectSingleOptByText(this.h,h);
    selectSingleOptByText(this.d,d);
    selectSingleOptByText(this.m,m);
    selectSingleOptByText(this.y,y);
		
}

function TimeSelector_now()
{
    this.updateFromDate(new Date());
}

// offset should be time in minutes.
function TimeSelector_add(offset)
{
    this._operation(offset, 1);
}

function TimeSelector_sub(offset)
{
    this._operation(offset, -1);
}

function TimeSelector_operation(offset, sign)
{    
    var d=this.toDate();
    // Need to pass a value in milliseconds... offset is in minutes. 
    d.setTime(d.getTime()+sign*(offset*60000.0));       // 60sec/min*1000millisec/sec=60000millisec/min
    this.updateFromDate(d);
}

// Wrapper so that can have both start and end time selectors in one object. 
// This object is used very actively by QuickSelectors, which have to modify both 
// start and the end time.
function StartEndTimeSelector(start, end)
{
    this.start=start;
    this.end=end;
    
    // Method mappings.
    this.updateFromDate=StartEndTimeSelector_updateFromDate;
	this.toString=StartEndTimeSelector_toString;
	this.fromString=StartEndTimeSelector_fromString;
}

function StartEndTimeSelector_toString()
{
	return this.start.toString() + " - " + this.end.toString();
}

function StartEndTimeSelector_fromString(s)
{
	if (s==null)
	{
		return;
	}
	// Expect a fromat such as:
	// Mar 5 2006 11:30:39 - Mar 5 2006 14:30:39
	var strArray=s.split(' - ');    	
	
	this.start.fromString(strArray[0]);
	this.end.fromString(strArray[1]);	
}


function StartEndTimeSelector_updateFromDate(sDate, eDate)
{
    this.start.updateFromDate(sDate);
    this.end.updateFromDate(eDate);
}

/////////////////////////////
//Cookie Handling
/////////////////////////////

//function getCookie(c_name)
//{
//    if (document.cookie.length>0)
//	{
//		c_start=document.cookie.indexOf(c_name + "=");
//		if (c_start!=-1)
//        { 
//        	c_start=c_start + c_name.length+1;
//        	c_end=document.cookie.indexOf(";",c_start);
//        	if (c_end==-1) 
//			{
//				c_end=document.cookie.length;
//			}		
//        	return unescape(document.cookie.substring(c_start,c_end));
//        } 
//      }
//    return null;
//}
//
//
//function setCookie(c_name,value,exdate, path)
//{
//	// path=(path==null)? "": "path="+path+"
//	document.cookie=c_name+ "=" +escape(value)+ ((exdate==null) ? "" : "; expires="+exdate.toGMTString());
//}


function getCookie( name ) {
	var start = document.cookie.indexOf( name + "=" );
	var len = start + name.length + 1;
	if ( ( !start ) && ( name != document.cookie.substring( 0, name.length ) ) ) {
		return null;
	}
	if ( start == -1 ) return null;
	var end = document.cookie.indexOf( ';', len );
	if ( end == -1 ) end = document.cookie.length;
	return unescape( document.cookie.substring( len, end ) );
}

function setCookie(name, value, path, expires)
{
	document.cookie = name+'='+escape( value ) +
		((expires)? ';expires='+expires.toGMTString() : '' ) + 
		((path)? ';path=' + path : '' );
}

function setCookieOLD( name, value, expires, path, domain, secure ) {
	var today = new Date();
	today.setTime( today.getTime() );
	if ( expires ) {
		expires = expires * 1000 * 60 * 60 * 24;
	}
	var expires_date = new Date( today.getTime() + (expires) );
	document.cookie = name+'='+escape( value ) +
		( ( expires ) ? ';expires='+expires_date.toGMTString() : '' ) + //expires.toGMTString()
		( ( path ) ? ';path=' + path : '' ) +
		( ( domain ) ? ';domain=' + domain : '' ) +
		( ( secure ) ? ';secure' : '' );
}

function deleteCookie( name, path, domain ) {
	if ( getCookie( name ) ) document.cookie = name + '=' +
			( ( path ) ? ';path=' + path : '') +
			( ( domain ) ? ';domain=' + domain : '' ) +
			';expires=Thu, 01-Jan-1970 00:00:01 GMT';
}


/////////////////////////////
// String manipulation
/////////////////////////////

function stripStr(s) {

  s=s.replace(/^\s+/g,""); // strip leading whitespace 
  return s.replace(/\s+$/g,""); // strip trailing whitespace
}


/////////////////////////////
//Element showing/hiding
/////////////////////////////
function hideEl(id)
{
    if (!browser.isNS4x)
    {
        document.getElementById(id).style.display='none';
    }
}
function showEl(id)
{
    if (!browser.isNS4x)
    {
        document.getElementById(id).style.display='inline';
    }
}
/////////////////////////////
//Coppying options between selection boxes
/////////////////////////////
function getSelectedText(obj)
{
	if (obj.options.selectedIndex>-1)
	{
		return obj.options[obj.options.selectedIndex].text;
	}
	return null;
	
}

function selectAllOptions(obj) {
  for (var i=0; i<obj.options.length; i++) {
      obj.options[i].selected = true;
      }
  }
function removeSelectedOptions(from) {
  for (var i=(from.options.length-1); i>=0; i--) {
      var o=from.options[i];
      if (o.selected) {
          from.options[i] = null;
          }
      }
  from.selectedIndex = -1;
  }

function removeAllOptions(from) {
  for (var i=(from.options.length-1); i>=0; i--) {
      from.options[i] = null;
      }
  from.selectedIndex = -1;
  }
  
function selectionToString(obj, sep) 
{
	var sep = (sep == null) ? ";" : sep;
	
	var s="";
  	for (var i=0; i<(obj.options.length); i++) 
	{
		s+=obj.options[i].text + ((i<(obj.options.length-1))? sep: "");		
    }	
	return s;
}	
		
function sortSelect(obj) 
{
	var o = new Array();

	if (obj.options==null) { return; }
	for (var i=0; i<obj.options.length; i++) 
	{
		o[o.length] = new Option( obj.options[i].text, obj.options[i].value, obj.options[i].defaultSelected, obj.options[i].selected) ;
	}
	
	if (o.length==0) { return; }
	
	o = o.sort(
		function(a,b) 
		{
			al=a.text.toLowerCase();
			bl=b.text.toLowerCase();
			if (al < bl) { return -1;}
			if (al > bl) { return 1; }
			return 0;
		}
		);

	for (var i=0; i<o.length; i++) 
	{
		obj.options[i] = new Option(o[i].text, o[i].value, o[i].defaultSelected, o[i].selected);
	}
}

	
// NEED TO CHECK IF THIS WORKS IN IE.
function sortSelectOLD(obj) {
  var o = new Array();
  if (obj.options==null) { return; }
  for (var i=0; i<obj.options.length; i++) {
      o[o.length] = new Option( obj.options[i].text, obj.options[i].value, obj.options[i].defaultSelected, obj.options[i].selected) ;
      }
  if (o.length==0) { return; }
  o = o.sort(
      function(a,b) {

          if ((a.text+"") < (b.text+"")) { return -1; }
          if ((a.text+"") > (b.text+"")) { return 1; }
          return 0;
          }
      );

for (var i=0; i<o.length; i++) {
      obj.options[i] = new Option(o[i].text, o[i].value, o[i].defaultSelected, o[i].selected);
      }
  }
// OLD.. doent work in IE when have no values. 
function copySelectedOptionsOLD(from,to) {
  var options = new Object();
  for (var i=0; i<to.options.length; i++) {
      options[to.options[i].value] = to.options[i].text;
      }
  for (var i=0; i<from.options.length; i++) {
      var o = from.options[i];
      if (o.selected) {
          if (options[o.value] == null || options[o.value] == "undefined" || options[o.value]!=o.text) {
              to.options[to.options.length] = new Option( o.text, o.value, false, false);
              }
          }
      }
  if ((arguments.length<3) || (arguments[2]==true)) 
    {
      sortSelect(to);
    }
  from.selectedIndex = -1;
  to.selectedIndex = -1;
  }

// Only worry about the text and not value. 
function copySelectedOptions(from,to) 
{
    var options = new Object();
    for (var i=0; i<to.options.length; i++) 
    {
        options[to.options[i].text] = to.options[i].text;
    }
    for (var i=0; i<from.options.length; i++) 
    {
        var o = from.options[i];
        if (o.selected) 
        {
            if (options[o.text] == null || options[o.text] == "undefined" || options[o.text]!=o.text) 
            {
                var newOp=new Option();
                newOp.text=o.text;
                newOp.value=o.value;
                to.options[to.options.length] = newOp;
            }
        }
    }
    if ((arguments.length<3) || (arguments[2]==true)) 
    {
        sortSelect(to);
    }
    from.selectedIndex = -1;
    to.selectedIndex = -1;
}


function copyAllOptions(from,to) {
  selectAllOptions(from);
  if (arguments.length==2) {
      copySelectedOptions(from,to);
      }
  else if (arguments.length==3) {
      copySelectedOptions(from,to,arguments[2]);
      }
  }

function selectSingleOptByText(obj, txt)
{
    if ((obj==null) || (obj=="None") || (obj=="undefined"))
    {
        return 
    }

    // Do a check if dealing with a <select> tag object - if not assume the object has a value property and try setting it to txt.
    if (!obj.options)
    {
        obj.value=txt;
        return;
    }
    
    // If made it here, we must be dealing with a <select> tag object. 
    var def=obj.options.selectedIndex;
    var found=false;
    
    for (var i=0; i<obj.options.length; i++) 
    {
        if (obj.options[i].text==txt)
        {
            obj.options[i].selected=true;
            found=true;
        }
        else
        {
            obj.options[i].selected=false;
        }
    }
    
    // Make sure we go to the default if didn't find a match.
    if (!found)
    {
        obj.options[def].selected=true;
    }
}

function isTextInOptions(txt, obj)
{
    for (var i=0; i<obj.options.length; i++) 
    {
        if (obj.options[i].text==txt)
        {
			return true;
        }
    }
	return false;
}

// Adding to 'obj'.  Options are in the string 'strList' seperated by sep
function addTextOptions(obj, str, sep)
{
	//Lets have emtpy space be a default seperator.
  	var sep = (sep == null) ? /\s+/ : sep;

    if (str=='')
        return;

    var strArray=str.split(sep);    
	
    for (var i=0; i<strArray.length; i++) 
    {
        var o=new Option();
        o.text=strArray[i];
        obj.options[obj.options.length]=o; 
    }
}


function selectSingleOptByValue(obj, val)
{
    var def=obj.options.selectedIndex;
    var found=false;
    
    for (var i=0; i<obj.options.length; i++) 
    {
        if (obj.options[i].value==val)
        {
            obj.options[i].selected=true;
            found=true;
        }
        else
        {
            obj.options[i].selected=false;
        }
    }
    
    // Make sure we go to the default if didn't find a match.
    if (!found)
    {
        obj.options[def].selected=true;
    }
}
  
function clearValue(element){ element.value="";}

///////////
//Other... utility functions
//////////
function popupPage(url, txt) 
{
	day = new Date();
	id = day.getTime();
	eval("page" + id + " = window.open(url+'?'+txt, '" + id + "', 'toolbar=0,scrollbars=1,location=0, \
             statusbar=1,menubar=0,resizable=1,width=200,height=200');");
}

/////////////////////////
//Radio button control
//////////////////////
function getSelectedRadio(group) {
   for(i = 0; i < group.length; i++) {
      if (group[i].checked) {
         return i;
      }
   }
   return -1;
}

function clearButtons(group)
{
	for (i=0; i < group.length; i++) 
	{

		if (group[i].checked == true) 
		{
	    		group[i].checked = false;
    		}
   	}
}

function setButtonWithValue(group, val)
{
	for (i=0; i < group.length; i++) 
	{
		if (group[i].value == val) 
		{
	    		group[i].checked = true;
    		}
   	}
}

///////////////////////
//Time setting helpers.
//////////////////////////
function setStartTimeOptions(startSecond, startSecondSelection,  startMinute, startMinuteSelection, startHour, 
		 startHourSelection, startDay, startDaySelection,  startMonth, startMonthSelection,  
		startYear, startYearSelection)
{
selectSingleOptByText(startSecondSelection, startSecond);
selectSingleOptByText(startMinuteSelection, startMinute);
selectSingleOptByText(startHourSelection, startHour);
selectSingleOptByText(startDaySelection, startDay);
selectSingleOptByText(startMonthSelection, startMonth);
selectSingleOptByText(startYearSelection, startYear);

}

function setEndTimeOptions(endSecond, endSecondSelection,  endMinute, endMinuteSelection, endHour, 
		 endHourSelection, endDay, endDaySelection,  endMonth, endMonthSelection,  
		endYear, endYearSelection)
{
selectSingleOptByText(endSecondSelection, endSecond);
selectSingleOptByText(endMinuteSelection, endMinute);
selectSingleOptByText(endHourSelection, endHour);
selectSingleOptByText(endDaySelection, endDay);
selectSingleOptByText(endMonthSelection, endMonth);
selectSingleOptByText(endYearSelection, endYear);

}

function updateTimeFromQuickSelector2(quickLapseValue, startTimeArray, endTimeArray)
{
    var endTime = new Date();                // Get current time.

    //Special case, want the start date to be Jan 1, 2002
    if (quickLapseValue=="-1")
    {
        var startTime = new Date(2002, 0, 1,0,0,0);
    }
    else
    {
        // quickLapseValue in minutes, but want milliseconds
        var startTime = new Date(endTime.getTime()-quickLapseValue*60.0*1000.0); 
    }

    //TESTING
    //document.forms[0]['%(XLABEL)s'].value=startTime.toLocaleString();
    //document.forms[0]['%(YLABEL)s'].value=endTime.toLocaleString(); 
    
    setStartTimeOptions(startTime.getSeconds(), startTimeArray[0], 
                    startTime.getMinutes(), startTimeArray[1], 
                    startTime.getHours(), startTimeArray[2], 
                    startTime.getDate(), startTimeArray[3], 
                    startTime.getMonth()+1, startTimeArray[4], 
                    startTime.getFullYear(), startTimeArray[5]);

    setEndTimeOptions(endTime.getSeconds(), endTimeArray[0], 
                    endTime.getMinutes(), endTimeArray[1], 
                    endTime.getHours(), endTimeArray[2], 
                    endTime.getDate(), endTimeArray[3], 
                    endTime.getMonth()+1, endTimeArray[4], 
                    endTime.getFullYear(), endTimeArray[5]);

}

////////////////////////////
//Multiple selections code
////////////////////////
// ===================================================================
// Author: Matt Kruse <matt@mattkruse.com>
// WWW: http://www.mattkruse.com/
//
// NOTICE: You may use this code for any purpose, commercial or
// private, without any further permission from the author. You may
// remove this notice from your final code if you wish, however it is
// appreciated by the author if at least my web site address is kept.
//
// You may *NOT* re-distribute this code in any way except through its
// use. That means, you can include it in your product, or your web
// site, or any other form where the code is actually being used. You
// may not put the plain javascript up on your site for download or
// include it in your javascript libraries for download. 
// If you wish to share this code with others, please just point them
// to the URL instead.
// Please DO NOT link directly to my .js files from your site. Copy
// the files to your server and use them there. Thank you.
// ===================================================================

// HISTORY
// ------------------------------------------------------------------
// March 31, 2004: First release
/* 

DESCRIPTION: This library allows you to easily create select boxes whose
contents depend on the value in a parent select box. It supports default
options, preselected options, single or multiple-select lists, multiple
form fields referencing the same list structure, form resetting, and most
importantly, it's backwards-compatible way back to Netscape 4!

COMPATABILITY: Netscape 4+, IE, Opera >5 (O5 didn't support new Option()),
and should work on all other newer browsers.

USAGE:

	// Create a new object, passing in the fields that make up the dynamic set 
	// of lists.
var dol = new DynamicOptionList("Field1","Child1","Child2");
	
	// Or, you can create it empty, and pass in sets of select objects later
var dol = new DynamicOptionList();
dol.addDependentFields("Field1","Child1","Child2");

	// Once you have the list object defined, you can additional sets of dependent
	// fields, too. These sets will act as separate groups of related fields, but
	// will all use the same options and data.
dol.addDependentOptions("Field1","Child2-1","Child2-2");

	// By default, the script will automatically find the form where your select
	// objects exist. But you can explicitly set it if you wish, either by form 
	// name or index.
dol.setFormName("MyForm");
dol.setFormIndex(1);

	// Now define the options that will exist in sub-lists. This is done in a 
	// very logical way - you say for an option in the parent, populate the child
	// with specific options. When selecting which parent option you're dealing
	// with, you can either select by its value or its display text. This command
	// says, for an option in the parent list that has value="Value1", if it is
	// selected then populate the child list with the given sub-options.
dol.forValue("Value1").addOptions("Suboption1","Suboption2","Suboption3");

	// And you can also say, for an option in the parent list that has display
	// text of "Text1", if it is selected then populate the child list with the
	// given sub-options.
dol.forText("Text1").addOptions("Suboption1","Suboption2","Suboption3");

	// For multi-level lists, you just continue the chain...
	// This says, if an option with value "Value1" is selected in the first list,
	// then an option with values "Value2" is selected in the second list, populate
	// the third list with these options.
dol.forValue("Value1").forValue("Value2").addOptions("1","2","3");

	// If the options you want to add should have different values and dislplay
	// text, you can do that
dol.forValue("Value1").addOptionsTextValue("Text2","Value2");

	// When an option is selected from the first list, and the options in the 
	// second list are populated, you may want to have one of the options in the
	// child list be selected by default.
dol.forValue("Value1").setDefaultOptions("MyValue");

	// When the page first loads, you may set the values of the dependent select
	// lists to be selected by default. For example, when a user is editing an
	// existing record where they've already selected from the parent/child
	// relationships. This is different from the default option in that this
	// value is only selected when the page LOADS. If the user changes selections,
	// this will be lost.
dol.forValue("Value1").setValues("MyPreselectedValue");

	// By default, if there are is no option which should be selected in the child
	// list, the code will automatically select the first option in the list. If 
	// you want it to instead set selectedIndex = -1 (nothing selected - works in
	// most browsers but not all) than you can tell it to do that instead
dol.selectFirstOption = false;

// MODIFYING THE HTML
// If you are supporting Netscape 4.x browsers, you will need to insert a call to
// the library to populate options. This is because Netscape4 will not expand the
// size of the select box as new options are added, so you have to "pad" the list
// with blank options in order for it to work right. 
// This is the ONLY change you should need to make to your HTML. To do this, just
// add a javascript block between your <select> </select> tags like this:

<select name="list1"><script>dol.printOptions("list1")</script></select>

// You only need to pass it the name of the select options that it should print
// options for.


NOTES:
 - There seems to be an issue with Netscape6, if you hit Reload on the page. It
   doesn't happen every time, and I can't figure out why it happens at all.

 - If your select objects have onChange handlers in them, you'll need to manually
   add a call to the DynamicOptionList code to trigger the population of the child
   list. For example,
   
   <select onChange="yourfunction(); dol.change(this)">
 
*/ 
// Global objects to keep track of DynamicOptionList objects created on the page
var dynamicOptionListCount=0;
var dynamicOptionListObjects = new Array();

// Init call to setup lists after page load. One call to this function sets up all lists.
function initDynamicOptionLists() {
	// init each DynamicOptionList object
	for (var i=0; i<dynamicOptionListObjects.length; i++) {
		var dol = dynamicOptionListObjects[i];

		// Find the form associated with this list
		if (dol.formName!=null) { 
			dol.form = document.forms[dol.formName];
		}
		else if (dol.formIndex!=null) {
			dol.form = document.forms[dol.formIndex];
		}
		else {
			// Form wasn't set manually, so go find it!
			// Search for the first form element name in the lists
			var name = dol.fieldNames[0][0];
			for (var f=0; f<document.forms.length; f++) {
				if (typeof(document.forms[f][name])!="undefined") {
					dol.form = document.forms[f];
					break;
				}
			}
			if (dol.form==null) {
				alert("ERROR: Couldn't find form element "+name+" in any form on the page! Init aborted"); return;
			}
		}

		// Form is found, now set the onchange attributes of each dependent select box
		for (var j=0; j<dol.fieldNames.length; j++) {
			// For each set of field names...
			for (var k=0; k<dol.fieldNames[j].length-1; k++) {
				// For each field in the set...
				var selObj = dol.form[dol.fieldNames[j][k]];
				if (typeof(selObj)=="undefined") { alert("Select box named "+dol.fieldNames[j][k]+" could not be found in the form. Init aborted"); return; }
				// Map the HTML options in the first select into the options we created
				if (k==0) {
					if (selObj.options!=null) {
						for (l=0; l<selObj.options.length; l++) {
							var sopt = selObj.options[l];
							var m = dol.findMatchingOptionInArray(dol.options,sopt.text,sopt.value,false);
							if (m!=null) {
								var reselectForNN6 = sopt.selected;
								var m2 = new Option(sopt.text, sopt.value, sopt.defaultSelected, sopt.selected);
								m2.selected = sopt.selected; // For some reason I need to do this to make NN4 happy
								m2.defaultSelected = sopt.defaultSelected;
								m2.DOLOption = m;
								selObj.options[l] = m2;
								selObj.options[l].selected = reselectForNN6; // Reselect this option for NN6 to be happy. Yuck.
							}
						}
					}
				}
				if (selObj.onchange==null) {
					// We only modify the onChange attribute if it's empty! Otherwise do it yourself in your source!
					selObj.onchange = new Function("dynamicOptionListObjects["+dol.index+"].change(this)");
				}
			}
		}
	}
	// Set the preselectd options on page load 
	resetDynamicOptionLists();
}

// This function populates lists with the preselected values. 
// It's pulled out into a separate function so it can be hooked into a 'reset' button on a form
// Optionally passed a form object which should be the only form reset
function resetDynamicOptionLists(theform) {
	// reset each DynamicOptionList object
	for (var i=0; i<dynamicOptionListObjects.length; i++) {
		var dol = dynamicOptionListObjects[i];
		if (typeof(theform)=="undefined" || theform==null || theform==dol.form) {
			for (var j=0; j<dol.fieldNames.length; j++) {
				dol.change(dol.form[dol.fieldNames[j][0]],true); // Second argument says to use preselected values rather than default values
			}
		}
	}
}

// An object to represent an Option() but just for data-holding
function DOLOption(text,value,defaultSelected,selected) {
	this.text = text;
	this.value = value;
	this.defaultSelected = defaultSelected;
	this.selected = selected;
	this.options = new Array(); // To hold sub-options
	return this;
}

// DynamicOptionList CONSTRUCTOR
function DynamicOptionList() {
	this.form = null;// The form this list belongs to
	this.options = new Array();// Holds the options of dependent lists
	this.longestString = new Array();// Longest string that is currently a potential option (for Netscape)
	this.numberOfOptions = new Array();// The total number of options that might be displayed, to build dummy options (for Netscape)
	this.currentNode = null;// The current node that has been selected with forValue() or forText()
	this.currentField = null;// The current field that is selected to be used for setValue()
	this.currentNodeDepth = 0;// How far down the tree the currentNode is
	this.fieldNames = new Array();// Lists of dependent fields which use this object
	this.formIndex = null;// The index of the form to associate with this list
	this.formName = null;// The name of the form to associate with this list
	this.fieldListIndexes = new Object();// Hold the field lists index where fields exist
	this.fieldIndexes = new Object();// Hold the index within the list where fields exist
	this.selectFirstOption = true;// Whether or not to select the first option by default if no options are default or preselected, otherwise set the selectedIndex = -1
	this.numberOfOptions = new Array();// Store the max number of options for a given option list
	this.longestString = new Array();// Store the longest possible string 
	this.values = new Object(); // Will hold the preselected values for fields, by field name
	
	// Method mappings
	this.forValue = DOL_forValue;
	this.forText = DOL_forText;
	this.forField = DOL_forField;
	this.forX = DOL_forX;
	this.addOptions = DOL_addOptions;
	this.addOptionsTextValue = DOL_addOptionsTextValue;

	this.addOptionsText=DOL_addOptionsText;

	this.setDefaultOptions = DOL_setDefaultOptions;
	this.setValues = DOL_setValues;
	this.setValue = DOL_setValues;
	this.setFormIndex = DOL_setFormIndex;
	this.setFormName = DOL_setFormName;
	this.printOptions = DOL_printOptions;
	this.addDependentFields = DOL_addDependentFields;
	this.change = DOL_change;
	this.child = DOL_child;
	this.selectChildOptions = DOL_selectChildOptions;
	this.populateChild = DOL_populateChild;
	this.change = DOL_change;
	this.addNewOptionToList = DOL_addNewOptionToList;
	this.findMatchingOptionInArray = DOL_findMatchingOptionInArray;

	// Optionally pass in the dependent field names
if (arguments.length > 0) {
		// Process arguments and add dependency groups
		for (var i=0; i<arguments.length; i++) {
			this.fieldListIndexes[arguments[i].toString()] = this.fieldNames.length;
			this.fieldIndexes[arguments[i].toString()] = i;
		}
		this.fieldNames[this.fieldNames.length] = arguments;
	}
	
	// Add this object to the global array of dynamicoptionlist objects
	this.index = window.dynamicOptionListCount++;
	window["dynamicOptionListObjects"][this.index] = this;
}

// Given an array of Option objects, search for an existing option that matches value, text, or both
function DOL_findMatchingOptionInArray(a,text,value,exactMatchRequired) {
	if (a==null || typeof(a)=="undefined") { return null; }
	var value_match = null; // Whether or not a value has been matched
	var text_match = null; // Whether or not a text has been matched
	for (var i=0; i<a.length; i++) {
		var opt = a[i];
		// If both value and text match, return it right away
		if (opt.value==value && opt.text==text) { return opt; }
		if (!exactMatchRequired) {
			// If value matches, store it until we complete scanning the list
			if (value_match==null && value!=null && opt.value==value) {
				value_match = opt;
			}
			// If text matches, store it for later
			if (text_match==null && text!=null && opt.text==text) {
				text_match = opt;
			}
		}
	}
	return (value_match!=null)?value_match:text_match;
}

// Util function used by forValue and forText
function DOL_forX(s,type) {
	if (this.currentNode==null) { this.currentNodeDepth=0; }
	var useNode = (this.currentNode==null)?this:this.currentNode;
	var o = this.findMatchingOptionInArray(useNode["options"],(type=="text")?s:null,(type=="value")?s:null,false);
	if (o==null) {
		o = new DOLOption(null,null,false,false);
		o[type] = s;
		useNode.options[useNode.options.length] = o;
	}
	this.currentNode = o;
	this.currentNodeDepth++;
	return this;
}

// Set the portion of the list structure that is to be used by a later operation like addOptions
function DOL_forValue(s) { return this.forX(s,"value"); }

// Set the portion of the list structure that is to be used by a later operation like addOptions
function DOL_forText(s) { return this.forX(s,"text"); }

// Set the field to be used for setValue() calls
function DOL_forField(f) { this.currentField = f; return this; }

// Create and add an option to a list, avoiding duplicates
function DOL_addNewOptionToList(a, text, value, defaultSelected) {
	var o = new DOLOption(text,value,defaultSelected,false);
	// Add the option to the array
	if (a==null) { a = new Array(); }
	for (var i=0; i<a.length; i++) {
		if (a[i].text==o.text && a[i].value==o.value) {
			if (o.selected) { 
				a[i].selected=true;
			}
			if (o.defaultSelected) {
				a[i].defaultSelected = true;
			}
			return a;
		}
	}
	a[a.length] = o;
}

// Add sub-options to the currently-selected node, with the same text and value for each option
function DOL_addOptions() {
	if (this.currentNode==null) { this.currentNode = this; }
	if (this.currentNode["options"] == null) { this.currentNode["options"] = new Array(); }
	for (var i=0; i<arguments.length; i++) {
		var text = arguments[i];
		this.addNewOptionToList(this.currentNode.options,text,text,false);
		if (typeof(this.numberOfOptions[this.currentNodeDepth])=="undefined") {
			this.numberOfOptions[this.currentNodeDepth]=0;
		}
		if (this.currentNode.options.length > this.numberOfOptions[this.currentNodeDepth]) {
			this.numberOfOptions[this.currentNodeDepth] = this.currentNode.options.length;
		}
		if (typeof(this.longestString[this.currentNodeDepth])=="undefined" || (text.length > this.longestString[this.currentNodeDepth].length)) {
			this.longestString[this.currentNodeDepth] = text;
		}
	}
	this.currentNode = null;
	this.currentNodeDepth = 0;
}

// Add sub-options to the currently-selected node, specifying the text and setting value to null 
function DOL_addOptionsText() {
	if (this.currentNode==null) { this.currentNode = this; }
	if (this.currentNode["options"] == null) { this.currentNode["options"] = new Array(); }
	for (var i=0; i<arguments.length; i++) {
		var text = arguments[i];
		this.addNewOptionToList(this.currentNode.options,text, value, false);
		if (typeof(this.numberOfOptions[this.currentNodeDepth])=="undefined") {
			this.numberOfOptions[this.currentNodeDepth]=0;
		}
		if (this.currentNode.options.length > this.numberOfOptions[this.currentNodeDepth]) {
			this.numberOfOptions[this.currentNodeDepth] = this.currentNode.options.length;
		}
		if (typeof(this.longestString[this.currentNodeDepth])=="undefined" || (text.length > this.longestString[this.currentNodeDepth].length)) {
			this.longestString[this.currentNodeDepth] = text;
		}
	}
	this.currentNode = null;
	this.currentNodeDepth = 0;
}



// Add sub-options to the currently-selected node, specifying separate text and values for each option
function DOL_addOptionsTextValue() {
	if (this.currentNode==null) { this.currentNode = this; }
	if (this.currentNode["options"] == null) { this.currentNode["options"] = new Array(); }
	for (var i=0; i<arguments.length; i++) {
		var text = arguments[i++];
		var value = arguments[i];
		this.addNewOptionToList(this.currentNode.options,text,value,false);
		if (typeof(this.numberOfOptions[this.currentNodeDepth])=="undefined") {
			this.numberOfOptions[this.currentNodeDepth]=0;
		}
		if (this.currentNode.options.length > this.numberOfOptions[this.currentNodeDepth]) {
			this.numberOfOptions[this.currentNodeDepth] = this.currentNode.options.length;
		}
		if (typeof(this.longestString[this.currentNodeDepth])=="undefined" || (text.length > this.longestString[this.currentNodeDepth].length)) {
			this.longestString[this.currentNodeDepth] = text;
		}
	}
	this.currentNode = null;
	this.currentNodeDepth = 0;
}



// Find the first dependent list of a select box
// If it's the last list in a chain, return null because there are no children
function DOL_child(obj) {
	var listIndex = this.fieldListIndexes[obj.name];
	var index = this.fieldIndexes[obj.name];
	if (index < (this.fieldNames[listIndex].length-1)) {
		return this.form[this.fieldNames[listIndex][index+1]];
	}
	return null;
}

// Set the options which should be selected by default for a certain value in the parent
function DOL_setDefaultOptions() {
	if (this.currentNode==null) { this.currentNode = this; }
	for (var i=0; i<arguments.length; i++) {
		var o = this.findMatchingOptionInArray(this.currentNode.options,null,arguments[i],false);
		if (o!=null) {
			o.defaultSelected = true;
		}
	}
	this.currentNode = null;
}

// Set the options which should be selected when the page loads. This is different than the default value and ONLY applies when the page LOADS
function DOL_setValues() {
	if (this.currentField==null) { 
		alert("Can't call setValues() without using forField() first!");
		return;
	}
	if (typeof(this.values[this.currentField])=="undefined") {
		this.values[this.currentField] = new Object();
	}
	for (var i=0; i<arguments.length; i++) {
		this.values[this.currentField][arguments[i]] = true;
	}
	this.currentField = null;
}

// Manually set the form for the object using an index
function DOL_setFormIndex(i) {
	this.formIndex = i;
}

// Manually set the form for the object using a form name
function DOL_setFormName(n) {
	this.formName = n;
}

// Print blank <option> objects for Netscape4, since it refuses to grow or shrink select boxes for new options
function DOL_printOptions(name) {
	// Only need to write out "dummy" options for Netscape4
    if ((navigator.appName == 'Netscape') && (parseInt(navigator.appVersion) <= 4)){
		var index = this.fieldIndexes[name];
		var ret = "";
		if (typeof(this.numberOfOptions[index])!="undefined") {
			for (var i=0; i<this.numberOfOptions[index]; i++) { 
				ret += "<OPTION>";
			}
		}
		ret += "<OPTION>";
		if (typeof(this.longestString[index])!="undefined") {
			for (var i=0; i<this.longestString[index].length; i++) {
				ret += "_";
			}
		}
		document.writeln(ret);
	}
}

// Add a list of field names which use this option-mapping object.
// A single mapping object may be used by multiple sets of fields
function DOL_addDependentFields() {
	for (var i=0; i<arguments.length; i++) {
		this.fieldListIndexes[arguments[i].toString()] = this.fieldNames.length;
		this.fieldIndexes[arguments[i].toString()] = i;
	}
	this.fieldNames[this.fieldNames.length] = arguments;
}

// Called when a parent select box is changed. It populates its direct child, then calls change on the child object to continue the population.
function DOL_change(obj, usePreselected) {
	if (usePreselected==null || typeof(usePreselected)=="undefined") { usePreselected = false; }
	var changedListIndex = this.fieldListIndexes[obj.name];
	var changedIndex = this.fieldIndexes[obj.name];
	var child = this.child(obj);
	if (child == null) { return; } // No child, no need to continue
	if (obj.type == "select-one") {
		// Treat single-select differently so we don't have to scan the entire select list, which could potentially speed things up
		if (child.options!=null) {
			child.options.length=0; // Erase all the options from the child so we can re-populate
		}
		if (obj.options!=null && obj.options.length>0 && obj.selectedIndex>=0) {
			var o = obj.options[obj.selectedIndex];
			this.populateChild(o.DOLOption,child,usePreselected);
			this.selectChildOptions(child,usePreselected);
		}
	}
	else if (obj.type == "select-multiple") {
		// For each selected value in the parent, find the options to fill in for this list
		// Loop through the child list and keep track of options that are currently selected
		var currentlySelectedOptions = new Array();
		if (!usePreselected) {
			for (var i=0; i<child.options.length; i++) {
				var co = child.options[i];
				if (co.selected) {
					this.addNewOptionToList(currentlySelectedOptions, co.text, co.value, co.defaultSelected);
				}
			}
		}
		child.options.length=0;
		if (obj.options!=null) {
			var obj_o = obj.options;
			// For each selected option in the parent...
			for (var i=0; i<obj_o.length; i++) {
				if (obj_o[i].selected) {
					// if option is selected, add its children to the list
 					this.populateChild(obj_o[i].DOLOption,child,usePreselected);
				}
			}
			// Now go through and re-select any options which were selected before
			var atLeastOneSelected = false;
			if (!usePreselected) {
				for (var i=0; i<child.options.length; i++) {
					var m = this.findMatchingOptionInArray(currentlySelectedOptions,child.options[i].text,child.options[i].value,true);
					if (m!=null) {
						child.options[i].selected = true;
						atLeastOneSelected = true;
					}
				}
			}
			if (!atLeastOneSelected) {	
				this.selectChildOptions(child,usePreselected);
			}
		}
	}
	// Change all the way down the chain
	this.change(child,usePreselected);
}
function DOL_populateChild(dolOption,childSelectObj,usePreselected) {
	// If this opton has sub-options, populate the child list with them
	if (dolOption!=null && dolOption.options!=null) {
		for (var j=0; j<dolOption.options.length; j++) {
			var srcOpt = dolOption.options[j];
			if (childSelectObj.options==null) { childSelectObj.options = new Array(); }
			// Put option into select list
			var duplicate = false;
			var preSelectedExists = false;
			for (var k=0; k<childSelectObj.options.length; k++) {
				var csi = childSelectObj.options[k];
				if (csi.text==srcOpt.text && csi.value==srcOpt.value) {
					duplicate = true;
					break;
				}
			}
			if (!duplicate) {
				var newopt = new Option(srcOpt.text, srcOpt.value, false, false);
				newopt.selected = false; // Again, we have to do these two statements for NN4 to work
				newopt.defaultSelected = false;
				newopt.DOLOption = srcOpt;
				childSelectObj.options[childSelectObj.options.length] = newopt;
			}
		}
	}
}

// Once a child select is populated, go back over it to select options which should be selected
function DOL_selectChildOptions(obj,usePreselected) {
	// Look to see if any options are preselected=true. If so, then set then selected if usePreselected=true, otherwise set defaults
	var values = this.values[obj.name];
	var preselectedExists = false;
	if (usePreselected && values!=null && typeof(values)!="undefined") {
		for (var i=0; i<obj.options.length; i++) {
			var v = obj.options[i].value;
			if (v!=null && values[v]!=null && typeof(values[v])!="undefined") {
				preselectedExists = true;
				break;
			}
		}
	}
	// Go back over all the options to do the selection
	var atLeastOneSelected = false;
	for (var i=0; i<obj.options.length; i++) {
		var o = obj.options[i];
		if (preselectedExists && o.value!=null && values[o.value]!=null && typeof(values[o.value])!="undefined") {
			o.selected = true;
			atLeastOneSelected = true;
		}
		else if (!preselectedExists && o.DOLOption!=null && o.DOLOption.defaultSelected) {
			o.selected = true;
			atLeastOneSelected = true;
		}
		else {
			o.selected = false;
		}
	}
	// If nothing else was selected, select the first one by default
	if (this.selectFirstOption && !atLeastOneSelected && obj.options.length>0) {
		obj.options[0].selected = true;
	}
	else if (!atLeastOneSelected &&  obj.type=="select-one") {
		obj.selectedIndex = -1;
	}
}





