#!/bin/csh -f
#
# ECS_LOGERR -- Log ECS errors. This program will sample several ECS records
# searching for errors, and if they are found, they are logged into a file.
# This program is intended to run permanently in the background.
#
# PG (pedro) 24/Jan/2001
#
# pgroszko 14/Mar/2004
# Minor modifications to fit into the GEA scheme...
# log location change.
# /usr/bin/date -> /bin/date
# awk -e <blah> -> awk <blah>
#

echo GEMINI_SITE=$GEMINI_SITE
echo GEA_BASE=$GEA_BASE
echo GEA_DATA=$GEA_DATA

unalias *

# Software debug flags (0/1). Both should be zero when running normally.
set debugflag = 0
set testflag  = 0

# Delay used to wait between samples (seconds)
set delay = 5

# Delay used to wait when the ECS is not responding (seconds)
set longdelay = 300

# Log file name
set logpath = "$GEA_DATA/ecs/logger"
set logfile = "$logpath/error.log"


# Echo log file namec
echo "Errors will be logged in $logfile"

# Process command line arguments
while ($#argv > 0)
    if ("$argv[1]" == "-d") then
	set debugflag = 1
    else if ("$argv[1]" == "-t") then
	set testflag  = 1
    endif
    shift
end

# Test
if ($testflag) then
    set delay     = 5
    set longdelay = 30
    set logfile   = "./error.log"
endif

#-------------------------------------------------------------------
# Motor state record names (error=5)
set dm_state = "ec:domemotor.MIP"		# dome
set ts_state = "ec:topShtrmotor.MIP"		# bottom shutter
set bs_state = "ec:botShtrmotor.MIP"		# top shutter
set ev_state = "ec:eastVentGatemotor.MIP"	# east vent gate
set wv_state = "ec:westVentGatemotor.MIP"	# west vent gate

# Error message record names
set dm_msg = "ec:domemotor.MESS"		# dome
set ts_msg = "ec:topShtrmotor.MESS"		# top shutter
set bs_msg = "ec:botShtrmotor.MESS"		# bottom shutter
set ev_msg = "ec:eastVentGatemotor.MESS"	# east vent gate
set wv_msg = "ec:westVentGatemotor.MESS"	# west vent gate

# Faults
set dm_fault1 = "ec:fault:word2:word"		# dome 1
set dm_fault2 = "ec:fault:word3:word"		# dome 2
set ts_fault  = "ec:fault:word0:word"		# top shutter
set bs_fault  = "ec:fault:word1:word"		# bottom shutter
set ev_fault  = "ec:fault:word4:word"		# east vent gate
set wv_fault  = "ec:fault:word5:word"		# west vent gate
set sw_fault  = "ec:fault:word6:word"		# software
set lm_fault  = "ec:fault:word16:word"		# limits
set en_fault  = "ec:fault:word17:word"		# encoder

# Demand & position
set dm_demand  = "ec:moveDome.B"
set dm_pos     = "ec:domePos"
set dm_encoder = "ec:domemotor.MPOS"
set ts_demand  = "ec:moveShtrs.B"
set ts_pos     = "ec:topShtrPos"
set bs_demand  = "ec:moveShtrs.C"
set bs_pos     = "ec:botShtrPos"
set bs_skew    = "ec:botShtrSkew"
set ev_demand  = "ec:moveVgates.B"
set ev_pos     = "ec:eastVentGatePos"
set wv_demand  = "ec:moveVgates.C"
set wv_pos     = "ec:westVentGatePos"

# PCU key position bit (ECS=1)
set ecs_key = "ec:fault:word6:bits.B1"

# ECS health
set ecs_health = "ec:health"
#-------------------------------------------------------------------

# Initialize error flags
set erflag = 0
set ecflag = 0
set dmflag = 0
set tsflag = 0
set bsflag = 0
set evflag = 0
set wvflag = 0

# Create the log file if it doesn't exist
if (-e $logfile == 0) then
    mkdir -p $logpath
    cp /dev/null $logfile
endif

# Mark new start of logging
set date    = `/bin/date | awk '{print $1 "-" $3 "/" $2 "/" $6 "-" $4}'`
echo "-----------------------------------------------------------" >> $logfile
echo " New log started $date" >> $logfile
echo "-----------------------------------------------------------" >> $logfile

# Loop forever
while (1)

    # Format system date
    set date    = `/bin/date | awk '{print $1 "-" $3 "/" $2 "/" $6 "-" $4}'`
    # Check whether the ECS is alive
    caget $ecs_health >& /dev/null
    if ($status == 1) then
	if ($ecflag == 1) then
	    echo "$date EC ECS not responding" >> $logfile
	    echo "-" >> $logfile
	    set ecflag = 1
	endif
	sleep $longdelay
	continue
    else if ($ecflag == 1) then
	echo "$date EC ECS now responding" >> $logfile
	echo "-" >> $logfile
	set ecflag = 0
    endif

    if ($debugflag) then
	echo "After health: ecflag=$ecflag"
    endif

    # Check whether the PCU key is in the CMPTR position. A one will
    # indicate that this is the case. If not, sleep and try again.
    # If there is a timeout reading the key (status==1) assume that
    # it's not in the CMPTR position.
    set keypos = `caget $ecs_key | awk '{print int($2)}'`
    if ($status == 1) set keypos = 0
    if ("$keypos" == 0 && $testflag == 0) then
	if ($debugflag) echo "sleep for $delay seconds"
	sleep $delay
	continue
    endif

    if ($debugflag) then
	echo "After keypos: keypos=$keypos, testflag=$testflag"
    endif

    # Get all motor status
    set dmstate = `caget $dm_state | awk '{print int($2)}'`
    set tsstate = `caget $ts_state | awk '{print int($2)}'`
    set bsstate = `caget $bs_state | awk '{print int($2)}'`
    set evstate = `caget $ev_state | awk '{print int($2)}'`
    set wvstate = `caget $wv_state | awk '{print int($2)}'`

    # Assign default values when null values are read.
    if ("$dmstate" == "") set dmstate = 0;
    if ("$tsstate" == "") set tsstate = 0;
    if ("$bsstate" == "") set bsstate = 0;
    if ("$evstate" == "") set evstate = 0;
    if ("$wvstate" == "") set wvstate = 0;

    if ($debugflag) then
	echo "After state: dm=$dmstate, ts=$tsstate, bs=$bsstate, ev=$evstate, wv=$wvstate"
    endif

    # Check whether there is an error with the dome
    if ("$dmstate" == 5) then
	if ($dmflag == 0) then
	    set errmsg = `caget $dm_msg | awk '{print $2 " " $3 " " $4 " " $5 " " $6 " " $7 " " $8 " " $9}'`
	    echo "$date DM $errmsg" >> $logfile
	    set dmflag = 1
	    set erflag = 1
	endif
    else
	set dmflag = 0
    endif

    if ($debugflag) then
	echo "After dome error: $dmflag, erflag=$erflag"
    endif

    # Check whether there is an error with the top shutter
    if ("$tsstate" == 5) then
	if ($tsflag == 0) then
	    set errmsg = `caget $ts_msg | awk '{print $2 " " $3 " " $4 " " $5 " " $6 " " $7 " " $8 " " $9}'`
	    echo "$date TS $errmsg" >> $logfile
	    set tsflag = 1
	    set erflag = 1
	endif
    else
	set tsflag = 0
    endif

    if ($debugflag) then
	echo "After top shutter error: $tsflag, erflag=$erflag"
    endif

    # Check whether there is an error with the bottom shutter
    if ("$bsstate" == 5) then
	if ($bsflag == 0) then
	    set errmsg = `caget $bs_msg | awk '{print $2 " " $3 " " $4 " " $5 " " $6 " " $7 " " $8 " " $9}'`
	    echo "$date BS $errmsg" >> $logfile
	    set bsflag = 1
	    set erflag = 1
	endif
    else
	set bsflag = 0
    endif

    if ($debugflag) then
	echo "After bottom shutter error: $bsflag, erflag=$erflag"
    endif

    # Check whether there is an error with the east vent gate
    if ("$evstate" == 5) then
	if ($evflag == 0) then
	    set errmsg = `caget $ev_msg | awk '{print $2 " " $3 " " $4 " " $5 " " $6 " " $7 " " $8 " " $9}'`
	    echo "$date EV $errmsg" >> $logfile
	    set evflag = 1
	    set erflag = 1
	endif
    else
	set evflag = 0
    endif

    if ($debugflag) then
	echo "After east vent gate error: $evflag, erflag=$erflag"
    endif

    # Check whether there is an error with the west vent gate
    if ("$wvstate" == 5) then
	if ($wvflag == 0) then
	    set errmsg = `caget $wv_msg | awk '{print $2 " " $3 " " $4 " " $5 " " $6 " " $7 " " $8 " " $9}'`
	    echo "$date WV $errmsg" >> $logfile
	    set wvflag = 1
	    set erflag = 1
	endif
    else
	set wvflag = 0
    endif

    if ($debugflag) then
	echo "After west vent gate error: $wvflag, erflag=$erflag"
    endif

    # Log all the dome demand, position, and faults if there are any errors
    if ($erflag) then

	set dmdem = `caget $dm_demand  | awk '{print $2}'`
	set dmpos = `caget $dm_pos     | awk '{print $2}'`
	set dmenc = `caget $dm_encoder | awk '{print $2}'`

	set tsdem = `caget $ts_demand  | awk '{print $2}'`
	set tspos = `caget $ts_pos     | awk '{print $2}'`
	set bsdem = `caget $bs_demand  | awk '{print $2}'`
	set bspos = `caget $bs_pos     | awk '{print $2}'`

	set bsskew = `caget $bs_skew   | awk '{print $2}'`

	set evdem = `caget $ev_demand  | awk '{print $2}'`
	set evpos = `caget $ev_pos     | awk '{print $2}'`
	set wvdem = `caget $wv_demand  | awk '{print $2}'`
	set wvpos = `caget $wv_pos     | awk '{print $2}'`

	set dmflt1 = `caget $dm_fault1 | awk '{printf ("%x", $2)}'`
	set dmflt2 = `caget $dm_fault2 | awk '{printf ("%x", $2)}'`

	set tsflt  = `caget $ts_fault  | awk '{printf ("%x", $2)}'`
	set bsflt  = `caget $bs_fault  | awk '{printf ("%x", $2)}'`

	set evflt  = `caget $ev_fault  | awk '{printf ("%x", $2)}'`
	set wvflt  = `caget $wv_fault  | awk '{printf ("%x", $2)}'`

	set lmflt  = `caget $lm_fault  | awk '{printf ("%x", $2)}'`
	set swflt  = `caget $sw_fault  | awk '{printf ("%x", $2)}'`
	set enflt  = `caget $en_fault  | awk '{printf ("%x", $2)}'`

	echo "$date DP demand=$dmdem, position=$dmpos, encoder=$dmenc" >> $logfile
	echo "$date TP demand=$tsdem, position=$tspos"              >> $logfile
	echo "$date BP demand=$bsdem, position=$bspos skew=$bsskew" >> $logfile
	echo "$date EP demand=$evdem, position=$evpos"              >> $logfile
	echo "$date WP demand=$wvdem, position=$wvpos"              >> $logfile

	echo "$date FL dm1=$dmflt1, dm2=$dmflt2, ts=$tsflt, bs=$bsflt, ev=$evflt, wv=$wvflt, lm=$lmflt, sw=$swflt, en=$enflt" >> $logfile
	echo "-" >> $logfile

	set erflag = 0
    endif

    if ($debugflag) then
	echo "After faults erflag=$erflag"
	echo "sleep for $delay seconds"
	echo "--------------------------"
    endif

    # Wait for next check
    sleep $delay
end
