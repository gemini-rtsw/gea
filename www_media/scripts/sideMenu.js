
//File created by menuCreator.py
function writeMenu()
{
    var s='<table class="menu" width="130" cellspacing="0" cellpadding="0"><tr><td>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Daily/Reports</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/engineeringPage?">Engineering</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/sysMonitorPage?">System Monitor</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/logWatcherPage?">Log Watcher</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://project.gemini.edu:2010/Plan/Overview.aspx">Weekly Plan</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/remedy/frsPage?">Fault Reports</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/remedy/frsPage?FORMAT=ticket">Ticket Search</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/remedy/frsPage?FORMAT=user">User Search</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/remedy/frsPage?FORMAT=stats">Stats/Graphs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/nightlog/nightLogPage?">Night Log</a></td></tr> \n\
<tr><td class="menuItem">Metrics</td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/metrics/nightLogPage?FORMAT=Report&SITE=MK">EMM Report</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/metrics/telMetricsPage?">Telescope</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/metrics/laserMetricsPage?">Laser</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/labs">GEA <i>labs</i></a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Systems</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/agPage?">A&G</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/crcsPage?">Crcs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/ecsPage?">Ecs</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/systems/ecs/ecsLoggerPage?">Ecs Logger</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/gisPage?">Gis</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/gwsPage?">Gws (Weather)</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/laserPage?">Laser</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/systems/laser/btoPage?">Bto</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/systems/laser/lisPage?">Lis</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/systems/laser/lsePage">Lse</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/mcsPage?">Mcs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/pcsPage?">Pcs</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/systems/pcs/m1AnimationsPage">m1 Animation</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/systems/pcs/m1SurfaceRTPage?">m1 Surface</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/prPage?">Pr</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/scsPage?">Scs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/tcsPage?">Tcs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/systems/wfsPage?">Wfs</a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Instruments</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/altairPage?">Altair</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/gmosPage?">Gmos</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/gnirsPage?">Gnirs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/gpolGcalPage?">Gpol/Gcal</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/igrins2Page?">Igrins-2</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/nifsPage?">Nifs</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/instruments/niriPage?">Niri</a></td></tr> \n\
<tr><td class="menuSubItem">&nbsp;&nbsp;&nbsp<a class="menuSubItem" href="/pages/instruments/niri/niriFocusPage?">Niri Focus</a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Compilations</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/compilations/calPage?">Calibrations</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/compilations/iqPage?">IQ</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/compilations/temporaryPage?">Temporary</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/compilations/versionsPage?">Versions</a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Real Time</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/rt/timeProbePage?">Time Probe</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="/pages/rt/healthPage?">Health</a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Admin</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://geanorth.hi.gemini.edu:4800">Archiver Status</a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
<table class="miniMenu" width="130" cellspacing="0">\n\
<tr><td class="menuTitle">Links</td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://internal.gemini.edu/science/GNqueue/qpt-plans/tonight.html">Queue Plan</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://internal.gemini.edu/sos/node/3204">Phone Numbers</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://internal.gemini.edu/telescope/tempdir/telMKWeather.html">MKO Weather</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://www.gemini.edu">Gemini Home</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://opswiki.wikis.gemini.edu/index.php/Main_Page">Ops Wiki</a></td></tr> \n\
<tr><td class="menuItem"><a class="menuItem" href="http://swg.wikis-internal.gemini.edu/index.php/Main_Page">Swg Wiki</a></td></tr> \n\
</table>\n\
<table width="100%" cellspacing="0" cellpadding="0"><tr><td>&nbsp;</td></tr></table>\n\
</td></tr></table>\n\
';
    document.write(s);
}
