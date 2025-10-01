#!/usr/bin/env python3
"""
Quick server restart script
"""
import subprocess
import sys
import time
import os

def restart_server():
    print("🔄 Restarting PRP AI Assistant System...")
    
    # Kill any existing Python processes on port 8000
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        time.sleep(1)
    except:
        pass
    
    # Change to the correct directory
    os.chdir(r"C:\Users\User\OneDrive\Desktop\1111")
    
    # Start the new server
    print("🚀 Starting server with updated code...")
    subprocess.Popen([sys.executable, "prp_app.py"], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    print("✅ Server restarted! Visit http://127.0.0.1:8000")
    print("📱 Network access: http://192.168.1.156:8000")

if __name__ == "__main__":
    restart_server()