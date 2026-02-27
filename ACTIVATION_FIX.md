# Fixing PowerShell Execution Policy Error

## The Problem

PowerShell is blocking the activation script due to Windows security policies. This is a common issue on Windows systems.

## Solutions (Choose One)

### Solution 1: Use Command Prompt Instead (Easiest)

**Don't use PowerShell** - Use Command Prompt (cmd.exe) instead:

1. Open **Command Prompt** (not PowerShell)
2. Navigate to your project:
   ```cmd
   cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
   ```
3. Activate the environment:
   ```cmd
   spaceenv\Scripts\activate.bat
   ```

**OR** use the provided batch file:
```cmd
activate_env.bat
```

### Solution 2: Use Python Directly (No Activation Needed)

You can run Python commands directly without activating:

```cmd
spaceenv\Scripts\python.exe -m pip install -r requirements.txt
spaceenv\Scripts\python.exe main.py
```

Or create aliases:
```cmd
set PYTHON=spaceenv\Scripts\python.exe
set PIP=spaceenv\Scripts\pip.exe

%PIP% install -r requirements.txt
%PYTHON% main.py
```

### Solution 3: Fix PowerShell Execution Policy (Requires Admin)

**Option A: Allow scripts for current user only (Recommended)**
```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option B: Allow scripts for this session only**
```powershell
# In PowerShell (no admin needed):
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
spaceenv\Scripts\activate
```

**Option C: Bypass policy for single command**
```powershell
powershell -ExecutionPolicy Bypass -File spaceenv\Scripts\Activate.ps1
```

### Solution 4: Use the Batch File Provided

I've created `activate_env.bat` for you. Simply double-click it or run:
```cmd
activate_env.bat
```

## Recommended Workflow

### For Command Prompt Users:
```cmd
cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
activate_env.bat
pip install -r requirements.txt
python main.py
```

### For PowerShell Users (After Fixing Policy):
```powershell
cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
spaceenv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Quick Reference

| Method | Command | Works In |
|--------|---------|----------|
| Batch file | `activate_env.bat` | CMD |
| Direct Python | `spaceenv\Scripts\python.exe` | CMD/PowerShell |
| CMD activation | `spaceenv\Scripts\activate.bat` | CMD only |
| PowerShell (fixed) | `spaceenv\Scripts\activate` | PowerShell |

## Verify It's Working

After activation, you should see `(spaceenv)` at the start of your command prompt:
```
(spaceenv) C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI>
```

## Still Having Issues?

1. **Make sure virtual environment exists:**
   ```cmd
   dir spaceenv\Scripts
   ```
   Should show `activate.bat` and `python.exe`

2. **If it doesn't exist, create it:**
   ```cmd
   python -m venv spaceenv
   ```

3. **Use Command Prompt instead of PowerShell** - This is the simplest solution!

---

**Tip:** Most Windows developers use Command Prompt (cmd.exe) for Python virtual environments to avoid these PowerShell issues.
