#!/bin/bash

# ==============================================================================
# GEA Index Maintenance Script
# Purpose: Prevents index crashes by moving old data to 'basement' when > 1.9GB.
# Logic:   Checks size -> Moves oldest year -> Cleans config -> Reindexes -> Repeats.
# ==============================================================================

# CONFIGURATION
# 1.9 GB Limit (Safe buffer below 2GB crash limit)
LIMIT_BYTES=1900000000
DATA_ROOT="/gemsoft/var/data/gea/data/data"
LOG_FILE="/gemsoft/var/log/gea/maintenance_audit.log"

# Function for logging with timestamp
log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# List of subsystems to check (Based on your logs and confirmed paths)
SUBSYSTEMS="scs gis laser gmos ag niri mcs tcs pr ecs altair pcsact igrins2 bto"

for subsystem in $SUBSYSTEMS; do
    SUB_DIR="$DATA_ROOT/$subsystem"
    BASEMENT="$SUB_DIR/basement"
    
    # Check if subsystem exists
    if [ ! -d "$SUB_DIR" ]; then
        log_msg "SKIP: $subsystem (Directory not found)"
        continue
    fi

    # Create basement if it doesn't exist (Critical for laser, gmos, tcs, etc.)
    if [ ! -d "$BASEMENT" ]; then
        log_msg "INIT: Creating missing basement for $subsystem"
        mkdir -p "$BASEMENT"
        chown software:software "$BASEMENT"
    fi
    
    log_msg "START: Processing $subsystem"
    
    # LOOP: Prune years until size is safe
    while true; do
        # Get index size (0 if missing)
        CURRENT_SIZE=$(stat -c %s "$SUB_DIR/master_index" 2>/dev/null || echo 0)
        
        # Check if safe
        if [ "$CURRENT_SIZE" -lt "$LIMIT_BYTES" ]; then
            log_msg "OK: $subsystem index size is safe ($((CURRENT_SIZE/1024/1024)) MB)"
            break
        fi

        log_msg "ALERT: $subsystem index too big ($((CURRENT_SIZE/1024/1024)) MB). Cleaning required."
        
        # 1. Find oldest year in the active folder
        # (Looks for 4-digit folders like '2017', sorts numerically, picks the first)
        OLDEST_YEAR=$(ls -1 "$SUB_DIR" | grep -E '^[0-9]{4}$' | sort -n | head -n 1)
        
        if [ -z "$OLDEST_YEAR" ]; then
            log_msg "ERROR: No year folders found in $subsystem to move! Cannot reduce size further."
            break
        fi
        
        log_msg "ACTION: Moving $subsystem/$OLDEST_YEAR to basement..."
        
        # 2. Move data to basement
        if [ -d "$SUB_DIR/$OLDEST_YEAR" ]; then
            mv "$SUB_DIR/$OLDEST_YEAR" "$BASEMENT/"
            if [ $? -eq 0 ]; then
                 log_msg "SUCCESS: Moved $OLDEST_YEAR to $BASEMENT"
            else
                 log_msg "CRITICAL: Failed to move $OLDEST_YEAR. Stopping loop for safety."
                 break
            fi
        fi
        
        # 3. Sanitize config (REQUIRED: prevents reindex crash)
        # Deletes any line containing the year path (e.g. "2017/")
        sed -i "/$OLDEST_YEAR\//d" "$SUB_DIR/indexconfig.xml"
        
        # 4. Re-index to shrink the binary file
        log_msg "ACTION: Re-indexing $subsystem..."
        /gemsoft/opt/gea/bin/reindex "$subsystem"
    done
done
