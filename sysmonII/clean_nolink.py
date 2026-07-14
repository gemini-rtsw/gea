#!/usr/bin/env python3
"""
One-off cleanup for REL-4927 follow-up: remove bogus "noLink": true flags
from sysmonII.json that were injected by a failed GEA archive lookup at
config load and then persisted to disk by a web-UI save (saveConfig added
in REL-4906 serializes the whole in-memory config, including the injected
runtime flag).

For every monitor with options.noLink set, re-run the archive lookup.
If the PV IS found in an archive the noLink is bogus -> remove it.
If the PV is NOT in any archive the noLink is legitimate -> keep it.

Dry run by default; pass --write to modify the file (a .bak backup is made).
Run on the sysmon host (e.g. mkogea-lv1), then reload sysmon:
    python3 clean_nolink.py            # review
    python3 clean_nolink.py --write
    kill -USR1 $(pgrep -f sysmonII)    # reload config so memory matches disk
"""

import json, os, shutil, sys
import xmlrpc.client

CONF = os.path.join(os.environ.get('GEMINI_TOP', '/gemsoft'),
                    "etc/gea/sysmonII/sysmonII.json")

site = os.environ.get('GEMINI_SITE', 'MK')
if site == 'CP': server = "http://geasouth.cl.gemini.edu/"
else:            server = "http://geanorth.hi.gemini.edu/"

ds = xmlrpc.client.Server(server + "run/ArchiveDataServer.cgi")
archives = [a for a in ds.archiver.archives()
            if not a['name'].startswith('-') and len(a['name']) >= 2]

def archived(pvname):
    for a in archives:
        try:
            if ds.archiver.names(a['key'], pvname):
                return a['name']
        except Exception as e:
            print("  WARN names() failed in %s for %s: %s" % (a['name'], pvname, e))
    return None

with open(CONF) as f:
    config = json.load(f)

removed, kept = [], []
for sysname, sysconf in config['systems'].items():
    for mon in sysconf.get('monitor', []):
        opts = mon.get('options') or {}
        if not opts.get('noLink'):
            continue
        pv = mon['pvname']
        arch = archived(pv)
        if arch:
            del opts['noLink']
            removed.append((sysname, pv, arch))
        else:
            kept.append((sysname, pv))

print("\nBOGUS noLink removed (PV is archived):")
for s, pv, arch in removed: print("  %-10s %-40s in archive %s" % (s, pv, arch))
print("\nLegitimate noLink kept (PV not in any archive):")
for s, pv in kept: print("  %-10s %s" % (s, pv))

if '--write' in sys.argv:
    if removed:
        shutil.copy2(CONF, CONF + ".bak")
        tmp = CONF + ".tmp"
        with open(tmp, "w") as f:
            json.dump(config, f, indent=1)
        os.replace(tmp, CONF)
        print("\nWrote %s (backup at %s.bak) - now reload sysmon (kill -USR1)" % (CONF, CONF))
    else:
        print("\nNothing to change.")
else:
    print("\nDRY RUN - nothing written. Re-run with --write to apply.")
