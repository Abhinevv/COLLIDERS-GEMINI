# ⚡ Quick Run Guide - No PowerShell Needed!

## 🎯 Easiest Way: Double-Click to Run!

**Just double-click this file:**
```
run_program.bat
```

That's it! The batch file will:
- ✓ Use the virtual environment automatically
- ✓ Install dependencies if needed
- ✓ Run the program
- ✓ Open results in your browser

---

## 🔧 Manual Run (Command Prompt)

**Don't use PowerShell!** Use **Command Prompt** instead:

### Step 1: Open Command Prompt
- Press `Win + R`
- Type `cmd` and press Enter

### Step 2: Navigate to Project
```cmd
cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
```

### Step 3: Run the Batch File
```cmd
run_program.bat
```

**OR** activate and run manually:
```cmd
spaceenv\Scripts\activate.bat
python main.py
```

---

## 🚀 Direct Python Method (No Activation)

You don't need to activate! Just use Python directly:

```cmd
cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
spaceenv\Scripts\python.exe main.py
```

---

## ⚠️ Why PowerShell Doesn't Work

PowerShell has security restrictions that block scripts. **Command Prompt doesn't have this issue!**

**Solutions:**
1. ✅ **Use Command Prompt** (easiest - recommended)
2. ✅ **Use `run_program.bat`** (double-click it)
3. ✅ **Use Python directly** (no activation needed)
4. ⚙️ Fix PowerShell (if you really want to use it)

---

## 🔧 Fix PowerShell (Optional)

If you really want to use PowerShell:

**Option A: Run this command in PowerShell (as Administrator)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option B: Bypass for this session only**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
spaceenv\Scripts\activate
```

**But honestly, just use Command Prompt - it's easier!**

---

## 📋 Summary

| Method | Command | Works In |
|--------|---------|----------|
| **Double-click** | `run_program.bat` | Windows Explorer |
| **Batch file** | `run_program.bat` | Command Prompt |
| **CMD activation** | `spaceenv\Scripts\activate.bat` | Command Prompt |
| **Direct Python** | `spaceenv\Scripts\python.exe main.py` | Any terminal |
| **PowerShell** | Requires fixing execution policy | PowerShell |

---

**💡 Tip: Just double-click `run_program.bat` - it handles everything!**
