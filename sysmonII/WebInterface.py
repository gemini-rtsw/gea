#!/usr/bin/env python3

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

import html
import time
import json
import pika
from Cache import pvType

import logging
log = logging.getLogger("sysmonII")

htmlheader = """<html>
 <head>
  <title> System Monitor II </title>
  <link rel="stylesheet" href="sysmonII.css"/>
  <script src="sysmonII.js"> </script>
 </head>
 <body onLoad="main();">
"""

htmltailer = """  <div id="infopopup" onMouseLeave="hideInfo();">
   <fieldset id="plotbox">
    <legend> Cached Values </legend>
    <img src="NoData.gif" id="plotimg"/>
   </fieldset>
   <table id="infotable"/>
   <div id="triggerdiv" style="margin-top:6px;"></div>
  </div>
 </body>
</html>
"""

gealink = "http://geanorth.hi.gemini.edu/pages/common/plotterPage?PATTERN=%s&SYSTEMS=%s"	# pvname geaengine

class WebInterface(BaseHTTPRequestHandler):

  def showMonitor(self):
    htstr    = htmlheader
    smII     = self.server.sysmon
    cache    = smII.cache
    monitors = smII.monitors
    systems  = smII.systems

    t = html.table()
    """ This doesn't work when displayed in an <iframe>
    r = t.row()
    sl  = "\n"
    sl += "        <center>\n"
    for sysname in systems:
      sl += '         <a href = "#{0}">{0}</a> &nbsp;\n'.format(sysname.upper())
    sl += "        </center>\n    "
    c = r.col(sl)
    """
    for sysname in sorted(systems):
      system = systems[sysname]
      r = t.row()
      c = r.col('<a name="{0}">{0}</a>'.format(sysname.upper()), clas = "goodsysname")
      c = r.col(system.comment if system.comment else "&nbsp;")
      r = t.row()
      c = r.col("Channel&nbsp;Name", clas = "heading")
      surprise = "&nbsp;" * 1
      c = r.col(surprise,           clas = "heading")
      c = r.col("Value (Filtered)", clas = "heading")
      c = r.col("Description",      clas = "heading")
      c = r.col("Filter",           clas = "heading")
      c = r.col("Trigger",          clas = "heading")
      c = r.col("Options",          clas = "heading")
  
      for index, monitor in enumerate(system.monitors):
        pvname =  monitor.pvname
        r = t.row()

        if monitor.options and 'noLink' in monitor.options:
          cm = pvname
        else:
          cm = '<a target="_parent" href="%s">%s</a>' % (monitor.geaurl, pvname)
        c = r.col(cm)
       
        c = r.col("",  clas = monitor.uuid + " info")
        c = r.col("-", clas = monitor.uuid + " value")
        c = r.col(monitor.desc if monitor.desc else "&nbsp;")
  
        fmsg = []
        cm = "-"
        for flt in monitor.fltconf:
          if flt == 'null': continue
          fmsg += ("%s:%s" % (flt, monitor.fltconf[flt]),)
        if len(fmsg): cm = ", ".join(fmsg)
        c = r.col(cm)
  
        tmsg = []
        cm = "-"
        for tgr in monitor.trgconf:
          if tgr == "not" or tgr == "exact":
            tmsg += ("%s:\"%s\"" % (tgr, monitor.trgconf[tgr]),)
          else:
            tmsg += ("%s:%s" % (tgr, monitor.trgconf[tgr]),)
        if len(tmsg): cm = ", ".join(tmsg)
        c = r.col(cm)
  
        omsg = []
        cm = "-"
        if monitor.options:
          for opt in monitor.options:
            if type(monitor.options[opt]) == type(True):
              omsg += (opt, )
            else:
              omsg += ("%s:%s" % (opt, monitor.options[opt]),)
          if len(omsg): cm = ", ".join(omsg)
        c = r.col(cm)
  
      # If the last table row count was odd, insert a dummy row to even up alternate colors.

      if r.rowcount & 1:
        r = t.row()
        c = r.col("", style="display:none;")
  
      if system.notify:
        r = t.row()
        c = r.col("Email List:")
        c = r.col(system.notify)

        r = t.row()
        c = r.col("", style="display:none;")

        r = t.row()
        ebuts = """
  Email notification <b class="emailactive {0}">Unknown</b> &nbsp;
  <button type="button" class="emailbutton {0}" onclick="email_enable('{0}');" >&nbsp;&nbsp;</button>
  <hr>
""".format(sysname)

        c = r.col(ebuts)
    htstr += t.show(indent = 2)
    htstr += htmltailer
    return htstr




  def jsonLatest(self, period):
    #
    # Return a list of pv's that have changed with the time period in the
    # form of (for each pv):
    #
    # {
    #  "name":   "MTEST:RAND",		// 
    #  "value":  "6.329899"		// Always returns string because this is used for dislay only.
    #  "status": "OK",			// OK, DISCONNECTED, NOT READY, WARN, FAIL
    #  "message": "Insufficient data",	// Error message.
    # },
    # Also return a list of the notification state for each system in the form of:
    # {"emailnotifications":{"rtems":true, "scs":false, ... }}
    #

    smII     = self.server.sysmon
    cache    = smII.cache
    systems  = smII.systems

    pvs    = cache

    ups = {}
    em  = {}
    ack = {}
    for sysname in sorted(systems):
      system = systems[sysname]
      em[sysname] = system.emailenable
      ack[sysname] = system.acknowledge
      for monitor in system.monitors:
        pvname =  monitor.pvname
        pv = cache[pvname]
        if len(pv.values) == 0: continue


        value = None

        # If both the last connection state change and value timestamps are older than the time of interested, continue.

        def paintValue():
          value = pv.values[-1]

          if   pv.type == pvType.String:  pass
          elif pv.type == pvType.Integer: value = "%d" % value
          elif pv.type == pvType.Float:   value = "%f" % value
          elif pv.type == pvType.Enum:    value = "%d" % value
          if monitor.fltval != None:
            f = [k for k in monitor.fltconf][0]               # f == filter type, i.e., "median", "average", etc.
            try:
              if f == 'median' or f == 'average' or f == 'slope':
                value += " (%f)" % monitor.fltval
              elif f == 'null':
                value.__str__()
              else:
                value += " (%s)" % monitor.fltval.__str__()
            except:
              value = "???" 
              log.warn("Value conversion error: %s %s" % (pvname, monitor.fltval))
          return value

        t = time.time()
        latest = max(pv.connstamps[-1], pv.timestamps[-1])
        if latest <= (t - period) and latest >= (t - (60 * 30)): continue # Always update after 30 minutes.

#        if pv.connstamps[-1] <= t and pv.timestamps[-1] <= t: continue

        st = "#"
        if not pv.connected:      st = "DISCONNECTED"
        elif len(pv.values) <= 1: st = "NOT READY"
        elif monitor.failed:
          st = "FAIL"
          value = paintValue()
        else:
          st = "OK"
          value = paintValue()

        try:
          pv.meta['status'] = st	# When starting up, meta's not set yet.
        except:
          pass

        ups[monitor.uuid] = {"value":value, "status":st, "message":monitor.message}
    js = {"updates":ups}
    js["emailnotifications"] = em
    js["acknowledge"] = ack
    return json.dumps(js, indent = 1)




  def jsonEmail(self, sysname, enable):
    #
    # Enable (or disable) email notification for sysname.
    #
    smII     = self.server.sysmon
    systems  = smII.systems

    enable = True if enable == "true".lower() else False	# cgi vars are all strings.
    system = systems[sysname]
    system.emailenable = enable
    if system.acknowledge:
      system.acknowledge = False 
    self.sendRabbitMsg({"type":"email", "system":sysname, "email":enable})
    log.debug("Email %s for %s" % ("enabled" if enable else "disabled", sysname))
    return json.dumps({'success':True}, indent = 1)
 



  def jsonTrigger(self, uuid, trigger):
    """
      Update trigger settings for a monitor and save to config file.
    """

    smII     = self.server.sysmon
    monitors = smII.monitors

    try:
      mon = monitors[uuid]
    except:
      return json.dumps({'error': "trigger bad uuid"}, indent = 1)

    # Update in-memory trigger config
    mon.trgconf.clear()
    mon.trgconf.update(trigger)
    mon.monconf['trigger'] = mon.trgconf

    # Re-assign trigger function
    t = mon.trgconf
    if ('high' in t) and ('low' in t):
      mon.trigger = mon.rangeTrigger
    elif 'low' in t:
      mon.trigger = mon.lowTrigger
    elif 'high' in t:
      mon.trigger = mon.highTrigger
    elif 'exact' in t:
      mon.trigger = mon.exactTrigger
    elif 'not' in t:
      mon.trigger = mon.notTrigger
    elif 'slope' in t:
      mon.trigger = mon.slopeTrigger
    elif 'null' in t:
      mon.trigger = mon.nullTrigger
    elif 'heartbeat' in t:
      mon.trigger = mon.heartbeatTrigger

    # Write updated config to disk
    confpath = smII.confdir + "/etc/gea/sysmonII/sysmonII.json"
    try:
      with open(confpath, "w") as f:
        json.dump(smII.config, f, indent = 1)
    except Exception as e:
      log.critical("Failed to write config: %s" % e)
      return json.dumps({'error': "Failed to save config"}, indent = 1)

    log.info("Trigger updated for %s: %s" % (uuid, trigger))
    return json.dumps({'success': True}, indent = 1)


  def jsonInfo(self, uuid):
    #
    # Return meta data (ioc host, precision, units, etc.) for
    # pvname.
    #

    smII     = self.server.sysmon
    cache    = smII.cache
    monitors = smII.monitors
    systems  = smII.systems

    try:
      mon = monitors[uuid]
    except:
      return json.dumps({'error': "pvinfo bad argument"}, indent = 1)

    pvname = mon.pvname
    pv = cache[pvname]
    mt = pv.meta
        
    #
    # Decode the following, "by hand" as they will be shown to the user and need
    # cleanedup first.
    #
    if pv.meta: 
      mt['Host'] = pv.meta['host'].rsplit(":", 1)[0] if 'host' in pv.meta and pv.meta['host'] else "Unknown"
      mt['Type'] = pv.meta['type']                   if 'type' in pv.meta and pv.meta['type'] else "Unknown"
      if 'rate' in pv.meta and pv.meta['rate']:
        mt['Rate'] = "%.3f Hz (%.3f seconds)" % (1.0 / pv.meta['rate'], pv.meta['rate'])
      mt['Cached'] = "%d" % len(pv.values)
      # mt['Reconnects'] = "%d" % pv.disconn
#      if pv.meta['units']:            mt['units']            = pv.meta['units']
      if pv.meta['precision']:        mt['Precision']        = pv.meta['precision']
      if pv.meta['enum_strs']:        mt['Enumeration']      = pv.meta['enum_strs']
      if pv.meta['description']:      mt['EPICS Description']= pv.meta['description']
      if pv.meta['monitor_deadband']: mt['Monitor Deadband'] = pv.meta['monitor_deadband']
      if pv.meta['alarm_deadband']:   mt['Alarm Deadband']   = pv.meta['alarm_deadband']
      if pv.meta['archive_deadband']: mt['Archive Deadband'] = pv.meta['archive_deadband']
    else:
      mt = {'Status':"No Metadata"}

    ## if 'fvalue' in mon: mt['Filtered Value'] = mon['fvalue'].__str__()
    ## if 'status' in mon: mt['Filter Message'] = mon['status'].__str__()
    # if 'description' in mon: mt['Configured Description']  = mon['description']
    mt['uuid']  = uuid
    if len(pv.values) > 0:
      mt['value'] = pv.values[-1]

    plotdata = mon.getPlot()

    return json.dumps({'meta': mt, "plotdata":plotdata, "trigger":mon.trgconf, "uuid":uuid}, indent = 1)





  def do_GET(self):
    """
      urlargs = urlparse(self.path)
      self.command:         GET
      self.path:            foobar?bar=1&foo=2
      urlargs.path:         foobar
      urlargs.query:        bar=1&foo=2
      self.request_version: HTTP/1.1
    """

    urlargs = urlparse(self.path)
    queries = {}
    try:
      for q in urlargs.query.split("&"):
        n, v = q.split("=")
        queries[n] = v
    except: pass

    #
    # Handle serving the main page.
    #
    if urlargs.path == "/":
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()

      monhtml = self.showMonitor()

      self.wfile.write(bytes(monhtml, "utf8"))
      return

    #
    # Special instance's to serve css's and js's
    #
    elif urlargs.path == "/sysmonII.css":
      self.send_response(200)
      self.send_header('Content-type','text/css')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()

      with open("sysmonII.css", "r") as f:
        css = f.read()

      self.wfile.write(bytes(css, "utf8"))
      return

    elif urlargs.path == "/sysmonII.js":
      self.send_response(200)
      self.send_header('Content-type','text/javascript')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()

      with open("sysmonII.js", "r") as f:
        js = f.read()

      self.wfile.write(bytes(js, "utf8"))
      return

    elif urlargs.path == "/NoData.gif":
      self.send_response(200)
      self.send_header('Content-type','image/gif')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()

      with open("NoData.gif", "rb") as f:
        im = f.read()

      self.wfile.write(im)
      return
  
  
    #
    # Serve json requests.
    #

    #
    # "http://localhost:8080/latest?period=2000"
    #
    # Return list of pv's that have changed in the last, "period" (defaults to 60 seconds).
    #
    # For each pv, returns:
    # {
    #  "pvname": "MTEST:RAND",		// 
    #  "status": "OK",			// OK, DISCONNECTED, NOT READY, WARN, FAIL
    #  "value":  "6.329899"		// Always returns string because this is used for dislay only.
    # },

    elif urlargs.path == "/latest":
      self.send_response(200)
      self.send_header('Content-type','application/json')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()
      try:    period = float(queries['period'])
      except: period = 60.0
      self.wfile.write(bytes(self.jsonLatest(period), "utf8"))
      return


    #
    # "http://localhost:8080/pvinfo?pvname=MTEST:RAND&uuid=scs:1"
    #
    # Returns meta information, and saved data for a process variable.
    # Note that for plotting data, one pixel can represent more than
    # one datapoint.
    # E.g, if the plotting area is 200 pixels wide, and
    # we are plotting data for an hour, and the pv is updating twice
    # per second, that means that each pixel represents
    # 3600 / 200 * 2 == 36 samples. For this reason for each pixel
    # we give the min/avg/max for all samples at that pixel-time (36
    # samples in the above example).
    # Alternatively, if we're plotting 5 minutes of data that's changing
    # once per minute, that'd be 200 / 5 = 40, or 1 datapoint for every
    # 40 pixels.
    #
    # For requested pv, returns:
    # {
    #  "pvname": "MTEST:RAND"		// Echo back pvname as the javascript is async.
    #  "meta":   {"name":"value", .. }	// Meta data (ioc host, precision, etc.)
    #  "plot... " still working on this...
    # },

    elif urlargs.path == "/pvinfo":
      self.send_response(200)
      self.send_header('Content-type','application/json')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()
      self.wfile.write(bytes(self.jsonInfo(queries['uuid']), "utf8"))
      return

    elif urlargs.path == "/email":
      self.send_response(200)
      self.send_header('Content-type','application/json')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()
      self.wfile.write(bytes(self.jsonEmail(queries['system'], queries['enable']), "utf8"))
      return

    elif urlargs.path == "/plot":
      pagehtml = """data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="""
      self.send_response(200)
      self.send_header('Content-type','image/png')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()
      self.wfile.write(bytes(pagehtml, "utf8"))
      return

    elif urlargs.path == "/bingo":
      pagehtml = """<html>
<div>
 <h1> Cows </h1>
 <img src="http://localhost:8080/plot"/>
</div>
"""
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()
      self.wfile.write(bytes(pagehtml, "utf8"))
      return

    #
    # Return error for all other queries.
    #
    else:
      self.send_response(404)
      self.send_header('Content-type','text/html')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()
      errmsg = """<html>
 <head>
  <title> 404 Not %s Found </title>
 </head>
 <body>
  <h1> %s Not Found </h1>
 </body>
</html>""" % (urlargs.path, urlargs.path)
      self.wfile.write(bytes(errmsg, "utf8"))
      return

#
# HACK ALERT:
#   The following was added after-the-fact to support the THS email notification statuses.
# This code should be moved to a general notification class.
#

  def do_POST(self):
    urlargs = urlparse(self.path)

    if urlargs.path == "/trigger":
      self.send_response(200)
      self.send_header('Content-type','application/json')
      self.send_header('Access-Control-Allow-Origin','*')
      self.end_headers()

      content_length = int(self.headers.get('Content-Length', 0))
      body = self.rfile.read(content_length)
      try:
        data = json.loads(body)
        uuid = data['uuid']
        trigger = data['trigger']
      except Exception as e:
        self.wfile.write(bytes(json.dumps({'error': str(e)}), "utf8"))
        return
      self.wfile.write(bytes(self.jsonTrigger(uuid, trigger), "utf8"))
      return

    else:
      self.send_response(404)
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write(bytes("Not Found", "utf8"))
      return


  def sendRabbitMsg(self, msg):
    """
       Send a generic rabbit message.
    """

    cred = pika.PlainCredentials('gea', 'gea')
    con  = pika.BlockingConnection( pika.ConnectionParameters('localhost', 5672, '/', cred))
    ch   = con.channel()

    msg  = json.dumps(msg)

    ch.exchange_declare(exchange='sysmon', exchange_type='fanout')
    ch.basic_publish(exchange='sysmon', routing_key='', body = msg)

    con.close()


  def log_message(self, format, *args):
    log.debug(format % args)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


if __name__ == '__main__':
  log.debug('Starting web server...')
  httpd = ThreadedHTTPServer(('127.0.0.1', 8080), WebInterface)
  log.debug('Running web server...')
  httpd.serve_forever()
