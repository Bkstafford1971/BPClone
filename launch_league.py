#!/usr/bin/env python3
"""
launch_league.py — Launches the League Server with Browser Management

When you close the browser, this script automatically:
1. Stops the league server
2. Closes the terminal
3. Cleans up all associated processes

Usage:
  python3 launch_league.py
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
SERVER_SCRIPT = BASE_DIR / "league_server.py"
SERVER_URL = "http://localhost:5000"
PORT = 5000

def find_free_port(start_port=5000, max_attempts=10):
    """Find an available port, in case 5000 is in use."""
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
    """Launch the League server process."""
    print(f"[LAUNCHER] Starting League Server on port {PORT}...")
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
    """Open the league in the default browser."""
    print(f"[LAUNCHER] Opening browser to {SERVER_URL}...")
    try:
        webbrowser.open(SERVER_URL)
        print(f"[LAUNCHER] Browser launched")
    except Exception as e:
        print(f"[WARNING] Could not auto-open browser: {e}")
        print(f"[INFO] Please manually open: {SERVER_URL}")

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
    print("BLOODSPIRE League/Admin Server Launcher")
    print("=" * 60)
    print("[NOTE] This is the ADMIN PANEL")
    print("[NOTE] Closing this browser will STOP the server")
    print()
    
    # Start the server
    server_process = launch_server()
    
    # Wait for server to be ready
    if not wait_for_server(SERVER_URL):
        print("[ERROR] Server failed to start within timeout")
        kill_process(server_process)
        sys.exit(1)
    
    # Launch browser
    launch_browser()
    
    print("\n[LAUNCHER] Admin panel is monitoring...")
    print("[LAUNCHER] Close the admin panel browser to stop the server and exit")
    print("[LAUNCHER] (Regular game browsers can be closed without stopping the server)")
    print("=" * 60 + "\n")
    
    try:
        # Monitor the admin browser/server
        import socket
        last_connection = time.time()
        monitor_interval = 1
        timeout_after_disconnect = 30  # Give 30 seconds after last connection before assuming browser is closed
        
        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', PORT))
                sock.close()
                
                if result == 0:
                    last_connection = time.time()
            except:
                pass
            
            # Check if server is still running
            if server_process.poll() is not None:
                print("\n[LAUNCHER] Server stopped unexpectedly")
                break
            
            # If no connection for timeout_after_disconnect seconds, assume admin browser is closed
            if time.time() - last_connection > timeout_after_disconnect:
                print("\n[LAUNCHER] Admin panel closed - shutting down server")
                break
            
            time.sleep(monitor_interval)
    
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Interrupted by user")
    
    finally:
        print("[LAUNCHER] Cleaning up...")
        kill_process(server_process)
        print("[LAUNCHER] Server stopped")
        print("[LAUNCHER] Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
