
program=watcher.py
logfile=$GEA_LOG/$(basename $program .py).log

if ! ps -eaf | egrep -v grep | egrep -q $program; then
    echo $(date +%D\/%M\/%y\ %H:%M:%S) $program restarted >> $logfile
    nohup ./$program >> $logfile 2>&1 &
fi
