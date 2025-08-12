#!/usr/bin/env python3

import os
import sys
import time

import Cache
import Monitor

class System:
  """
    There's one instance of these per system on the gui. It contains the notification methods for that system. Each
  monitor has a reference to it's system instance.
  """

  def __init__(self, sysname, sysconf):
    self.sysname  = sysname
    self.site     = os.environ['GEMINI_SITE'] if 'GEMINI_SITE' in os.environ else "MK"
    self.confdir  = os.environ['GEMINI_TOP']  if 'GEMINI_TOP'  in os.environ else "./"
    self.notify   = sysconf['notify']         if 'notify'      in sysconf else None
    self.desc     = sysconf['description']    if 'description' in sysconf else None
    self.comment  = sysconf['comment']        if 'comment'     in sysconf else None
    self.emailenable = False
    self.acknowledge = False
    self.ackCnt = 0
    self.monitors = []

