#!/usr/bin/env python3

import os
import sys
import time
from bisect import bisect_left
import Cache
import Monitor
import pika
import json
import smtplib
import io
import base64
from enum import Enum
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image, ImageDraw
from Cache import pvType
from datetime import datetime

import logging
log = logging.getLogger("sysmonII")

class MonitorException(Exception):
  """ Raised when a filter or trigger fails."""

class InsufficientData(Exception):
  """ Raised when there is not enough data for the operation."""

  def __init__(self, message):
    self.message = message

class State(Enum):
  UNINITIALIZED = 1
  NODATA        = 2	# Actually, insufficent data.
  OPERATIONAL   = 3


class Monitor:
  """
    There's one instance of these per monitor (line) on the gui. It contains the notification methods for that system. Each
  monitor has a reference to it's system instance.
  """

  def __init__(self, pvname, monconf):
    self.site     = os.environ['GEMINI_SITE'] if 'GEMINI_SITE' in os.environ else "MK"
    self.confdir  = os.environ['GEMINI_TOP']  if 'GEMINI_TOP'  in os.environ else "./"
    self.pvname   = pvname
    self.monconf  = monconf
    self.fltconf  = self.monconf['filter']
    self.filter   = self.unknownFilter
    self.fltsecs  = None
    self.fltcnt   = None
    self.doemail  = None
    self.message  = None			# If anything fails, put a message here (and trigger code will not be called). Else None
    self.fltval   = None			# If filtering succeeds, put value here (and call the trigger code). Else None
    self.trgconf  = monconf['trigger']
    self.trigger  = self.unknownTrigger
    try:
      self.options  = self.monconf['options']
    except:
      log.warn("OPTIONS FAIL %s" % monconf)
      raise
    self.system   = None			# Filled out by loadconfig. References system this is a monitor for
    self.cache	  = None			# Filled out by loadconfig. References cache of data this monitor is monitoring.
    self.config   = None			# Filled out by loadconfig.
    self.uuid     = None
    self.desc     = monconf['description']
    self.failed   = False
    self.state    = State.UNINITIALIZED
    self.geaurl   = None

    if not self.doemail: log.warn("NOT SENDING EMAIL\'S {0}".format(self.doemail))

    f = self.fltconf
    t = self.trgconf

    if 'average' in f:
      self.filter = self.averageFilter
      self.fltsecs, self.fltcnt = self.parseSpan(f['average'])
    elif 'median' in f:
      self.filter = self.medianFilter
      self.fltsecs, self.fltcnt = self.parseSpan(f['median'])
    elif 'slope' in f:
      self.filter = self.slopeFilter
      self.fltsecs, self.fltcnt = self.parseSpan(f['slope'])
    elif 'null' in f:
      self.filter = self.nullFilter
    elif 'bit' in f:
      self.filter = self.bitFilter 
      self.fltsecs, self.fltcnt = self.parseSpan(f['bit']) 
    else:
      self.filter = self.unknownFilter
      raise MonitorException("Unknown filter \"%s\"" % f, self.pvname)


    if ('high' in t) and ('low' in t):
      self.trigger = self.rangeTrigger
    elif 'low' in t:
      self.trigger = self.lowTrigger
    elif 'high' in t:
      self.trigger = self.highTrigger
    elif 'exact' in t:
      self.trigger = self.exactTrigger
    elif 'not' in t:
      self.trigger = self.notTrigger
    elif 'slope' in t:
      self.trigger = self.slopeTrigger
    elif 'null' in t:
      self.trigger = self.nullTrigger
    elif 'heartbeat' in t:
      self.trigger = self.heartbeatTrigger
    else:
      self.trigger = self.unknownTrigger
      raise MonitorException("Unknown trigger \"%s\" \"%s\"" % (t, self.pvname))



  def CheckAndNotify(self):
    """
      Main routine that filters, check for triggers, and if triggered, sends a notification.
    """
    
    if len(self.cache.values) == 0:	# Check if no data.
      self.message = "No data \"%s\"." % self.pvname
      raise InsufficientData(self.message)

    try:
      self.filter()
    except MonitorException as e:
      self.message = "Monitor Filter Exception \"%s\"." % e

    if self.fltval is None: return		# Not enough values yet, come back later.

    try:
      self.trigger()
    except MonitorException as e:
      self.message = "Monitor Trigger Exception \"%s\"." % e
    self.message = None




  def parseSpan(self, span):
    """
      Parse the value of a filter to determine the range of data. It
    can be either a time range or a number of samples range.
    """

    smpls = None
    secs  = None
    at, aa = span.split("=")
    aa = int(aa)

    if   'seconds' == at: secs  = aa
    elif 'minutes' == at: secs  = aa * 60
    elif 'hours'   == at: secs  = aa * 60 * 60
    elif 'samples' == at: smpls = aa
    elif 'num'  == at: smpls = aa
    else: pass

    log.debug("parseSpan %s %s %s" % (span, secs, smpls))
    return secs, smpls

  def bestfit(self, xs, ys):
    n = len(xs)
    xbar = sum(xs) / n
    ybar = sum(ys) / n

    numer = sum([xi * yi for xi, yi in zip(xs, ys)]) - n * xbar * ybar
    denum = sum([xi ** 2 for xi in xs]) - n * xbar ** 2

    if denum: return numer / denum
    return 0.0


  def getNumericSpan(self):
    """
      Get a span of numeric values in the cache depending on fltsecs
    or fltcnt for use by average and friends.
    """

    if self.fltsecs:
      values, timestamps = self.cache.getTimeSlice(time.time() - self.fltsecs)
    else:
      values, timestamps = self.cache.getSlice(self.fltcnt)

    if len(values) < 3:	# Need at least three datapoints to compute a sum/median/slope
      self.message = "Insufficient data acquired (%d < %d) for %s" % (len(values), 3, self.pvname)
      raise InsufficientData(self.message)

    return values, timestamps



  def averageFilter(self):
    values, timestamps = self.getNumericSpan() 

    self.fltval = sum(values) / len(values)
    log.debug("Average name %s count %d value %f" % (self.pvname, len(values), self.fltval))


  def bitFilter(self):
    self.fltval = (self.cache.values[-1] >> self.fltcnt) & 1
    log.debug("Bit name %s bit num %d value %f" % (self.pvname, self.fltcnt, self.fltval))



  def medianFilter(self):
    values, timestamps = self.getNumericSpan()

    dd = sorted(values)
    dl = len(values)

    if (dl & 1) == 1:
      self.fltval = dd[int(dl / 2)]          # Will return value in middle of sorted array.
    else:
      dl = int(dl / 2)
      self.fltval = (dd[dl - 1] + dd[dl]) / 2.0  # Return average of two values in middle.

    log.debug("Median name %s count %d value %f" % (self.pvname, len(values), self.fltval))





  def slopeFilter(self):
    # We can't use getNumericSpan for slope filter as it needs both the values and
    # the timestamps intact. In this case:

    values, timestamps = self.getNumericSpan()

    self.fltval = self.bestfit(timestamps, values)

    log.debug("Fit name %s count %d value %f" % (self.pvname, len(values), self.fltval))


  def nullFilter(self):
    if len(self.cache.values) == 0:
      self.message = "No data for %s" % self.pvname
      raise InsufficientData(self.message)
    ty = self.cache.type
  ##  if "TEST" in self.cache.pvname and ty != pvType.Integer and ty != pvType.Float and ty == pvType.Enum:		# Check if it's even plotable
  ##    print("nullFilter %s %f %f" % (self.cache.pvname, self.cache.values[0], self.cache.values[-1]))
    self.fltval = self.cache.values[-1]



  def unknownFilter(self):
    raise MonitorException("Unknown filter")



  def rangeTrigger(self):
    self.notify((self.fltval <= self.trgconf['low']) or (self.fltval >= self.trgconf['high']))

  def lowTrigger(self):
    self.notify(self.fltval <= self.trgconf['low'])

  def highTrigger(self):
    self.notify(self.fltval >= self.trgconf['high'])

  def slopeTrigger(self):
    self.notify(self.fltval >= self.trgconf['high'])

  def nullTrigger(self):			# Always succeds
    return

  def exactTrigger(self):
    self.notify(self.fltval == self.trgconf['exact'])
    log.debug("exact %s %s" % (self.fltval, self.trgconf))
    pass

  def notTrigger(self):
    self.notify(self.fltval != self.trgconf['not'  ])
    log.debug("not %s %s" % (self.fltval, self.trgconf))
    pass

  def heartbeatTrigger(self):
    self.failed = False
    log.debug("heartbeat %s %s" % (self.fltval, self.trgconf))
    pass

  def unknownTrigger(self):
    self.failed = False
    log.debug("Unknown Trigger %s %s" % (self.fltval, self.trgconf))

  def notify(self, failed):

    if failed == self.failed:
      return						# Do noting if no change
    self.failed = failed

    # Debugging...
    if failed == False:                 log.info("NO EMAIL because it didn't fail %s" % self.pvname)
    if self.doemail == False:           log.info("NO EMAIL all email is disabled in the config file %s" % self.pvname)
    if 'noAlarm' in self.options:       log.info("NO EMAIL because this monitor has noAlarm set %s" % self.pvname)
    if self.system.emailenable == None: log.info("NO EMAIL because emails disabled for this system from the webpage %s" % self.pvname)
    if self.system.notify == None:      log.info("NO EMAIL because the notify list is empty %s" % self.pvname)

    if ( failed                           and
         self.doemail == True             and
         'noAlarm' not in self.options    and
         self.system.notify               and
         self.system.emailenable):

      msg = MIMEMultipart('alternative')
      msg['Subject'] = "sysMon: Triggered for %s" % self.cache.pvname
      msg['From']    = 'noreply@gemini.edu'
      msg['To']      = self.system.notify.replace(" ", ", ")
      report  = "<html>\n"
      report += " <body>\n"
      report += "  <h1> System Monitor Triggered </h1>\n"
      report += "    <p> If you resolved this and re-enabled the alarm, or this appears to be a serious issue, please reply to ths email with a summary of your findings. Another alert will be sent every 15 minutes until this issue is acknowledged. To acknowledge this alert, go to sysmon and click the Acknowledge button next to the affected system. </p>"
      report += "  <table>"
      report += "   <tr>"
      report += "    <td> system:  <td> %s" % self.system.sysname
      report += "   <tr>"
      report += "    <td> pv:      <td> <a target=\"_parent\" href=\"%s\">%s</a>" % (self.geaurl, self.pvname)
      report += "   <tr>"
      report += "    <td> value:   <td> %s" % self.fltval
      report += "   <tr>"
      report += "    <td> filter:  <td> %s" % self.fltconf
      report += "   <tr>"
      report += "    <td> trigger: <td> %s" % self.trgconf
      report += "   <tr>"
      report += "    <td> time stamp: <td> %s" % datetime.now()

      report += "  </table>"
      report += " </body>\n"
      report += "</html>\n"
      msg.attach(MIMEText(report, 'html'))

      self.system.acknowledge = True
      while self.system.acknowledge:
        for N in range(1, 5):					# Try four times to send the email. See FR-72397
          try:
            s = smtplib.SMTP('hbfsmtprelay-lv1')
            s.send_message(msg)
            s.quit()
            # self.system.emailenable = False			# Disable alerts for this system
            log.info("EMAIL SENT {0} {1}".format(msg['To'], self.pvname))
            break							# Send successful, done.
          except:
            log.info("EMAIL SEND FAILED {0} Retry: {1}".format(msg['To'], self.pvname, N))
            time.sleep(2)

        for M in range(900 // 30): #Check every 30 seconds for 15 minutes
          if not self.system.acknowledge:
            break
          time.sleep(5)


      #Once out of the while loop, it means the alert has been acknowledged. Send another email to let people know
      msg2 = MIMEMultipart('alternative')
      msg2['Subject'] = "sysMon: Acknowledged for %s" % self.cache.pvname
      msg2['From']    = 'noreply@gemini.edu'
      msg2['To']      = self.system.notify.replace(" ", ", ")
      report2  = "<html>\n"
      report2 += " <body>\n"
      report2 += "  <h1> System Monitor Acknowledged</h1>\n"
      report2 += "    <p> The alert has been acknowledged. </p>"
      report2 += " </body>\n"
      report2 += "</html>\n"
      msg2.attach(MIMEText(report2, 'html'))
      
      for N in range(1, 5):
        try:
          s = smtplib.SMTP('hbfsmtprelay-lv1')
          s.send_message(msg2)
          s.quit()
          log.info("EMAIL SENT {0} {1}".format(msg2['To'], self.pvname))
          break							# Send successful, done.
        except:
          log.info("EMAIL SEND FAILED {0} Retry: {1}".format(msg2['To'], self.pvname, N))
          time.sleep(2)
          



    msg = {"type":    "alert",
           "failed":  failed,				# Build up rabbitmq msg
           "system":  self.system.sysname,
           "pv":      self.pvname,
           "value":   self.fltval,
           "filter":  self.fltconf,
           "trigger": self.trgconf }

    try:
      cred = pika.PlainCredentials('gea', 'gea')
      con  = pika.BlockingConnection( pika.ConnectionParameters('localhost', 5672, '/', cred))
      ch   = con.channel()
    except:
      try: con.close()	# Make half-hearted attempt to close just in case.
      except: pass
      log.info("IPC MSG SEND FAILED {0} {1}".format(msg['To'], self.pvname))
      return	# No network, nothing we can do.

    msg  = json.dumps(msg)

    ch.exchange_declare(exchange='sysmon', exchange_type='fanout')
    ch.basic_publish(exchange='sysmon', routing_key='', body = msg)

    con.close()




  def getPlot(self):
    ty = self.cache.type

    if ty != pvType.Integer and ty != pvType.Float and ty == pvType.Enum:		# Check if it's even plotable
      log.debug("TYtytytyty %s" % ty)
      return None

    width  = 400.0
    height = 100.0
    margin = 5.0		# 5 pixel margin
    widthM  = width  - margin * 2
    heightM = height - margin * 2
    img = Image.new("RGB", (int(width), int(height)), color="lightgreen")
    d   = ImageDraw.Draw(img)
    ct  = time.time()





    if 'null' in self.fltconf:
        values, timestamps = self.cache.getTimeSlice(ct - 60 * 5)		# Just show five minutes worth.
        v,      t,         = self.cache.getTimeSlice(ct - 60 * 4)
    else:
      if self.fltsecs:
        values, timestamps = self.cache.getTimeSlice(ct - int(self.fltsecs * 1.5))
        v,      t,         = self.cache.getTimeSlice(ct - int(self.fltsecs      ))
      else:
        if self.fltcnt == None: return None
        values, timestamps = self.cache.getSlice(int(self.fltcnt * 1.5))
        v,      t,         = self.cache.getSlice(int(self.fltcnt      )) 

    if len(values) <= 2: return None




    # Draw a rectangle behind where the actual filtered data is plotted.

    if ('high' in self.trgconf) and ('low' in self.trgconf):	# Range
      xscale  = widthM / (ct - timestamps[0]) 	     		# Number of seconds per pixel e.g.  1000 seconds / 400 pixels  - 2.5 seconds / px
      xoffset = -timestamps[0]

      Mn = min(min(values), self.trgconf['high'], self.trgconf['low'])
      Mx = max(max(values), self.trgconf['high'], self.trgconf['low'])

      yscale  = heightM / (Mx - Mn)
      yoffset = -Mn

    elif 'high' in self.trgconf:
      xscale  = widthM / (ct - timestamps[0]) 	     		# Number of seconds per pixel e.g.  1000 seconds / 400 pixels  - 2.5 seconds / px
      xoffset = -timestamps[0]

      Mn = min(min(values), self.trgconf['high'])
      Mx = max(max(values), self.trgconf['high'])

      yscale  = heightM / (Mx - Mn)
      yoffset = -Mn

    elif 'low' in self.trgconf:
      xscale  = widthM / (ct - timestamps[0]) 	     		# Number of seconds per pixel e.g.  1000 seconds / 400 pixels  - 2.5 seconds / px
      xoffset = -timestamps[0]
      Mn = min(min(values), self.trgconf['low'])
      Mx = max(max(values), self.trgconf['low'])

      yscale  = heightM / (Mx - Mn)
      yoffset = -Mn

    else:
      xscale  = widthM / (ct - timestamps[0]) 	     		# Number of seconds per pixel e.g.  1000 seconds / 400 pixels  - 2.5 seconds / px
      xoffset = -timestamps[0]
      Mn = min(values)
      Mx = max(values)

      yscale  = heightM / (Mx - Mn)
      yoffset = -Mn

    d.rectangle([(int(((t[0] + xoffset) * xscale) + margin + .5), 1), (width - 2, height - 2)], fill="lightblue")





    # Draw high and/or low bars.

    l = []

    if 'high' in self.trgconf:
      # Mx = max(max(values), self.trgconf['high'])
      Mx = self.trgconf['high']
      Mx = int(height - ((Mx + yoffset) * yscale) - margin + .5)
      l += ((        margin, Mx),)
      l += ((width - margin, Mx),)
      d.line(l, fill="blue")

    l = []

    if 'low' in self.trgconf:
      # Mn = min(min(values), self.trgconf['low'])
      Mn = self.trgconf['low']
      Mn = int(height - ((Mn + yoffset) * yscale) - margin + .5)
      l += ((        margin, Mn),)
      l += ((width - margin, Mn),)
      d.line(l, fill="red")






    l = []

    for v, ts in zip(values, timestamps):
      x = int(         ((ts + xoffset) * xscale) + margin + .5)
      y = int(height - ((v  + yoffset) * yscale) - margin + .5)
      l += ((x, y),)

    d.line(l, fill="black")

    imBytArr = io.BytesIO()
    img.save(imBytArr, format='PNG', optimize=True)
    img.close()

    return "data:image/png;base64," + base64.b64encode(imBytArr.getvalue()).decode()

