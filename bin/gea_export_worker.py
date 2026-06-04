#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
gea_export_worker - run one long-term raw data export to a gzipped CSV, off the web
request. The Data Export page (pages/common/dataExportPage.py) spawns this detached
for large requests, then polls the job's .status file; small requests call
GEAExport.runExport() inline instead and never reach this script.

The heavy lifting lives in pyGEA/GEAExport.runExport(); this is just the CLI/daemon
wrapper that detaches from the spawning CGI process and turns argv into that call.

Usage:
  gea_export_worker.py --jobid <id> --archivers "<a b>" --channels "<c1 c2>" \\
                       [--pattern <regex>] --start <secs> --end <secs>

  start/end are epoch seconds (the page already parsed the time-selector widget).
  --pattern is optional and is a single value (it may contain spaces), so it is NOT
  space-split the way --channels is.

Run as the 'software' user so ArchiveExport and the exports dir have correct perms.
"""

import os
import sys

# Make pyGEA importable.
sys.path.insert(0, os.path.join(os.environ.get("GEA_BASE", "/gemsoft/opt/gea"), "pyGEA"))

import GEAExport
from GEATime import Time


def _opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def _detach():
    """Fully detach from the parent (the CGI process): new session so we survive the
    request ending, and stdio redirected to /dev/null so nothing writes back to the
    browser. Status/output go to files, which is how the page tracks us."""
    os.setsid()
    devnull = open(os.devnull, 'r+')
    for fd in (sys.stdin, sys.stdout, sys.stderr):
        try:
            os.dup2(devnull.fileno(), fd.fileno())
        except (OSError, ValueError):
            pass


def main(argv):
    jobid = _opt(argv, '--jobid')
    archivers = (_opt(argv, '--archivers', '') or '').split()
    channels = (_opt(argv, '--channels', '') or '').split()
    pattern = _opt(argv, '--pattern')
    patterns = [pattern] if pattern else []
    start = _opt(argv, '--start')
    end = _opt(argv, '--end')

    if not jobid or start is None or end is None:
        sys.stderr.write(__doc__)
        return 2

    startTime = Time(float(start))
    endTime = Time(float(end))

    _detach()

    try:
        GEAExport.runExport(jobid, archivers, channels, patterns, startTime, endTime)
    except Exception:
        # runExport already recorded ERROR in the status file; nothing useful to do
        # with a traceback here since stdio is detached.
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
