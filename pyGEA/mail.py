#!/usr/bin/python

import sys
import poplib
import rfc822
import smtplib
import GEAVars

def getMail(server, user='gea', pass_='gea99'):
    
    _server=poplib.POP3(server)
    _server.user(user)
    _server.pass_(pass_)

    msgList=[]
    try:
        msgList=_getMessages(_server)
    finally:
        _server.quit()   # Want to make sure we do this to unlock the mailbox.

    return msgList

def _getMessages(server):

    (msgCount, msgBytes)=server.stat()
    return ['\n'.join(server.retr(i)[1]) for i in range(1, msgCount+1)] or []


def sendMail(fr, to, msg='', subject=''):
    
    server = smtplib.SMTP('localhost')
    
    if subject:
        subject='Subject: %s\r\n' % (subject,)
    
    msg='To: %s\r\n%s\r\n%s' % (', '.join(to), subject, msg)

    fr += '@gemini.edu'

    server.sendmail(fr, to, msg)
    server.quit()

def main(argv):

    try:
        server=argv[1]
    except IndexError:
        usage()
        sys.exit(1)
    
    print getMail(server)

def usage():
    print 'Usage: ', sys.argv[0], '<server>'

if __name__=='__main__':
    
    main(sys.argv)

    
