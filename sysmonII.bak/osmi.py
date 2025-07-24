#!/usr/bin/env python3

import re
import sys
import time
import json
import glob

foo = {}

all = {}
all['verbose']   = 4
all['doemail']   = False
all['emailfreq'] = 60

systems = {}

for fn in glob.glob("/gemsoft/etc/gea/sysMon/MK/*.config"):
  system = re.findall(r'\/([a-zA-Z0-9]+?)\.', fn)[0]
  with open(fn, "r") as f:
    sysopts = {}
    sysmons = []
    for line in f.readlines():
      line = line.strip()
      if len(line) < 2: continue
      if line.startswith("#"): continue
      if line.startswith(" "): continue
      if line.startswith("	"): continue

      #
      # Pull out global options for this system, namely email list and comments.
      #

      if line.startswith("["):
        opt = re.findall(r'\[(.+?)\]', line)
        if not len(opt): continue
        # print("OOOOOOOOO", opt[0].split("=", 1))
        name, value = opt[0].split("=", 1)
        sysopts[name] = value
        continue

      #
      # Extract the first four fields (pvname, exact, min, max)
      #

      config = line.split(None, 4)
      pvname = config[0]
      exact  = config[1]
      mini   = config[2]
      maxi   = config[3]

      #
      # Parse the remainder of the line len(config) > 4
      #

      opts   = []
      if len(config) > 4:

        #
        # Check if there's a decription at the end, prior to optional arguments
        # Description is always in double quotes.

        desc = re.findall(r'\"(.+?)\"', config[4])
        if len(desc): desc = desc[0]
        else:         desc = ""

        #
        # Parse the options.
        #

        opt = re.findall(r'\[(.+?)\]', config[4])
        if len(opt):
          opt = opt[0]
          oS   = {}
          filt = {}
          for o in opt.split(", "):
            # print("Option X%sX %s" % (opt, o.split("=")))
            # opts.append(o.split("="))
            oo = o.split("=")
            if len(oo) == 1:
              oS[oo[0]] = True
            else:
              oS[oo[0]] = oo[1]

          #
          # Build up triggers and filters
          #

          if 'median' in oS:
            filt['median'] = "samples=" + oS['median']
            oS.pop('median')

          if 'average' in oS:
            filt['average'] = "samples=" + oS['average']
            oS.pop('average')

          # oS['noAlarm'] = 'noAlarm' in oS
          # if 'noAlarm' in oS: oS.pop('noAlarm')

          if not len(filt): filt = {'null':True}
        else:
          oS = None
          filt = {'null':True}
          trigger = {'null':True}
        if exact is '-':
          trigger = {}
          try: trigger['low' ] = float(mini)
          except: pass
          try: trigger['high'] = float(maxi)
          except: pass
        else:
          if oS and 'not' in oS:
            oS.pop('not')
            try:
              trigger = {'not':int(exact)}
            except:
              try:
                trigger = {'not':float(exact)}
              except:
                trigger = {'not':exact}
          else:
            try:
              trigger = {'exact':int(exact)}
            except:
              try:
                trigger = {'exact':float(exact)}
              except:
                trigger = {'exact':exact}

      sysmons.append({'pvname':pvname, 'description':desc, 'filter':filt, 'trigger':trigger, 'options':oS})
    # print()
    # print()
    # print("XXX%sXXX" % system)
    # print(json.dumps(sysmons, indent = 1))
    # print()
    # print("YYYY")
    # print(json.dumps(sysopts, indent = 1))
  systems[system] = {}
  if 'emails'  in sysopts: systems[system]['notify']  = sysopts['emails']
  if 'comment' in sysopts: systems[system]['comment'] = sysopts['comment']
  systems[system]['monitor'] = sysmons

all['systems'] = systems
print(json.dumps(all, indent = 1))


      # print("values", pvname, desc, oS, trigger)
    #print("system", system, sysopts)
      # else: print(config)
  # print(json.dumps(sysopts, indent = 1))
  #print(json.dumps(sysmons, indent = 1))

"""
[emails=aebbers@gemini.edu tcumming@gemini.edu jwhite@gemini.edu stephens@gemini.edu ssanorth@gemini.edu gnqc@gemini.edu shardash@gemini.edu cyamasaki@gemini.edu nmasuda@gemini.edu etapia@gemini.edu lcatala@gemini.edu]

ao:temp1.VAL                -   -0.3   10    "DM temp"  [median=75, noAlarm]
ao:temp2.VAL                -	 0     17    "Heat Exchanger Air Inlet" [median=75]
ao:wfcs:getStatus4.VALL     -	-29    -5    "WFS"   [median=5]
ao:wfcs:getStatus4.VALM     -	-15.0  21.0  "WFS Controller"  [median=5]
ao:strapDevStatus.VALF      -	-13    -7    "STRAP Temperature"   [noAlarm, median=75]
sfo:ccdTemp                 -	-45    -35   "SFO CCD Temperature" [median=75]
ao:wfcs:xPatchIn            -   -0.1   0.5   "X Patch"   [noAlarm, query=LAPSE=lastWeek&YMIN=-0.1&YMAX=0.6]
ao:wfcs:yPatchIn            -   -0.55  -0.3  "Y Patch"   [noAlarm, query=LAPSE=lastWeek&YMIN=-0.6&YMAX=-0.1]
altairgate.existTestRate    -    0     500   "Epics Channel Access UDP Load" [median=75]
"""
