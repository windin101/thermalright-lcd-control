#!/bin/bash
# Monitor memory usage of Thermalright LCD Control GUI

echo "Memory Monitor for Thermalright LCD Control"
echo "========================================="
echo ""

echo "Finding GUI process..."
PID=$(pgrep -f thermalright-lcd-control-gui)

if [ -z "$PID" ]; then
    echo "GUI not running. Please start it first."
    echo "Run: thermalright-lcd-control-gui"
    exit 1
fi

echo "Found GUI process with PID: $PID"
echo "Monitoring memory usage every 2 seconds..."
echo "Press Ctrl+C to stop"
echo ""
echo "Timestamp              RSS (MB)   VMS (MB)   % Mem   Threads"
echo "------------------------------------------------------------"

while true; do
    if ps -p $PID > /dev/null; then
        # Get memory info
        MEM_INFO=$(ps -o rss,vsz,%mem -p $PID | tail -1)
        RSS_KB=$(echo $MEM_INFO | awk '{print $1}')
        VMS_KB=$(echo $MEM_INFO | awk '{print $2}')
        MEM_PERCENT=$(echo $MEM_INFO | awk '{print $3}')
        
        # Convert to MB
        RSS_MB=$((RSS_KB / 1024))
        VMS_MB=$((VMS_KB / 1024))
        
        # Get thread count
        THREADS=$(ps -o nlwp -p $PID | tail -1)
        
        # Get timestamp
        TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
        
        # Print with formatting
        printf "%-22s %-10s %-10s %-8s %-8s\n" "$TIMESTAMP" "$RSS_MB" "$VMS_MB" "$MEM_PERCENT" "$THREADS"
        
        # Warning if memory is high
        if [ $RSS_MB -gt 1000 ]; then
            echo "⚠️  WARNING: High memory usage! ${RSS_MB}MB"
        fi
        if [ $RSS_MB -gt 5000 ]; then
            echo "🚨 CRITICAL: Very high memory usage! ${RSS_MB}MB"
        fi
        
        sleep 2
    else
        echo "Process $PID no longer running"
        break
    fi
done