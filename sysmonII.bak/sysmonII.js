
var enablestr  = "Enable";	// Since these are compared, using var's to guarentee 
var disablestr = "Disable";	// they're the same all over.

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
        for (i = 0; i < v.length; ++i)
          v[i].innerHTML = val.fontcolor(color);
      }
      for (var sys in js['emailnotifications']) {
        var va = document.getElementsByClassName("emailactive " + sys);
        var vb = document.getElementsByClassName("emailbutton " + sys);
        if (js['emailnotifications'][sys]) {
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
