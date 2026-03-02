# 🎯 OPEN THIS FILE IN YOUR BROWSER

## PowerShell is Blocking - Use Browser Instead!

Your PowerShell execution policy is blocking all scripts. No problem - I've created a simple HTML solution!

## What to Do (10 seconds)

### Step 1: Open the HTML File
Double-click this file to open it in your browser:
```
CLICK_TO_POPULATE.html
```

Or right-click and choose "Open with" → Your browser (Chrome, Edge, Firefox, etc.)

### Step 2: Click the Button
The page will show:
- Current database counts
- A big blue button that says "Click Here to Populate Database"
- Click it!

### Step 3: Wait 5-10 Seconds
You'll see:
- "Populating database... Please wait..."
- Then: "✅ Success! Added 450 satellites"

### Step 4: Refresh AstroCleanAI
Go back to your AstroCleanAI browser tab and press:
```
Ctrl + Shift + R
```

You should now see:
- **Satellites: 450+**
- **Debris: 500**
- Fast Mode will auto-start!

## What the HTML File Does

1. Calls the API endpoint: `http://localhost:5000/api/populate_satellites`
2. Reads all TLE files from `data/` directory
3. Adds satellites to database
4. Shows you the results

## If It Doesn't Work

Make sure:
1. ✅ Server is running (http://localhost:5000)
2. ✅ You're opening the HTML file in a browser
3. ✅ You clicked the blue button
4. ✅ You waited for "Success!" message

## Alternative: Manual PowerShell

If you want to bypass the execution policy manually:

1. Open PowerShell as Administrator
2. Run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
cd "C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI"
python quick_populate.py
```

---

**ACTION**: Open `CLICK_TO_POPULATE.html` in your browser NOW! 🚀
