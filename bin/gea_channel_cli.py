#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
gea_channel_cli - add / delete / list GEA channels for ONE archiver from the
command line, then restart just that archiver. Run as the 'software' user (so
the full GEA environment and file permissions are correct).

This is the shell equivalent of the manual runbook, scoped to one archiver:
  - edit config/<archiver>/<archiver>.cnfg
  - regenerate <archiver>-group.xml (update_config)
  - restart that one archiver (disable/enable via the daemon)

Usage:
  gea_channel_cli.py list <archiver>
  gea_channel_cli.py add  <archiver> <pv> [period] [mode]      # mode: Monitor|Scan
  gea_channel_cli.py del  <archiver> <pv>
  gea_channel_cli.py restart <archiver>

  # also put it on a display page section (optional):
  gea_channel_cli.py add <archiver> <pv> --page <pageName> --section "<Section>" \\
                        [--label "<label>"] [--format Plot|Spreadsheet]

Examples:
  gea_channel_cli.py add pcs m1:MCB005:Ch1SolRbk 1 Monitor
  gea_channel_cli.py add pcs m1:MCB005:Ch1SolRbk --page pcsPage --section "Hydraulic Valves" --label "Zone 8" --format Spreadsheet
  gea_channel_cli.py del pcs m1:MCB005:Ch1SolRbk
  gea_channel_cli.py list pcs
"""

import sys
import os

# Make pyGEA importable (gea_channel lives there).
sys.path.insert(0, os.path.join(os.environ.get("GEA_BASE", "/gemsoft/opt/gea"), "pyGEA"))

import gea_channel


def _opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]

    try:
        if cmd == "list":
            archiver = argv[2]
            print("Channels archived by '%s':" % archiver)
            for pv in sorted(gea_channel.existing_pvs(archiver)):
                print("  " + pv)
            return 0

        if cmd == "restart":
            archiver = argv[2]
            print("Restarting archiver '%s' ..." % archiver)
            print(gea_channel.restart_archiver(archiver))
            return 0

        if cmd == "add":
            archiver = argv[2]
            pv = argv[3]
            rest = argv[4:]
            # positional args = the leading ones before any --option
            pos = []
            for a in rest:
                if a.startswith("--"):
                    break
                pos.append(a)
            period = int(pos[0]) if len(pos) >= 1 and pos[0].isdigit() else 1
            mode = pos[1] if len(pos) >= 2 else "Monitor"
            page = _opt(rest, "--page")
            section = _opt(rest, "--section")
            label = _opt(rest, "--label")
            fmt = _opt(rest, "--format")

            r = gea_channel.add_channel(archiver, pv, period=period, mode=mode,
                    page=page, section=section, fmt=fmt, label=label,
                    restart=True)
            print("Added '%s' to '%s'." % (r["pv"], archiver))
            if r.get("restarted"):
                print("  " + (r.get("restart_info") or "archiver restarted"))
            elif r.get("restart_needed"):
                print("  (restart was needed; run: gea_channel_cli.py restart %s)" % archiver)
            for w in r.get("warnings", []):
                print("  note: " + w)
            return 0

        if cmd == "del":
            archiver = argv[2]
            pv = argv[3]
            rest = argv[4:]
            page = _opt(rest, "--page")
            section = _opt(rest, "--section")
            r = gea_channel.delete_channel(archiver, pv, page=page,
                    section=section, restart=True)
            print("Deleted '%s' from '%s'." % (r["pv"], archiver))
            if r.get("restarted"):
                print("  " + (r.get("restart_info") or "archiver restarted"))
            return 0

        print("Unknown command '%s'.\n" % cmd)
        print(__doc__)
        return 2

    except gea_channel.ChannelError, e:
        sys.stderr.write("ERROR: %s\n" % e)
        return 1
    except IndexError:
        sys.stderr.write("ERROR: missing argument.\n\n")
        print(__doc__)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
