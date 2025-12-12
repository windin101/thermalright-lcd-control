#!/usr/bin/env python3
"""
Memory monitor for Thermalright LCD Control GUI
Run this alongside the GUI to monitor memory usage
"""

import psutil
import time
import os
import threading
from datetime import datetime

def monitor_memory(pid=None, interval=5, log_file="memory_usage.log"):
    """
    Monitor memory usage of a process
    
    Args:
        pid: Process ID to monitor (None = current process)
        interval: Check interval in seconds
        log_file: File to log memory usage
    """
    if pid is None:
        pid = os.getpid()
    
    process = psutil.Process(pid)
    
    print(f"Monitoring memory usage for PID {pid} ({process.name()})")
    print(f"Logging to: {log_file}")
    print("=" * 60)
    
    with open(log_file, 'w') as f:
        f.write("Timestamp,RSS_MB,VMS_MB,Percent,Threads,Open_Files\n")
    
    try:
        while True:
            try:
                mem_info = process.memory_info()
                mem_percent = process.memory_percent()
                num_threads = process.num_threads()
                num_files = len(process.open_files())
                
                rss_mb = mem_info.rss / 1024 / 1024
                vms_mb = mem_info.vms / 1024 / 1024
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                log_line = f"{timestamp},{rss_mb:.1f},{vms_mb:.1f},{mem_percent:.1f},{num_threads},{num_files}"
                
                with open(log_file, 'a') as f:
                    f.write(log_line + "\n")
                
                print(f"{timestamp} - RSS: {rss_mb:.1f}MB, VMS: {vms_mb:.1f}MB, %: {mem_percent:.1f}, "
                      f"Threads: {num_threads}, Files: {num_files}")
                
                # Alert if memory usage is high
                if rss_mb > 1000:  # > 1GB
                    print(f"⚠️  WARNING: High memory usage! {rss_mb:.1f}MB")
                if rss_mb > 5000:  # > 5GB
                    print(f"🚨 CRITICAL: Very high memory usage! {rss_mb:.1f}MB")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print("Process terminated or access denied")
                break
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

def find_gui_process():
    """Find the thermalright-lcd-control-gui process"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'thermalright-lcd-control-gui' in ' '.join(cmdline):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor memory usage of Thermalright LCD Control GUI")
    parser.add_argument("--pid", type=int, help="Process ID to monitor (auto-detected if not specified)")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds")
    parser.add_argument("--log", default="memory_usage.log", help="Log file name")
    
    args = parser.parse_args()
    
    pid = args.pid
    if pid is None:
        pid = find_gui_process()
        if pid is None:
            print("Could not find thermalright-lcd-control-gui process")
            print("Please start the GUI first or specify --pid manually")
            exit(1)
        else:
            print(f"Found GUI process with PID: {pid}")
    
    monitor_memory(pid=pid, interval=args.interval, log_file=args.log)