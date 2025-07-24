#!/usr/bin/env python3

import os
import sys
import time
from bisect import bisect_left
import Cache
import Monitor
import pika
import json
import smtplib
import io
import base64
from enum import Enum
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from PIL import Image, ImageDraw
from Cache import pvType

eaddrs = ["tom.cumming@noirlab.edu", "angelic.ebbers@noirlab.edu"]

if True:
      msg = MIMEMultipart('alternative')
      msg['Subject'] = "sysMon: Triggered for %s" % "TEST again 3"
      msg['From']    = 'noreply@gemini.edu'
      msg['To']      = ", ".join(eaddrs)
      report  = "<html>\n"
      report += " <body>\n"
      report += "  <h1> TEST System Monitor Triggered </h1>\n"
      report += "  <table>"
      report += "   <tr>"
      report += "    <td> system:  <td> %s" % "TEST"
      report += "   <tr>"
      report += "    <td> pv:      <td> <a target=\"_parent\" href=\"%s\">%s</a>" % ("TEST", "TEST")
      report += "   <tr>"
      report += "    <td> value:   <td> %s" % "TEST"
      report += "   <tr>"
      report += "    <td> filter:  <td> %s" % "TEST"
      report += "   <tr>"
      report += "    <td> trigger: <td> %s" % "TEST"

      report += "  </table>"
      report += " </body>\n"
      report += "</html>\n"
      msg.attach(MIMEText(report, 'html'))
      s = smtplib.SMTP('hbfsmtprelay-lv1')
      # s.send_mail('noreply@gemini.edu', msg['To'], msg.as_string())
      s.send_message(msg)
      s.quit()
