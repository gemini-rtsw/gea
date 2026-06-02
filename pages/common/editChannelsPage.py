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
        # Render bare (no side menu/header) -- this opens in a small popup.
        self.standAlone = True
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)

    def _getLocalRequests(self):
        # Always process, even with no extra request keys, so the listing renders.
        return RequestCollection({None: Request()})

    def _processRequest(self, request, stream):
        html = self.html

        page    = request.get("PAGE", "")
        section = request.get("SECTION", "")
        add_pv  = request.get("ADD", "")
        del_pv  = request.get("DEL", "")
        fmt     = request.get("FORMAT", "")
        label   = request.get("LABEL", "")
        period  = request.get("PERIOD", "1")
        mode    = request.get("MODE", "Monitor")

        if not page or not section:
            html.doc.append("<p>Missing PAGE or SECTION.</p>")
            return

        archiver = _archiver_for_page(page)

        # Handle an add or delete action first, report the outcome.
        try:
            if add_pv:
                r = gea_channel.add_channel(archiver, add_pv, period=period,
                        mode=mode, page=page, section=section,
                        fmt=(fmt or None), label=(label or None))
                note = "Added '%s' to '%s'." % (r["pv"], section)
                if r.get("restarted"):
                    note += " Archiver '%s' restarted." % archiver
                for w in r.get("warnings", []):
                    note += " " + w
                stream.write(note)
            elif del_pv:
                r = gea_channel.delete_channel(archiver, del_pv,
                        page=page, section=section)
                note = "Deleted '%s' from '%s'." % (r["pv"], section)
                if r.get("restarted"):
                    note += " Archiver '%s' restarted." % archiver
                stream.write(note)
        except gea_channel.ChannelError, e:
            stream.write("Error: %s (no changes kept)" % e)
        except Exception, e:
            stream.write("Unexpected error: %s (no changes kept)" % e)

        # Render the section's current channels + the add form.
        html.doc.append(self._render(page, section, archiver))

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
        h.append('<div style="margin:1em; font-family:sans-serif;">')
        h.append("<h3>Edit channels &mdash; %s</h3>" % section)
        h.append("<p>Page: <code>%s</code>" % page)
        h.append("&nbsp; Archiver: <code>%s</code></p>"
                 % (archiver or "(none -- display only)"))

        h.append('<table border="1" cellpadding="4" cellspacing="0">')
        h.append("<tr><th>Channel</th><th>Label</th><th>Display</th>"
                 "<th>Period</th><th>Mode</th><th>Archived</th><th></th></tr>")
        for row in rows:
            delurl = "%s?%s" % (here, qp(PAGE=page, SECTION=section, DEL=row["pv"]))
            arch = "yes" if row.get("archived") else "<b>no</b>"
            h.append("<tr><td><code>%s</code></td><td>%s</td>"
                     "<td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                     '<td><a href="%s" onclick="return confirm('
                     "'Delete %s%s?')\">delete</a></td></tr>"
                     % (row["pv"], row["label"] or "&nbsp;",
                        row.get("format") or "Plot",
                        row.get("period") or "&nbsp;",
                        row.get("mode") or "&nbsp;",
                        arch, delurl, row["pv"],
                        (" and restart "+archiver) if archiver else ""))
        if not rows:
            h.append('<tr><td colspan="7"><i>No channels in this section yet.</i></td></tr>')
        h.append("</table>")

        # Add form (GET back to this page with ADD=...).
        h.append('<h4>Add a channel to this section</h4>')
        h.append('<form method="GET" action="%s">' % here)
        h.append('<input type="hidden" name="PAGE" value="%s"/>' % page)
        h.append('<input type="hidden" name="SECTION" value="%s"/>' % section)
        h.append('PV name: <input type="text" name="ADD" size="34" '
                 'placeholder="m1:x:y.VAL"/><br/>')
        h.append('Label: <input type="text" name="LABEL" size="34"/><br/>')
        h.append('Display as: <select name="FORMAT">'
                 '<option value="">Plot</option>'
                 '<option value="Plot">Plot</option>'
                 '<option value="Spreadsheet">Spreadsheet</option></select><br/>')
        h.append('Period (s): <input type="text" name="PERIOD" value="1" size="4"/> '
                 'Mode: <select name="MODE">'
                 '<option>Monitor</option><option>Scan</option></select><br/><br/>')
        h.append('<input type="submit" value="Add channel"/>')
        h.append('</form>')
        if archiver:
            h.append('<p style="color:#666;font-size:0.85em;">Adding a new PV '
                     'will restart archiver <code>%s</code> (a few seconds). '
                     'An already-archived PV is added to the display only.</p>'
                     % archiver)
        h.append('</div>')
        return "\n".join(h)


def main(outStream=GEAVars.outStream, standAlone=False):
    EditChannelsPage(outStream, standAlone).run()


if __name__ == "__main__":
    main(GEAVars.outStream, standAlone=True)
