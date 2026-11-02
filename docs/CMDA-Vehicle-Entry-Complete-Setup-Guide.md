# CMDA Steel Yard Vehicle Entry Management

## Complete Setup and Operations Guide

**Application:** CMDA Market Management Committee — Chennai Steel Yard intranet portal  
**Version:** 1.0.0  
**Audience:** IT staff or a supervisor setting up a new Windows PC as the yard server  
**Last updated:** 1 November 2026

This document covers a **new machine** from a blank Windows install through daily use, client PCs, backup, and restore.

---

## 1. What this system is

This is an **intranet** application. One PC in the yard is the **server**. Gate PCs are **clients**. Operators open a web browser; they do not install the database on the gate PCs.

| Role | What runs there | What the person does |
|---|---|---|
| Server PC (this application) | Node.js + SQLite database | Keep the program running all day |
| Gate 1 / Gate 2 / Gate 3 PCs | Browser only (Chrome or Edge) | Register entry, process exit, print receipts |

All three gates share **one** database. A lorry entered at Gate 1 appears on Gate 2 and Gate 3 within a few seconds.

**Do not** start the server on more than one PC. **Do not** copy the database file onto each gate PC.

---

## 2. How the network works

```
  [Gate 1 PC] ----\
                    \     LAN / Wi-Fi
  [Gate 2 PC] -------->  Server PC  (Node.js on port 3000)
                    /     SQLite file: cmda_yard.db
  [Gate 3 PC] ----/
```

- Server listens on **all network cards**, port **3000**.
- Clients use: `http://SERVER-LAN-IP:3000`  
  Example on the current yard network: `http://192.168.0.110:3000`
- The server PC can also use: `http://localhost:3000`
- All PCs must be on the **same LAN** (same office network / same Wi-Fi, not mobile hotspot unless the server is on that hotspot too).
- The system works **without internet**. Internet is needed only once, to install Node.js and run `npm install`.

---

## 3. What you need before starting

### 3.1 Server PC (one machine)

| Item | Requirement |
|---|---|
| Operating system | Windows 10 or Windows 11 (64-bit) |
| RAM | 4 GB minimum, 8 GB recommended |
| Disk | At least 2 GB free (application + growing database) |
| Network | Ethernet preferred (more stable than Wi-Fi) |
| Power | Keep the PC on during working hours; use a UPS if possible |
| Folder location | Example: `C:\vechile-entry-managment` or `D:\vechile-entry-managment` |

Give the server a **fixed (static) LAN IP** so gate PCs do not lose the address after a restart. Ask the network admin, or set it in Windows:

**Settings → Network & Internet → Ethernet (or Wi-Fi) → Hardware properties → Edit IP assignment → Manual → IPv4**

Example:

- IP address: `192.168.0.110`
- Subnet mask: `255.255.255.0`
- Gateway: your router (often `192.168.0.1`)

### 3.2 Client / gate PCs (two or three machines)

| Item | Requirement |
|---|---|
| Browser | Microsoft Edge or Google Chrome (current version) |
| Network | Same LAN as the server |
| Extra software | **None.** Do not install Node.js or SQLite on gate PCs. |
| Printer | Optional thermal printer for 80 mm receipts (Windows default printer) |

### 3.3 Software you must install (server PC only)

| Software | Required? | Why |
|---|---|---|
| **Node.js LTS** (includes **npm**) | **Yes** | Runs the server |
| Microsoft Edge or Google Chrome | Yes (usually already on Windows) | To test the portal on the server |
| SQLite installer | **No** | Database is a file; Node.js uses it directly |
| MySQL / PostgreSQL | **No** | Not used |
| Python / Git | No | Not required to run the yard system |

Optional later:

| Software | When you need it |
|---|---|
| DB Browser for SQLite | To open `cmda_yard.db` and inspect records |
| Visual Studio Build Tools | Only if `npm install` fails while building `sqlite3` |

---

## 4. Install Node.js on a new Windows PC

You need a PC with internet for this step (or a USB copy of the Node.js installer).

### 4.1 Download

1. Open a browser and go to: [https://nodejs.org](https://nodejs.org)
2. Download **LTS** (Long Term Support), Windows 64-bit **.msi** installer.  
   Example: Node.js 22 LTS or newer. This project was tested with **Node.js 24**.
3. Do **not** download the “Current” (non-LTS) build unless LTS is unavailable.

### 4.2 Run the installer

1. Double-click the `.msi` file.
2. Click **Next**.
3. Accept the license → **Next**.
4. Keep the default folder (`C:\Program Files\nodejs\`) → **Next**.
5. On **Custom Setup**, leave all features enabled. Confirm that **npm package manager** and **Add to PATH** are included.
6. If you see **Tools for Native Modules**, you may tick it. It is optional; skip it if the yard PC should stay simple.
7. Click **Install**. Allow User Account Control if Windows asks.
8. Click **Finish**.
9. **Close and reopen** any Command Prompt or PowerShell windows so PATH is updated.

### 4.3 Confirm Node.js works

1. Press **Windows key**, type `powershell`, open **Windows PowerShell**.
2. Run:

```powershell
node -v
npm -v
```

3. You should see version numbers, for example:

```
v24.12.0
11.6.2
```

If you see `'node' is not recognized`:

- Restart the PC and try again.
- Reinstall Node.js and ensure **Add to PATH** is selected.

---

## 5. Copy the application onto the new PC

Copy the **entire project folder** to the server, for example:

```
D:\vechile-entry-managment
```

or

```
C:\vechile-entry-managment
```

### 5.1 What must be copied

| Item | Copy? | Notes |
|---|---|---|
| `server.js` | Yes | Main program |
| `package.json` | Yes | Package list |
| `package-lock.json` | Yes | Exact versions |
| `start.bat` | Yes | Easy start |
| `public\` | Yes | Web screens |
| `db\` | Yes | Database design (`schema.sql`, `init.js`) |
| `docs\` | Yes | This documentation |
| `cmda_yard.db` | Only if you want **existing** records | Skip for a **blank** new yard |
| `cmda_yard.db-wal` and `cmda_yard.db-shm` | Together with the `.db` if you copy a live database | See backup section |
| `node_modules\` | Optional | Safer to run `npm install` on the new PC |
| `index.html` / `server.txt` at the folder root | Not used by the running app | The live page is `public\index.html` |

**Do not** copy only `index.html`. The running website is served from the `public` folder.

### 5.2 Blank system vs existing data

- **New yard / empty database:** do **not** copy `cmda_yard.db`. The server creates a fresh file on first start.
- **Moving an existing yard:** copy the database files as described in **Section 14 Restore**.

---

## 6. First-time setup on the server PC

1. Open the project folder in File Explorer, for example `D:\vechile-entry-managment`.
2. In the empty area of the folder, hold **Shift** and **right-click** → **Open PowerShell window here**  
   (or open PowerShell and `cd` to the folder).
3. Install application libraries (needs internet the first time):

```powershell
cd D:\vechile-entry-managment
npm install
```

4. Wait until you see `added ... packages`. A `node_modules` folder will appear.
5. You do **not** install SQLite separately. The first time you start the server, it creates:

```
D:\vechile-entry-managment\cmda_yard.db
```

and loads gates and fee rates from `db\schema.sql`.

### 6.1 If `npm install` fails

Most Windows PCs use a **prebuilt** `sqlite3` binary and succeed.

If the log shows `node-gyp` / `MSBUILD` / `Python` errors:

1. Install **Visual Studio Build Tools**: [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Select **Desktop development with C++**.
3. Restart the PC.
4. Run `npm install` again.

If the PC has **no internet**, copy a complete `node_modules` folder from a PC that already ran `npm install` with the **same Node.js major version** (for example both on Node 24).

---

## 7. Allow the server through Windows Firewall

Gate PCs cannot connect until Windows allows **TCP port 3000**.

1. On the **server PC**, click Start, type `PowerShell`.
2. Right-click **Windows PowerShell** → **Run as administrator**.
3. Run:

```powershell
netsh advfirewall firewall add rule name="CMDA Vehicle Entry" dir=in action=allow protocol=TCP localport=3000
```

4. You should see `Ok.`

To confirm the rule exists:

```powershell
netsh advfirewall firewall show rule name="CMDA Vehicle Entry"
```

If a third-party antivirus firewall is installed, allow Node.js or port 3000 there as well.

---

## 8. How to start the server

The server must stay running while gates are working. Closing the window **stops** the system for every client.

### 8.1 Easiest way (recommended)

1. Open folder `D:\vechile-entry-managment` (or wherever you copied it).
2. Double-click **`start.bat`**.
3. If Windows SmartScreen appears, choose **More info** → **Run anyway**.
4. Leave the black window **open**.

`start.bat` will:

- Check that Node.js is installed
- Run `npm install` if `node_modules` is missing
- Start the server

### 8.2 Manual start (PowerShell)

```powershell
cd D:\vechile-entry-managment
npm start
```

or:

```powershell
cd D:\vechile-entry-managment
node server.js
```

### 8.3 What a successful start looks like

```
CMDA Vehicle Entry server is running.
Database file: D:\vechile-entry-managment\cmda_yard.db
On this PC:    http://localhost:3000
On LAN client: http://192.168.0.110:3000
```

Write down the **LAN client** line. That is the address for Gate 1, Gate 2, and Gate 3.

If several LAN IPs are printed, use the one on the yard network (usually `192.168.x.x`), not a virtual adapter.

### 8.4 Test on the server PC

1. Open Edge or Chrome.
2. Go to `http://localhost:3000`
3. You should see the **Sign in** page (navy CMDA panel and a white card).
4. Default username: **admin** — default password: **admin**
5. Click **Enter portal**.
6. You should see **CMDA MARKET MANAGEMENT COMMITTEE** and a green line: **Connected to central server.**

### 8.5 How to stop the server

1. Click the server window.
2. Press `Ctrl + C`.
3. If it asks to terminate, confirm, or close the window.

Wait until gates have finished the current ticket before stopping.

---

## 9. Connect client PCs (Gate 1, Gate 2, Gate 3)

On **each** gate PC:

1. Confirm the PC is on the same network as the server (same IP range, for example `192.168.0.x`).
2. Open Edge or Chrome.
3. In the address bar type the LAN URL from the server window, for example:

```
http://192.168.0.110:3000
```

4. Press Enter.
5. Sign in with **admin** / **admin** (or the yard password if it was changed).
6. You should see the portal and **Connected to central server.**
7. Optional: pin or bookmark the page, or set it as the browser home page.

### 9.1 Create a desktop shortcut on a gate PC

1. Right-click the desktop → **New** → **Shortcut**.
2. Location:

```
http://192.168.0.110:3000
```

3. Name it `CMDA Vehicle Entry` → **Finish**.

Replace the IP with the server’s real LAN IP.

### 9.2 Three clients at the same time

Supported. Typical use:

| PC | Operator selects |
|---|---|
| Gate 1 | System Terminal Gate = Gate 1 |
| Gate 2 | Gate 2 |
| Gate 3 | Gate 3 |

Rules:

- Start **one** server only.
- A vehicle number that is already **inside** cannot be entered again until it exits.
- Screens refresh about every **4 seconds**.

### 9.3 Sign in to the portal

Every operator (server PC and each gate PC) must sign in before vehicle entry is available.

| Field | Default value |
|---|---|
| Username | `admin` |
| Password | `admin` |

1. The first screen is the professional **Sign in** page.
2. Enter the username and password, then click **Enter portal**.
3. A wrong password shows **Invalid username or password.**
4. Use **Sign out** in the top-right of the portal when the shift ends.
5. The session lasts **12 hours**. After that, sign in again.

The `admin` account is created automatically the first time the server starts. All three gates may use the same account.

---

## 10. Using the application (operators)

Sign in first (Section 9.3). Vehicle entry, exit, and reports are blocked until the session is valid.

### 10.1 Vehicle entry

1. Choose **System Terminal Gate**.
2. Type **Vehicle Number** (example: `TN 04 AB 1234`).
3. Choose **Vehicle Type** and **Entry Type** (Single or Multiple).
4. Keep **Entry Date & Time** (filled automatically) unless you must correct it.
5. Click **SAVE TO CENTRAL DATABASE**.

### 10.2 Vehicle exit

1. Find the vehicle in **Vehicle Movement Log** (use Search if needed).
2. Click **Process Exit**.
3. Choose **Exit Gate** and confirm time.
4. Leave **Auto-Print Thermal Receipt** ticked if a printer is ready.
5. Click **CONFIRM & SYNC**.
6. Allow pop-ups in the browser if the receipt window is blocked.

### 10.3 Daily settlement

1. Choose the date.
2. **Total Collected** and **Exited Count** fill automatically (vehicles that **exited** that date).
3. **DOWNLOAD CSV** saves a spreadsheet of the log.
4. **PRINT REPORT** prints the page (hides buttons).

### 10.4 Fee rules (stored in the database)

Charging is **one slab per 24 hours**, minimum **1 slab**, calculated on the server.

| Vehicle type | Single entry (₹) | Multiple entry (₹) |
|---|---|---|
| Lorry / Trailers / Multiaxle | 165 | 240 |
| Light Motor Vehicle (LMV) | 65 | 120 |
| Steel Yard Trailers Association | 65 | 120 |

Example: a lorry on a single pass that stays 26 hours = 2 slabs × 165 = **₹330**.

To change rates later, edit table `vehicle_types` in `cmda_yard.db` (see DB Browser in Section 16) or update `db\schema.sql` only for **new** empty databases. Existing rates live in the database file, not in the web page.

---

## 11. Database design (for IT)

Engine: **SQLite 3**, file `cmda_yard.db` next to `server.js`.  
Mode: WAL (Write-Ahead Logging) so several gates can read while one write happens.

| Table | Purpose |
|---|---|
| `gates` | Gate 1, Gate 2, Gate 3 |
| `vehicle_types` | Codes, display names, single/multiple rates |
| `vehicles` | One row per visit (entry, optional exit, amount) |

Important rules:

- `vehicles.number` may appear only **once** while `exit` is empty (vehicle still inside).
- Exit amount is calculated by the server, not trusted from the browser.

You do **not** run a separate database service. If the server PC is off, nobody can use the portal.

---

## 12. Backup (do this every day)

The live data is **not** inside `index.html`. It is in:

```
D:\vechile-entry-managment\cmda_yard.db
D:\vechile-entry-managment\cmda_yard.db-wal
D:\vechile-entry-managment\cmda_yard.db-shm
```

The `-wal` and `-shm` files appear while the server is running. A backup is complete only if you copy **all three** that exist, or you stop the server first and then copy `cmda_yard.db` (WAL is merged on a clean stop).

### 12.1 Recommended daily backup (stop, then copy)

1. Tell gate operators to pause for one minute.
2. In the server window press `Ctrl + C` to stop the server.
3. Open File Explorer at the project folder.
4. Copy these files if they exist:
   - `cmda_yard.db`
   - `cmda_yard.db-wal`
   - `cmda_yard.db-shm`
5. Paste them into a backup folder named with the date, for example:

```
D:\CMDA-Backups\2026-11-01\
E:\USB-CMDA\2026-11-01\
```

6. Start the server again (`start.bat`).
7. Keep at least **7 daily copies** plus **one copy off the server PC** (USB drive or another computer).

### 12.2 Backup using `backup.bat`

1. Stop the server if you can (`Ctrl + C`).
2. Double-click **`backup.bat`** in the project folder.
3. Press any key when asked.
4. Files are saved under `D:\vechile-entry-managment\backups\` in a dated folder.
5. Copy that dated folder to a USB drive.

### 12.3 Backup with PowerShell (after the server is stopped)

Run in PowerShell. Change the paths if your folders are different.

```powershell
$src = "D:\vechile-entry-managment"
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$dest = "D:\CMDA-Backups\$stamp"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "$src\cmda_yard.db" $dest -ErrorAction SilentlyContinue
Copy-Item "$src\cmda_yard.db-wal" $dest -ErrorAction SilentlyContinue
Copy-Item "$src\cmda_yard.db-shm" $dest -ErrorAction SilentlyContinue
Write-Host "Backup saved to $dest"
Get-ChildItem $dest
```

### 12.4 Quick copy while the server is running (emergency only)

If you cannot stop the server, copy **all three** files (`cmda_yard.db`, `.db-wal`, `.db-shm`) in the **same moment** into the same backup folder. This is usually good enough for this yard, but a stopped-server copy is safer.

Never copy only `cmda_yard.db` while the server is running and then delete the WAL files. That can lose the latest entries.

### 12.5 What else to back up (less often)

Once after setup, and again after any program change, copy the application folder **except** `node_modules`:

- `server.js`, `package.json`, `package-lock.json`, `start.bat`
- `public\`
- `db\`
- `docs\`

The database backup is the one that protects **vehicle records and revenue**.

### 12.6 Suggested backup calendar

| When | What |
|---|---|
| Every evening | Database files to `D:\CMDA-Backups\` |
| Every evening | Same copy to a USB drive taken off site |
| First day of month | Keep that day’s folder for 12 months |
| After fee/rate change | Extra named copy, e.g. `after-rate-change` |

---

## 13. Restore from backup

1. Stop the server (`Ctrl + C`).
2. In the project folder, rename the current files (do not delete until restore works):

```
cmda_yard.db          →  cmda_yard.db.old
cmda_yard.db-wal      →  cmda_yard.db-wal.old
cmda_yard.db-shm      →  cmda_yard.db-shm.old
```

3. Copy the three files from the backup folder into `D:\vechile-entry-managment`.
4. Names must be exactly:
   - `cmda_yard.db`
   - `cmda_yard.db-wal` (if it was in the backup)
   - `cmda_yard.db-shm` (if it was in the backup)
5. Start the server.
6. Open `http://localhost:3000` and confirm recent vehicles are visible.

If the restore looks wrong, stop the server, remove the restored files, and put the `.old` files back.

---

## 14. Move the system to a brand-new server PC

1. On the **old** PC, stop the server and take a database backup (Section 12.1).
2. On the **new** PC, install Node.js (Section 4).
3. Copy the application folder (Section 5).
4. Run `npm install` (Section 6).
5. Copy the backup database files into the new project folder (Section 13).
6. Set a static IP if possible (Section 3.1).
7. Add the firewall rule (Section 7).
8. Start the server and note the **new** LAN IP.
9. Update shortcuts on every gate PC to the new IP.
10. Keep the old PC offline as a server so two copies of the database are not used at once.

---

## 15. Start the server automatically when Windows starts

Use this so the yard does not depend on someone remembering `start.bat`.

### 15.1 Startup folder (simple)

1. Press `Windows + R`, type `shell:startup`, press Enter.
2. Right-click inside that folder → **New** → **Shortcut**.
3. Target:

```
D:\vechile-entry-managment\start.bat
```

4. Name: `CMDA Vehicle Entry Server`.
5. Sign in to Windows on the server PC each morning (or set Windows to auto-login if that is allowed).

A command window will appear after login. **Do not close it.**

### 15.2 Task Scheduler (runs even before login — optional)

1. Open **Task Scheduler**.
2. **Create Basic Task** → name `CMDA Vehicle Entry Server`.
3. Trigger: **When the computer starts**.
4. Action: **Start a program**.
5. Program: `C:\Program Files\nodejs\node.exe`
6. Arguments: `server.js`
7. Start in: `D:\vechile-entry-managment`
8. Open Properties → **Run whether user is logged on or not** (if policy allows) → **Run with highest privileges**.
9. If the task cannot open the LAN, add the firewall rule again and confirm the PC has a network connection at boot (wired is more reliable).

---

## 16. Optional tools

### 16.1 DB Browser for SQLite

Download: [https://sqlitebrowser.org](https://sqlitebrowser.org)

1. Stop the server before editing, or open the file **read-only** while it is running.
2. Open `cmda_yard.db`.
3. Use **Browse Data** on `vehicles` to search a plate number.
4. To change a fee, edit `vehicle_types` (`single_rate`, `multiple_rate`).

Do not edit `vehicles` by hand unless you are correcting a known mistake. Wrong times will change the billed amount on the next calculation only for **new** exits; already saved `amount` stays until you change that row.

---

## 17. Folder map

```
vechile-entry-managment\
  start.bat                 Double-click to start
  backup.bat                Double-click to copy the database
  server.js                 Server program
  package.json              Node package list
  cmda_yard.db              Live database (created on first run)
  cmda_yard.db-wal          WAL file while server is running
  cmda_yard.db-shm          Shared-memory file while server is running
  public\
    index.html              Operator screen
    qrcode.min.js           QR codes on receipts (works without internet)
  db\
    schema.sql              Tables, gates, default rates
    init.js                 Optional: rebuild schema
  docs\
    README.md
    CMDA-Vehicle-Entry-Complete-Setup-Guide.md   This file
```

---

## 18. Troubleshooting

| Problem | What to check |
|---|---|
| `'node' is not recognized` | Install Node.js LTS and restart. |
| `npm install` fails | Internet, then Visual Studio Build Tools (Section 6.1). |
| Browser on server shows “Cannot reach the central server” | Server window closed. Start `start.bat` again. |
| Gate PC cannot open the page | Same LAN? Correct IP? Server running? Firewall port 3000? |
| Page opens but old data | You started a **second** copy of the folder with a different `cmda_yard.db`. Use one folder only. |
| “Vehicle already inside” | That plate has an open visit. Process Exit, or search the log. |
| Receipt does not print | Allow pop-ups. Set the thermal printer as Windows default. Paper size 80 mm. |
| LAN IP changed after restart | Set a static IP (Section 3.1) and update gate shortcuts. |
| Port already in use | Another `node server.js` is running. Close it, or use Task Manager to end `Node.js JavaScript Runtime`. |
| Database locked / busy | Only one server process. Close extra `start.bat` windows. |
| Lost records | Restore last night’s backup (Section 13). |

### 18.1 Find the server LAN IP yourself

On the server PC, PowerShell:

```powershell
ipconfig
```

Look for **IPv4 Address** on Ethernet, for example `192.168.0.110`. Gate URL is `http://THAT-IP:3000`.

### 18.2 Confirm the API from the server

```powershell
Invoke-RestMethod http://localhost:3000/api/health
```

A healthy reply includes `"ok": true`.

From a gate PC, replace `localhost` with the server IP.

---

## 19. Security notes (intranet)

- This portal is designed for a **closed yard LAN**, not the public internet.
- Do not forward port 3000 on the office router to the internet.
- Operators must sign in. Default account is **admin** / **admin**. Change this password if people outside the yard desk can reach the LAN.
- Restrict Wi-Fi and physical access to gate desks.
- Keep Windows Update enabled on the server PC.

---

## 20. New-machine checklist (print this page)

**Software**

- [ ] Windows 10/11 64-bit
- [ ] Node.js LTS installed (`node -v` and `npm -v` work)
- [ ] Edge or Chrome available

**Files**

- [ ] Project folder copied (including `public`, `db`, `server.js`, `package.json`, `start.bat`)
- [ ] `npm install` completed
- [ ] Empty DB for a new site, **or** restored `cmda_yard.db` (+ wal/shm if present)

**Network**

- [ ] Static LAN IP set on the server
- [ ] Firewall rule for TCP 3000
- [ ] Ethernet cable preferred

**Start**

- [ ] `start.bat` shows `CMDA Vehicle Entry server is running`
- [ ] `http://localhost:3000` shows the Sign in page
- [ ] Sign in with **admin** / **admin**
- [ ] Each gate PC opens `http://SERVER-IP:3000` and can sign in
- [ ] Test: save one vehicle, process exit, confirm amount

**Backup**

- [ ] Folder `D:\CMDA-Backups` (or USB) created
- [ ] First backup copied and opened to confirm files are not 0 KB
- [ ] Daily backup assigned to a named person (`backup.bat` after stopping the server)
- [ ] Optional: `start.bat` shortcut in the Windows Startup folder

---

## 21. Quick reference

| Task | Action |
|---|---|
| Install runtime | Node.js LTS from https://nodejs.org |
| Install app libraries | `npm install` inside the project folder |
| Start | Double-click `start.bat` |
| Local test | http://localhost:3000 |
| Sign in | Username `admin` / password `admin` |
| Gate PCs | http://SERVER-IP:3000 |
| Firewall | `netsh advfirewall firewall add rule name="CMDA Vehicle Entry" dir=in action=allow protocol=TCP localport=3000` |
| Daily backup | Stop server, double-click `backup.bat`, copy the new folder to USB |
| Restore | Stop server, replace those files, start again |
| Stop | `Ctrl + C` in the server window |

If the server window is closed, **no gate can work**. Treat that PC like a cash-office machine: leave it on, leave the window open, back up the database every day.
