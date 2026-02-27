# ⚡ Quick Fix - Copy & Paste These Commands

## In PowerShell Terminal:

**Step 1: Delete old TLE files**
```powershell
Remove-Item data\*.txt -ErrorAction SilentlyContinue
```

**Step 2: Download fresh TLE data**
```powershell
.\spaceenv\Scripts\python.exe fetch_tle.py
```

**Step 3: Run the program**
```powershell
.\spaceenv\Scripts\python.exe main.py
```

---

## Or Switch to Command Prompt:

1. Click dropdown next to `+` in terminal
2. Select "Command Prompt"
3. Then run:
```cmd
del data\*.txt
spaceenv\Scripts\python.exe fetch_tle.py
spaceenv\Scripts\python.exe main.py
```

---

## Or Use the Batch File:

**In PowerShell:**
```powershell
.\refresh_and_run.bat
```

**In Command Prompt:**
```cmd
refresh_and_run.bat
```
