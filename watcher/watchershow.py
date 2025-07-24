#!/usr/bin/env python

import os
import json
import html
# import random

GEA_CONF=os.getenv("GEA_CONF", "/gemsoft/etc/gea")
WATCHER_CONF=GEA_CONF + "/watcher/watcher.json"

class dumpWatcherConfig():
  
  def __init__(self):
  
    with open(WATCHER_CONF) as cfgfile:
      self.watchcfg = json.load(cfgfile)
      self.t        = html.table(clas="wtable")
      self.indent   = 0						# Counter for indentation inside table.
      self.altcntr  = 0


  
  def dumpitem(self, lst, name, altname = None):
    if name in lst and lst[name] != None:
      if   isinstance(lst[name], list): v = "&nbsp;".join(lst[name])
      elif isinstance(lst[name], dict): v = "&nbsp;".join(lst[name])
      elif isinstance(lst[name], int):  v = "&nbsp;%d" % lst[name]
      else:                             v = lst[name]
      n = altname if altname else name
  
      r = self.t.row(clas = self.clas)
      r.col(("&nbsp;" * self.indent * 4) + n + ": " + v)

  
  
  def dumpwatchers(self, watchers):
  
    t = self.t
  
    alt = 0
  
    for gmp in watchers:
  
      # if alt & 1: style  = "background:beige;"
      # else:       style  = "background:cornsilk;"
      if alt & 1: self.clas  = "mclrB"
      else:       self.clas  = "mclrA"
      alt += 1
  
      self.indent = 1
  
      if 'triggers' in gmp: m = "arm: \""
      else:                 m = "match: \""

      m  = "&nbsp;" * self.indent * 4 + m + gmp['match'] + "\""
      # m += "<span style=\"float:right;\" id=\"pickles\"> %d </span>"  % random.randint(0, 10)
      r = t.row(clas=self.clas)
      r.col(m)
  
      self.dumpitem(gmp, 'arm')
      self.dumpitem(gmp, 'stop')
      self.dumpitem(gmp, 'comment')
      self.dumpitem(gmp, 'C', "hidden comment")
  
      if 'action' in gmp:
        r = t.row(clas=self.clas)
        r.col(("&nbsp;" * self.indent * 4) + "actions: ")
        self.indent = 2
        for actn in gmp['action']:
          self.dumpitem(gmp['action'], actn)

      if 'triggers' in gmp:
        r = t.row(clas=self.clas)
        r.col("&nbsp;" * self.indent * 4 + "triggers:")
        for tgr in gmp['triggers']:
          self.indent = 2
          m  = "&nbsp;" * self.indent * 4 + "match: \"" + tgr['match'] + "\""
          # m += "<span style=\"float:right;\" id=\"pickles\"> %d </span>"  % random.randint(0, 10)
          r = t.row(clas=self.clas)
          r.col(m)
          self.indent = 3
          if 'action' in tgr:
            self.indent = 4
            for actn in tgr['action']:
              self.dumpitem(tgr['action'], actn)

  
  
  def dumpconfig(self):  

    watchcfg = self.watchcfg

    m = """  <style>
   .wtable, .wth, .wtd {
    border: 1px solid white;
   }
   .mclrA {
    background:beige;
   }
   .mclrB {
    background:#e0f0e0;
   }
  </style>
"""

    #
    # Show quick links at top.
    # 
  
    r = self.t.row(heading = True)

    m += "\n     <center>\n"
    for p in watchcfg['groups']:
      p = p.upper()
      m += "      <a href=\"#%s\">%s</a>&nbsp;\n" % (p, p)
    m += "     </center>\n   "
    r.col(m, style = "background:#e0ffe0")
  
    m = "\n     <center>\n"
    for p in watchcfg['watchers']:
      p = p.upper()
      m += "      <a href=\"#%s\">%s</a>&nbsp;\n" % (p, p)
    m += "     </center>\n   "
    r.col(m, style = "background:#e0ffe0")
  
    #
    # Show global settings
    #
  
    r = self.t.row(heading = True)
    r.col("Settings:", style = "background:#e0e0ff")
  
    verbose   = watchcfg['verbose']
    r = self.t.row()
    r.col("Verbosity", style = "background:#e0e0ff")
    r.col(verbose.__str__(), style = "background:#e0e0ff")
  
    doemail   = watchcfg['doemail']
    r = self.t.row()
    r.col("Enable&nbsp;sending&nbsp;email", style = "background:#e0e0ff")
    r.col(doemail.__str__(), style = "background:#e0e0ff")
  
    emailfreq   = watchcfg['emailfreq']
    r = self.t.row()
    r.col("Maximum email frequency", style = "background:#e0e0ff")
    r.col(emailfreq.__str__(), style = "background:#e0e0ff")
  
  
    #
    # Show group watch config.
    #
  
    r = self.t.row(heading = True)
    r.col("<center>Watch groups</center>", style = "background:salmon;")
  
    for p in watchcfg['groups']:
      r = self.t.row()
      r.col("<a name=\"%s\">%s</a>" % (p.upper(), p.upper()), style = "background:darksalmon;")
      self.dumpwatchers(watchcfg['groups'][p])
  
    r = self.t.row(heading = True)
    r.col("<center>Watchers</center>", style = "background:salmon;")
  
  
    #
    # Show individual watch configurations.
    #
  
    for w in watchcfg['watchers']:
      wchr = watchcfg['watchers'][w]
  
      r = self.t.row(heading = True)
      r.col("<a name=\"%s\">%s</a>" % (w.upper(), w.upper()), style = "background:darksalmon;")
  
      r = self.t.row()
      r.col("groups", style = "background:bisque;")
      r.col(" ".join(wchr['groups']), style = "background:bisque;")
  
      r = self.t.row()
      r.col("logfile pathname", style = "background:bisque;")
      r.col(wchr['pathname'], style = "background:bisque;")
  
      r = self.t.row()
      r.col("logfile type", style = "background:bisque;")
      r.col(wchr['logtype'], style = "background:bisque;")
  
      self.dumpwatchers(wchr['watches'])

    return self.t.show(margin = 2, indent = 1)
  


if __name__ == '__main__':
  dWC = dumpWatcherConfig()
  dWC.indent = 1
  dWC.altmargin = 4

  print("""Content-type: text/html

<!DOCTYPE html>
<html>
 <head>
  <title> Watcher Configuration Viewer </title>
  <style>
   table {
    border-collapse: collapse;
   }
   table, th, td {
    border: 2px solid white;
   }
   .mclrA {
    background:beige;
   }
   .mclrB {
    background:#e0f0e0;
   }
  </style>
 </head>
 <body>
""")
  
  print(dWC.dumpconfig())

  print(" </body>")
  print("</html>")

