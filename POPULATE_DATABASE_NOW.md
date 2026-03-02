# Populate Database - Action Required! 🚀

## Current Status

✅ Server is running on http://localhost:5000  
✅ 500 LEO debris added to database  
✅ 450+ TLE files exist in `data/` directory  
❌ Satellites NOT in database yet (showing 0 in frontend)

## The Problem

Your TLE files exist but the satellites aren't in the database. The frontend shows "Satellites: 0" because it queries the database, not the files.

## The Solution

I've added an API endpoint `/api/populate_satellites` that will read all TLE files and add them to the database.

## How to Fix (Choose ONE method)

### Method 1: Open Browser (EASIEST)
1. Open this file in your browser: `populate_db.html`
2. Click the "Populate Satellites from TLE Files" button
3. Wait for success message
4. Refresh your AstroCleanAI page

### Method 2: Use PowerShell
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/populate_satellites" -Method POST
```

### Method 3: Use curl
```bash
curl -X POST http://localhost:5000/api/populate_satellites
```

### Method 4: Use Python Script
```bash
.\spaceenv\Scripts\python.exe populate_satellites_from_files.py
```

### Method 5: Use Batch File
```bash
.\run_populate_satellites.bat
```

## What Will Happen

The endpoint will:
- Find all `sat_*.txt` files in the `data/` directory (~450 files)
- Read each file to get the satellite name
- Add each satellite to the database
- Skip any that already exist
- Return a summary

Expected result:
```json
{
  "status": "success",
  "added": 450,
  "skipped": 0,
  "total_files": 450
}
```

## After Populating

1. Refresh your browser (Ctrl+F5 or Ctrl+Shift+R)
2. You should see:
   - **Satellites: 450+**
   - **Debris Objects: 500**
3. Fast Mode will automatically start screening
4. You'll see actual collision probabilities!

## Why This Happened

The TLE files were created by previous scripts, but they never added the satellites to the database. The database and TLE files are separate - both need to be populated.

---

**Next Step**: Choose one of the methods above and run it NOW! The server is ready and waiting.
