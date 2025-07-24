      msg['To']      = ", ".join(eaddrs)
      s = smtplib.SMTP('hbfsmtprelay-lv1')
      s.send_message(msg)
