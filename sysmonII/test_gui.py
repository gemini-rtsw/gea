#!/usr/bin/env python3
"""
Standalone test server for the sysmonII trigger settings GUI.
Loads the real sysmonII.json config so all channels are shown.

Usage: python3 test_gui.py
Then open http://localhost:8080
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Load real config
with open("sysmonII.json", "r") as f:
    CONFIG = json.load(f)

# Build monitor and system data from real config
MONITORS = {}   # uuid -> {pvname, description, trigger, meta}
SYSTEMS  = {}   # sysname -> {comment, monitors: [uuid,...], notify}

for sysname in CONFIG['systems']:
    sysconf = CONFIG['systems'][sysname]
    uuids = []
    for offset, monconf in enumerate(sysconf['monitor']):
        uuid = "%s:%d" % (sysname, offset)
        uuids.append(uuid)
        MONITORS[uuid] = {
            "pvname": monconf['pvname'],
            "description": monconf.get('description', ''),
            "trigger": monconf['trigger'],
            "filter": monconf.get('filter', {}),
            "options": monconf.get('options', {}),
            "meta": {
                "status": "OK",
                "value": "-",
                "host": "test-mode",
                "type": "unknown",
                "uuid": uuid,
            }
        }
    SYSTEMS[sysname] = {
        "comment": sysconf.get('comment', ''),
        "monitors": uuids,
        "notify": sysconf.get('notify', ''),
        "notify2": sysconf.get('notify2', None),
    }

print("Loaded %d systems, %d monitors from sysmonII.json" % (len(SYSTEMS), len(MONITORS)))


def validate_trigger(trigger):
    """Validate trigger settings. Returns error string or None if valid."""
    if not isinstance(trigger, dict) or len(trigger) == 0:
        return "Trigger must be a non-empty object"

    keys = set(trigger.keys())
    valid_types = [
        {'low', 'high'}, {'low'}, {'high'}, {'exact'}, {'not'},
        {'heartbeat', 'rate'}, {'heartbeat'}, {'null'}, {'slope'},
    ]
    if keys not in valid_types:
        return "Invalid trigger key combination: %s" % keys

    for k in ('low', 'high', 'heartbeat', 'rate'):
        if k in trigger:
            if not isinstance(trigger[k], (int, float)):
                return "'%s' must be a number, got: %s" % (k, type(trigger[k]).__name__)

    if 'low' in trigger and 'high' in trigger:
        if trigger['low'] >= trigger['high']:
            return "Low (%s) must be less than high (%s)" % (trigger['low'], trigger['high'])

    if 'heartbeat' in trigger and trigger['heartbeat'] <= 0:
        return "Heartbeat must be greater than 0"

    if 'rate' in trigger and trigger['rate'] <= 0:
        return "Rate must be greater than 0"

    if 'exact' in trigger or 'not' in trigger:
        val = trigger.get('exact', trigger.get('not'))
        if not isinstance(val, (str, int, float)):
            return "exact/not value must be a string or number"

    return None


def build_html():
    """Build the main page HTML mimicking showMonitor()."""
    html = """<html>
 <head>
  <title> System Monitor II - TEST </title>
  <link rel="stylesheet" href="sysmonII.css"/>
  <script src="sysmonII.js"> </script>
 </head>
 <body onLoad="main();">
  <h3 style="color:orange; font-family:arial;">TEST MODE - Real Config, No EPICS</h3>
  <table>
"""
    for sysname in sorted(SYSTEMS):
        sys = SYSTEMS[sysname]
        html += '  <tr><td class="goodsysname">%s</td><td colspan="6">%s</td></tr>\n' % (sysname.upper(), sys["comment"])
        html += '  <tr><td class="heading">Channel&nbsp;Name</td>'
        html += '<td class="heading">&nbsp;</td>'
        html += '<td class="heading">Value (Filtered)</td>'
        html += '<td class="heading">Description</td>'
        html += '<td class="heading">Filter</td>'
        html += '<td class="heading">Trigger</td>'
        html += '<td class="heading">Options</td></tr>\n'

        for uuid in sys["monitors"]:
            mon = MONITORS[uuid]

            # Format filter string
            fmsg = []
            for flt in mon["filter"]:
                if flt == 'null': continue
                fmsg.append("%s:%s" % (flt, mon["filter"][flt]))
            fstr = ", ".join(fmsg) if fmsg else "-"

            # Format trigger string
            tmsg = []
            for tgr in mon["trigger"]:
                if tgr == "not" or tgr == "exact":
                    tmsg.append('%s:"%s"' % (tgr, mon["trigger"][tgr]))
                else:
                    tmsg.append("%s:%s" % (tgr, mon["trigger"][tgr]))
            tstr = ", ".join(tmsg) if tmsg else "-"

            # Format options string
            omsg = []
            if mon["options"]:
                for opt in mon["options"]:
                    if type(mon["options"][opt]) == type(True):
                        omsg.append(opt)
                    else:
                        omsg.append("%s:%s" % (opt, mon["options"][opt]))
            ostr = ", ".join(omsg) if omsg else "-"

            html += '  <tr>'
            html += '<td>%s</td>' % mon["pvname"]
            html += '<td class="%s info" style="text-align:center;"></td>' % uuid
            html += '<td class="%s value">-</td>' % uuid
            html += '<td>%s</td>' % mon["description"]
            html += '<td>%s</td>' % fstr
            html += '<td>%s</td>' % tstr
            html += '<td>%s</td>' % ostr
            html += '</tr>\n'

        # Email rows with edit buttons
        html += '  <tr><td>Email List (Primary):</td><td colspan="6"><button type="button" onclick="showEmailEdit(\'%s\', \'notify\');">Edit</button> <span class="emaillist %s">%s</span></td></tr>\n' % (sysname, sysname, sys["notify"])
        html += '  <tr><td colspan="7"><div class="emailedit %s" style="display:none;"></div></td></tr>\n' % sysname
        notify2 = sys.get("notify2") or "<i>none</i>"
        html += '  <tr><td>Email List (Secondary):</td><td colspan="6"><button type="button" onclick="showEmailEdit(\'%s\', \'notify2\');">Edit</button> <span class="emaillist2 %s">%s</span></td></tr>\n' % (sysname, sysname, notify2)
        html += '  <tr><td colspan="7"><div class="emailedit2 %s" style="display:none;"></div></td></tr>\n' % sysname

        html += '  <tr><td style="display:none;"></td></tr>\n'

        html += """  <tr><td colspan="7">
  Email notification <b class="emailactive {0}">Unknown</b> &nbsp;
  <button type="button" class="emailbutton {0}" onclick="email_enable('{0}');" >&nbsp;&nbsp;</button>
  <hr>
</td></tr>\n""".format(sysname)

    html += """  </table>
  <div id="infopopup" onMouseLeave="hideInfo();">
   <fieldset id="plotbox">
    <legend> Cached Values </legend>
    <img src="NoData.gif" id="plotimg"/>
   </fieldset>
   <table id="infotable"/>
   <div id="triggerdiv" style="margin-top:6px;"></div>
  </div>
 </body>
</html>"""
    return html


class TestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        urlargs = urlparse(self.path)

        if urlargs.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(build_html(), "utf8"))

        elif urlargs.path == "/sysmonII.css":
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            with open("sysmonII.css", "r") as f:
                self.wfile.write(bytes(f.read(), "utf8"))

        elif urlargs.path == "/sysmonII.js":
            self.send_response(200)
            self.send_header('Content-type', 'text/javascript')
            self.end_headers()
            with open("sysmonII.js", "r") as f:
                self.wfile.write(bytes(f.read(), "utf8"))

        elif urlargs.path == "/latest":
            ups = {}
            em = {}
            ack = {}
            for sysname in sorted(SYSTEMS):
                em[sysname] = True
                ack[sysname] = False
                for uuid in SYSTEMS[sysname]["monitors"]:
                    mon = MONITORS[uuid]
                    ups[uuid] = {
                        "value": str(mon["meta"]["value"]),
                        "status": mon["meta"]["status"],
                        "message": None
                    }
            js = {"updates": ups, "emailnotifications": em, "acknowledge": ack}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(js), "utf8"))

        elif urlargs.path == "/pvinfo":
            queries = {}
            for q in urlargs.query.split("&"):
                n, v = q.split("=")
                queries[n] = v
            uuid = queries.get("uuid", "")
            if uuid in MONITORS:
                mon = MONITORS[uuid]
                result = {"meta": mon["meta"], "plotdata": None, "trigger": mon["trigger"], "filter": mon["filter"], "options": mon["options"], "uuid": uuid}
            else:
                result = {"error": "unknown uuid: %s" % uuid}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), "utf8"))

        elif urlargs.path == "/NoData.gif":
            self.send_response(200)
            self.send_header('Content-type', 'image/gif')
            self.end_headers()
            try:
                with open("NoData.gif", "rb") as f:
                    self.wfile.write(f.read())
            except:
                import base64
                self.wfile.write(base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        urlargs = urlparse(self.path)

        if urlargs.path == "/trigger":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            uuid = data['uuid']
            trigger = data['trigger']

            # Validate trigger
            err = validate_trigger(trigger)
            if err:
                result = {"error": err}
            elif uuid in MONITORS:
                MONITORS[uuid]['trigger'] = trigger

                # Write back to sysmonII.json
                sysname, offset = uuid.rsplit(":", 1)
                offset = int(offset)
                CONFIG['systems'][sysname]['monitor'][offset]['trigger'] = trigger
                with open("sysmonII.json", "w") as f:
                    json.dump(CONFIG, f, indent=1)

                print("Updated trigger for %s: %s" % (uuid, trigger))
                result = {"success": True}
            else:
                result = {"error": "unknown uuid"}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), "utf8"))
        elif urlargs.path == "/filter":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            uuid = data['uuid']
            flt  = data['filter']

            if uuid in MONITORS:
                MONITORS[uuid]['filter'] = flt
                sysname, offset = uuid.rsplit(":", 1)
                offset = int(offset)
                CONFIG['systems'][sysname]['monitor'][offset]['filter'] = flt
                with open("sysmonII.json", "w") as f:
                    json.dump(CONFIG, f, indent=1)
                print("Updated filter for %s: %s" % (uuid, flt))
                result = {"success": True}
            else:
                result = {"error": "unknown uuid"}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), "utf8"))

        elif urlargs.path == "/options":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            uuid    = data['uuid']
            options = data['options']

            if uuid in MONITORS:
                MONITORS[uuid]['options'] = options
                sysname, offset = uuid.rsplit(":", 1)
                offset = int(offset)
                CONFIG['systems'][sysname]['monitor'][offset]['options'] = options
                with open("sysmonII.json", "w") as f:
                    json.dump(CONFIG, f, indent=1)
                print("Updated options for %s: %s" % (uuid, options))
                result = {"success": True}
            else:
                result = {"error": "unknown uuid"}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), "utf8"))

        elif urlargs.path == "/notify":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            sysname = data['system']
            notify  = data['notify'].strip()
            tier    = data.get('tier', 'notify')

            import re
            emails = notify.split()
            err = None

            # Tier 2 can be empty (clears it), tier 1 cannot
            if len(emails) == 0 and tier == 'notify':
                err = "Primary email list cannot be empty"
            elif len(emails) > 0:
                for addr in emails:
                    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', addr):
                        err = "Invalid email address: %s" % addr
                        break

            if err:
                result = {"error": err}
            elif sysname in SYSTEMS:
                val = notify if notify else None
                SYSTEMS[sysname][tier] = val
                CONFIG['systems'][sysname][tier] = val
                with open("sysmonII.json", "w") as f:
                    json.dump(CONFIG, f, indent=1)
                print("Updated %s for %s: %s" % (tier, sysname, notify))
                result = {"success": True}
            else:
                result = {"error": "unknown system"}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(result), "utf8"))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(format % args)


if __name__ == '__main__':
    port = 8080
    print("Starting test server on http://localhost:%d" % port)
    print("Click the 'i' next to any channel to see the info popup + trigger settings button.")
    httpd = HTTPServer(('127.0.0.1', port), TestHandler)
    httpd.serve_forever()
