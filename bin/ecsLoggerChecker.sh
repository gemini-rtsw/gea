#!/bin/bash

. /etc/profile


RES=`ps ax | grep "ecsLogger.csh" | grep -v -P "grep|nedit"`

if [ "X$RES" = "X" ]; then
	echo "Restarting the ecsLogger..."
	exec ecsLogger.csh $GEA_DATA/ecs/logger/error.log 
fi
