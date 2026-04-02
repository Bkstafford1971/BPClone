# Smart Server Launchers

This guide explains how to use the new smart launcher scripts.

## What They Do

### Game Server Launcher (`launch_game.py`)
**Server behavior:** Keeps running regardless of browser activity
- Start server and open game browser
- Close game browser → Server **stays running**
- Press **Ctrl+C** in terminal to stop server

### League/Admin Server Launcher (`launch_league.py`)
**Server behavior:** Stops when admin panel closes
- Start server and open admin panel browser
- Close admin panel browser → Server **stops automatically**
- Server keeps running as long as admin panel is open

---

## Usage

### Option 1: Windows Batch Files (Easiest on Windows)

**For the Game Server (keeps running):**
```
Double-click: START_GAME_SMART.bat
```

**For the League/Admin Server (stops when browser closes):**
```
Double-click: START_LEAGUE_SERVER_SMART.bat
```

### Option 2: Python Command Line (All Platforms)

**For the Game Server:**
```bash
python launch_game.py
```

**For the League/Admin Server:**
```bash
python launch_league.py
```

### Option 3: From Terminal Directly

**macOS/Linux:**
```bash
./launch_game.py
./launch_league.py
```

**Windows (PowerShell):**
```powershell
python launch_game.py
python launch_league.py
```

---

## Workflow Example

### Running the Game Server
1. Double-click `START_GAME_SMART.bat` (or run `python launch_game.py`)
2. Game server starts, browser opens to `http://localhost:8000`
3. Play the game, close/open browser tabs as needed
4. Server **stays running** the entire time
5. When done, press **Ctrl+C** in the terminal to stop the server

### Running the Admin Server
1. Double-click `START_LEAGUE_SERVER_SMART.bat` (or run `python launch_league.py`)
2. Admin server starts, browser opens to `http://localhost:5000`
3. Manage the league/admin panel
4. When you close the admin panel browser, server automatically stops
5. Terminal closes automatically

---

## Configuration

### Change the Port Numbers

Edit the launcher script and change these lines:

**For Game Server (launch_game.py):**
```python
PORT = 8000
SERVER_URL = "http://localhost:8000"
```

**For League Server (launch_league.py):**
```python
PORT = 5000
SERVER_URL = "http://localhost:5000"
```

### Change the Inactivity Timeout (Admin Panel Only)

Edit this line in `launch_league.py` (currently 30 seconds):
```python
timeout_after_disconnect = 30  # seconds
```

This is how long to wait after browser closes before stopping the server.

---

## Troubleshooting

### "Python is not installed or not in PATH"
- **Windows**: Install Python from [python.org](https://python.org)
- Make sure to check "Add Python to PATH" during installation

### Browser doesn't automatically open
- The server will still run correctly
- You can manually navigate to `http://localhost:8000` (Game) or `http://localhost:5000` (Admin)
- Server behavior stays the same (Game: keeps running, Admin: closes on browser close)

### "Port already in use" error
- Another process is using that port
- On Windows: `netstat -ano | findstr :8000` to find the process
- On macOS/Linux: `lsof -i :8000` to find the process
- Kill the process or change the port number in the launcher

### Game server won't stop
- Use **Ctrl+C** in the terminal running the launcher
- This forcefully terminates the server

---

## Advanced: Manual Server Control

If you want to run servers without the launchers:

**Game Server (normal, keeps running):**
```bash
python gui_server.py
```

**League Server (normal, keeps running):**
```bash
python league_server.py
```

Press **Ctrl+C** to stop either server.

---

## Key Differences

| Feature | Game Server | Admin Server |
|---------|------------|--------------|
| Browser close → Server stops | ❌ No | ✅ Yes |
| Manual Ctrl+C → Server stops | ✅ Yes | ✅ Yes |
| Server stays running | ✅ Yes | ❌ (closes with admin browser) |
| Protocol | Game clients can connect freely | Admin panel monitoring |


