# 🔧 Fix: Missing Dependencies

## The Problem

You're getting `ModuleNotFoundError: No module named 'requests'` because dependencies aren't installed in your virtual environment.

## ✅ Quick Fix (Choose One)

### Option 1: Use the Install Script (Easiest!)

**In VSCode Terminal:**
1. Make sure you're in the `AstroCleanAI` folder (not parent folder)
2. Run:
   ```cmd
   install_and_run.bat
   ```

This will:
- ✓ Install all dependencies
- ✓ Run the program automatically

---

### Option 2: Install Manually (VSCode Terminal)

**Step 1: Open Terminal in VSCode**
- Press `` Ctrl+` `` (backtick)
- **Make sure it's Command Prompt** (not PowerShell)
  - Click dropdown next to `+` → Select "Command Prompt"

**Step 2: Navigate to Correct Folder**
```cmd
cd AstroCleanAI
```

**Step 3: Install Dependencies**
```cmd
spaceenv\Scripts\python.exe -m pip install -r requirements.txt
```

**Step 4: Run Program**
```cmd
spaceenv\Scripts\python.exe main.py
```

---

### Option 3: Fix VSCode Settings

**The issue:** VSCode is running from the wrong folder!

1. **Open VSCode Settings:**
   - Press `Ctrl+,`
   - Or File → Preferences → Settings

2. **Make sure you opened the correct folder:**
   - File → Open Folder
   - Select: `C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI`
   - (Not the parent `AstroCleanAI` folder)

3. **Check Python Interpreter:**
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose: `.\spaceenv\Scripts\python.exe`

---

## 🎯 Complete Solution

### Step 1: Open Correct Folder in VSCode

**Important:** Make sure you open the inner `AstroCleanAI` folder:
```
C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
```

Not:
```
C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI
```

### Step 2: Install Dependencies

**In VSCode Terminal (Command Prompt):**
```cmd
cd AstroCleanAI
spaceenv\Scripts\python.exe -m pip install -r requirements.txt
```

### Step 3: Run Program

```cmd
spaceenv\Scripts\python.exe main.py
```

---

## 🔍 Verify Installation

Check if dependencies are installed:
```cmd
spaceenv\Scripts\python.exe -m pip list
```

You should see:
- numpy
- scipy
- pandas
- matplotlib
- plotly
- sgp4
- requests
- streamlit

---

## ⚙️ VSCode Terminal Settings

**To always use Command Prompt:**

1. Press `Ctrl+Shift+P`
2. Type: "Terminal: Select Default Profile"
3. Choose: "Command Prompt"

**Or add to settings.json:**
```json
"terminal.integrated.defaultProfile.windows": "Command Prompt"
```

---

## 🚀 After Installation

Once dependencies are installed, you can:

1. **Run from VSCode:**
   - Press `F5` or click ▶️ Run button

2. **Run from Terminal:**
   ```cmd
   spaceenv\Scripts\python.exe main.py
   ```

3. **Use the batch file:**
   ```cmd
   run_program.bat
   ```

---

## 📋 Quick Checklist

- [ ] Opened correct folder in VSCode (`AstroCleanAI\AstroCleanAI`)
- [ ] Terminal is Command Prompt (not PowerShell)
- [ ] Installed dependencies: `spaceenv\Scripts\python.exe -m pip install -r requirements.txt`
- [ ] Verified installation: `spaceenv\Scripts\python.exe -m pip list`
- [ ] Ran program: `spaceenv\Scripts\python.exe main.py`

---

**The key issue:** You need to install dependencies in the virtual environment. Use `spaceenv\Scripts\python.exe -m pip install` instead of just `pip install`!
