#!/usr/bin/env bash
# Helper script: run GUI with debug snapshot toggle enabled and collect generated files into /tmp/thermalright_debug_capture.tar.gz
# Usage: ./scripts/collect_preview_debug.sh [SECONDS_TO_RUN]

RUN_TIME=${1:-20}
# Ensure the preview debug toggle exists
touch /tmp/preview_debug_enabled

# Start GUI with console logging redirected to /tmp/gui_console.log
# Try to use the development launcher first (run_gui.sh), fallback to installed command
LOGFILE=/tmp/gui_console.log
rm -f $LOGFILE
if command -v thermalright-lcd-control-gui &> /dev/null; then
    # Prefer installed command to match production behavior
    GUI_CMD="GUI_LOG_TO_STDOUT=1 LOG_LEVEL=DEBUG thermalright-lcd-control-gui"
elif [[ -x ./run_gui.sh ]]; then
    GUI_CMD="GUI_LOG_TO_STDOUT=1 LOG_LEVEL=DEBUG ./run_gui.sh"
else
    echo "Could not find installed 'thermalright-lcd-control-gui' or ./run_gui.sh"
    exit 1
fi

# Run in background, capture pid
bash -c "$GUI_CMD" &> "$LOGFILE" &
GUI_PID=$!

# Run for given seconds so user can interact
echo "GUI started (pid: $GUI_PID). Run time: ${RUN_TIME}s. Interact with the GUI now, then wait..."
sleep ${RUN_TIME}

# Try to gracefully kill the GUI if it's still running
if kill -0 $GUI_PID &> /dev/null; then
    kill $GUI_PID
    sleep 1
fi

# Collect debug snapshots and log
OUT_PATH=/tmp/thermalright_debug_capture.tar.gz
rm -f "$OUT_PATH"
# Copy GUI console log
cp -f "$LOGFILE" /tmp/gui.log || true
# Copy system log if it exists
cp -f ~/.local/state/thermalright-lcd-control/thermalright-lcd-control-gui.log /tmp/gui_installed.log || true

tar -czvf "$OUT_PATH" /tmp/preview_debug_*.png /tmp/gui.log /tmp/gui_installed.log || true

# Show results and list files
echo "Created $OUT_PATH"
ls -l /tmp/preview_debug_*.png 2>/dev/null || true
ls -l /tmp/gui* 2>/dev/null || true

echo "Finished. Please upload $OUT_PATH when ready."
