#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import signal
import datetime
from epics import ca
from epics import PV
from enum import Enum
from bisect import bisect_left
from epics.ca import ChannelAccessException

import logging
log = logging.getLogger("sysmonII")

os.environ['EPICS_CA_ADDR_LIST'] = "10.2.2.255 10.2.5.43 10.2.126.101 10.2.10.21 10.1.5.66 192.168.1.203 10.1.10.24 10.24 10.2.128.20"


#
# Type of process variable
#

class pvType(Enum):
  Unknown = 1
  Integer = 2
  Float   = 3
  String  = 4
  Enum    = 5

#
# Lookup table to convert EPICS type to sysmonII type.
#

dbr2pvType = (
  pvType.String,   # 0 STRING
  pvType.Integer,  # 1 INT
  pvType.Float,    # 2 FLOAT
  pvType.Enum,     # 3 ENUM
  pvType.Integer,  # 4 CHAR
  pvType.Integer,  # 5 LONG
  pvType.Float,    # 6 DOUBLE
  pvType.Unknown,  # 7 unknown
  pvType.Unknown,  # 8 unknown
  pvType.Unknown,  # 9 unknown
  pvType.Unknown,  # 10 unknown
  pvType.Unknown,  # 11 unknown
  pvType.Unknown,  # 12 unknown
  pvType.Unknown,  # 13 unknown
  pvType.String,   # 14 TIME_STRING
  pvType.Integer,  # 15 TIME_SHORT
  pvType.Float,    # 16 TIME_FLOAT
  pvType.Enum,     # 17 TIME_ENUM
  pvType.Integer,  # 18 TIME_CHAR
  pvType.Integer,  # 19 TIME_LONG
  pvType.Float,    # 20 TIME_DOUBLE
  pvType.Unknown,  # 21 unknown
  pvType.Unknown,  # 22 unknown
  pvType.Unknown,  # 23 unknown
  pvType.Unknown,  # 24 unknown
  pvType.Unknown,  # 25 unknown
  pvType.Unknown,  # 26 unknown
  pvType.Unknown,  # 27 unknown
  pvType.String,   # 28 CTRL_STRING
  pvType.Integer,  # 29 CTRL_SHORT
  pvType.Float,    # 30 CTRL_FLOAT
  pvType.Enum,     # 31 CTRL_ENUM
  pvType.Integer,  # 32 CTRL_CHAR
  pvType.Integer,  # 33 CTRL_LONG
  pvType.Float,    # 34 CTRL_DOUBLE
  pvType.Unknown   # 35 unknown
)




class Cache:
  """
    Monitor a bunch if process variables, caching their values. Also handles reading the configuration file.
  """

  def __init__(self, pvname):

    self.pvname     = pvname
    self.site       = os.environ['GEMINI_SITE'] if 'GEMINI_SITE' in os.environ else "MK"
    self.confdir    = os.environ['GEMINI_TOP']  if 'GEMINI_TOP'  in os.environ else "./"
    self.maxhistory = 1000	  # Maximum number of pv values to retain.
    self.meta       = None        # Hang channel metadata here
    self.pvname     = pvname
    self.chid       = ca.create_channel(pvname, callback=self.onConnectionChange)
    self.subid      = None
    self.values     = []	  # Array of pv values
    self.timestamps = []	  # Timestamp of change in pv value in values[] above.
    self.connected  = False       # Connected flag.
    self.connects   = []	  # True if connected, false otherwise
    self.connstamps = []	  # Timestamp of the transisitons in connects[] above.
    self.type       = pvType.Unknown  # Simplified data types
    self.warning    = ""	  # Place to hang any funny business.




  def onConnectionChange(self, pvname, conn, **kws):
    """
       Callback for when there is a PV connection change
    """
    self.connected = conn

    if conn:
      if not self.subid:
        self.subid = ca.create_subscription(self.chid, use_time=True, callback=self.onValueChange)
      self.addConnect(True)
    else:
      self.addConnect(False)





  def addConnect(self, connected):
    """
       Add a PV connections tate to the cache and timestamp it. If the cache is full remove the oldest state/timestamp.
    """

    self.connects.append(connected)
    self.connstamps.append(time.time())

    if len(self.connects) > self.maxhistory:
      self.connects.pop(0)
      self.connstamps.pop(0)





  def onValueChange(self, pvname, value, **kws):
    """
       Callback for PV value change.
    """
    if pvname == 'pr:elec:helcoPwr':
      log.debug("XXXXXXXXXXXXXXXXXX %s %s" % (pvname, value))

    if self.connected:
      tsa = abs(time.time() - kws['timestamp'])
      if tsa > 60:
        self.warning = "CA timestamp and NTP timestamp differ by more than a minute (%d)." % (tsa)

      self.newValue(pvname, value, **kws)


  def newValue(self, pvname, value, **kws):

    if value is None: return

    if self.type == pvType.Unknown:

      if 'ftype' in kws:
        ftype = kws['ftype']
        self.type = dbr2pvType[ftype] if ftype < len(dbr2pvType) else pvType.Unknown

    if self.type == pvType.Enum and 'enum_strs' in kws:
      self.meta['enum_strs'] = kws['enum_strs']

    self.addValue(value)









  def addValue(self, value):
    """
       Add a PV value to the cache and timestamp it. If the cache is full remove the oldest value/timestamp
    """

    self.values.append(value)
    self.timestamps.append(time.time())

    if len(self.values) > self.maxhistory:
      self.values.pop(0)
      self.timestamps.pop(0)




  def getTimeSlice(self, timestamp):
    """
       Get slice starting at timestamp. Return both values and timestamps.
    """

    start = bisect_left(self.timestamps, timestamp)

    return(self.values[start:], self.timestamps[start:])

  
 
  def getSlice(self, start):
    """
       Get slice starting at start. Return both values and timestamps.
    """
    return(self.values[start:], self.timestamps[start:])




  def getMeta(self):
    """
       Get metadata for a process variable. Some's important (such as type and enum_strs if type == enum)
       others are informational.
    """

    meta = self.meta if self.meta else {}
    if 'status' not in meta: meta['status'] = "Unset"

    p = PV(self.pvname)
    time.sleep(.25)
    if p is None: return  	# Something waaay wrong, Abort.

    if p.get(timeout = .25, use_monitor = False) == None: return

    for vnam in ['value', 'host', 'ftype', 'type', 'units', 'precision', 'enum_strs']:

      try:
        meta[vnam] = eval("p.%s" % vnam)
      except AttributeError:
        meta[vnam] = None
#      log.debug(meta[vnam], end = " ")

    del p

    self.newValue(self.pvname, meta['value']) 


    #
    # Get some other interesting meta data that might not be available.
    #

    pvbase = re.sub(r'\..*$', '', self.pvname)

    for v, n in zip(['.MDEL', '.ADEL', '.HYST', '.VERS', '.DESC'],
                    ['monitor_deadband', 'archive_deadband', 'alarm_deadband', 'version', 'description']):
      if n in meta:
        # log.debug("Already tried %s %s" % (v, n))
        continue
      try:
        ch = ca.create_channel(pvbase + v)
        meta[n] = ca.get(ch, timeout = .1)
        del (ch)
      except ChannelAccessException:
        meta[n] = None

    self.meta = meta


 

  #
  # Main routine that does housekeeping, i.e., everything that's not done
  # asynchronously by callbacks. Since callbacks must be brief, and cannot
  # make any epics calls, that stuff's done here.
  #

  def run(self):

    if self.meta and 'host' in self.meta and self.meta['host']:
      # log.debug(self.pvname + " already got meta")
      return

    log.debug("CACHERUN %s" % self.pvname)
    self.getMeta()

    if self.meta:
      if len(self.values) > 2:
        self.meta['rate'] = ((self.timestamps[-1] - self.timestamps[0]) / len(self.values))
