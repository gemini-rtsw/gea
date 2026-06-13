#!/usr/bin/env python3

import os
import sys
import time
import json
import signal
import threading
import Reports

#from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import Cache
import System
import Monitor
import WebInterface

# CRITICAL ERROR WARNING INFO DEBUG NOTSET

import logging

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%x %R:%S", filename="/gemsoft/var/log/gea/sysmonII.log")
log = logging.getLogger("sysmonII")
log.setLevel("DEBUG")

class sysmonII:




  def __init__(self):
    self.site     = os.environ['GEMINI_SITE'] if 'GEMINI_SITE' in os.environ else "MK"
    self.confdir  = os.environ['GEMINI_TOP']  if 'GEMINI_TOP'  in os.environ else "./"
    self.cache    = {}
    self.monitors = {}
    self.systems  = {}
    self.reports  = Reports.Reports(self)
    self.loadConfig()

    signal.signal(signal.SIGINT,  self.sighandler)
    signal.signal(signal.SIGUSR1, self.sighandler)
    signal.signal(signal.SIGUSR2, self.sighandler)





  def loadConfig(self):
    """
      Load sysmon configuration json format file. Don't load if there's errors.
      TODO:
         Add some locks for reloading.
         Handle misconfigurations better.
    """

    try:
      with open(self.confdir + "/etc/gea/sysmonII/sysmonII.json", "r") as f:
        js = json.load(f)
        self.config = js
    except json.decoder.JSONDecodeError as e:
      log.critical("Loading sysmonII configuration failed.", e)
      try:
        self.config	# If there's already a configuration, use it.
      except:
        sys.exit()	# No configuration, exit.
    except:
      log.critical("Loading sysmonII configuration failed badly")
      sys.exit()

    # Set logging level from conf file.
    log.setLevel(js['verbose'] if 'verbose' in js else "DEBUG")

    for sysname in js['systems']:
      sysconf = js['systems'][sysname]
      system  = System.System(sysname, js['systems'][sysname])
      self.systems[sysname] = system
      offset = 0
      for monconf in sysconf['monitor']:
        pvname = monconf['pvname']
        uuid = "%s:%d" % (sysname, offset)	# A monitor is referenced by the system it belongs to and a uniq number, e.g., "altair:2".
        offset += 1
        m = Monitor.Monitor(pvname, monconf)
        m.pvname  = pvname
        m.monconf = monconf
        m.desc    = monconf['description']
        m.system  = system
        m.doemail = js['doemail'] if 'doemail' in js else False
        m.uuid    = uuid
        geaurl = m.resolveGeaLink()	# Sets m.geaurl/geaServer/geaArchName; notify() retries if this fails
        if m.options == None:
          m.options = {}
        if geaurl == None: m.options['noLink'] = True
        self.monitors[uuid] = m			# Indexed by uuid so that WebInterface can find it.
        system.monitors.append(m)
        if pvname in self.cache:
          m.cache = self.cache[pvname]
        else:
          c = Cache.Cache(pvname)
          self.cache[pvname] = c
          m.cache            = c
        

  def sighandler(self, signum, frame):
  
    log.info("Signal handler called with signal %d" % signum)
    if signum == signal.SIGINT:
      log.critical("Quiting due to SIGINT")
      sys.exit(0)
    elif signum == signal.SIGUSR1:
      log.info("Reloading configuration (SIGUSR1)")
      self.loadConfig()
    elif signum == signal.SIGUSR2:
      log.info("Dumping statistics (SIGUSR2)")
      self.reports.showStats(self)




  def UI(self):
  
    log.info('starting server... %d' % len(self.cache))
  
    httpd = ThreadedHTTPServer(('0.0.0.0', 8080), WebInterface.WebInterface)
  
    httpd.sysmon = self
    log.info('running server...')
    httpd.serve_forever()

  


  
  def Maintainer(self):
    st = time.time()

    while True:
      if time.time() - st < 30:
        time.sleep(1)
      elif time.time() - st < 3600:
        time.sleep(10)
      else:
        time.sleep(300)
  
      for pvname in self.cache:
        self.cache[pvname].run()


  
  

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
  pass


  
if __name__ == '__main__':

  #
  # Set up to capture signals.
  #

  with open("/var/run/sysmonII/sysmonII.pid", "w") as f:
    f.write("%d\n" % os.getpid())

  smII = sysmonII()

  uithread = threading.Thread(target = smII.UI)
  uithread.setDaemon(True)
  uithread.start()

  uithread = threading.Thread(target = smII.Maintainer)
  uithread.setDaemon(True)
  uithread.start()

  while True:
    for uuid in smII.monitors:
      try:
        smII.monitors[uuid].CheckAndNotify()
      except Monitor.InsufficientData as e:
        log.info(e)
        pass
    time.sleep(1.0)

