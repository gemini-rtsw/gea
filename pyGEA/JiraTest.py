#!/usr/bin/env python

import httplib
import base64
import json
import os

# export SSL_CERT_FILE=/etc/ssl/certs/cert.pem

# os.environ['SSL_CERT_FILE'] = "/etc/ssl/certs/ca-certificates.crt"
# os.environ['SSL_CERT_FILE'] = "/etc/ssl/certs/ca-bundle.crt"
os.environ['SSL_CERT_FILE'] = "/etc/ssl/certs/cert.pem"
# os.environ['SSL_CERT_FILE'] = "/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt"

if __name__ == "__main__":  

    up = base64.b64encode("swgsupportgs:b7&wp&4bG92(-6N@P")
    up = base64.b64encode("swgsupportgn:w44-(Ikz)Q(j8sG0Kp(@")
    jh = "hbfjiratest-lv2.hi.gemini.edu"
    jh = "osc.cl.gemini.edu"
    jh = "osc.hi.gemini.edu"
    rq = '/rest/api/2/search?jql="project"="FR"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Date+of+Occurrence"<="2018-09-06+10:00"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39524"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2011-01-06+10:00"+AND+"Occurred"<="2018-06-06+21:31"&fields="id"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2011-01-06+10:00"+AND+"Occurred"<="2018-06-06+21:31"&fields="id","fields"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2011-01-06+10:00"+AND+"Occurred"<="2018-06-06+21:31"+AND+"Time+Lost"+>+1&fields=id,customfield_10400,customfield_10300,status,resolution,assignee,summary&expand=names'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2018-01-06+00:00"+AND+"Occurred"<="2018-09-04+14:47"&fields=key,customfield_10400,assignee,customfield_10300'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2018-03-01+04:00"+AND+"Occurred"<="2018-03-02+17:00"&fields=key,customfield_10400,assignee,customfield_10300'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+assignee="tcumming"+AND+status="Assigned"+OR+status="Work In Progress"&fields=key,customfield_10400,assignee,customfield_10300'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+assignee="tcumming"&fields=key,customfield_10400,assignee,customfield_10300,status'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2018-01-31+16:00"+AND+"Occurred"<="2018-02-01+07:00"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-30005"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"assignee"="tcumming"+AND+"status"="pending"+OR+"status"="pending"&fields=key,customfield_10300,status,resolution,customfield_10400,summary,assignee,issuelinks,issuelinks,components,labels'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39525"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"assignee"="tcumming"+AND+"status"="Work+in+progress"&fields=key,customfield_10300,status,resolution,customfield_10400,summary,assignee,issuelinks,issuelinks,components,labels'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39525"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39408"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39856"&fields=key,reporter,customfield_10300,issuelinks,assignee,status,issuelinks,customfield_10400,summary,description,comment,attachment,customfield_10214,components,labels,resolution"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39856"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-30005"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"component"="Instruments"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2005-01-11+11:51"+AND+"Occurred"<="2018-09-18+11:51"&maxResults=1000&startAt=1000'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"labels"="Enclosure/ECS"'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-38584"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-39899"&fields=*all'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2018-10-09+11:10"+AND+"Occurred"<="2018-12-10+11:10"&fields=key,customfield_10301,status,resolution,customfield_10303,summary,issuelinks,issuelinks,assignee,components,labels&maxResults=1000'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-040195"&fields=key,reporter,customfield_10301,issuelinks,assignee,status,priority,issuelinks,customfield_10303,summary,description,comment,attachment,customfield_10302,components,labels,resolution&maxResults=1000'

    ra = '/rest/api/2/search?jql="project"="FR"+AND+"Occurred">="2018-12-14+07:30"+AND+"Occurred"<="2018-12-18+10:33"&fields=key,customfield_10301,status,resolution,customfield_10303,summary,issuelinks,issuelinks,assignee,components,labels&maxResults=1000'
    rq = '/rest/api/2/search?jql="project"="FR"+AND+"key"="FR-70256"&fields=*all'

    print rq

#  "Date value '2018-03-11T00:00:00' for field 'Date of Occurrence' is invalid. Valid formats include: 'yyyy/MM/dd HH:mm', 'yyyy-MM-dd HH:mm', 'yyyy/MM/dd', 'yyyy-MM-dd', or a period format e.g. '-5d', '4w 2d'."


# https://hbfjiratest-lv2.hi.gemini.edu/rest/api/2/search?jql=project=FR+AND+%22Date%20of%20Occurrence%22%3E2018-03-11&%22Date%20of%20Occurrence%22%3C2018-05-31&fields=id,key,comments

    hdr = {'Authorization' : 'Basic %s' %  up}
    con = httplib.HTTPSConnection(jh)
    con.request("GET", rq, headers = hdr)
    res = con.getresponse()
    print res.status, res.reason
    if res.status == 200:
        js = json.loads(res.read())
        #for issue in js['issues']:
            #print issue
            #resolution =  issue['fields']['resolution']['name'] if issue['fields']['resolution'] else ""
            #status     =  issue['fields']['status']['name']
            #assignee   =  issue['fields']['assignee']['name']
            #timelost   =  issue['fields']['customfield_10400']
            #occurred   =  issue['fields']['customfield_10300']
            #summary    =  issue['fields']['summary']
            #frnum      =  issue['key']
            #print " XXX ".join([frnum, occurred, status, resolution, "%f" % timelost, assignee, summary])
        print json.dumps(js, sort_keys = True, indent = 1)



""" URL to get you to a fault:

https://hbfjiratest-lv2.hi.gemini.edu/browse/FR-38721

"""

"""
 "fields": {
    "customfield_10400": 1.38,
    "resolution": null,
    "status": {
     "description": "This was auto-generated by JIRA Service Desk during workflow import",
     "iconUrl": "https://hbfjiratest-lv2.hi.gemini.edu/images/icons/status_generic.gif",
     "id": "10012",
     "name": "Work in progress",
     "self": "https://hbfjiratest-lv2.hi.gemini.edu/rest/api/2/status/10012",
     "statusCategory": {
      "colorName": "yellow",
      "id": 4,
      "key": "indeterminate",
      "name": "In Progress",
      "self": "https://hbfjiratest-lv2.hi.gemini.edu/rest/api/2/statuscategory/4"
     }
    }
   },
"""
