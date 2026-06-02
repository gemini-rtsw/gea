#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
editChannelsPage - the per-section channel editor reached from the [edit] link
next to a section title on any GEA page.

Query params:
    PAGE     the page's .channels file (e.g. systems/pcsPage.channels)
    SECTION  the section title to edit (e.g. Hydraulic Valves)

Shows the channels currently in that section, each with a Delete link, and a
small form to add one. Add/Delete submit back here (ADD=.. / DEL=..) and call
into gea_channel, which does the full runbook (edit .cnfg + .channels,
update_config, restart the archiver if needed). Results/errors are shown via
the standard GEA notice mechanism.

Python 2 (GEA frontend).
"""

import os
import urllib

import GEAVars
from pages.geaBasePage import GeaBasePage
from GEARequest import RequestCollection, Request
import gea_channel


def _js(s):
    """Escape a value for safe inclusion inside a single-quoted JS string."""
    return (s or "").replace("\\", "\\\\").replace("'", "\\'").replace('"', "&quot;")


def _archiver_for_page(pagefile):
    """A page file 'systems/pcsPage.channels' archives via the 'pcs' engine.
    Strip dir + 'Page.channels' to get the archiver name; verify it exists."""
    base = os.path.basename(pagefile)
    name = base
    for suff in ("Page.channels", ".channels"):
        if name.endswith(suff):
            name = name[:-len(suff)]
            break
    try:
        if name in gea_channel.list_archivers():
            return name
    except gea_channel.ChannelError:
        pass
    return None


class EditChannelsPage(GeaBasePage):
    """Per-section add/delete of GEA channels."""

    def _assemblePage(self, topMenuList=None):
        # Render bare (no side menu/header) -- this opens in an iframe modal.
        self.standAlone = True
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        self._acted = False          # guard: act on at most one request
        self._action_note = None     # outcome message to show above the listing

    def _getLocalRequests(self):
        # Always process, even with no extra request keys, so the listing renders.
        return RequestCollection({None: Request()})

    def _processRequest(self, request, stream):
        # GEA's run() may call this once PER request in the collection (the real
        # query-string request AND our empty local request). Two bugs came from
        # that: the action ran/rendered multiple times (double-add; stale list).
        # Fix: ACT at most once (guarded by self._acted, only on the request
        # that actually carries params), and RENDER the listing exactly once
        # (in _renderOnce, also guarded). So the displayed list is always a
        # single fresh read taken AFTER the write.
        page    = request.get("PAGE", "")
        section = request.get("SECTION", "")

        # An "action" request is one carrying a verb param. The empty local
        # request has none -> it only triggers the (guarded) render, never a write.
        action_keys = ("ADD", "EDIT", "DEL", "SETSEC", "RESTART")
        has_action = any(request.get(k, "") for k in action_keys)

        if page and section and has_action and not self._acted:
            self._acted = True
            self._action_note = self._doAction(request, page, section)

        # Render the listing once (after any action above has written to disk).
        self._renderOnce(page, section)

    def _doAction(self, request, page, section):
        """Perform the one add/edit/delete/setsec/restart. Returns a note str."""
        archiver = _archiver_for_page(page)
        add_pv  = request.get("ADD", "")
        del_pv  = request.get("DEL", "")
        edit_pv = request.get("EDIT", "")
        fmt     = request.get("FORMAT", "")
        label   = request.get("LABEL", "")
        period  = request.get("PERIOD", "1")
        mode    = request.get("MODE", "Monitor")
        setsec  = request.get("SETSEC", "")
        restart = request.get("RESTART", "")

        def _pending(r, msg):
            if r.get("restarted"):
                return msg + " " + (r.get("restart_info") or "archiver restarted")
            if r.get("restart_needed"):
                return msg + " NOT yet archived -- click 'Restart archiver' to apply."
            return msg

        try:
            if restart:
                info = gea_channel.restart_archiver(archiver)
                return "Restarting archiver '%s': %s" % (archiver, info)
            elif add_pv:
                r = gea_channel.add_channel(archiver, add_pv, period=period,
                        mode=mode, page=page, section=section,
                        fmt=(fmt or None), label=(label or None))
                return _pending(r, "Saved '%s' to '%s'." % (r["pv"], section))
            elif edit_pv:
                r = gea_channel.edit_channel(archiver, edit_pv, period=period,
                        mode=mode, page=page, section=section,
                        fmt=(fmt or None), label=(label or None))
                return _pending(r, "Updated '%s'." % r["pv"])
            elif del_pv:
                r = gea_channel.delete_channel(archiver, del_pv,
                        page=page, section=section)
                return _pending(r, "Deleted '%s' from '%s'." % (r["pv"], section))
            elif setsec:
                chpath = gea_channel.resolve_page(page)
                vals = {"ITEMSPERROW":   request.get("ITEMSPERROW", ""),
                        "SUBTABLE":      request.get("SUBTABLE", ""),
                        "CSSCLASS":      request.get("CSSCLASS", ""),
                        "QUERYSTRPAIRS": request.get("QUERYSTRPAIRS", "")}
                gea_channel.set_section_settings(chpath, section, vals)
                return ("Section layout updated for '%s' (display only; refresh "
                        "the page to see it)." % section)
        except gea_channel.ChannelError, e:
            return "Error: %s (no changes kept)" % e
        except Exception, e:
            return "Unexpected error: %s (no changes kept)" % e

    def _renderOnce(self, page, section):
        """Append the listing exactly once, no matter how many requests run."""
        if getattr(self, "_rendered", False):
            return
        self._rendered = True
        if not page or not section:
            self.html.doc.append("<p>Missing PAGE or SECTION.</p>")
            return
        archiver = _archiver_for_page(page)
        note = self._action_note
        body = self._render(page, section, archiver)
        if note:
            body = ('<div style="margin:1em;padding:6px;background:#e8f0ff;'
                    'border:1px solid #aac;font-family:sans-serif;">%s</div>%s'
                    % (note, body))
        self.html.doc.append(body)

    def _render(self, page, section, archiver):
        try:
            chpath = gea_channel.resolve_page(page)
            rows = gea_channel.section_channels(chpath, section, archiver)
        except gea_channel.ChannelError, e:
            return "<p>Cannot read page: %s</p>" % e

        qp = lambda **kw: "&".join(
            "%s=%s" % (k, urllib.quote(str(v))) for k, v in kw.items())
        here = GEAVars.dispatchScript + "/pages/common/editChannelsPage"

        h = []
        # Emit a COMPLETE html document. In standAlone mode the GEA wrapper
        # gives no <html>/<body>, so in an iframe the content collapses (only
        # the first line showed). A full doc with html,body{height:auto} fixes
        # the clipping.
        h.append('<html><head><meta charset="utf-8"/>'
                 '<style>html,body{height:auto;margin:0;}</style></head><body>')
        # Full-width, readable layout that scales with the window.
        h.append('<style>'
                 '.ecwrap{font-family:sans-serif;margin:1em;}'
                 '.ectbl{border-collapse:collapse;width:100%;table-layout:auto;}'
                 '.ectbl th,.ectbl td{border:1px solid #ccc;padding:4px 8px;'
                 'text-align:left;vertical-align:top;word-break:break-word;}'
                 '.ectbl th{background:#eee;}'
                 '.ectbl code{white-space:normal;}'
                 '.ecform input[type=text]{width:100%;box-sizing:border-box;}'
                 '.ecform td{padding:3px 6px;}'
                 '</style>')
        h.append('<div class="ecwrap">')
        h.append("<h3>Edit channels &mdash; %s</h3>" % section)
        h.append("<p>Page: <code>%s</code>" % page)
        h.append("&nbsp; Archiver: <code>%s</code></p>"
                 % (archiver or "(none -- display only)"))


        h.append('<table class="ectbl">')
        h.append("<tr><th>Channel</th><th>Label</th><th>Display</th>"
                 "<th>Period</th><th>Mode</th><th>Archived</th><th></th></tr>")
        for row in rows:
            delurl = "%s?%s" % (here, qp(PAGE=page, SECTION=section, DEL=row["pv"]))
            arch = "yes" if row.get("archived") else "<b>no</b>"
            # 'edit' pre-fills the form below with this row's values (JS), so you
            # change label/format/period/mode and resubmit as an edit.
            jsargs = "'%s','%s','%s','%s','%s'" % (
                _js(row["pv"]), _js(row["label"]), _js(row.get("format") or "Plot"),
                _js(row.get("period") or "1"), _js(row.get("mode") or "Monitor"))
            h.append("<tr><td><code>%s</code></td><td>%s</td>"
                     "<td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                     '<td><a href="#" onclick="fillEdit(%s);return false;">edit</a>'
                     ' &nbsp; '
                     '<a href="%s" onclick="return confirm('
                     "'Delete %s%s?')\">delete</a></td></tr>"
                     % (row["pv"], row["label"] or "&nbsp;",
                        row.get("format") or "Plot",
                        row.get("period") or "&nbsp;",
                        row.get("mode") or "&nbsp;",
                        arch, jsargs, delurl, row["pv"],
                        (" and restart "+archiver) if archiver else ""))
        if not rows:
            h.append('<tr><td colspan="7"><i>No channels in this section yet.</i></td></tr>')
        h.append("</table>")

        # ---- Section layout settings (display only; no archiver restart) -----
        try:
            ss = gea_channel.section_settings(chpath, section)
        except gea_channel.ChannelError:
            ss = {"ITEMSPERROW": "", "SUBTABLE": "", "CSSCLASS": "", "QUERYSTRPAIRS": ""}

        def _sel(cur, opts):
            out = []
            for val, txt in opts:
                s = " selected" if cur == val else ""
                out.append('<option value="%s"%s>%s</option>' % (val, s, txt))
            return "".join(out)

        h.append('<h4>Section layout</h4>')
        h.append('<form class="ecform" method="GET" action="%s">' % here)
        h.append('<input type="hidden" name="PAGE" value="%s"/>' % page)
        h.append('<input type="hidden" name="SECTION" value="%s"/>' % section)
        h.append('<input type="hidden" name="SETSEC" value="1"/>')
        h.append('<table style="width:100%;max-width:640px;">')
        h.append('<tr><td style="width:11em;">Columns (per row):</td>'
                 '<td><input type="text" name="ITEMSPERROW" value="%s" '
                 'style="width:5em;" placeholder="default"/> '
                 '<span class="small">how many channels per row</span></td></tr>'
                 % ss.get("ITEMSPERROW", ""))
        h.append('<tr><td>Own sub-table:</td><td><select name="SUBTABLE">%s'
                 '</select></td></tr>'
                 % _sel(ss.get("SUBTABLE", ""),
                        [("", "(default)"), ("True", "True"), ("False", "False")]))
        h.append('<tr><td>CSS class:</td>'
                 '<td><input type="text" name="CSSCLASS" value="%s" '
                 'placeholder="(default)"/></td></tr>' % ss.get("CSSCLASS", ""))
        h.append('<tr><td>Default queries:</td>'
                 '<td><input type="text" name="QUERYSTRPAIRS" value="%s" '
                 "placeholder=\"e.g. {'FORMAT':'Spreadsheet'}\"/></td></tr>"
                 % ss.get("QUERYSTRPAIRS", "").replace('"', "&quot;"))
        h.append('</table>')
        h.append('<input type="submit" value="Save section layout"/>')
        h.append('</form>')
        h.append('<p class="small">Leave a field blank to remove that setting '
                 '(falls back to the page/global default). Layout changes are '
                 'display-only &mdash; no archiver restart; refresh the page to '
                 'see them.</p>')
        h.append('<hr/>')

        # One form, used for both Add and Edit. 'edit' links flip it to edit mode
        # via JS (set the hidden mode field + the action field name + values).
        h.append('<h4 id="formtitle">Add a channel to this section</h4>')
        h.append('<form class="ecform" method="GET" action="%s">' % here)
        h.append('<input type="hidden" name="PAGE" value="%s"/>' % page)
        h.append('<input type="hidden" name="SECTION" value="%s"/>' % section)
        h.append('<table style="width:100%;max-width:640px;">')
        # The action field: name="ADD" by default; edit mode renames it to EDIT.
        h.append('<tr><td style="width:7em;">PV name:</td>'
                 '<td><input type="text" id="f_pv" name="ADD" '
                 'placeholder="m1:x:y.VAL"/></td></tr>')
        h.append('<tr><td>Label:</td>'
                 '<td><input type="text" id="f_label" name="LABEL"/></td></tr>')
        h.append('<tr><td>Display as:</td><td><select id="f_fmt" name="FORMAT">'
                 '<option value="Plot">Plot</option>'
                 '<option value="Spreadsheet">Spreadsheet</option></select></td></tr>')
        h.append('<tr><td>Period (s):</td>'
                 '<td><input type="text" id="f_period" name="PERIOD" value="1" '
                 'style="width:5em;"/> &nbsp; Mode: <select id="f_mode" name="MODE">'
                 '<option>Monitor</option><option>Scan</option></select></td></tr>')
        h.append('</table>')
        h.append('<input type="submit" id="f_submit" value="Add channel"/> '
                 '<input type="button" value="Clear" onclick="resetForm();"/>')
        h.append('</form>')
        # Restart warning + button, right here by Save so it's seen after saving:
        # saving writes the config but does NOT restart -- add everything, then
        # click this once to apply it all.
        if archiver:
            resturl = "%s?%s" % (here, qp(PAGE=page, SECTION=section, RESTART="1"))
            h.append('<div style="margin:1em 0;padding:8px;background:#fff7e0;'
                     'border:1px solid #e0c060;">'
                     'Saving writes the config but does <b>not</b> restart the '
                     'archiver, so a new channel is <b>not archived yet</b>. Add '
                     'everything you need, then apply it all at once:<br/><br/>'
                     '<a href="%s" onclick="return confirm('
                     "'Restart archiver %s now? (a few seconds)')\" "
                     'style="font-size:1.1em;">'
                     '&#9888; <b>Restart archiver %s now</b></a></div>'
                     % (resturl, archiver, archiver))
        # JS: fillEdit pre-fills + flips the form to edit; resetForm restores add.
        h.append("""<script type="text/javascript">
function setField(id,v){var e=document.getElementById(id);if(e)e.value=v;}
function fillEdit(pv,label,fmt,period,mode){
  setField('f_pv',pv); setField('f_label',label);
  setField('f_fmt',fmt||'Plot'); setField('f_period',period||'1'); setField('f_mode',mode||'Monitor');
  var pvf=document.getElementById('f_pv'); pvf.name='EDIT'; pvf.readOnly=true;
  document.getElementById('f_submit').value='Save changes';
  document.getElementById('formtitle').innerHTML='Edit channel: '+pv;
  pvf.focus();
}
function resetForm(){
  var pvf=document.getElementById('f_pv'); pvf.name='ADD'; pvf.readOnly=false; pvf.value='';
  setField('f_label',''); setField('f_fmt','Plot'); setField('f_period','1'); setField('f_mode','Monitor');
  document.getElementById('f_submit').value='Add channel';
  document.getElementById('formtitle').innerHTML='Add a channel to this section';
}
</script>""")
        h.append('</div>')
        h.append('</body></html>')
        return "\n".join(h)


def main(outStream=GEAVars.outStream, standAlone=False):
    EditChannelsPage(outStream, standAlone).run()


if __name__ == "__main__":
    main(GEAVars.outStream, standAlone=True)
