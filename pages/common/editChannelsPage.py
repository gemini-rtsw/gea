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

def _js_str(s):
    """Return a quoted JS string literal for s (e.g. 'foo' -> \"'foo'\")."""
    return "'" + _js(s) + "'"


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
        # GEA's run() can split a single submit across several Request objects
        # in the collection (and adds our empty local request too), calling this
        # once per object. So a single object may have ADD but not PAGE/SECTION,
        # or vice-versa -- which made the action get skipped (the "two clicks"
        # bug). Fix: MERGE every request's keys into one params dict across all
        # the calls, act once we have a full action, render once.
        if not hasattr(self, "_params"):
            self._params = {}
        for k in ("PAGE", "SECTION", "ADD", "EDIT", "DEL", "FORMAT", "LABEL",
                  "PERIOD", "MODE", "SETSEC", "RESTART", "ITEMSPERROW",
                  "SUBTABLE", "CSSCLASS", "QUERYSTRPAIRS"):
            v = request.get(k, "")
            if v != "" and k not in self._params:
                self._params[k] = v

        p = self._params
        page = p.get("PAGE", "")
        section = p.get("SECTION", "")
        action_keys = ("ADD", "EDIT", "DEL", "SETSEC", "RESTART")
        has_action = any(p.get(k, "") for k in action_keys)

        if page and section and has_action and not self._acted:
            self._acted = True
            self._action_note = self._doActionMerged(p, page, section)

        # Render only once we've resolved the action (so the listing reflects the
        # write) -- or, if this request carries no action at all, render the
        # plain listing. Deferring avoids rendering a stale list before the
        # action's params arrive in a later request iteration (the two-click bug).
        if page and section and (self._acted or not has_action):
            self._renderOnce(page, section)

    def _auto_edit_js(self):
        """After an Add, KILL the dialog and reopen it fresh -- tear the whole
        iframe overlay out of the parent and recreate it pointing at the plain
        listing URL. This is the bluntest possible refresh and doesn't depend on
        re-navigating the existing iframe (which didn't refresh on the first
        click). Empty string when there's nothing to do."""
        ae = getattr(self, "_auto_edit", None)
        if not ae:
            return ""
        # Plain listing URL (no action) for the freshly-reopened dialog.
        base = getattr(self, "_here", "") or ""
        page = self._params.get("PAGE", "")
        section = self._params.get("SECTION", "")
        import urllib as _u
        listurl = "%s?PAGE=%s&SECTION=%s" % (
            base, _u.quote(page), _u.quote(section))
        return ("""try{
  var P=window.parent;
  if(P && P!==window && P.document){
    var ov=P.document.getElementById('geaEditOverlay');
    if(ov && ov.parentNode){ ov.parentNode.removeChild(ov); }  // KILL it
    if(P.geaEditChannels){ P.geaEditChannels(%s); }             // BRING IT BACK
  } else {
    window.location.href=%s;   // not framed: just reload the listing
  }
}catch(e){ try{window.location.href=%s;}catch(e2){} }"""
                % (_js_str(listurl), _js_str(listurl), _js_str(listurl)))

    def _doActionMerged(self, p, page, section):
        """Perform the one add/edit/delete/setsec/restart. `p` is the merged
        params dict. Returns a note str."""
        archiver = _archiver_for_page(page)
        add_pv  = p.get("ADD", "")
        del_pv  = p.get("DEL", "")
        edit_pv = p.get("EDIT", "")
        fmt     = p.get("FORMAT", "")
        label   = p.get("LABEL", "")
        period  = p.get("PERIOD", "1")
        mode    = p.get("MODE", "Monitor")
        setsec  = p.get("SETSEC", "")
        restart = p.get("RESTART", "")

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
                # Auto-fire an edit of the just-added channel so the dialog
                # refreshes exactly the way a manual edit press does (which works).
                self._auto_edit = {"pv": r["pv"], "fmt": (fmt or "Plot"),
                                   "label": (label or ""), "period": str(period),
                                   "mode": mode}
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
                vals = {"ITEMSPERROW":   p.get("ITEMSPERROW", ""),
                        "SUBTABLE":      p.get("SUBTABLE", ""),
                        "CSSCLASS":      p.get("CSSCLASS", ""),
                        "QUERYSTRPAIRS": p.get("QUERYSTRPAIRS", "")}
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
        body = self._render(page, section, archiver, note=self._action_note)
        self.html.doc.append(body)

    def _render(self, page, section, archiver, note=None):
        try:
            chpath = gea_channel.resolve_page(page)
            rows = gea_channel.section_channels(chpath, section, archiver)
        except gea_channel.ChannelError, e:
            return "<p>Cannot read page: %s</p>" % e

        qp = lambda **kw: "&".join(
            "%s=%s" % (k, urllib.quote(str(v))) for k, v in kw.items())
        here = GEAVars.dispatchScript + "/pages/common/editChannelsPage"
        self._here = here

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

        # Add/Save is a REAL HTML <form> GET submit -- the same native browser
        # navigation as the delete link, and identical to how Edit submits (Edit
        # only pre-fills these same fields, then submits this same form). A form
        # submit serializes the field VALUES at submit time, so there is no
        # JS-built URL and no <a> href that can be read stale before onclick runs
        # -- that timing gap is exactly why the old <a>/window.location Add needed
        # two clicks while Edit (whose href was set during idle) worked. The PV
        # field is named ADD; edit mode renames it to EDIT (fillEdit), like the
        # original working version. The form action is `here` (same base as the
        # delete link); target=_self keeps it in this iframe.
        h.append('<h4 id="formtitle">Add a channel to this section</h4>')
        h.append('<form id="f_form" method="GET" action="%s" target="_self" '
                 'onsubmit="return canAdd();">' % here)
        h.append('<input type="hidden" name="PAGE" value="%s"/>' % page)
        h.append('<input type="hidden" name="SECTION" value="%s"/>' % section)
        h.append('<table style="width:100%;max-width:640px;">')
        h.append('<tr><td style="width:7em;">PV name:</td>'
                 '<td><input type="text" id="f_pv" name="ADD" placeholder="m1:x:y.VAL"/></td></tr>')
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
        h.append('<input type="submit" id="f_submit" value="Add channel" '
                 'style="padding:5px 14px;border:1px solid #888;background:#eee;"/>'
                 ' &nbsp; '
                 '<a href="#" onclick="resetForm();return false;">Clear</a>')
        h.append('</form>')
        # Show the outcome of the last action HERE, by the button -- the list can
        # be long, so a message at the top would scroll out of view.
        if note:
            h.append('<div style="margin:1em 0;padding:8px;background:#e8f0ff;'
                     'border:1px solid #88a;font-weight:bold;">%s</div>' % note)
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
        # The form submits natively (GET) just like the delete link navigates.
        # JS does NO navigation: it only (a) validates a non-empty PV on submit,
        # and (b) for Edit, pre-fills the fields and flips the PV field's name
        # from ADD to EDIT. Add and Edit therefore travel the IDENTICAL submit
        # path -- the only difference is the action key in the serialized form.
        h.append("""<script type="text/javascript">
function gv(id){var e=document.getElementById(id);return e?e.value:'';}
function setField(id,v){var e=document.getElementById(id);if(e)e.value=v;}
function canAdd(){
  if(!gv('f_pv')){ alert('Enter a PV name.'); return false; }
  return true;   // let the browser submit the form natively
}
function fillEdit(pv,label,fmt,period,mode){
  setField('f_pv',pv); setField('f_label',label);
  setField('f_fmt',fmt||'Plot'); setField('f_period',period||'1'); setField('f_mode',mode||'Monitor');
  var pvf=document.getElementById('f_pv');
  pvf.name='EDIT'; pvf.readOnly=true;        // submit as an edit, lock the PV
  document.getElementById('f_submit').value='Save changes';
  document.getElementById('formtitle').innerHTML='Edit channel: '+pv;
  pvf.focus();
}
function resetForm(){
  var pvf=document.getElementById('f_pv');
  pvf.name='ADD'; pvf.readOnly=false; pvf.value='';
  setField('f_label',''); setField('f_fmt','Plot'); setField('f_period','1'); setField('f_mode','Monitor');
  document.getElementById('f_submit').value='Add channel';
  document.getElementById('formtitle').innerHTML='Add a channel to this section';
}
%s
</script>""" % self._auto_edit_js())
        h.append('</div>')
        h.append('</body></html>')
        return "\n".join(h)


def main(outStream=GEAVars.outStream, standAlone=False):
    EditChannelsPage(outStream, standAlone).run()


if __name__ == "__main__":
    main(GEAVars.outStream, standAlone=True)
