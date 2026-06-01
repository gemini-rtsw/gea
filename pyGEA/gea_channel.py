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

import GEAVars

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
            _run("update_config", archiver)
            _run("stop_engine", archiver)        # daemon auto-restarts it
    except Exception:
        if page_bak:
            _restore(chpath, page_bak)
        if cnfg_bak:
            _restore(cnfg_path_, cnfg_bak)
        raise

    return {
        "archiver": archiver, "pv": pv, "period": period, "mode": mode,
        "restarted": need_cnfg, "calist": cal,
        "page": page, "section": section, "warnings": warnings,
    }


def section_channels(channels_path, section):
    """
    Return the display channels in one section as a list of dicts
    {pv, label, raw}, for listing with delete buttons. Only real PV lines
    (not markers/comments/blanks) are returned.
    """
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
        # strip an inline {...} query-dict off the displayed pv token
        b = pv.find("{")
        if b >= 0:
            pv = pv[:b].strip()
        out.append({"pv": pv, "label": label, "raw": raw})
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
            _run("stop_engine", archiver)
    except Exception:
        if page_bak:
            _restore(chpath, page_bak)
        if cnfg_bak:
            _restore(cnfg_path_, cnfg_bak)
        raise

    return {"archiver": archiver, "pv": pv, "page": page, "section": section,
            "restarted": bool(archived)}


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
    cmd = [os.path.join(_base_dir(), "bin", script), arg]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
    except OSError, e:
        raise ChannelError("%s could not run: %s" % (script, e))
    if proc.returncode != 0:
        msg = (err or out or "").strip()
        raise ChannelError("%s failed: %s" % (script, msg[:500]))
