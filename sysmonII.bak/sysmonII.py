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
      print("Loading sysmonII configuration failed.", e)
      try:
        self.config	# If there's already a configuration, use it.
      except:
        sys.exit()	# No configuration, exit.
    except:
      print("Loading sysmonII configuration failed badly")
      sys.exit()

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
        geaurl = self.getGeaLink(pvname)
        m.geaurl  = geaurl
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
        

  def getGeaLink(self, pvname):
    import xmlrpc.client

    self.site     = os.environ['GEMINI_SITE'] if 'GEMINI_SITE' in os.environ else "MK"

    if self.site == 'CP': localserver = "http://geasouth.cl.gemini.edu/"
    else:                 localserver = "http://geanorth.hi.gemini.edu/"

    dataServer = xmlrpc.client.Server(localserver + "run/ArchiveDataServer.cgi")

    for archiver in dataServer.archiver.archives():
        if archiver['name'][0:1] == '-' or len(archiver['name']) < 2:
            continue
    
        key  = archiver['key'];
        name = archiver['name'];
    
        try: 
          matches = dataServer.archiver.names(key, pvname)
          if matches: 
            return "%s/pages/common/plotterPage?PATTERN=%s&SYSTEMS=%s" % (localserver, pvname, name)
        except:
          pass

    return None
    
  def sighandler(self, signum, frame):
  
    print(3, "Signal handler called with signal %d" % signum)
    if signum == signal.SIGINT:
      print(0, "Quiting due to SIGINT")
      sys.exit(0)
    elif signum == signal.SIGUSR1:
      print(3, "Reloading configuration (SIGUSR1)")
      self.loadConfig()
    elif signum == signal.SIGUSR2:
      print(3, "Dumping statistics (SIGUSR2)")
      self.reports.showStats(self)




  def UI(self):
  
    # print('X')
    print('starting server... %d' % len(self.cache))
    # print('X')
  
    httpd = ThreadedHTTPServer(('0.0.0.0', 8080), WebInterface.WebInterface)
  
    httpd.sysmon = self
    print('running server...')
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
        print(e)
        pass
    time.sleep(1.0)

