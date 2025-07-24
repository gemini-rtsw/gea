#!/usr/bin/env python
    
import GEAVars
import MySQLdb
import datetime
    
nlUser   = 'gea'
nlPasswd = 'gea99'
nlDB     = 'NightLog'
gnhostname = 'localhost'
gnhostname = 'hbfgeadev'
gnhostname = 'geanorth.hi.gemini.edu'
gshostname = 'geasouth.cl.gemini.edu'
localsite  = GEAVars.site




from GEAException import GEAException
class NightlogException(GEAException):
    pass




class nightLogDB:
    """
    Wrapper for the mysql nightlog and quality log tables in the nightlog database.
    """

    def __init__(self):

        if localsite == 'MK':
            self.hostname   = gnhostname
            self.remotehost = gshostname
        elif localsite == 'CP':
            self.hostname   = gshostname
            self.remotehost = gnhostname
        else:
            raise NightlogException('Site %s unknown' % localsite)

        try:                                # A pythonism to find if a variable is
            nightLogDB.opened               # unitialized.
        except:
            nightLogDB.mysqlDB  = MySQLdb.connect(host=self.hostname, user=nlUser, passwd=nlPasswd, db=nlDB)
            nightLogDB.mysqlCur = nightLogDB.mysqlDB.cursor()
            nightLogDB.opened   = None      # Initialize it.
            nightLogDB.mysqlDBalt  = None
            nightLogDB.mysqlCuralt = None


    def __del__(self):

        pass

    def getNightLog(self, site, date):
        """
        Generic, "get everything" nightlogish. Used by the Nightlog and Nightlog Entry pages.
        """
    
        if site == None:
            r = {}
            r['MK'] = self.getNightLog('MK', date)
            r['CP'] = self.getNightLog('CP', date)
            return r
        
        if site != 'MK' and site != 'CP':
            raise NightlogException('Site %s unknown' % site)

        if site == localsite:
            mdb = self.mysqlDB
            mc  = self.mysqlCur
        else:
            if self.mysqlDBalt is None:
                self.mysqlDBalt  = MySQLdb.connect(host=self.remotehost, user='gea', passwd='gea99', db='NightLog')
                self.mysqlCuralt = self.mysqlDBalt.cursor()
            mdb = self.mysqlDBalt
            mc  = self.mysqlCuralt
    
        nlquery = "select * from NightLog where cdate = %04d%02d%02d" % (date.year, date.month, date.day) 
        mc.execute(nlquery) 
        res = mc.fetchall() 
        if len(res) == 0: return None
    
        if len(res) != 1: raise NightlogException("Length of response is not one, it's %d." % (len(res)))
    
        r = {}

        r['date']       = res[0][0]
        # mdate = res[0][1]
        r['submitter']  = res[0][2]
        r['almanac']    = res[0][3]
        r['ssupport']   = res[0][4]
        r['bsupport']   = res[0][5]
        r['psupport']   = res[0][6]
        r['programs']   = res[0][7]
        r['entprog']    = res[0][8]
        r['scihrs']     = res[0][9]
        r['enghrs']     = res[0][10]
        r['weatherhrs'] = res[0][11]
        r['commhrs']    = res[0][12]
        r['lasershut']  = res[0][13]
        r['blankshut']  = res[0][14]
        r['inst']       = res[0][15]
        r['plan']       = res[0][16]
        r['summary']    = res[0][17]
        r['problems']   = res[0][18]
        r['details']    = res[0][19]

        qlquery = "select * from QualityLog where date = %04d%02d%02d" % (date.year, date.month, date.day) 
        mc.execute(qlquery) 
        res = mc.fetchall() 
        if len(res) == 0:
            r['qlog'] = None
            return r

        rt = []
        for rlt in res:
            rl = {}
            rl['time']    = rlt[1]
            rl['wavelen'] = rlt[2]
            rl['fwhm']    = rlt[3]
            rl['strehl']  = rlt[4]
            rl['airmass'] = rlt[5]
            rl['notes']   = rlt[6]
            rt.append(rl)
    
        r['qlog'] = rt 
        return r
    




    def putNightLog(self, date, nightlog):

        """
        Generic, "put everything" nightlogish. Used by the Nightlog and Nightlog Entry pages.
        """

        if nightlog == None: return
    
        mdb = self.mysqlDB
        mc  = self.mysqlCur
    
        nlquery = "select count(*) from NightLog where cdate = %04d%02d%02d" % (date.year, date.month, date.day)
        mc.execute(nlquery) 
        count = mc.fetchone()[0]

        date = datetime.datetime.utcnow()
        date = datetime.date(date.year, date.month, date.day)

        if count == 0:
            nlsql = """insert into NightLog values
            ('%04d%02d%02d', '%04d%02d%02d',
            '%s', '%s', '%s', '%s', '%s', '%s', '%s',
            %f, %f, %f, %f, %f, %f, '%s', '%s', '%s', '%s', '%s') """ % (
                nightlog['date'].year, nightlog['date'].month, nightlog['date'].day, 
                date.year, date.month, date.day,
                nightlog['submitter'], 
                nightlog['almanac'], 
                nightlog['ssupport'], 
                nightlog['bsupport'], 
                nightlog['psupport'], 
                nightlog['programs'], 
                nightlog['entprog'], 
                nightlog['scihrs'], 
                nightlog['enghrs'], 
                nightlog['weatherhrs'], 
                nightlog['commhrs'], 
                nightlog['lasershut'], 
                nightlog['blankshut'], 
                nightlog['inst'], 
                nightlog['plan'], 
                nightlog['summary'], 
                nightlog['problems'], 
                nightlog['details'])

        elif count == 1:
            nlsql = """update set 
                mdate      = '%04d%02d%02d',
                submitter  = '%s',
                almanac    = '%s',
                ssupport   = '%s',
                bsupport   = '%s',
                psupport   = '%s',
                programs   = '%s',
                entprog    = '%s',
                scihrs     = '%s',
                enghrs     = '%s',
                weatherhrs = '%s',
                commhrs    = '%s',
                lasershut  = '%s',
                blankshut  = '%s',
                inst       = '%s',
                plan       = '%s',
                summary    = '%s',
                problems   = '%s',
                details    = '%s'
                where cdate = '%04d%02d%02d') """ % (
                    nightlog['mdate'].year, nlentry['mdate'].month, nlentry['mdate'].day, 
                    nightlog['submitter'],
                    nightlog['almanac'],
                    nightlog['ssupport'],
                    nightlog['bsupport'],
                    nightlog['psupport'],
                    nightlog['programs'],
                    nightlog['entprog'],
                    nightlog['scihrs'],
                    nightlog['enghrs'],
                    nightlog['weatherhrs'],
                    nightlog['commhrs'],
                    nightlog['lasershut'],
                    nightlog['blankshut'],
                    nightlog['inst'],
                    nightlog['plan'],
                    nightlog['summary'],
                    nightlog['problems'],
                    nightlog['details'],
                    date.year, date.month, date.day)
        else:
            raise NightlogException("There are %d night log entries for %04d/%02d/%02d" % (count, date.year, date.month, date.day))
         
        mysqlCur.execute(nlsql)

        nlquery = "select * from NightLog where cdate = %04d%02d%02d" % (date.year, date.month, date.day) 
        mc.execute(nlquery) 
        res = mc.fetchall() 
        if len(res) == 0: return None
    
        if len(res) != 1: raise NightlogException("Length of response is not one, it's %d." % (len(res)))
    
        r = {}

        r['date']       = res[0][0]
        # mdate = res[0][1]
        r['submitter']  = res[0][2]
        r['almanac']    = res[0][3]
        r['ssupport']   = res[0][4]
        r['bsupport']   = res[0][5]
        r['psupport']   = res[0][6]
        r['programs']   = res[0][7]
        r['entprog']    = res[0][8]
        r['scihrs']     = res[0][9]
        r['enghrs']     = res[0][10]
        r['weatherhrs'] = res[0][11]
        r['commhrs']    = res[0][12]
        r['lasershut']  = res[0][13]
        r['blankshut']  = res[0][14]
        r['inst']       = res[0][15]
        r['plan']       = res[0][16]
        r['summary']    = res[0][17]
        r['problems']   = res[0][18]
        r['details']    = res[0][19]

        qlquery = "select * from QualityLog where date = %04d%02d%02d" % (date.year, date.month, date.day) 
        mc.execute(qlquery) 
        res = mc.fetchall() 
        if len(res) == 0:
            r['qlog'] = None
            return r

        rt = []
        for rlt in res:
            rl = {}
            rl['time']    = rlt[1]
            rl['wavelen'] = rlt[2]
            rl['fwhm']    = rlt[3]
            rl['strehl']  = rlt[4]
            rl['airmass'] = rlt[5]
            rl['notes']   = rlt[6]
            rt.append(rl)
    
        r['qlog'] = rt 
        return r
    


if __name__=='__main__':

    night = datetime.date.today() + datetime.timedelta(days = 200)

    bar = nightLogDB()

    """
    foo = bar.getNightLog(None, night)
    if foo:
        if foo['MK']: 
            print 'MK', foo['MK']['date'], foo['MK']['submitter'],
            if foo['MK']['qlog']: print "QLOG", foo['MK']['qlog'][0]['time']
            else: print
        if foo['CP']:
            print 'CP', foo['CP']['date'], foo['CP']['submitter'],
            if foo['CP']['qlog']: print "QLOG", "foo['CP']['qlog'][0]['time']"
            else: print
    """

    foo = bar.getNightLog("CP", night)
    if foo:
        print 'CP', foo['date'], foo['submitter'],
        if foo['qlog']: print "QLOG", foo['qlog'][0]['time']
        else: print

    night = datetime.date.today() - datetime.timedelta(days = 20)
    foo = bar.getNightLog("CP", night)
    night = datetime.date.today() - datetime.timedelta(days = 30)
    foo = bar.getNightLog("CP", night)
    night = datetime.date.today() - datetime.timedelta(days = 40)
    foo = bar.getNightLog("CP", night)
    if foo:
        print 'CP', foo['date'], foo['submitter'],
        if foo['qlog']: print "QLOG", foo['qlog'][0]['time']
        else: print

    """
    foo = bar.getNightLog("CP", night)
    if foo:
        print 'CP', foo['date'], foo['submitter'],
        if foo['qlog']: print "QLOG", foo['qlog'][0]['time']
        else: print

    foo = bar.getNightLog(None, night)
    if foo:
        if foo['MK']: 
            print 'MK', foo['MK']['date'], foo['MK']['submitter'],
            if foo['MK']['qlog']: print "QLOG", foo['MK']['qlog'][0]['time']
            else: print
        if foo['CP']:
            print 'CP', foo['CP']['date'], foo['CP']['submitter'],
            if foo['CP']['qlog']: print "QLOG", "foo['CP']['qlog'][0]['time']"
            else: print

    foo = bar.getNightLog("MK",  datetime.date(2013, 2, 3))
    if foo:
        print 'MK', foo['date'], foo['submitter'],
        if foo['qlog']: print "QLOG", foo['qlog'][0]['time']
        else: print

    foo = bar.getNightLog("CP",  datetime.date(2013, 2, 3))
    if foo: 
        print 'CP', foo['date'], foo['submitter'],
        if foo['qlog']: print "QLOG", foo['qlog'][0]['time']
        else: print

    foo = bar.getNightLog(None, datetime.date(2013, 2, 3))
    if foo:
        if foo['MK']: 
            print 'MK', foo['MK']['date'], foo['MK']['submitter'],
            if foo['MK']['qlog']: print "QLOG", foo['MK']['qlog'][0]['time']
            else: print
        if foo['CP']:
            print 'CP', foo['CP']['date'], foo['CP']['submitter'],
            if foo['CP']['qlog']: print "QLOG", foo['CP']['qlog'][0]['time']
            else: print



    """

