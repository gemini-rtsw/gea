#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
dataExportPage - download long-term RAW engineering data as a gzipped CSV.

The plotter's Spreadsheet button runs ArchiveExport synchronously inside the web
request, so long ranges time out and the output is padded text rather than CSV. This
page is the robust alternative for bulk/long-term downloads:

  * pick any number of channels (or a pattern) + a time range
  * get a *long-format*, gzipped CSV: one row per (channel, sample) --
    channel,timestamp,value,status -- with NO point cap, decimation, or interpolation
  * small requests run inline and return a link immediately; large ones are handed to
    a detached worker (bin/gea_export_worker) and the page shows a job you can poll
  * a "Recent exports" table lists every job in the exports dir (shared by everyone),
    so you can close the browser and come back later to grab the gzip, or delete one

Query params:
    ACTION=export   submit a new export (with SYSTEMS/CHANNELS/PATTERN + time widget)
    ACTION=delete & JOBID=<id>     remove a job's status + gzip
    JOBID=<id> & POLL=1            return just that job's current status (for polling)

The backend (sizing, ArchiveExport, CSV conversion, status files) lives in
pyGEA/GEAExport.py and is shared with the worker.

Python 2 (GEA frontend).
"""

import cgi
import os
import subprocess

import GEAVars
import GEAExport
from GEAExport import RUNNING, DONE, ERROR
from GEAHtml import HTMLFormCont, HTMLTimeSelectorSimple, \
    HTMLTextBox, HTMLCont, HtmlHelper
from GEARequest import RequestCollection, Request
from GEATime import Time
from pages.geaBasePage import GeaBasePage


def _esc(s):
    """Make an untrusted string safe to splice into the recent-exports HTML. Channel
    names / patterns / ArchiveExport error text are user- or data-controlled and the
    table is shared by all users, so two hazards:

      * HTML metacharacters -> stored XSS. cgi.escape(quote=True) handles these.
      * '%(...)s' sequences -> HTMLObject.__str__ runs the HTMLCont body through
        `% self.vars` then `% self.taggedVars` (GEAHtml.py). self.vars is a StrDict
        that returns missing keys verbatim (so it won't KeyError), but a value like
        '%(JS)s' could still be silently rewritten to the widget's JS tag.

    Replacing '%' with the HTML entity '&#37;' removes the second hazard cleanly: the
    rendered output is still '%', but the string handed to the format passes contains
    no literal '%', so no value can be reinterpreted as a format spec."""
    return cgi.escape(s or '', quote=True).replace('%', '&#37;')


def _fmtSize(nbytes):
    """Human-readable file size."""
    n = float(nbytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024.0 or unit == 'GB':
            return "%.0f %s" % (n, unit) if unit == 'B' else "%.1f %s" % (n, unit)
        n /= 1024.0


class DataExportPage(GeaBasePage):
    """Long-term raw data export page."""

    def _assemblePage(self, topMenuList=None):
        GeaBasePage._assemblePage(self, topMenuList=topMenuList)
        html = self.html
        self._note = None        # message shown at the top after an action

        # Intro.
        html.intro = HTMLTextBox(vars={'text':
            "Download raw engineering data as a gzipped CSV (long format: one row per "
            "channel sample -- channel,timestamp,value,status). Every archived sample "
            "in the range is included; no decimation or interpolation is applied.\n"
            "Small requests download right away; large ones run in the background and "
            "appear in 'Recent exports' below when ready."})
        html.doc.append(html.intro)

        # Export form.
        html.form = HTMLFormCont(vars={'cgifile': self.calledName})
        html.doc.append(html.form)

        # Simple start/end selector (no plotter entry-list / "fix time" management),
        # defaulting to the last 24h.
        html.timeSelector = HTMLTimeSelectorSimple()
        html.timeSelector.vars.update(Time.startEndTime2Dict(
            Time(self.genTime.seconds - Time.secPerDay), self.genTime,
            allCaps=False, monthAsWord=True))
        html.form.append(html.timeSelector)

        # Checkbox tree of ALREADY-ARCHIVED channels (built from the same hierarchy file
        # the plotter uses). Ticking a channel adds it to the export -- plain HTML
        # checkboxes, submitted natively, so it does not depend on the add-button JS
        # that was failing. A free-text field is kept for power users / patterns.
        html.form.append(HTMLCont(body=[self._channelTreeHTML()]))
        html.form.append(HTMLCont(body=[self._channelTextFieldsHTML()]))

        # The submit ("Update") in HTMLFormCont posts the form; ACTION marks it as an
        # export request (vs. the page just rendering the recent-exports table).
        html.form.append(HTMLCont(body=[
            '<input type="hidden" name="ACTION" value="export">']))

    def _channelTreeHTML(self):
        """A collapsible checkbox tree of already-archived channels, built from the
        LIVE archiver list -- grouped by archiver, from the data server (the same
        backend the GEA system pages resolve against), so it matches what those pages
        show. Each leaf channel is a plain HTML checkbox (name=EXPORTCHAN,
        value=<channel>); checking it includes that channel in the export. No
        JavaScript -- the browser submits the checked values natively, which is why
        this works where the old add-button flow did not.

        NOT built from plotterPage.channels: that is a hand-maintained ~500-channel
        'favorites' file that nothing keeps in sync, so it did not match reality."""
        try:
            groups = GEAExport.archivedChannelTree()
        except Exception, e:
            return ('<div class="widgetChanSelLabel">Channel list unavailable '
                    '(data server): %s</div>' % _esc(str(e)))

        if not groups:
            return ('<div class="widgetChanSelLabel">No archived channels reported by '
                    'the data server.</div>')

        out = ['<div align="center"><table width="700"><tr><td>',
               '<b>Archived channels</b> &mdash; tick to include in the export '
               '(grouped by archiver):',
               '<div style="max-height:360px;overflow:auto;border:1px solid #ccc;'
               'padding:6px;text-align:left;">']
        for archiver, channels in groups:
            out.append('<details><summary><b>%s</b> (%d)</summary>'
                       '<div style="margin-left:1.5em;">'
                       % (_esc(archiver), len(channels)))
            for ch in channels:
                e = _esc(ch)
                out.append('<label style="display:block;"><input type="checkbox" '
                           'name="EXPORTCHAN" value="%s"> %s</label>' % (e, e))
            out.append('</div></details>')
        out.append('</div></td></tr></table></div>')
        return '\n'.join(out)

    def _channelTextFieldsHTML(self):
        """Free-text Channels / Pattern fields for users who already know PV names or
        want a regex. Combined with whatever is ticked in the tree."""
        return (
            '<div align="center"><table width="700">'
            '<tr><td width="13%%" class="widgetChanSelLabel">Channels:</td>'
            '<td><input type="text" name="CHANNELS" size="60" maxlength="500" '
            'value="%s"> <span style="color:#888;">(space-separated PV names; '
            'optional &mdash; or use the tree above)</span></td></tr>'
            '<tr><td width="13%%" class="widgetChanSelLabel">Pattern:</td>'
            '<td><input type="text" name="PATTERN" size="60" maxlength="256" '
            'value="%s"> <span style="color:#888;">(optional regex, e.g. '
            'm1:ANB1.*:binDmdRbk1)</span></td></tr>'
            '</table></div>'
        ) % (_esc(self._params.get('CHANNELS', '') if hasattr(self, '_params') else ''),
             _esc(self._params.get('PATTERN', '') if hasattr(self, '_params') else ''))

    def _getLocalRequests(self):
        # Always run _processRequest, even with an empty query string, so the recent
        # exports table renders on a bare page load.
        return RequestCollection({None: Request()})

    def _processRequest(self, request, stream):
        # GEA may split one submit across several Request objects; merge the keys we
        # care about across calls (same approach as editChannelsPage).
        if not hasattr(self, "_params"):
            self._params = {}
            self._acted = False
        for k in ("ACTION", "JOBID", "SYSTEMS", "SYSTEMS2",
                  "CHANNELS", "PATTERN", "EXPORTCHAN",
                  "STARTYEAR", "STARTMONTH", "STARTDAY", "STARTHOUR",
                  "STARTMINUTE", "STARTSECOND",
                  "ENDYEAR", "ENDMONTH", "ENDDAY", "ENDHOUR",
                  "ENDMINUTE", "ENDSECOND"):
            v = request.get(k, "")
            if v != "" and k not in self._params:
                self._params[k] = v

        p = self._params
        action = p.get("ACTION", "")

        if not self._acted:
            self._acted = True
            try:
                if action == "delete" and p.get("JOBID", ""):
                    GEAExport.deleteJob(p["JOBID"])
                    self._note = "Deleted export %s." % p["JOBID"]
                elif action == "export":
                    self._note = self._doExport(p, stream)
            except Exception, e:
                self._note = "Error: %s" % e

            self._renderResults(request)

    # ---- actions -----------------------------------------------------------

    def _doExport(self, p, stream):
        """Validate the request, then run inline (small) or spawn the worker (large).
        Returns the note to show at the top of the page."""
        startTime = Time().fromStartTimeDict(p, allCaps=True, monthAsWord="Auto")
        endTime = Time().fromEndTimeDict(p, allCaps=True, monthAsWord="Auto")

        # Channels come from the checkbox tree (EXPORTCHAN, space-joined by the request
        # parser) and/or the free-text Channels field; merge and de-dup, keeping order.
        ticked = (p.get('EXPORTCHAN', '') or '').split()
        typed = (p.get('CHANNELS', '') or '').split()
        channels = []
        for c in ticked + typed:
            if c not in channels:
                channels.append(c)
        patterns = GEAExport.patternList({'PATTERN': p.get('PATTERN', '')})

        if not channels and not patterns:
            return ("Please tick at least one channel in the tree, or enter a "
                    "channel/pattern.")
        if int(endTime.seconds) <= int(startTime.seconds):
            return "End time must be after start time."

        # Systems are optional: the export reads the master index (which spans every
        # archiver) and selects by -match, so an explicit SYSTEMS list is only used for
        # the input-injection guard / record-keeping. Empty is fine when the user only
        # ticked tree channels.
        archivers = GEAExport.epicsArchivers(
            {'SYSTEMS': p.get('SYSTEMS', ''), 'SYSTEMS2': p.get('SYSTEMS2', '')})

        jobid = GEAExport.newJobId()
        meta = {'channels': ' '.join(channels + patterns),
                'start': startTime.string16, 'end': endTime.string16,
                'created': Time().string16}

        if GEAExport.shouldRunInline(startTime, endTime, channels, patterns):
            GEAExport.runExport(jobid, archivers, channels, patterns,
                                startTime, endTime, meta)
            return "Export ready below."

        # Large: record a RUNNING status now (so it shows up immediately), then spawn
        # the detached worker to actually build it.
        GEAExport.writeStatus(jobid, RUNNING, "Queued...", meta)
        self._spawnWorker(jobid, archivers, channels, patterns, startTime, endTime)
        return ("Export started in the background (job %s). It will appear as 'Done' "
                "below when ready -- you can leave and come back." % jobid)

    def _spawnWorker(self, jobid, archivers, channels, patterns, startTime, endTime):
        """Launch gea_export_worker fully detached so it outlives this CGI request.

        channels/archivers never contain whitespace (EPICS naming), so they round-trip
        through a space-joined arg. A PATTERN may contain spaces, so it goes as its own
        single arg (at most one) rather than being space-joined and re-split."""
        worker = os.path.join(GEAVars.path.fileSys.bin, 'gea_export_worker.py')
        cmd = [worker,
               '--jobid', jobid,
               '--archivers', ' '.join(archivers),
               '--channels', ' '.join(channels),
               '--start', repr(float(startTime.seconds)),
               '--end', repr(float(endTime.seconds))]
        if patterns:
            cmd += ['--pattern', patterns[0]]
        # close_fds so the child doesn't keep the request's socket open; the worker
        # itself does setsid()+stdio redirect to finish detaching.
        subprocess.Popen(cmd, close_fds=True,
                         stdin=open(os.devnull, 'r'),
                         stdout=open(os.devnull, 'w'),
                         stderr=open(os.devnull, 'w'))

    # ---- rendering ---------------------------------------------------------

    def _renderResults(self, request):
        """Top-of-page note + the recent-exports table. Restores the form fields the
        user submitted so a re-submit is easy. If any job is still building, emits a
        meta-refresh so the page reloads itself (and the download link appears) when
        the worker finishes -- no JS, no manual refresh, and it stops once all done."""
        if self._note:
            # The note can carry exception text derived from user input, so escape HTML
            # metacharacters. _esc also neutralizes '%', which matters because the note
            # is substituted into the HTMLTextBox body and then runs through the
            # widget's `% self.taggedVars` pass.
            self.html.doc.insert(0, HTMLTextBox(vars={'text': _esc(self._note)}))

        widget, building = self._recentExportsWidget()
        if building:
            # Refresh to the CLEAN page URL (no query string), NOT the current one --
            # the current URL still carries ACTION=export & the channel/time params, so
            # a bare refresh would re-submit the export every interval (a pile of dup
            # jobs). Pointing at calledName just re-renders the listing until done.
            self.html.doc.insert(0, HTMLCont(body=[
                '<meta http-equiv="refresh" content="5; url=%s">' % self.calledName]))
        self.html.doc.append(widget)

        # Restore the submitted time range into the selector. (The channel tree and
        # text fields render their own state from self._params directly.)
        self._setWidgetVars(self.html.timeSelector, self._params, [])

    def _recentExportsWidget(self):
        """An HTML table of every job in the exports dir, newest first, with a
        download link (when ready), status, size, time range, and a Delete link.
        Returns (widget, building) where `building` is True if any job is still
        running (used to drive the page auto-refresh)."""
        building = False
        rows = ['<table class="textBox2" border="1" cellpadding="4">',
                '<tr><th>Created</th><th>Channels</th><th>Range</th>'
                '<th>Status</th><th>Size</th><th>Download</th><th></th></tr>']

        jobs = GEAExport.listJobs()
        if not jobs:
            rows.append('<tr><td colspan="7"><i>No exports yet.</i></td></tr>')

        for job in jobs:
            state = job['state']
            if state == DONE and job['gzReady']:
                dl = HtmlHelper.createLink(
                    'CSV (gz)',
                    os.path.join(GEAVars.path.web.exports, job['jobid'] + '.csv.gz'))
                size = _fmtSize(job['size'])
            elif state == ERROR:
                dl = ''
                size = ''
            else:
                dl = '<i>building...</i>'
                size = ''
                building = True

            status = _esc(state)
            if job['message']:
                status += ': ' + _esc(job['message'])

            delLink = HtmlHelper.createLink('Delete', self.calledName,
                                            ACTION='delete', JOBID=job['jobid'])

            rng = '%s &rarr; %s' % (_esc(job.get('start', '')),
                                    _esc(job.get('end', '')))
            rows.append(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                '<td>%s</td><td>%s</td><td>%s</td></tr>' % (
                    _esc(job.get('created', '')), _esc(job.get('channels', '')), rng,
                    status, size, dl, delLink))

        rows.append('</table>')
        return HTMLCont(body=['\n'.join(rows)]), building


def main(outStream=GEAVars.outStream, standAlone=False):
    DataExportPage(outStream, standAlone).run()


if __name__ == '__main__':
    main()
