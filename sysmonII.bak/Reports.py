#!/usr/bin/env python3
  
import os
import re
import sys
import time
import datetime
from Cache import pvType
  
  
  #
  # Misc routines that print reports of internal states. Likely ends up in logfile.
  #
  
  
class Reports:

  def __init__(self, smII):
    self.smII = smII 
  
  def columnate(self, x):
    """
      Print a 2d list as a pretty column'd table.
    """
  
    w = [max(map(len, col)) for col in zip(*x)]
  
    for r in x:
      print("   " + "  ".join((v.ljust(w) for v, w in zip(r, w))))
  
  
  
  
  def showStats(self, smII):
    """
    General pv information report.
    """
  
  
    print(3, "Dumping Statistics")
    print(3, "Cache Report")
  
    print("Cached Process Variable Report")
    x = [["Name", "Type", "Value", "Timestamp", "Rate", "Age", "Cnt", "Comments", "UUID"]]
  
    for pvname in self.smII.cache:
      pv = self.smII.cache[pvname]
      if len(pv.values):
        if len(pv.values) >= 1:
          age = "%.2f" % (time.time() - pv.timestamps[-1])
        else:
          age = "-"
  
        ts = "%.2f" % pv.timestamps[0]
        num = "%d" % len(pv.values)
        rt = "%.2f" % pv.meta['rate'] if pv.meta and 'rate' in pv.meta else "-"
  
        if pv.type == pvType.String:
          x.append([pvname, pv.type.name, pv.values[-1], ts, rt, age, num, ""])
        elif pv.type == pvType.Enum:
          e = pv.meta['enum_strs'].__str__() if pv.meta and 'enum_strs' in pv.meta else "no enum_strs"
          x.append([pvname, pv.type.name, "%d" % pv.values[-1], ts, rt, age, num, e])
        else:
          x.append([pvname, pv.type.name, "%f" % pv.values[-1], ts, rt, age, num, ""])
      else:
        x.append([pvname, pv.type.name, "NO DATA",
                  "NO TIMESTAMPS", "-", "-", "%d" % len(pv.values), ""])
  
    print()
    self.columnate(x)
    print()
  
    #
    # Generate metadata report
    #
  
    print("Metadata Report")
    x = [["pvname", "host", "ftype", "type", "units", "precision", "mondb", "archdb", "alrmdb", "ver", "desc",
          "enum_strs"]]
  
    for pvname in self.smII.cache:
      pv = self.smII.cache[pvname]
      if not pv.meta:
        x.append([pvname, "No metadata", "", "", "", "", "", "", "", "", "", ""])
      else:
        y = [pvname]
        for n in ['host', 'ftype', 'type', 'units', 'precision', 'monitor_deadband', 'archive_deadband',
                  'alarm_deadband', 'version', 'description', 'enum_strs']:
          if n in pv.meta:
            y.append(pv.meta[n].__str__())
          else:
            y.append(" ")
        x.append(y)
  
    print()
    self.columnate(x)
    print()
  
    #
    # Show filter and trigger report.
    #
  
    print("Monitors Report")
    x = [["UUID", "Pvname", "Filter", "Filter Value", "Trigger", "Failed"]]
  
    for uuid in self.smII.monitors:
      m = self.smII.monitors[uuid]
      prow = [uuid]
      prow.append(m.pvname)
      prow.append(m.fltconf.__str__())
      prow.append(m.fltval.__str__())
      prow.append(m.trgconf.__str__())
      prow.append(m.failed.__str__())
      x.append(prow)
    """
    self.confdir  = os.environ['GEMINI_TOP']  if 'GEMINI_TOP'  in os.environ else "./"
    self.pvname   = pvname
    self.monconf  = monconf
    self.fltconf  = self.monconf['filter']
    self.filter   = self.unknownFilter
    self.fltsecs  = None
    self.fltcnt   = None
    self.message  = None                        # If anything fails, put a message here (and trigger code will not be called). Else None
    self.fltval   = None                        # If filtering succeeds, put value here (and call the trigger code). Else None
    self.trgconf  = monconf['trigger']
    self.trigger  = self.unknownTrigger
    self.options  = self.monconf['options']
    self.system   = None                        # Filled out by loadconfig. References system this is a monitor for
    self.cache    = None                        # Filled out by loadconfig. References cache of data this monitor is monitoring.
    self.config   = None                        # Filled out by loadconfig.
    self.uuid     = None
    self.desc     = monconf['description']
    self.failed   = False
    self.state    = State.UNINITIALIZED
    self.geaurl   = None
    """

  
    print()
    self.columnate(x)
    print()
  
    #
    # Show per system metadata
    #
  
    print("Systems Report")

    for sysname in self.smII.systems:
      s = self.smII.systems[sysname]
      print(sysname)
      print("    ", s.site        if s.site    else "-")
      print("    ", s.confdir     if s.site    else "-")
      print("    ", s.notify      if s.notify  else "-")
      print("    ", s.comment     if s.comment else "-")
      print("    ", s.desc        if s.desc    else "-")
      print("    ", s.emailenable)

  
    print()
    print("Open files %d" % len(os.listdir('/proc/self/fd')))
    print()

