
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

  // Add settings buttons
  let triggerDiv = document.getElementById("triggerdiv");
  triggerDiv.innerHTML = "";
  triggerDiv.style.display = "block";

  var settingsDiv = document.createElement("div");
  settingsDiv.id = "settingsform";
  triggerDiv.appendChild(settingsDiv);

  let btn = document.createElement("button");
  btn.innerText = "Trigger";
  btn.onclick = function() { showTriggerForm(info['trigger'], info['uuid'], settingsDiv); };
  triggerDiv.appendChild(btn);

  let fbtn = document.createElement("button");
  fbtn.innerText = "Filter";
  fbtn.style.marginLeft = "4px";
  fbtn.onclick = function() { showFilterForm(info['filter'], info['uuid'], settingsDiv); };
  triggerDiv.appendChild(fbtn);

  let obtn = document.createElement("button");
  obtn.innerText = "Options";
  obtn.style.marginLeft = "4px";
  obtn.onclick = function() { showOptionsForm(info['options'], info['uuid'], settingsDiv); };
  triggerDiv.appendChild(obtn);

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
  var err = null;

  if (type == "range") {
    var lo = parseNum(document.getElementById("triglow").value);
    var hi = parseNum(document.getElementById("trighigh").value);
    if (!isNum(lo)) { err = "Low must be a number"; }
    else if (!isNum(hi)) { err = "High must be a number"; }
    else if (lo >= hi) { err = "Low must be less than High"; }
    else { trigger['low'] = lo; trigger['high'] = hi; }
  } else if (type == "low") {
    var lo = parseNum(document.getElementById("triglow").value);
    if (!isNum(lo)) { err = "Low must be a number"; }
    else { trigger['low'] = lo; }
  } else if (type == "high") {
    var hi = parseNum(document.getElementById("trighigh").value);
    if (!isNum(hi)) { err = "High must be a number"; }
    else { trigger['high'] = hi; }
  } else if (type == "exact") {
    var val = document.getElementById("trigexact").value;
    if (val === "") { err = "Value cannot be empty"; }
    else { trigger['exact'] = parseNum(val); }
  } else if (type == "not") {
    var val = document.getElementById("trignot").value;
    if (val === "") { err = "Value cannot be empty"; }
    else { trigger['not'] = parseNum(val); }
  } else if (type == "heartbeat") {
    var hb = parseNum(document.getElementById("trigheartbeat").value);
    var rt = parseNum(document.getElementById("trigrate").value);
    if (!isNum(hb) || hb <= 0) { err = "Timeout must be a positive number"; }
    else if (!isNum(rt) || rt <= 0) { err = "Rate must be a positive number"; }
    else { trigger['heartbeat'] = hb; trigger['rate'] = rt; }
  } else if (type == "null") {
    trigger['null'] = true;
  }

  if (err) {
    alert(err);
    return;
  }

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var js = JSON.parse(this.responseText);
      if (js['error']) {
        alert("Error: " + js['error']);
      } else {
        container.innerHTML = "<b>Saved.</b>";
        // Update trigger column in the table
        var infoCell = document.getElementsByClassName(uuid + " info")[0];
        if (infoCell) {
          var row = infoCell.parentElement;
          var cells = row.getElementsByTagName("td");
          if (cells.length >= 6) {
            var tmsg = [];
            for (var k in trigger) {
              if (k == "not" || k == "exact")
                tmsg.push(k + ':"' + trigger[k] + '"');
              else
                tmsg.push(k + ":" + trigger[k]);
            }
            cells[5].innerHTML = tmsg.length ? tmsg.join(", ") : "-";
          }
        }
      }
    }
  };
  xhttp.open("POST", "/trigger", true);
  xhttp.setRequestHeader("Content-Type", "application/json");
  xhttp.send(JSON.stringify({uuid: uuid, trigger: trigger}));
}

function parseNum(val) {
  if (val === "" || val === null || val === undefined) return NaN;
  var n = Number(val);
  return isNaN(n) ? val : n;
}

function isNum(val) {
  return typeof val === "number" && !isNaN(val);
}


/*
 * Filter settings form.
 */

function detectFilterType(filter) {
  if ('average' in filter) return "average";
  if ('median' in filter)  return "median";
  if ('slope' in filter)   return "slope";
  if ('bit' in filter)     return "bit";
  if ('null' in filter)    return "null";
  return "null";
}

function parseFilterSpan(filter, ftype) {
  var span = filter[ftype];
  if (!span || typeof span !== "string") return {unit: "seconds", value: ""};
  var parts = span.split("=");
  return {unit: parts[0], value: parts[1] || ""};
}

function showFilterForm(filter, uuid, container) {
  container.innerHTML = "";

  var currentType = detectFilterType(filter);

  var label = document.createElement("b");
  label.innerText = "Filter Type: ";
  container.appendChild(label);

  var sel = document.createElement("select");
  sel.id = "flttype";
  var types = ["null", "average", "median", "slope", "bit"];
  for (var i = 0; i < types.length; i++) {
    var opt = document.createElement("option");
    opt.value = types[i];
    opt.text  = types[i];
    if (types[i] == currentType) opt.selected = true;
    sel.appendChild(opt);
  }
  container.appendChild(sel);
  container.appendChild(document.createElement("br"));

  var fields = document.createElement("div");
  fields.id = "fltfields";
  container.appendChild(fields);

  function renderFields() {
    fields.innerHTML = "";
    var t = sel.value;

    if (t == "null") return;

    if (t == "bit") {
      var parsed = (currentType == "bit") ? parseFilterSpan(filter, "bit") : {unit:"num", value:""};
      addField(fields, "Bit Number", "fltbitnum", parsed.value);
    } else {
      var parsed = (currentType == t) ? parseFilterSpan(filter, t) : {unit:"seconds", value:""};

      var ulbl = document.createElement("label");
      ulbl.innerText = "Unit: ";
      fields.appendChild(ulbl);

      var usel = document.createElement("select");
      usel.id = "fltunit";
      var units = ["seconds", "minutes", "hours", "samples"];
      for (var i = 0; i < units.length; i++) {
        var opt = document.createElement("option");
        opt.value = units[i];
        opt.text  = units[i];
        if (units[i] == parsed.unit) opt.selected = true;
        usel.appendChild(opt);
      }
      fields.appendChild(usel);
      fields.appendChild(document.createTextNode(" "));
      addField(fields, "Value", "fltspan", parsed.value);
    }
  }

  sel.onchange = renderFields;
  renderFields();

  container.appendChild(document.createElement("br"));

  var savebtn = document.createElement("button");
  savebtn.innerText = "Save";
  savebtn.onclick = function() { saveFilter(uuid, sel.value, container); };
  container.appendChild(savebtn);

  var cancelbtn = document.createElement("button");
  cancelbtn.innerText = "Cancel";
  cancelbtn.style.marginLeft = "4px";
  cancelbtn.onclick = function() { container.innerHTML = ""; };
  container.appendChild(cancelbtn);
}

function saveFilter(uuid, type, container) {
  var filter = {};
  var err = null;

  if (type == "null") {
    filter['null'] = true;
  } else if (type == "bit") {
    var val = document.getElementById("fltbitnum").value;
    var n = parseInt(val);
    if (isNaN(n) || n < 0) { err = "Bit number must be a non-negative integer"; }
    else { filter['bit'] = "num=" + n; }
  } else {
    var unit = document.getElementById("fltunit").value;
    var val  = document.getElementById("fltspan").value;
    var n = parseInt(val);
    if (isNaN(n) || n <= 0) { err = "Span value must be a positive integer"; }
    else { filter[type] = unit + "=" + n; }
  }

  if (err) {
    alert(err);
    return;
  }

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var js = JSON.parse(this.responseText);
      if (js['error']) {
        alert("Error: " + js['error']);
      } else {
        container.innerHTML = "<b>Saved.</b>";
        // Update filter column in the table
        var infoCell = document.getElementsByClassName(uuid + " info")[0];
        if (infoCell) {
          var row = infoCell.parentElement;
          var cells = row.getElementsByTagName("td");
          if (cells.length >= 5) {
            var fmsg = [];
            for (var k in filter) {
              if (k == "null") continue;
              fmsg.push(k + ":" + filter[k]);
            }
            cells[4].innerHTML = fmsg.length ? fmsg.join(", ") : "-";
          }
        }
      }
    }
  };
  xhttp.open("POST", "/filter", true);
  xhttp.setRequestHeader("Content-Type", "application/json");
  xhttp.send(JSON.stringify({uuid: uuid, filter: filter}));
}


/*
 * Options form.
 */

function showOptionsForm(options, uuid, container) {
  container.innerHTML = "";

  if (!options) options = {};

  var label = document.createElement("b");
  label.innerText = "Options:";
  container.appendChild(label);
  container.appendChild(document.createElement("br"));

  var opts = [
    {key: "noAlarm", label: "No Alarm (suppress email alerts)"},
    {key: "noLink",  label: "No Link (hide GEA plotter link)"}
  ];

  for (var i = 0; i < opts.length; i++) {
    var cb = document.createElement("input");
    cb.type = "checkbox";
    cb.id   = "opt_" + opts[i].key;
    cb.checked = (opts[i].key in options) && options[opts[i].key];
    container.appendChild(cb);
    var lbl = document.createElement("label");
    lbl.htmlFor = cb.id;
    lbl.innerText = " " + opts[i].label;
    container.appendChild(lbl);
    container.appendChild(document.createElement("br"));
  }

  container.appendChild(document.createElement("br"));

  var savebtn = document.createElement("button");
  savebtn.innerText = "Save";
  savebtn.onclick = function() { saveOptions(uuid, container); };
  container.appendChild(savebtn);

  var cancelbtn = document.createElement("button");
  cancelbtn.innerText = "Cancel";
  cancelbtn.style.marginLeft = "4px";
  cancelbtn.onclick = function() { container.innerHTML = ""; };
  container.appendChild(cancelbtn);
}

function saveOptions(uuid, container) {
  var options = {};

  if (document.getElementById("opt_noAlarm").checked) options['noAlarm'] = true;
  if (document.getElementById("opt_noLink").checked)  options['noLink']  = true;

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var js = JSON.parse(this.responseText);
      if (js['error']) {
        alert("Error: " + js['error']);
      } else {
        container.innerHTML = "<b>Saved.</b>";
        // Update options column in the table
        var infoCell = document.getElementsByClassName(uuid + " info")[0];
        if (infoCell) {
          var row = infoCell.parentElement;
          var cells = row.getElementsByTagName("td");
          if (cells.length >= 7) {
            var omsg = [];
            for (var k in options) omsg.push(k);
            cells[6].innerHTML = omsg.length ? omsg.join(", ") : "-";
          }
        }
      }
    }
  };
  xhttp.open("POST", "/options", true);
  xhttp.setRequestHeader("Content-Type", "application/json");
  xhttp.send(JSON.stringify({uuid: uuid, options: options}));
}


/*
 * Email list editor.
 */

function showEmailEdit(sysname, tier) {
  var suffix   = (tier == "notify2") ? "2" : "";
  var listSpan = document.getElementsByClassName("emaillist" + suffix + " " + sysname)[0];
  var editDiv  = document.getElementsByClassName("emailedit" + suffix + " " + sysname)[0];

  var currentEmails = listSpan.innerText.trim();
  if (currentEmails == "none") currentEmails = "";

  editDiv.style.display = "block";
  editDiv.innerHTML = "";

  var tierLabel = (tier == "notify2") ? "Secondary" : "Primary";
  var label = document.createElement("b");
  label.innerText = "Edit " + tierLabel + " email list (one per line):";
  editDiv.appendChild(label);
  editDiv.appendChild(document.createElement("br"));

  var textarea = document.createElement("textarea");
  textarea.id    = "emailtext_" + tier + "_" + sysname;
  textarea.rows  = 4;
  textarea.cols  = 80;
  textarea.value = currentEmails.replace(/ /g, "\n");
  textarea.style.fontFamily = "arial, helvetica, sans-serif";
  textarea.style.fontSize   = "10pt";
  editDiv.appendChild(textarea);
  editDiv.appendChild(document.createElement("br"));

  if (tier == "notify2") {
    var note = document.createElement("i");
    note.innerText = "Secondary list receives alerts only after 15 minutes (escalation). Leave empty to disable.";
    note.style.fontSize = "9pt";
    editDiv.appendChild(note);
    editDiv.appendChild(document.createElement("br"));
  }

  var savebtn = document.createElement("button");
  savebtn.innerText = "Save";
  savebtn.onclick = function() { saveEmailList(sysname, tier); };
  editDiv.appendChild(savebtn);

  var cancelbtn = document.createElement("button");
  cancelbtn.innerText = "Cancel";
  cancelbtn.style.marginLeft = "4px";
  cancelbtn.onclick = function() { editDiv.style.display = "none"; editDiv.innerHTML = ""; };
  editDiv.appendChild(cancelbtn);
}

function saveEmailList(sysname, tier) {
  var textarea = document.getElementById("emailtext_" + tier + "_" + sysname);
  var raw      = textarea.value.trim();

  // Normalize: split on whitespace/newlines, rejoin with spaces
  var emails = raw.split(/\s+/).filter(function(e) { return e.length > 0; });

  // Tier 1 cannot be empty, tier 2 can
  if (emails.length == 0 && tier == "notify") {
    alert("Primary email list cannot be empty");
    return;
  }

  // Basic email validation
  var emailRe = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  for (var i = 0; i < emails.length; i++) {
    if (!emailRe.test(emails[i])) {
      alert("Invalid email address: " + emails[i]);
      return;
    }
  }

  var notify = emails.join(" ");
  var suffix = (tier == "notify2") ? "2" : "";

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var js = JSON.parse(this.responseText);
      if (js['error']) {
        alert("Error: " + js['error']);
      } else {
        // Update display
        var listSpan = document.getElementsByClassName("emaillist" + suffix + " " + sysname)[0];
        listSpan.innerHTML = notify ? notify : "<i>none</i>";
        var editDiv = document.getElementsByClassName("emailedit" + suffix + " " + sysname)[0];
        editDiv.style.display = "none";
        editDiv.innerHTML = "";
      }
    }
  };
  xhttp.open("POST", "/notify", true);
  xhttp.setRequestHeader("Content-Type", "application/json");
  xhttp.send(JSON.stringify({system: sysname, notify: notify, tier: tier}));
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
