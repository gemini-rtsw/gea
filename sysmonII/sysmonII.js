
var enablestr  = "Enable";	// Since these are compared, using var's to guarentee 
var disablestr = "Disable";	// they're the same all over.
var ackstr = "Acknowledge";      

function main() {
  infoSetup();
  updateLatest();
}

//  var actv = document.getElementsByClassName("emailactive " + sysname);

function email_enable(sys) {
  var vb = document.getElementsByClassName("emailbutton " + sys);
  var enable = (vb[0].innerText == enablestr);

  vb[0].disabled = true;	// Until page updated.

  doAjax("/email?system=" + sys + "&enable=" + enable, function(js) { // The state gets toggled here.
    if (js['error']) {
      alert(js['error']);
    }
  }); 
}


/*
 * Support for, "info" popup.
 */

var pvdata    = [];
var pvdataLow = [];
var pvdataHi  = [];
// var pvplotting = false;
var pvNames   = [];

function infoSetup() {
  var pvValues = document.getElementsByClassName("info");

  for (var i = 0; i < pvValues.length; ++i) {
    value = pvValues[i];
    value.addEventListener("click", showInfo);
    value.style.color    = "blue";
    // value.style.fontSize = "larger";
    value.innerHTML = "&nbsp;i&nbsp;";
  }
}




/* /latest returns array that looks like:

{"updates": [
    "ao:temp1.VAL": {"value": "4.439542", "status": "NOT READY" }, ...
  ],
 "emailnotifications": [
      "ecs": true,
      "pcs": true,
      .
      .
      .
  ]
}

*/

function updateLatest() {
  doAjax("/latest?period=2000", function(js) {
    if (js['error']) {
      alert(js['error']);
    }
    else {
      for (var uuid in js['updates']) {
        var pvs = js['updates'][uuid];
        var val = pvs['value'] ? pvs['value'] : "-";
        switch (pvs['status']) {
          case 'OK':           color = "green";  break;
          case 'DISCONNECTED': color = "black", val = '<b>DISCONNECTED</b>';  break;
          case 'NOT READY':    color = "gray",  val = '-';   break;
          case 'WARN':         color = "orange"; break;
          case 'FAIL':         color = "red";    break;
          default:             color = "purple"; break;
        }
        var v = document.getElementsByClassName(uuid + " value");
        for (i = 0; i < v.length; ++i){
	  var formattedValue;
          try {
            formattedValue = pvs['value'].fontcolor(color);
          }
          catch (error) { // In case the value was null
            formattedValue = "".fontcolor(color);
          }
          finally {
            v[i].innerHTML = formattedValue;
          }
        }
      }
      for (var sys in js['emailnotifications']) {
        var va = document.getElementsByClassName("emailactive " + sys);
        var vb = document.getElementsByClassName("emailbutton " + sys);
	if (js['acknowledge'][sys]) {
          va[0].innerHTML = "<font color=\"orange\">Not Acknowledged</font>"
	  vb[0].innerHTML = ackstr;
	}
        else if (js['emailnotifications'][sys]) {
          va[0].innerHTML = "Enabled";
          vb[0].innerHTML = disablestr;
        }
        else {
          va[0].innerHTML = "<font color=\"red\">Disabled</font>";
          vb[0].innerHTML = enablestr;
        }
        vb[0].disabled = false;
      }
    }
  });
  setTimeout(updateLatest, 2000);
}




function doAjax(url, cb) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var js = JSON.parse(this.responseText);
      return(cb(js));
    }
  };
  xhttp.open("GET", url, true);
  xhttp.send();
}




function showInfoTable(info, event, infopopup, uuid) {
  let inforow;
  let infocell;

  pd = info['plotdata']

  let pdBX = document.getElementById("plotbox");
  let pdIM = document.getElementById("plotimg");

  if (pd) {
    pdIM.setAttribute('src', pd);
    pdIM.style.display = "block";
    pdBX.style.display = "block";
  }
  else {
    pdIM.style.display = "none";
    pdBX.style.display = "none";
  }

  mt = info['meta']

  let infotable = document.getElementById("infotable");
  infotable.innerHTML = "";

  for (let key in mt) {
    inforow  = infotable.insertRow(-1);
    infocell = inforow.insertCell(0);
    infocell.appendChild(document.createTextNode(key));
    infocell = inforow.insertCell(1);
    infocell.appendChild(document.createTextNode(mt[key]));
  }

  // Add trigger settings button
  let triggerDiv = document.getElementById("triggerdiv");
  triggerDiv.innerHTML = "";
  triggerDiv.style.display = "block";

  let btn = document.createElement("button");
  btn.innerText = "Trigger Settings";
  btn.onclick = function() { showTriggerForm(info['trigger'], info['uuid'], triggerDiv); };
  triggerDiv.appendChild(btn);

  // Absolute position if it won't fit.
  if (infopopup.clientHeight + event.clientY > window.innerHeight) {
    var y = event.clientY - infopopup.clientHeight;
    if (y < 5) y = 5;
      infopopup.style.top = y + window.scrollY;
  }
  else {
    infopopup.style.top  = event.clientY + window.scrollY;
  }
  infopopup.style.left = event.clientX;
  infopopup.style.visibility = "visible";
}


/*
 * Trigger settings form.
 */

var triggerTypes = ["low", "high", "exact", "not", "heartbeat", "null"];

function detectTriggerType(trigger) {
  if (('high' in trigger) && ('low' in trigger)) return "range";
  if ('low' in trigger)       return "low";
  if ('high' in trigger)      return "high";
  if ('exact' in trigger)     return "exact";
  if ('not' in trigger)       return "not";
  if ('heartbeat' in trigger) return "heartbeat";
  if ('null' in trigger)      return "null";
  return "null";
}

function showTriggerForm(trigger, uuid, container) {
  container.innerHTML = "";

  var currentType = detectTriggerType(trigger);

  // Type selector
  var label = document.createElement("b");
  label.innerText = "Trigger Type: ";
  container.appendChild(label);

  var sel = document.createElement("select");
  sel.id = "trigtype";
  var types = ["range", "low", "high", "exact", "not", "heartbeat", "null"];
  for (var i = 0; i < types.length; i++) {
    var opt = document.createElement("option");
    opt.value = types[i];
    opt.text  = types[i];
    if (types[i] == currentType) opt.selected = true;
    sel.appendChild(opt);
  }
  container.appendChild(sel);
  container.appendChild(document.createElement("br"));

  // Value fields container
  var fields = document.createElement("div");
  fields.id = "trigfields";
  container.appendChild(fields);

  function renderFields() {
    fields.innerHTML = "";
    var t = sel.value;

    if (t == "range") {
      addField(fields, "Low",  "triglow",  trigger['low']  || "");
      addField(fields, "High", "trighigh", trigger['high'] || "");
    } else if (t == "low") {
      addField(fields, "Low", "triglow", trigger['low'] || "");
    } else if (t == "high") {
      addField(fields, "High", "trighigh", trigger['high'] || "");
    } else if (t == "exact") {
      addField(fields, "Value", "trigexact", trigger['exact'] || "");
    } else if (t == "not") {
      addField(fields, "Value", "trignot", trigger['not'] || "");
    } else if (t == "heartbeat") {
      addField(fields, "Timeout (s)", "trigheartbeat", trigger['heartbeat'] || "");
      addField(fields, "Rate",        "trigrate",      trigger['rate'] || "");
    }
    // null has no fields
  }

  sel.onchange = renderFields;
  renderFields();

  container.appendChild(document.createElement("br"));

  // Save button
  var savebtn = document.createElement("button");
  savebtn.innerText = "Save";
  savebtn.onclick = function() { saveTrigger(uuid, sel.value, container); };
  container.appendChild(savebtn);

  // Cancel button
  var cancelbtn = document.createElement("button");
  cancelbtn.innerText = "Cancel";
  cancelbtn.style.marginLeft = "4px";
  cancelbtn.onclick = function() {
    container.innerHTML = "";
    var btn = document.createElement("button");
    btn.innerText = "Trigger Settings";
    btn.onclick = function() { showTriggerForm(trigger, uuid, container); };
    container.appendChild(btn);
  };
  container.appendChild(cancelbtn);
}

function addField(parent, labelText, inputId, value) {
  var lbl = document.createElement("label");
  lbl.innerText = labelText + ": ";
  parent.appendChild(lbl);
  var inp = document.createElement("input");
  inp.type = "text";
  inp.id   = inputId;
  inp.size = 10;
  inp.value = value;
  parent.appendChild(inp);
  parent.appendChild(document.createTextNode(" "));
}

function saveTrigger(uuid, type, container) {
  var trigger = {};

  if (type == "range") {
    trigger['low']  = parseNum(document.getElementById("triglow").value);
    trigger['high'] = parseNum(document.getElementById("trighigh").value);
  } else if (type == "low") {
    trigger['low'] = parseNum(document.getElementById("triglow").value);
  } else if (type == "high") {
    trigger['high'] = parseNum(document.getElementById("trighigh").value);
  } else if (type == "exact") {
    trigger['exact'] = document.getElementById("trigexact").value;
  } else if (type == "not") {
    trigger['not'] = document.getElementById("trignot").value;
  } else if (type == "heartbeat") {
    trigger['heartbeat'] = parseNum(document.getElementById("trigheartbeat").value);
    trigger['rate']      = parseNum(document.getElementById("trigrate").value);
  } else if (type == "null") {
    trigger['null'] = true;
  }

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var js = JSON.parse(this.responseText);
      if (js['error']) {
        alert("Error: " + js['error']);
      } else {
        container.innerHTML = "<b>Saved.</b>";
      }
    }
  };
  xhttp.open("POST", "/trigger", true);
  xhttp.setRequestHeader("Content-Type", "application/json");
  xhttp.send(JSON.stringify({uuid: uuid, trigger: trigger}));
}

function parseNum(val) {
  var n = Number(val);
  return isNaN(n) ? val : n;
}


function showInfo(e) {

  var infopopup = document.getElementById("infopopup");
  var uuid      = e.currentTarget.classList.item(0);

  doAjax("/pvinfo?uuid=" + uuid, function(js) {
    if (js['error']) {
      location.reload();
    }
    else {
      showInfoTable(js, e, infopopup, uuid);
    }
  });
}

function hideInfo() {
  document.getElementById("infopopup").style.visibility = "hidden";
}
