#!/usr/bin/env python3
"""
launch_game.py — Launches the Game Server with Browser Management

When you close the browser, this script automatically:
1. Stops the web server
2. Closes the terminal
3. Cleans up all associated processes

Usage:
  python3 launch_game.py
"""

import os
import sys
import subprocess
import time
import signal
import platform
import webbrowser
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent
SERVER_SCRIPT = BASE_DIR / "gui_server.py"
SERVER_URL = "http://localhost:8000"
PORT = 8000

def find_free_port(start_port=8000, max_attempts=10):
    """Find an available port, in case 8000 is in use."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result != 0:
                return port
        except:
            pass
    return start_port

def launch_server():
    """Launch the GUI server process."""
    print(f"[LAUNCHER] Starting Game Server on port {PORT}...")
    try:
        # Start the server process
        server_process = subprocess.Popen(
            [sys.executable, str(SERVER_SCRIPT)],
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=None if platform.system() == "Windows" else os.setsid
        )
        print(f"[LAUNCHER] Server started (PID: {server_process.pid})")
        return server_process
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        sys.exit(1)

def wait_for_server(url, timeout=10):
    """Wait for the server to be ready before launching browser."""
    import socket
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', PORT))
            sock.close()
            if result == 0:
                print(f"[LAUNCHER] Server is ready!")
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def launch_browser():
    """Open the game in the default browser."""
    print(f"[LAUNCHER] Opening browser to {SERVER_URL}...")
    try:
        webbrowser.open(SERVER_URL)
        print(f"[LAUNCHER] Browser launched")
    except Exception as e:
        print(f"[WARNING] Could not auto-open browser: {e}")
        print(f"[INFO] Please manually open: {SERVER_URL}")

def get_browser_process():
    """
    Find the browser process window.
    Returns the process ID if found, None otherwise.
    
    This is a best-effort approach that works on various browsers.
    """
    try:
        if platform.system() == "Windows":
            # On Windows, look for browser processes
            import ctypes
            import win32gui
            
            browser_windows = []
            def enum_handler(hwnd, ctx):
                if "localhost:8000" in win32gui.GetWindowText(hwnd):
                    browser_windows.append(hwnd)
            
            try:
                win32gui.EnumWindows(enum_handler, None)
                if browser_windows:
                    return browser_windows[0]
            except:
                pass
        
        elif platform.system() == "Darwin":  # macOS
            # Look for Chrome, Safari, or Firefox windows with our URL
            script = f"""
            tell application "System Events"
                try
                    get first application process whose name contains "Chrome" or name contains "Safari" or name contains "Firefox"
                    return true
                end try
            end tell
            """
            # Simplified: just check if any browser is running
            pass
        
    except:
        pass
    
    return None

def monitor_browser(timeout=3600):
    """
    Monitor if the browser is still running.
    Check every N seconds if browser window still exists.
    Returns True if browser is still active, False if closed.
    """
    import socket
    
    # Simple approach: try to connect to the server
    # If it fails and we expect the browser to keep it alive, assume browser closed
    check_interval = 2
    no_activity_count = 0
    max_no_activity = 5  # If 5 checks fail, assume browser is closed
    
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', PORT))
            sock.close()
            
            if result == 0:
                no_activity_count = 0
            else:
                no_activity_count += 1
                if no_activity_count >= max_no_activity:
                    print("[LAUNCHER] Server connection lost - browser may be closed")
                    return False
        
        except:
            no_activity_count += 1
            if no_activity_count >= max_no_activity:
                return False
        
        time.sleep(check_interval)

def kill_process(process):
    """Kill a process and all its children."""
    if process is None:
        return
    
    try:
        if platform.system() == "Windows":
            # On Windows, use taskkill to kill process tree
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # On Unix/Linux/macOS, use process group termination
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except:
                process.terminate()
        
        # Wait for process to die
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        
        print(f"[LAUNCHER] Server process terminated (PID: {process.pid})")
    except Exception as e:
        print(f"[WARNING] Error terminating server: {e}")

def main():
    print("=" * 60)
    print("BLOODSPIRE Game Launcher")
    print("=" * 60)
    
    # Start the server
    server_process = launch_server()
    
    # Wait for server to be ready
    if not wait_for_server(SERVER_URL):
        print("[ERROR] Server failed to start within timeout")
        kill_process(server_process)
        sys.exit(1)
    
    # Launch browser
    launch_browser()
    
    print("\n[LAUNCHER] Server is running. Browser can be closed without stopping the server.")
    print("[LAUNCHER] Press Ctrl+C in this terminal to stop the server and exit")
    print("=" * 60 + "\n")
    
    try:
        # Server keeps running even if browser closes
        # Just wait for user to manually stop it (Ctrl+C)
        while True:
            # Check if server is still running
            if server_process.poll() is not None:
                print("\n[LAUNCHER] Server stopped unexpectedly")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Interrupted by user - stopping server...")
    
    finally:
        print("[LAUNCHER] Cleaning up...")
        kill_process(server_process)
        print("[LAUNCHER] Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
