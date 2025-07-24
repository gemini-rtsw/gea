#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import pika
import signal
import datetime
from dateutil.parser import parse
from pygtail import Pygtail


class arm:
  match     = None
  armed     = False
  stop      = -1
  count     = 0
  comment   = ""
  triggers  = []
  
class trg:
  match     = None
  comment   = ""
  action    = None
  timestamp = 0

class stats:
  count     = 0
  matches   = 0
  timestamp = time.time()




class watcher:

  def __init__(self):
    self.doemail = True
  
    self.site       = os.environ['GEMINI_SITE'] if 'GEMINI_SITE' in os.environ else "MK"
    self.confdir    = (os.environ['GEMINI_TOP']  if 'GEMINI_TOP'  in os.environ else "/tmp") + "/"
    self.offsetpath = "/tmp/offsets/"
    self.reload     = False
    self.verbose    = 9
    self.ph         = {}

    self.logf = open(self.confdir + "/var/log/gea/watcher.log", "a")
    self.log(0, "Log started")

    self.readconfig()

    with open("/var/run/watcher/watcher.pid", "w") as f:
        f.write("%d\n" % os.getpid())

    self.stats   = {}
    self.history = {}
    for id in self.watchers:
      self.stats[id] = stats()
      self.history[id] = []


  def log(self, level, msg):

    if level > self.verbose: return

    logd = datetime.datetime.now().strftime("%m/%d/%y %H:%M:%S ")
    self.logf.write(logd + msg + "\n")
    # print(logd + msg)
    self.logf.flush()



  def sighandler(self, signum, frame):
    self.log(3, "Signal handler called with signal %d" % signum)
    if signum == signal.SIGINT:
      self.log(0, "Quiting due to SIGINT")
      sys.exit(0)
    elif signum == signal.SIGUSR1:
      self.log(3, "Reloading configuration (SIGUSR1)")
      self.reload = True	# Do the actual reload while lines are not being matched.
    elif signum == signal.SIGUSR2:
      self.log(3, "Dumping statistics (SIGUSR2)")
      self.showstats()

  signal.signal(signal.SIGINT,  sighandler)
  signal.signal(signal.SIGUSR1, sighandler)
  signal.signal(signal.SIGUSR2, sighandler)


#
# Print a 2d list as a pretty column'd table.
#

  def columnate(self, p, x):

    w = [max(map(len, col)) for col in zip(*x)]

    for r in x:
      self.log(p, "   " + "  ".join((v.ljust(w) for v, w in zip(r, w))))




  def showstats(self):
    import math

    self.log(0, "Watcher Statistics")
    self.log(0, "Current logging level %d." % self.verbose)
    self.log(0, "Email notifications %s." % ("enabled" if self.doemail else "disabled"))
    self.log(0, "Email frequency is %s seconds." % self.emailfreq)

    # Wierd math is just to form columns. Add .01 because math.log10(0) won't work. Ljust() is ok w/ -numbers
    idsW  = max(len(i) for i in self.watchers) + 2
    cntsW = int(math.log10(max(self.stats[i].count   for i in self.watchers)  + .01) + 2)
    mtchW = int(math.log10(max(self.stats[i].matches for i in self.watchers)  + .01) + 2)

    x = [["Id", "Count", "Matches", "Timestamp"]]

    for id in self.watchers:
      x.append([id, "%d" % self.stats[id].count, "%d" % self.stats[id].matches, "%f" % self.stats[id].timestamp])

    self.columnate(0, x)

    for id in self.watchcache:
      self.log(0, "id: " + id)
      for arm in self.watchcache[id]:
        self.log(0, "    arm.match:   " + arm.match)
        self.log(0, "    arm.armed:   " + arm.armed.__str__())
        self.log(0, "    arm.stop:    %d" % arm.stop)
        self.log(0, "    arm.count:   %d" % arm.count)
        self.log(0, "    arm.comment: " + arm.comment)
        for trg in arm.triggers:
          self.log(0, "        trg.match:   " + trg.match.__str__())
          self.log(0, "        trg.comment: " + trg.comment)
          self.log(0, "        trg.action:  " + trg.action.__str__())



  def readconfig(self):
    """
       Read the json format configuration file into a more runtime
    compatable format.

    """
  
    with open(self.confdir + "etc/gea/watcher/watcher.json", "r") as f:
      self.watcherconf = json.load(f)
  
    self.watchers  = self.watcherconf['watchers']
    self.groups    = self.watcherconf['groups']
    self.verbose   = self.watcherconf['verbose']
    self.doemail   = self.watcherconf['doemail']
    self.emailfreq = self.watcherconf['emailfreq'] * 60
  
  # Create a cache for quick look up while receiving loglines.
  
    self.watchcache = {}

    watchers = self.watchers
    groups   = self.groups
    
    for id in watchers:
      watchers[id]['errmsg'] = False
      arms = []
      for w in watchers[id]['watches']:
        trgs = []
        if 'triggers' in w:
          for ts in w['triggers']:
            t = trg()
            t.match   = ts['match']
            t.count   = 0
            t.comment = ts['comment'] if 'comment' in ts else ""
            t.action  = ts['action']
            trgs += (t, )
        else:
          t = trg()
          t.match   = None
          t.comment = w['comment'] if 'comment' in w else ""
          t.action  = w['action']
          trgs += (t, )
        a = arm()
        a.comment  = w['comment'] if 'comment' in w else ""
        a.match    = w['match']
        if t.match: a.stop = w['stop']	# a.stop only if there's a trigger
        a.armed    = False
        a.triggers = trgs
        arms += (a, )
      for g in watchers[id]['groups']:
        for w in groups[g]:
          trgs = []
          if 'triggers' in w:
            for ts in w['triggers']:
              t = trg()
              t.match   = ts['match']
              t.count   = 0
              t.comment = ts['comment'] if 'comment' in ts else ""
              t.action  = ts['action']
              trgs += (t, )
          else:
            t = trg()
            t.match   = None
            t.comment = w['comment'] if 'comment' in w else ""
            t.action  = w['action']
            trgs += (t, )
          a = arm()
          a.comment  = w['comment'] if 'comment' in w else ""
          a.match    = w['match']
          if t.match: a.stop = w['stop']	# a.stop only if there's a trigger
          a.armed    = False
          a.triggers = trgs
          arms += (a, )
    
      self.watchcache[id] = arms


  



  def action(self, id, match, trigger, comment, line):
    """
       Take appropriate configured action when there's a match.
  
    """
    action = trigger.action
    self.stats[id].matches += 1

    # print("ACTION:", id, match, trigger, comment, line)

    if 'email' in action:

      time_since_last_email = time.time() - trigger.timestamp

      # self.log(1, "%s: EMAIL DELAY %f %s %s %s" %
      #     (id, time_since_last_email, comment, action['email'], line))

      if time_since_last_email < self.emailfreq:
        self.log(1, "%s: Email not sent due to email frequency setting %f %s %s %s" %
          (id, time_since_last_email, comment, action['email'], line))
      else:
  
        trigger.timestamp = time.time()

        if not self.doemail:
          self.log(1, "%s: NOMAIL %s %s %s" % (id, comment, action['email'], line))
        else:
  
          import smtplib
          from email.mime.multipart import MIMEMultipart
          from email.mime.text import MIMEText
  
          msg = MIMEMultipart('alternative')
          if comment:
            msg['Subject'] = "WATCHER %s: Triggered on \"%s\"" % (id, comment)
          else:
            msg['Subject'] = "WATCHER %s: Triggered on \"%s\"" % (id, match)
          msg['From']    = 'noreply@gemini.edu'
          msg['To']      = ", ".join(action['email'])
          report  = "<html>\n"
          report += " <head> Watcher Alert </head>\n"
          report += " <body>\n"
          report += "  <h1> %s log watcher triggered.</h1>\n" % id
          report += "  <pre>\n"
          if comment:
            report += "Comment:          %s.\n" % comment
          report += "Trigger:        \"%s\"\n" % match
          report += "Offending line: \"%s\"\n" % line
          report += "Logfile:        \"%s\"\n" % self.watcherconf['watchers'][id]['pathname']
          report += "\n"
          report += "History:"
          for n in self.history[id]:
            report += "    " + n + "\n"
          report += "\n"
          report += "  </pre>\n"
          report += " </body>\n"
          report += "</html>\n"
          msg.attach(MIMEText(report, 'html'))
          s = smtplib.SMTP('hbfsmtprelay-lv1')
          s.sendmail('noreply@gemini.edu', action['email'], msg.as_string())
          s.quit()
          self.log(1, "%s: Email sent" % id)
    if 'log' in action:
      self.log(0, "%s: %s %s %s" % (id, comment, action['log'], line))
    if 'msgq' in action:
      credentials = pika.PlainCredentials('gea', 'gea')
      connection = pika.BlockingConnection( pika.ConnectionParameters('localhost', 5672, '/', credentials))
      channel = connection.channel()
      channel.exchange_declare(exchange='watcher', exchange_type='fanout')
      message = {"id":id, "match":match, "commment":comment, "line":line}
      channel.basic_publish(exchange='watcher', routing_key='', body=json.dumps(message))
      connection.close()

  



  def watch(self, id, line):
    """
       Match line with watchers[id] match entries. If there is a match,
    take configured action.
    """
  
    if id not in self.watchcache: return

    # print("WATCH %s" % line)
  
    for arm in self.watchcache[id]:
      if arm.armed:
        for trg in arm.triggers:
          if trg.match in line:
            self.log(4, "%s: Triggered when armed on \"%s\" then triggered on \"%s\"." % (id, arm.match, trg.match))
            self.log(5, "%s: Triggered comment \"%s\"." % (id, trg.comment))
            self.log(5, "%s: The offending line was \"%s\"." % (id, line))
            self.log(5, "%s: Triggered action %s" % (id, trg.action))
            self.action(id, trg.match, trg, trg.comment, line)
            arm.armed = False
          else:
             arm.count += 1
             if arm.count >= arm.stop:
               arm.count = 0
               arm.armed = False
               self.log(2, "%s: Trigger aborted due to linecount exceeded (\"%s\"->\"%s\", %d)." \
                  % (id, arm.match, trg.match, arm.stop))
      elif arm.match in line:
        if arm.triggers[0].match:
          arm.armed = True
        else:
          self.log(4, "%s: Immediate trigger on \"%s\"." % (id, arm.match))
          self.log(4, "%s: The offending line was \"%s\"." % (id, line))
          self.log(5, "%s: Immediate trigger comment %s" % (id, arm.comment))
          self.action(id, arm.match, arm.triggers[0], arm.comment, line)








  def run(self):

    """
       Top level routine to handle walking through all log files,
    attempting to pull newly written lines from each, and passing each
    line to watch(..)  that will handle matching the lines and handling
    match actions.

    """

    while True:
      for id in self.watchers:
        fn = self.watcherconf['watchers'][id]['pathname']	# The logfile
        lt = self.watcherconf['watchers'][id]['logtype']	# How to read lines (handle log rotation, etc.)

        if not os.path.isfile(fn):				# "Never" happens, but could.
          if self.watcherconf['watchers'][id]['errmsg']:
            continue						# Don't repeat the error message
          self.log(5, "File not found: \"%s\"." % fn)
          self.watcherconf['watchers'][id]['errmsg'] = True
          continue
        if lt == 'perle': tailer = self.logtype_perle		# Get generator for logtype
        else:             tailer = self.logtype_default
        for line in tailer(id, fn):				# Read out all new lines
          line = line.strip()
          self.history[id].append(line)				# Save in logline history.
          if len(self.history[id]) > 10: self.history[id].pop(0)# / but limit history size.
          self.stats[id].count += 1				# Keep statisics, dumped by SIGUSR2
          self.stats[id].timestamp = time.time()		# /
          self.watch(id, line)					# Actually do the matching
      time.sleep(5)						# Poll once per 5 seconds.
      if self.reload:						# Reload configuration file when SIGUSR1 received.
        self.readconfig()
        self.reload = False





  def logtype_default(self, id, pathname):

    """
       Generator for unconfigured (or unknown) log types. Simply emulates,
    "tail -f".

    """

    of = self.offsetpath + id + ".offset"
    try:
      for line in Pygtail(pathname, offset_file = of, read_from_end = True, every_n = 100):
        yield(line.strip())
    except:
      self.log(1, "Trash in: \"%s\"." % pathname)



  def logtype_perle(self, id, pathname):

    """
       Generator for lines logged by Perle's that get log-turned by
    script on pisces.

    """

    class perle:
      fh       = None
      filesize = 0			# Filesize
      newsize  = 0			# For checking for file size change (i.e., new logdata)
      filepos  = 0			# Our current position in the file

    # If no metadata, create some on open

    if id not in self.ph:
      pd = perle()
      self.ph[id] = pd

      try:    pd.fh = open(pathname, "r", errors="ignore")
      except: return

      pd.fh.seek(0, 2)			# Start at the end of the file
      pd.filesize = os.stat(pathname).st_size
      pd.filepos  = pd.filesize

    else:
      pd = self.ph[id]

    def parsedate(line):
      """ Return unixtimestamp parsed from the log message. Used to verify it's not a duplicate """
      try:

        d = re.match("<([\/\w\s:]*)>", line)
        if d != None: return parse(d.group(1), fuzzy = True).timestamp()

        d = re.match("(^[\w\s:]*) : ", line)
        if d != None: return parse(d.group(1), fuzzy = True).timestamp()
        
        d = re.match("^(\w\w\w\s\w\w\w\s+\d\s+[\d:]+\s+\d+)\s", line)
        if d != None: return parse(d.group(1), fuzzy = True).timestamp()
        
        return parse(line, fuzzy = True).timestamp()
      except:
        self.log(2, "Parsing date failed \"%s\"" % line)
        return 0	# Will force line to be dropped.
     
  
    # self.log(5, "%s: Start line scan: %s %d" % (id, pathname, pd.filepos))

    while True:
      pd.newsize = os.stat(pathname).st_size
      # print("MMM", pathname, pd.newsize, pd.filesize)
      if pd.newsize > pd.filesize:				# New size is larger, new log messages(s) written.
        # print("New loglines written", pd.newsize, pd.filesize)
        break;
      elif pd.newsize < pd.filesize:				# New size is smaller, logfile rotated.
        # print("Logfile rotated", pd.newsize, pd.filesize)
        pd.fh.seek(0, 0)					# Start at the start of the file.
        break;
      else:							# No filesize change, wait and loop.
        return None						# No filesize change, give up.

    pd.filesize = pd.newsize
      
    # At this point there s/b at least one line in the logfile. Read
    # (i.e., yield) up to 200 hundred new lines. This limit will give other
    # logfiles a chance to be read.
    for i in range(0, 200):
      # print("XXm", i)
      # line = pd.fh.readline().strip()
      line = pd.fh.readline()
      line = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', line)		# Remove control characters.
     
      # print("XXX", i)
      if len(line):
        # self.log(6, "LINE: %s %s" % (id, line))
        lndt = parsedate(line)			# Parse the date
        if lndt == None: continue		# Line had no date, skip.
        self.log(6, "%s: Current time %f, logtime %f" % (id, lndt, time.time()))
        if (time.time() - lndt) > 300:	# Allow log messages from the future
          self.log(5, "%s: Message too old: %s" % (id, line))
          continue				# Line timestamp is outside threshold, skip.
        # self.log(6, "LN %s: %s" % (id, line))
        yield(line)
      else:
        self.log(6, "LN %s done" % id)
        break
      pd.filepos = pd.fh.tell()

    self.log(6, "%s: End line scan" % (id))
    return None



if __name__ == '__main__':
  w = watcher()
  w.run()
