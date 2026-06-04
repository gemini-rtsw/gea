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
    ACTION=export   submit a new export (ticked EXPORTCHAN boxes and/or CHANNELS
                    field, plus the time-selector widget)
    ACTION=delete & JOBID=<id>     remove a job's status + gzip

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


# Bump when the channel-tree structure or build logic changes, so a deploy
# invalidates any cached channel_tree.<ver>.html instead of serving a stale layout.
_TREE_CACHE_VERSION = 3

# Tree top level: menu category -> [(display label, <page>.channels file), ...],
# mirroring the GEA side menu so the export tree matches what users browse. Pages
# that don't exist (or are empty) at a given site are simply skipped at render time.
_MENU_TREE = [
    ('Systems', [
        ('A&G', 'systems/agPage.channels'),
        ('CRCS', 'systems/crcsPage.channels'),
        ('ECS', 'systems/ecsPage.channels'),
        ('GIS', 'systems/gisPage.channels'),
        ('GWS (Weather)', 'systems/gwsPage.channels'),
        ('Laser', 'systems/laserPage.channels'),
        ('  BTO', 'systems/laser/btoPage.channels'),
        ('  LIS', 'systems/laser/lisPage.channels'),
        ('  LSE', 'systems/laser/lsePage.channels'),
        ('LGSF', 'systems/lgsfPage.channels'),
        ('M2TS', 'systems/m2tsPage.channels'),
        ('MCS', 'systems/mcsPage.channels'),
        ('PCS', 'systems/pcsPage.channels'),
        ('PR', 'systems/prPage.channels'),
        ('SCS', 'systems/scsPage.channels'),
        ('TCS', 'systems/tcsPage.channels'),
        ('WFS', 'systems/wfsPage.channels'),
        ('ASCAM', 'systems/ascamPage.channels'),
    ]),
    ('Instruments', [
        ('Altair', 'instruments/altairPage.channels'),
        ('GMOS', 'instruments/gmosPage.channels'),
        ('GNIRS', 'instruments/gnirsPage.channels'),
        ('GPOL/GCAL', 'instruments/gpolGcalPage.channels'),
        ('IGRINS-2', 'instruments/igrins2Page.channels'),
        ('Michelle', 'instruments/michellePage.channels'),
        ('NIFS', 'instruments/nifsPage.channels'),
        ('NIRI', 'instruments/niriPage.channels'),
        ('NIRI Focus', 'instruments/niri/niriFocusPage.channels'),
        ('TReCS', 'instruments/trecsPage.channels'),
        ('bHROS', 'instruments/bhrosPage.channels'),
    ]),
    ('Engineering', [
        ('Environment', 'engineering/environmentPage.channels'),
        ('Telescope', 'engineering/telescopePage.channels'),
        ('IQ', 'engineering/iqPage.channels'),
        ('Seeing Monitor', 'engineering/seeingMonitorPage.channels'),
        ('Altair', 'engineering/altairPage.channels'),
        ('GMOS', 'engineering/gmosPage.channels'),
        ('GNIRS', 'engineering/gnirsPage.channels'),
        ('Michelle', 'engineering/michellePage.channels'),
        ('NIFS', 'engineering/nifsPage.channels'),
        ('NIRI', 'engineering/niriPage.channels'),
        ('NIRI Focus', 'engineering/niriFocusPage.channels'),
        ('TReCS', 'engineering/trecsPage.channels'),
        ('bHROS', 'engineering/bhrosPage.channels'),
    ]),
    ('Compilations', [
        ('Calibrations', 'compilations/calPage.channels'),
        ('IQ', 'compilations/iqPage.channels'),
        ('Sensors', 'compilations/sensorsPage.channels'),
        ('Temporary', 'compilations/temporaryPage.channels'),
        ('Versions', 'compilations/versionsPage.channels'),
    ]),
]


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


def _jsStr(s):
    """A safe single-quoted JS string literal for s (used for the poll URL)."""
    s = (s or '').replace('\\', '\\\\').replace("'", "\\'")
    return "'" + s + "'"


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

        # Status poll (ACTION=status, standalone): the doc is already a bare container
        # and _processRequest will append just the recent-exports table. Skip building
        # the heavy form/tree -- it isn't shown and would waste the cache read.
        if 'ACTION=status' in GEAVars.environ.get('QUERY_STRING', ''):
            return

        # Intro.
        html.intro = HTMLTextBox(vars={'text':
            "Download raw engineering data as a ZIP of per-channel CSV files (one file "
            "per channel, columns: timestamp,value; timestamps are full ISO date+time). "
            "Every archived sample in the range is included; no decimation or "
            "interpolation is applied.\n"
            "Exports run in the background and appear in 'Recent exports' below, with "
            "progress, offering a download link when ready."})
        html.doc.append(html.intro)

        # Export form. HTMLFormCont's default submit button says "Update" (it's the
        # generic plotter form); relabel it "Download" for this page by overriding the
        # instance's header/footer -- without touching the shared class.
        html.form = HTMLFormCont(vars={'cgifile': self.calledName})
        _submit = ('<div align="center">'
                   '<input type="submit" value="Download" '
                   'onClick="return globalSubmit();"><hr></div>')
        # GET (the proven path every other GEA page uses). The tree no longer submits a
        # checkbox per channel -- the selection is collapsed client-side into the single
        # CHANNELS field -- so the URL stays short for normal use and there's no POST-
        # body parsing to depend on.
        html.form.header = ['<form METHOD="GET" ACTION="%(cgifile)s">\n'
                            '<script language="JavaScript">\n'
                            'var globalSubmitFunctions=new Array();\n'
                            'function globalSubmit(){'
                            'for(var i=0;i<globalSubmitFunctions.length;i++){'
                            'if(!globalSubmitFunctions[i]()){return false;}}return true;}'
                            '</script>\n' + _submit]
        html.form.footer = [_submit + '</form>']
        html.doc.append(html.form)

        # Simple start/end selector (no plotter entry-list / "fix time" management),
        # defaulting to the last 24h.
        html.timeSelector = HTMLTimeSelectorSimple()
        html.timeSelector.vars.update(Time.startEndTime2Dict(
            Time(self.genTime.seconds - Time.secPerDay), self.genTime,
            allCaps=False, monthAsWord=True))
        html.form.append(html.timeSelector)

        # Checkbox tree of ALREADY-ARCHIVED channels, grouped as on the GEA pages.
        # Ticking a channel adds it to the export -- plain HTML checkboxes, submitted
        # natively. Below it, a single text field to list channel names directly.
        html.form.append(HTMLCont(body=[self._channelTreeHTML()]))
        html.form.append(HTMLCont(body=[self._channelListFieldHTML()]))

        # The submit ("Update") in HTMLFormCont posts the form; ACTION marks it as an
        # export request (vs. the page just rendering the recent-exports table).
        html.form.append(HTMLCont(body=[
            '<input type="hidden" name="ACTION" value="export">']))

    def _channelTreeHTML(self):
        """Cached wrapper around _buildChannelTreeHTML. Building the tree expands every
        pattern in 48 page files against ~4700 PVs (~24M regex ops) and emits thousands
        of checkboxes -- far too slow to do on every CGI request. So we render it once,
        cache the HTML to a file, and serve that until it ages out (lazy rebuild; no
        cron needed). genTime gives the cache its 'now' for the age check.

        The cache filename carries a version tag: bump _TREE_CACHE_VERSION whenever the
        tree's structure/build logic changes, so a deploy automatically invalidates the
        old cache instead of serving a stale layout for up to a day."""
        return GEAExport.cachedHTML('channel_tree.%s.html' % _TREE_CACHE_VERSION,
                                    self._buildChannelTreeHTML,
                                    now=self.genTime.seconds)

    def _buildChannelTreeHTML(self):
        """A collapsible checkbox tree that mirrors the GEA page grouping: menu category
        -> page -> Section -> Cell -> channels (with the human labels from the page
        files). Built from the same <page>.channels files the system/engineering/etc.
        pages render, so it matches what users see on those displays.

        Page lines that are regex patterns (the GEA default) are expanded against the
        live archived-PV list (GEAExport.expandPattern) so every checkbox is a concrete,
        individually selectable PV. Plain HTML checkboxes (name=EXPORTCHAN) -- the
        browser submits the checked values natively, no JS."""
        out = ['<div align="center"><table width="700"><tr><td>',
               '<b>Archived channels</b> &mdash; tick to include in the export '
               '(grouped as on the GEA pages):',
               '<div style="max-height:380px;overflow:auto;border:1px solid #ccc;'
               'padding:6px;text-align:left;">']

        # Dedup is PER SECTION, not global: the same PV legitimately appears on more
        # than one GEA page (e.g. mc:elCurrentPos shows under MCS, GIS, and Telescope),
        # so a global 'seen' set would make it vanish from every page but the first one
        # rendered. Within a single section we still avoid an exact duplicate checkbox.
        for catName, pages in _MENU_TREE:
            out.append('<details><summary><b>%s</b></summary>'
                       '<div style="margin-left:1em;">' % _esc(catName))
            for pageLabel, pageFile in pages:
                sections = self._parsePageChannels(pageFile)
                if not sections:
                    continue
                out.append('<details style="margin-left:1em;"><summary>%s</summary>'
                           '<div style="margin-left:1em;">' % _esc(pageLabel))
                for secName, entries in sections:
                    out.append('<details style="margin-left:1em;"><summary>%s'
                               '</summary><div style="margin-left:1.5em;">'
                               % _esc(secName or '(unnamed)'))
                    seen = set()
                    for value, label, isPattern in entries:
                        pvs = GEAExport.expandPattern(value) if isPattern else [value]
                        for pv in pvs:
                            if pv in seen:
                                continue
                            seen.add(pv)
                            e = _esc(pv)
                            shown = e if not label else '%s <span style="color:#888;">'\
                                '(%s)</span>' % (e, _esc(label))
                            out.append('<label style="display:block;">'
                                       '<input type="checkbox" class="expchan" '
                                       'value="%s" onclick="exportSyncChannels()"> '
                                       '%s</label>' % (e, shown))
                    out.append('</div></details>')
                out.append('</div></details>')
            out.append('</div></details>')
        out.append('</div></td></tr></table></div>')
        out.append(self._channelSyncJS())
        return '\n'.join(out)

    def _channelSyncJS(self):
        """JS that keeps the 'Channels:' field in sync with the tree checkboxes. On any
        tick/untick (and once on load), the field is rebuilt as: the values of all
        checked tree boxes, PLUS any tokens the user typed that don't belong to a tree
        box (so manual entries survive). The field (CHANNELS) is what the form submits;
        the checkboxes themselves are not submitted."""
        return '''<script language="JavaScript">
function exportSyncChannels(){
  var fld=document.getElementById('exportChannels');
  if(!fld) return;
  var boxes=document.getElementsByClassName
            ? document.getElementsByClassName('expchan')
            : [];
  // Set of all known tree-channel values, and the set currently checked.
  var known={}, checked=[];
  for(var i=0;i<boxes.length;i++){
    known[boxes[i].value]=1;
    if(boxes[i].checked) checked.push(boxes[i].value);
  }
  // Keep manually-typed tokens that aren't tree channels.
  var manual=[], toks=fld.value.split(/\\s+/);
  for(var j=0;j<toks.length;j++){
    if(toks[j] && !known[toks[j]] && manual.indexOf(toks[j])==-1) manual.push(toks[j]);
  }
  fld.value=checked.concat(manual).join(' ');
}
// Reflect any pre-checked state on load.
if(window.addEventListener){ window.addEventListener('load', exportSyncChannels, false); }
</script>'''

    def _parsePageChannels(self, pageFile):
        """Parse a GEA <page>.channels file into [(sectionName, [(value, label,
        isPattern), ...]), ...], preserving the section/cell grouping and the human
        labels. Mirrors HTMLDynChanTable's line format: '#[SECTION] name', '#[CELL]
        name' (a labeled sub-group), and channel lines '<value> [C] {query} # label'
        where [C] marks a literal channel (else a regex pattern). Other '#[...]'
        option lines and site-mismatched [MK]/[CP] lines are skipped."""
        import GEAVars
        path = os.path.join(GEAVars.path.fileSys.geaConf, 'pages', pageFile)
        try:
            f = open(path)
            try:
                text = f.read()
            finally:
                f.close()
        except IOError:
            return []

        site = GEAVars.site
        sections = []
        cur = None        # (name, entries)
        for raw in text.split('\n'):
            line = raw.rstrip()
            if line.strip() == '':
                continue
            # Site gating on any line.
            skip = False
            for s in ('[MK]', '[CP]'):
                if s in line:
                    if s[1:3] != site:
                        skip = True
                        break
                    line = line.replace(s, '')
            if skip:
                continue

            if line.startswith('#[SECTION]'):
                cur = (line[len('#[SECTION]'):].strip(), [])
                sections.append(cur)
                continue
            if line.startswith('#[CELL]'):
                continue   # a cell is just a visual label; flatten its channels in
            if line.startswith('#'):
                continue   # other options / comments

            # A channel/pattern line. Strip [C] (literal), [FORMAT1], {query}.
            isPattern = True
            if '[C]' in line:
                line = line.replace('[C]', '')
                isPattern = False
            line = line.replace('[FORMAT1]', '')
            b, e = line.find('{'), line.find('}')
            if -1 < b < e:
                line = line[:b] + line[e + 1:]
            # Human label after '#'.
            i = line.find('#')
            if i > 0:
                value = line[:i].strip()
                label = line[i:].lstrip('#').strip()
            else:
                value = line.strip()
                label = ''
            if not value:
                continue
            if cur is None:
                cur = ('', [])
                sections.append(cur)
            cur[1].append((value, label, isPattern))
        return sections

    def _channelListFieldHTML(self):
        """The single source of truth for what gets exported: a text field holding the
        space-separated channel list. Ticking boxes in the tree auto-fills this field
        (exportSyncChannels), and you can also type/edit names directly. The form
        submits THIS field (CHANNELS) -- the tree checkboxes are not submitted
        themselves, so it doesn't matter how many you tick."""
        cur = _esc(self._params.get('CHANNELS', '')) if hasattr(self, '_params') else ''
        return (
            '<div align="center"><table width="700">'
            '<tr><td width="13%%" class="widgetChanSelLabel">Channels:</td>'
            '<td><input type="text" id="exportChannels" name="CHANNELS" size="70" '
            'maxlength="100000" value="%s"> '
            '<span style="color:#888;">(ticked tree channels appear here; you can '
            'also edit)</span></td></tr>'
            '</table></div>'
        ) % cur

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
                  "CHANNELS",
                  "STARTYEAR", "STARTMONTH", "STARTDAY", "STARTHOUR",
                  "STARTMINUTE", "STARTSECOND",
                  "ENDYEAR", "ENDMONTH", "ENDDAY", "ENDHOUR",
                  "ENDMINUTE", "ENDSECOND"):
            v = request.get(k, "")
            if v != "" and k not in self._params:
                self._params[k] = v

        p = self._params
        action = p.get("ACTION", "")

        if self._acted:
            return
        self._acted = True

        # Status fragment: return ONLY the recent-exports table, standalone. The page's
        # JS polls this every few seconds while a job builds, swapping it into the
        # status div -- so the channel tree (and any groups you've opened) stay put.
        # This replaced a full-page meta-refresh, which collapsed the tree each poll.
        if action == "status":
            self.standAlone = True
            widget, _building = self._recentExportsWidget()
            self.html.doc.append(widget)
            return

        if action in ("export", "delete"):
            # State-changing actions: do the work, then bounce the browser to the clean
            # page URL (Post/Redirect/Get). Otherwise the browser sits on the
            # ACTION=export POST result, and a refresh re-submits it -> a duplicate
            # export every refresh. location.replace so the action URL isn't kept in
            # history (a back-button press won't re-fire it either).
            try:
                if action == "delete" and p.get("JOBID", ""):
                    GEAExport.deleteJob(p["JOBID"])
                elif action == "export":
                    # _doExport returns a non-empty string on a validation problem
                    # (e.g. no channels picked); show it instead of redirecting so the
                    # user sees what to fix.
                    err = self._doExport(p, stream)
                    if err:
                        self._note = err
                        self._renderResults(request)
                        return
            except Exception, e:
                # Show the error rather than redirecting, so it isn't lost.
                self._note = "Error: %s" % e
                self._renderResults(request)
                return
            self._renderRedirect()
            return

        self._renderResults(request)

    def _renderRedirect(self):
        """Bounce to the clean page URL after a state-changing action (PRG). Rendered
        as a tiny standalone page: run() has already sent the text/html header, so we
        can't issue an HTTP 3xx -- a client-side location.replace achieves the same
        thing (and drops the action URL from history so refresh/back won't re-fire)."""
        self.standAlone = True
        url = self.calledName
        self.html.doc.append(HTMLCont(body=[
            '<html><head><meta http-equiv="refresh" content="0; url=%s">'
            '<script>window.location.replace(%s);</script></head>'
            '<body>Working&hellip; <a href="%s">continue</a></body></html>'
            % (url, _jsStr(url), url)]))

    # ---- actions -----------------------------------------------------------

    def _doExport(self, p, stream):
        """Validate the request and spawn the background export. Returns an error
        message string on a validation problem, or None on success (the caller then
        redirects to the clean page, where the new job shows as 'building...')."""
        startTime = Time().fromStartTimeDict(p, allCaps=True, monthAsWord="Auto")
        endTime = Time().fromEndTimeDict(p, allCaps=True, monthAsWord="Auto")

        # Channels all come from the single CHANNELS field: the tree checkboxes auto-fill
        # it client-side (exportSyncChannels) and the user can also type names. De-dup,
        # keep order. The page deals only in explicit names (no pattern field), though
        # the export backend still supports patterns.
        typed = (p.get('CHANNELS', '') or '').split()
        channels = []
        for c in typed:
            if c not in channels:
                channels.append(c)
        patterns = []

        if not channels:
            return "Please tick at least one channel, or list channel names."
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

        # ALWAYS run in the background. Running even a "small" export inline blocks the
        # web request -- and ArchiveExport can take minutes (or many calls, when the
        # corrupt-file bisection kicks in), which made "Download" hang the browser.
        # Record RUNNING now so the job appears immediately, then spawn the detached
        # worker and return at once; the poller shows progress and the link when ready.
        GEAExport.writeStatus(jobid, RUNNING, "Queued...", meta)
        self._spawnWorker(jobid, archivers, channels, patterns, startTime, endTime)
        return None   # success -> caller redirects to the clean page

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
        """Top-of-page note + the recent-exports table (wrapped in #exportStatus).
        Restores the submitted time range. If any job is building, appends the poll JS
        that refreshes only that table in place until the job finishes."""
        if self._note:
            # The note can carry exception text derived from user input, so escape HTML
            # metacharacters. _esc also neutralizes '%', which matters because the note
            # is substituted into the HTMLTextBox body and then runs through the
            # widget's `% self.taggedVars` pass.
            self.html.doc.insert(0, HTMLTextBox(vars={'text': _esc(self._note)}))

        widget, building = self._recentExportsWidget()
        # Wrap the table in a div the JS can refresh in place. Polling only this div
        # (not a full-page reload) leaves the channel tree and any groups you've opened
        # untouched while a job builds.
        self.html.doc.append(HTMLCont(body=['<div id="exportStatus">']))
        self.html.doc.append(widget)
        self.html.doc.append(HTMLCont(body=['</div>']))
        if building:
            self.html.doc.append(HTMLCont(body=[self._statusPollJS()]))

        # Restore the submitted time range into the selector. (The channel tree and
        # text fields render their own state from self._params directly.)
        self._setWidgetVars(self.html.timeSelector, self._params, [])

    def _statusPollJS(self):
        """JS that refreshes ONLY the #exportStatus div (the recent-exports table) every
        5s by fetching ACTION=status, leaving the channel tree untouched. Stops polling
        once the fetched fragment no longer contains a 'building' job. Falls back to
        XMLHttpRequest so it works on older browsers in the control room."""
        # STANDALONE=true makes run() build a bare container (no header/side-menu) so
        # the fetched fragment is just the table.
        url = '%s?ACTION=status&STANDALONE=true' % self.calledName
        return ('''<script language="JavaScript">
(function(){
  var url=%s, timer=null;
  function poll(){
    var x=new XMLHttpRequest();
    x.open('GET', url, true);
    x.onreadystatechange=function(){
      if(x.readyState!=4) return;
      if(x.status==200 && x.responseText){
        var d=document.getElementById('exportStatus');
        if(d){ d.innerHTML=x.responseText; }
        // Keep polling only while something is still building.
        if(x.responseText.indexOf('<!--BUILDING-->')==-1){
          if(timer){ clearInterval(timer); timer=null; }
        }
      }
    };
    x.send();
  }
  timer=setInterval(poll, 5000);
})();
</script>''' % _jsStr(url))

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
            if state == DONE and job['ready']:
                dl = HtmlHelper.createLink(
                    'ZIP',
                    os.path.join(GEAVars.path.web.exports, job['jobid'] + '.zip'))
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
        if building:
            # Explicit marker the poll JS keys off (don't rely on matching visible
            # text, which a channel name could coincidentally contain).
            rows.append('<!--BUILDING-->')
        return HTMLCont(body=['\n'.join(rows)]), building


def main(outStream=GEAVars.outStream, standAlone=False):
    DataExportPage(outStream, standAlone).run()


if __name__ == '__main__':
    main()
