#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
gea_channel - the "add a channel" runbook, as a single callable.

This is the backend for the one Add-Channel button on the GEA pages. It does,
in order, what the manual runbook does:

  Step 3  append the PV to config/<archiver>/<archiver>.cnfg
  Step 4  append a display line to the page's .channels file, in a chosen section
  Step 5  run update_config <archiver>
  Step 7  restart that one archiver (only if the .cnfg actually changed)
  Step 9  if the PV's host isn't in the archiver's <calist>, WARN (that case
          needs a manual full restart; we don't attempt it)

It runs inside the GEA CGI frontend, which already has the full GEA environment
(GEA_BASE/GEA_CONF/GEA_DATA via GEAVars), so update_config finds its perl libs.

Every file write is atomic (temp + rename) with a .bak; if update_config or the
restart fails, both files are rolled back -- the operation is all-or-nothing.

Python 2 (the frontend is Python 2).
"""

import os
import re
import shutil
import subprocess
import logging

import GEAVars

log = logging.getLogger("gea_channel")

# Conservative PV-name check; a malformed name would break ConvertEngineConfig.
PV_RE = re.compile(r"^[A-Za-z0-9_]+(:[A-Za-z0-9_]+)*(\.[A-Za-z0-9_]+)?$")
VALID_MODES = ("Monitor", "Scan")
SECTION_MARK = "#[SECTION]"


class ChannelError(Exception):
    """Caller-facing; message is safe to show on the page."""
    pass


def _conf_dir():
    return GEAVars.path.fileSys.geaConf            # /gemsoft/etc/gea

def _base_dir():
    return GEAVars.path.fileSys.geaRoot            # /gemsoft/opt/gea

def cnfg_path(archiver):
    return os.path.join(_conf_dir(), "config", archiver, archiver + ".cnfg")

def archiveconfig_path():
    return os.path.join(_conf_dir(), "archiveconfig.xml")


def list_archivers():
    """Archiver names from archiveconfig.xml <engine directory='...'>."""
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(archiveconfig_path())
    except Exception, e:
        raise ChannelError("Cannot read archiveconfig.xml: %s" % e)
    names = [e.get("directory") for e in tree.iter("engine") if e.get("directory")]
    if not names:
        raise ChannelError("No archivers found in archiveconfig.xml")
    return sorted(names)


def _calist(archiver):
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(archiveconfig_path())
    except Exception:
        return []
    for e in tree.iter("engine"):
        if e.get("directory") == archiver:
            cal = e.find("calist")
            if cal is not None and cal.text:
                return cal.text.split()
    return []


def _engine_ports(archiver):
    """
    For one archiver, return (daemon_port, engine_port) from archiveconfig.xml.
    The daemon's HTTP interface (on daemon_port) drives disable/enable of an
    engine addressed by its engine_port. Returns (None, None) if not found.
    """
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(archiveconfig_path())
    except Exception, e:
        raise ChannelError("Cannot read archiveconfig.xml: %s" % e)
    for daemon in tree.iter("daemon"):
        dport = daemon.find("port")
        dport = dport.text.strip() if (dport is not None and dport.text) else None
        for e in daemon.iter("engine"):
            if e.get("directory") == archiver:
                ep = e.find("port")
                ep = ep.text.strip() if (ep is not None and ep.text) else None
                return (dport, ep)
    return (None, None)


# ---- section-level layout settings (display only; no archiver restart) -----

# marker -> (offset after the marker text, so line[offset:] is the value).
# Offsets match GEAHtml._parseSectionStr exactly.
_SECTION_MARKERS = [
    ("ITEMSPERROW",   "#[ITEMSPERROW]", 14),
    ("SUBTABLE",      "#[SUBTABLE]",    11),
    ("CSSCLASS",      "#[CSSCLASS]",    11),
    ("QUERYSTRPAIRS", "#[QUERYSTRPAIRS]", 16),
]


def section_settings(channels_path, section):
    """Return the current section-level marker values: {ITEMSPERROW, SUBTABLE,
    CSSCLASS, QUERYSTRPAIRS} -- empty string if a marker isn't present."""
    out = dict((k, "") for k, _m, _o in _SECTION_MARKERS)
    f = open(channels_path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()
    in_sec = False
    for raw in lines:
        s = raw.strip()
        if s.startswith(SECTION_MARK):
            in_sec = (s[len(SECTION_MARK):].strip() == section)
            continue
        if not in_sec:
            continue
        for key, marker, off in _SECTION_MARKERS:
            if s.startswith(marker):
                out[key] = s[off:].strip()
    return out


def set_section_settings(channels_path, section, values):
    """
    Set/replace/remove the section's layout markers from a {KEY: value} dict.
    A blank value removes that marker (falls back to the file/global default).
    Validates each value the same way GEAHtml does. Writes atomically with a
    .bak. Channel lines and other content are left untouched. Returns content.
    """
    # Validate before touching anything.
    clean = {}
    for key, _marker, _off in _SECTION_MARKERS:
        if key not in values:
            continue
        v = (values[key] or "").strip()
        if v == "":
            clean[key] = ""          # means: remove the marker
            continue
        if key == "ITEMSPERROW":
            try:
                iv = int(v)
                if iv <= 0:
                    raise ValueError
            except ValueError:
                raise ChannelError("Columns (ITEMSPERROW) must be a positive integer")
            clean[key] = str(iv)
        elif key == "SUBTABLE":
            if v.lower() not in ("true", "false", "1", "0"):
                raise ChannelError("Subtable must be True or False")
            clean[key] = "True" if v.lower() in ("true", "1") else "False"
        elif key == "CSSCLASS":
            if " " in v or "{" in v:
                raise ChannelError("CSS class must be a single class name")
            clean[key] = v
        elif key == "QUERYSTRPAIRS":
            # Must be a valid python dict literal (GEAHtml eval()s it).
            try:
                import ast
                d = ast.literal_eval(v)
                if not isinstance(d, dict):
                    raise ValueError
            except Exception:
                raise ChannelError("Default queries must be a dict literal, "
                                   "e.g. {'FORMAT':'Spreadsheet'}")
            clean[key] = v

    marker_for = dict((k, m) for k, m, _o in _SECTION_MARKERS)

    f = open(channels_path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()

    # Find the section span [start, end).
    start = None
    end = len(lines)
    for i, raw in enumerate(lines):
        if raw.strip().startswith(SECTION_MARK):
            title = raw.strip()[len(SECTION_MARK):].strip()
            if start is None and title == section:
                start = i
            elif start is not None:
                end = i
                break
    if start is None:
        raise ChannelError("Section '%s' not found" % section)

    # Within the section: drop existing marker lines we're setting, remember
    # where to insert new ones (right after the section title line).
    body = lines[start + 1:end]
    keys_we_set = set(clean.keys())
    kept = []
    for raw in body:
        s = raw.strip()
        drop = False
        for key in keys_we_set:
            if s.startswith(marker_for[key]):
                drop = True
                break
        if not drop:
            kept.append(raw)

    # Build the new marker lines (skip blanks = removed).
    new_markers = []
    for key, marker, _off in _SECTION_MARKERS:
        if key in clean and clean[key] != "":
            new_markers.append("%s %s" % (marker, clean[key]))

    new_section = [lines[start]] + new_markers + kept
    new_lines = lines[:start] + new_section + lines[end:]
    content = "\n".join(new_lines)
    _write_atomic(channels_path, content)
    return content


def existing_pvs(archiver):
    pvs = set()
    try:
        f = open(cnfg_path(archiver))
    except IOError:
        raise ChannelError("No config file for archiver '%s'" % archiver)
    try:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("!"):
                continue
            pvs.add(s.split()[0])
    finally:
        f.close()
    return pvs


def page_sections(channels_path):
    """Ordered list of section titles in a .channels file (for the dropdown)."""
    secs = []
    try:
        f = open(channels_path)
    except IOError:
        raise ChannelError("No such page file: %s" % channels_path)
    try:
        for line in f:
            s = line.strip()
            if s.startswith(SECTION_MARK):
                secs.append(s[len(SECTION_MARK):].strip())
    finally:
        f.close()
    return secs


def resolve_page(name):
    """Resolve a page file. `name` is normally the path GEAHtml uses, relative
    to pages/ (e.g. 'systems/pcsPage.channels'). Fall back to a basename walk."""
    if os.path.isabs(name):
        return name
    want = name if name.endswith(".channels") else name + ".channels"
    pagesdir = os.path.join(_conf_dir(), "pages")
    # First: direct join (GEAHtml reads pages exactly this way).
    direct = os.path.join(pagesdir, want)
    if os.path.isfile(direct):
        return direct
    # Fall back: search by basename anywhere under pages/.
    base = os.path.basename(want)
    hits = []
    for root, _dirs, files in os.walk(pagesdir):
        if base in files:
            hits.append(os.path.join(root, base))
    if not hits:
        raise ChannelError("Page file '%s' not found" % want)
    if len(hits) > 1:
        raise ChannelError("Page file '%s' is ambiguous" % want)
    return hits[0]


# --------------------------------------------------------------------------
# The one entry point.
# --------------------------------------------------------------------------

def add_channel(archiver, pv, period=1, mode="Monitor",
                page=None, section=None, fmt=None, label=None):
    """
    Run the runbook for one PV. `page`/`section` are optional (display side);
    if omitted, only the archiver side is touched. Returns a dict describing
    what happened, including a 'warnings' list. Raises ChannelError on failure
    (with both files rolled back).
    """
    pv = (pv or "").strip()
    if archiver not in list_archivers():
        raise ChannelError("Unknown archiver '%s'" % archiver)
    if not PV_RE.match(pv):
        raise ChannelError("Invalid PV name '%s'" % pv)
    try:
        period = int(period)
    except (TypeError, ValueError):
        raise ChannelError("Period must be a whole number of seconds")
    if period <= 0:
        raise ChannelError("Period must be positive")
    if mode not in VALID_MODES:
        raise ChannelError("Mode must be Monitor or Scan")

    warnings = []
    already_archived = pv in existing_pvs(archiver)

    # Stage the .channels edit (validate placement before any write).
    chpath = None
    chlines = None
    if page and section:
        chpath = resolve_page(page)
        chlines = _channels_with_added(chpath, section, pv, fmt, label)

    # If nothing to do on the archiver side and it's already archived, we may
    # still be adding a display line. Decide whether a restart is needed.
    need_cnfg = not already_archived
    if not need_cnfg:
        warnings.append("PV is already archived; no archiver restart needed.")

    # Step 9: new-IP detection is best-effort -- we can't map PV->host reliably,
    # so we just surface the calist so the user can judge.
    cal = _calist(archiver)

    cnfg_bak = None
    page_bak = None
    cnfg_path_ = cnfg_path(archiver)
    try:
        if need_cnfg:
            cnfg_bak = _append_cnfg(archiver, pv, period, mode)
        if chlines is not None:
            page_bak = _write_atomic(chpath, "\n".join(chlines))
        if need_cnfg:
            _run("update_config", archiver)      # fast; also validates the .cnfg
    except Exception:
        if page_bak:
            _restore(chpath, page_bak)
        if cnfg_bak:
            _restore(cnfg_path_, cnfg_bak)
        raise

    # Files are committed + update_config succeeded. Now trigger the full
    # restart in the background (only needed when the .cnfg actually changed).
    restart_info = None
    if need_cnfg:
        restart_info = restart_one_engine(archiver)

    return {
        "archiver": archiver, "pv": pv, "period": period, "mode": mode,
        "restart_triggered": need_cnfg, "restart_info": restart_info,
        "calist": cal, "page": page, "section": section, "warnings": warnings,
    }


def cnfg_meta(archiver):
    """Map each archived PV to its config metadata: {pv: {period, mode}}.
    Used to show how a channel is being archived alongside its display info."""
    meta = {}
    try:
        f = open(cnfg_path(archiver))
    except IOError:
        return meta
    try:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("!"):
                continue
            parts = s.split()
            meta[parts[0]] = {
                "period": parts[1] if len(parts) > 1 else "",
                "mode":   parts[2] if len(parts) > 2 else "",
            }
    finally:
        f.close()
    return meta


def section_channels(channels_path, section, archiver=None):
    """
    Return the display channels in one section as a list of dicts:
      {pv, label, raw, format, period, mode, archived}
    'format' is the display FORMAT (Plot/Spreadsheet) from the line; period/mode
    come from the archiver's .cnfg (if `archiver` given). Only real PV lines
    (not markers/comments/blanks) are returned.
    """
    meta = cnfg_meta(archiver) if archiver else {}
    f = open(channels_path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()
    out = []
    in_sec = False
    for raw in lines:
        s = raw.strip()
        if s.startswith(SECTION_MARK):
            in_sec = (s[len(SECTION_MARK):].strip() == section)
            continue
        if not in_sec or not s or s.startswith("#") or s.startswith("!"):
            continue
        h = raw.find("#")
        if h >= 0:
            pv = raw[:h].strip()
            label = raw[h:].lstrip("#").strip()
        else:
            pv = s
            label = ""
        # Pull the display FORMAT out of an inline {...} query-dict, then strip
        # the dict off the displayed pv token.
        fmt = ""
        b = pv.find("{")
        if b >= 0:
            dictpart = pv[b:]
            m = re.search(r"'FORMAT'\s*:\s*'([^']*)'", dictpart)
            if m:
                fmt = m.group(1)
            pv = pv[:b].strip()
        m = meta.get(pv, {})
        out.append({"pv": pv, "label": label, "raw": raw, "format": fmt,
                    "period": m.get("period", ""), "mode": m.get("mode", ""),
                    "archived": pv in meta})
    return out


def delete_channel(archiver, pv, page=None, section=None):
    """
    Remove a PV's display line from a page section (and/or its .cnfg line).
    If page/section given, removes the matching display line. If `archiver`
    given and the PV is archived, also removes it from the .cnfg and restarts.
    All-or-nothing with .bak rollback. Returns a summary dict.
    """
    pv = (pv or "").strip()
    if not pv:
        raise ChannelError("No PV given to delete")

    chpath = None
    chcontent = None
    if page and section:
        chpath = resolve_page(page)
        chcontent = _channels_without(chpath, section, pv)

    archived = archiver and (pv in existing_pvs(archiver))

    cnfg_bak = None
    page_bak = None
    cnfg_path_ = cnfg_path(archiver) if archiver else None
    try:
        if archived:
            cnfg_bak = _cnfg_without(archiver, pv)
        if chcontent is not None:
            page_bak = _write_atomic(chpath, chcontent)
        if archived:
            _run("update_config", archiver)
    except Exception:
        if page_bak:
            _restore(chpath, page_bak)
        if cnfg_bak:
            _restore(cnfg_path_, cnfg_bak)
        raise

    restart_info = restart_one_engine(archiver) if archived else None
    return {"archiver": archiver, "pv": pv, "page": page, "section": section,
            "restart_triggered": bool(archived), "restart_info": restart_info}


def edit_channel(archiver, pv, period=None, mode=None,
                 page=None, section=None, fmt=None, label=None):
    """
    Change an existing channel in place: rewrite its display line (label/format)
    in the page section, and its .cnfg line (period/mode). The PV name itself is
    not changed (changing it is a delete + add). Restarts the archiver only if
    period/mode actually changed. All-or-nothing with .bak rollback.
    """
    pv = (pv or "").strip()
    if not pv:
        raise ChannelError("No PV given to edit")
    if mode is not None and mode not in VALID_MODES:
        raise ChannelError("Mode must be Monitor or Scan")

    # ---- stage the .channels display-line rewrite ----------------------------
    chpath = None
    chcontent = None
    if page and section:
        chpath = resolve_page(page)
        # Build the new display line, then replace the old one in place.
        newline = _display_line(pv, fmt, label)
        chcontent = _channels_replaced(chpath, section, pv, newline)

    # ---- decide whether the .cnfg (period/mode) changed ----------------------
    cnfg_changed = False
    new_cnfg = None
    if archiver and (period is not None or mode is not None) and pv in existing_pvs(archiver):
        cur = cnfg_meta(archiver).get(pv, {})
        new_period = str(period) if period is not None else cur.get("period", "1")
        new_mode   = mode if mode is not None else cur.get("mode", "Monitor")
        try:
            ip = int(new_period)
            if ip <= 0:
                raise ValueError
        except (TypeError, ValueError):
            raise ChannelError("Period must be a positive whole number")
        if (new_period, new_mode) != (cur.get("period", ""), cur.get("mode", "")):
            cnfg_changed = True
            new_cnfg = _cnfg_replaced(archiver, pv, ip, new_mode)

    cnfg_bak = None
    page_bak = None
    cnfg_path_ = cnfg_path(archiver) if archiver else None
    try:
        if cnfg_changed:
            cnfg_bak = new_cnfg            # already written (returns .bak)
        if chcontent is not None:
            page_bak = _write_atomic(chpath, chcontent)
        if cnfg_changed:
            _run("update_config", archiver)
    except Exception:
        if page_bak:
            _restore(chpath, page_bak)
        if cnfg_bak:
            _restore(cnfg_path_, cnfg_bak)
        raise

    restart_info = restart_one_engine(archiver) if cnfg_changed else None
    return {"archiver": archiver, "pv": pv, "page": page, "section": section,
            "restart_triggered": cnfg_changed, "restart_info": restart_info}


def _display_line(pv, fmt, label):
    parts = [pv]
    if fmt:
        if fmt not in ("Plot", "Spreadsheet"):
            raise ChannelError("Format must be Plot or Spreadsheet")
        parts.append("{'FORMAT':'%s'}" % fmt)
    line = " ".join(parts)
    if label:
        label = label.strip().lstrip("#").strip()
        if "{" in label or "}" in label or "\n" in label:
            raise ChannelError("Label has illegal characters")
        line += "  # " + label
    return line


def _channels_replaced(path, section, pv, newline):
    """Return file content with the PV's line in `section` replaced by newline."""
    f = open(path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()
    in_sec = False
    replaced = 0
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith(SECTION_MARK):
            in_sec = (s[len(SECTION_MARK):].strip() == section)
            continue
        if in_sec and s and not s.startswith("#") and not s.startswith("!"):
            val = raw.split("#", 1)[0]
            b = val.find("{")
            if b >= 0:
                val = val[:b]
            if val.strip() == pv:
                lines[i] = newline
                replaced += 1
    if replaced == 0:
        raise ChannelError("'%s' not found in section '%s'" % (pv, section))
    return "\n".join(lines)


def _cnfg_replaced(archiver, pv, period, mode):
    """Rewrite the PV's .cnfg line with new period/mode. Returns .bak path."""
    path = cnfg_path(archiver)
    bak = path + ".bak"
    shutil.copy2(path, bak)
    f = open(path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s and not s.startswith("#") and not s.startswith("!") and s.split()[0] == pv:
            lines[i] = "%-32s %d  %s" % (pv, period, mode)
    _write_atomic(path, "\n".join(lines))
    return bak


def _channels_without(path, section, pv):
    """Return file content with the PV's display line removed from `section`."""
    f = open(path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()
    out = []
    in_sec = False
    removed = 0
    for raw in lines:
        s = raw.strip()
        if s.startswith(SECTION_MARK):
            in_sec = (s[len(SECTION_MARK):].strip() == section)
            out.append(raw)
            continue
        if in_sec and s and not s.startswith("#") and not s.startswith("!"):
            val = raw.split("#", 1)[0]
            b = val.find("{")
            if b >= 0:
                val = val[:b]
            if val.strip() == pv:
                removed += 1
                continue
        out.append(raw)
    if removed == 0:
        raise ChannelError("'%s' not found in section '%s'" % (pv, section))
    return "\n".join(out)


def _cnfg_without(archiver, pv):
    path = cnfg_path(archiver)
    bak = path + ".bak"
    shutil.copy2(path, bak)
    f = open(path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()
    out = []
    removed = 0
    for raw in lines:
        s = raw.strip()
        if s and not s.startswith("#") and not s.startswith("!") and s.split()[0] == pv:
            removed += 1
            continue
        out.append(raw)
    if removed == 0:
        os.remove(bak)
        raise ChannelError("'%s' not in config" % pv)
    _write_atomic(path, "\n".join(out))
    return bak


# ---- file edits (atomic, with .bak) ---------------------------------------

def _append_cnfg(archiver, pv, period, mode):
    path = cnfg_path(archiver)
    bak = path + ".bak"
    shutil.copy2(path, bak)
    f = open(path)
    try:
        content = f.read()
    finally:
        f.close()
    if content and not content.endswith("\n"):
        content += "\n"
    content += "%-32s %d  %s\n" % (pv, period, mode)
    _write_atomic(path, content)
    return bak


def _channels_with_added(path, section, pv, fmt, label):
    """Return the file's lines with one display line spliced into `section`."""
    f = open(path)
    try:
        lines = f.read().split("\n")
    finally:
        f.close()

    # Build the display line in the file's idiom.
    parts = [pv]
    if fmt:
        if fmt not in ("Plot", "Spreadsheet"):
            raise ChannelError("Format must be Plot or Spreadsheet")
        parts.append("{'FORMAT':'%s'}" % fmt)
    line = " ".join(parts)
    if label:
        label = label.strip().lstrip("#").strip()
        if "{" in label or "}" in label or "\n" in label:
            raise ChannelError("Label has illegal characters")
        line += "  # " + label

    # Find the section's span and insert at its end (before trailing blanks).
    start = None
    for i, raw in enumerate(lines):
        if raw.strip().startswith(SECTION_MARK):
            title = raw.strip()[len(SECTION_MARK):].strip()
            if start is None and title == section:
                start = i
            elif start is not None:
                end = i
                break
    else:
        end = len(lines)
    if start is None:
        raise ChannelError("Section '%s' not found in page" % section)

    at = end
    while at - 1 > start and lines[at - 1].strip() == "":
        at -= 1
    lines.insert(at, line)
    return lines


def _write_atomic(path, content):
    """Write content to path atomically, leaving path+'.bak'. Returns .bak."""
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    tmp = path + ".tmp"
    try:
        fh = open(tmp, "w")
        try:
            fh.write(content)
        finally:
            fh.close()
        os.rename(tmp, path)
    except Exception, e:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise ChannelError("Failed to write %s: %s" % (path, e))
    return bak


def _restore(path, bak):
    if bak and os.path.exists(bak):
        os.rename(bak, path)


# ---- run the perl scripts (full GEA env is already present in the CGI) ----

def _run(script, arg):
    """Run a GEA bin script with a single arg, synchronously; raise on non-zero."""
    _run_args([script, arg])


def _run_args(argv):
    """Run a GEA bin script with arbitrary args (e.g. ['update_indices','-s','pcs']),
    synchronously; raise on non-zero. Sourcing the full GEA env is unnecessary
    here -- the CGI already has it."""
    cmd = [os.path.join(_base_dir(), "bin", argv[0])] + list(argv[1:])
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
    except OSError, e:
        raise ChannelError("%s could not run: %s" % (argv[0], e))
    if proc.returncode != 0:
        msg = (err or out or "").strip()
        raise ChannelError("%s failed: %s" % (argv[0], msg[:500]))


def restart_one_engine(archiver):
    """
    Restart ONLY this archiver's engine, using the ArchiveDaemon's own
    disable/enable mechanism -- not stop_gea/start_gea (which would drop all 24
    archivers and take minutes).

    The daemon's HTTP interface (on the daemon's port) supports:
      GET /disable/<engine_port>  -> writes DISABLED.txt and stops the engine
      GET /enable/<engine_port>   -> removes DISABLED.txt and forces an
                                     immediate re-check, so the daemon restarts
                                     just that engine within a second or two.

    This is the daemon's designed way to cycle one engine, and (unlike a bare
    stop_engine) the enable step forces the restart instead of waiting for the
    next scheduled start. Returns a short status string. Raises ChannelError if
    the ports can't be found or the daemon can't be reached.
    """
    dport, eport = _engine_ports(archiver)
    if not dport or not eport:
        raise ChannelError("Could not find daemon/engine ports for '%s' in "
                           "archiveconfig.xml" % archiver)
    host = os.environ.get("GEA_HOST", "localhost")

    # Use the daemon's own disable/enable cycle -- the same two buttons on the
    # Archiver Status page that work when a human clicks them. The trick is to
    # WAIT between them: disable stops the engine, but if we enable before it has
    # actually died, the daemon still sees it running and won't restart it (that
    # was the earlier bug). So: disable, poll until the engine port stops
    # answering (it's really down), then enable to force the immediate restart.
    #
    # Always talk to the daemon over localhost: the web frontend and the daemon
    # run on the same box, the daemon's HTTP answers on localhost:port, and this
    # avoids DNS / cross-host firewall issues (GEA_HOST may name a sibling box
    # the frontend can't route to).
    host = "localhost"

    # Mirror what start_gea does, but for this one archiver. start_gea runs
    # update_config all + update_indices all + run_daemon all. We already ran
    # update_config <archiver> (caller).
    #
    # update_indices refreshes the DATA-SERVER index/serverconfig (for reading
    # archived data back into plots) -- it is NOT required for the engine to
    # start recording the new channel (that's update_config + the restart). It
    # also writes $GEA_BASE/etc/serverconfig.xml, which the web user often can't
    # write. So run it best-effort: if it fails (e.g. permissions), warn but DO
    # NOT abort the whole add -- the channel is archived regardless, and the
    # index side gets sorted by the next update_indices/start_gea.
    index_note = ""
    try:
        _run_args(["update_indices", "-s", archiver])
    except ChannelError, e:
        log.warning("update_indices failed (non-fatal): %s", e)
        index_note = " (plots may lag until next reindex)"

    # Cycle just this engine via the daemon's disable/enable (same as the
    # Archiver Status buttons): disable stops it; wait until it's really down;
    # enable forces the daemon to restart it immediately with the new config.
    _daemon_http(host, dport, "/disable/%s" % eport)
    _wait_until_down(host, eport, timeout=15)
    _daemon_http(host, dport, "/enable/%s" % eport)
    return "archiver restarted" + index_note


def _wait_until_down(host, port, timeout=15):
    """Poll the engine's port until it stops answering (engine is down)."""
    import socket, time
    for _i in range(int(timeout)):
        try:
            s = socket.create_connection((host, int(port)), timeout=2)
            s.close()
            time.sleep(1)            # still up; wait and retry
        except (socket.error, ValueError):
            return True              # refused/unreachable -> it's down
    return False


def _daemon_http(host, port, path):
    """GET path from the ArchiveDaemon's HTTP interface; raise on failure."""
    import socket
    try:
        s = socket.create_connection((host, int(port)), timeout=10)
    except (socket.error, ValueError), e:
        raise ChannelError("Cannot reach ArchiveDaemon at %s:%s (%s)"
                           % (host, port, e))
    try:
        s.sendall("GET %s HTTP/1.0\r\n\r\n" % path)
        data = ""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    finally:
        s.close()
    # The daemon returns an HTML page; an explicit ERROR means the action failed.
    if "ERROR" in data:
        raise ChannelError("Daemon rejected %s: %s"
                           % (path, data.split("ERROR", 1)[1][:200]))
    return data
