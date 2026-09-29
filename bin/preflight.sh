#!/bin/bash
# GEA PRE-FLIGHT SAFETY CHECK (v2 - Excludes casnooper)

DATA_ROOT="/gemsoft/var/data/gea/data/data"
LOG_DIR="/gemsoft/var/log/gea"
REINDEX_TOOL="/gemsoft/opt/gea/bin/reindex"

# REMOVED: casnooper (Missing config)
SUBSYSTEMS="scs gis laser gmos ag niri mcs tcs pr ecs altair pcsact igrins2 bto"

echo "============================================="
echo "   GEA INDEX MAINTENANCE: SAFETY CHECK v2    "
echo "============================================="

# 1. CHECK USER IDENTITY
CURRENT_USER=$(whoami)
echo -n "[CHECK] User Identity: "
if [ "$CURRENT_USER" == "software" ]; then
    echo "PASS (Running as '$CURRENT_USER')"
else
    echo "FAIL"
    echo "   -> ERROR: You are '$CURRENT_USER'. You MUST run this as 'software'."
    exit 1
fi

# 2. CHECK REINDEX TOOL
echo -n "[CHECK] Reindex Tool:  "
if [ -x "$REINDEX_TOOL" ]; then
    echo "PASS (Found & Executable)"
else
    echo "FAIL"
    echo "   -> ERROR: $REINDEX_TOOL not found."
    exit 1
fi

# 3. CHECK LOGGING ACCESS
echo -n "[CHECK] Log Directory: "
if [ -w "$LOG_DIR" ]; then
    echo "PASS (Writable)"
else
    echo "FAIL"
    echo "   -> ERROR: Cannot write to $LOG_DIR."
    exit 1
fi

echo "---------------------------------------------"
echo "Checking Subsystem Permissions..."

ALL_CLEAR=true

# 4. CHECK EACH SUBSYSTEM
for sub in $SUBSYSTEMS; do
    DIR="$DATA_ROOT/$sub"
    CONFIG="$DIR/indexconfig.xml"

    if [ ! -d "$DIR" ]; then
        echo "   [SKIP] $sub (Directory not found)"
        continue
    fi

    # Check Write Permissions
    if [ -w "$DIR" ]; then
        PERM_STATUS="OK"
    else
        PERM_STATUS="FAIL (No Write Access)"
        ALL_CLEAR=false
    fi

    # Check Config File
    if [ -f "$CONFIG" ]; then
        CONF_STATUS="OK"
    else
        CONF_STATUS="FAIL (Missing indexconfig.xml)"
        ALL_CLEAR=false
    fi

    echo "   - $sub: Write=$PERM_STATUS | Config=$CONF_STATUS"
done

echo "============================================="
if [ "$ALL_CLEAR" = true ]; then
    echo "RESULT: SYSTEM IS READY." 
    echo "You may proceed with the screen session."
else
    echo "RESULT: ISSUES DETECTED."
    echo "Fix the FAIL items before running the main script."
fi
