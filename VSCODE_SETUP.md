# 🎯 Running AstroCleanAI in VSCode

## Quick Start (3 Methods)

### Method 1: Use the Run Button (Easiest!)

1. **Open `main.py`** in VSCode
2. **Click the ▶️ Run button** at the top right
3. **Or press `F5`** to start debugging
4. **Or press `Ctrl+F5`** to run without debugging

That's it! VSCode will use the virtual environment automatically.

---

### Method 2: Use Integrated Terminal

1. **Open Terminal in VSCode:**
   - Press `` Ctrl+` `` (backtick) or
   - Go to `Terminal` → `New Terminal`

2. **Make sure it's Command Prompt** (not PowerShell):
   - If it shows PowerShell, click the dropdown arrow next to `+`
   - Select "Command Prompt"

3. **Run the program:**
   ```cmd
   spaceenv\Scripts\python.exe main.py
   ```

   **OR** if virtual environment is activated:
   ```cmd
   python main.py
   ```

---

### Method 3: Use Python Extension

1. **Select Python Interpreter:**
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose: `.\spaceenv\Scripts\python.exe`

2. **Run the file:**
   - Right-click on `main.py`
   - Select "Run Python File in Terminal"

---

## 🔧 Configure VSCode (One-Time Setup)

I've created configuration files for you:

### Files Created:
- `.vscode/launch.json` - Debug configurations
- `.vscode/settings.json` - Python interpreter settings

### What This Does:
- ✅ Sets Python interpreter to your virtual environment
- ✅ Configures terminal to use Command Prompt (avoids PowerShell issues)
- ✅ Sets up debug configurations

---

## 🚀 Running the Program

### Option A: Run Button
1. Open `main.py`
2. Click **▶️ Run** button (top right)
3. Or press **`F5`**

### Option B: Terminal Command
1. Open terminal: `` Ctrl+` ``
2. Run: `spaceenv\Scripts\python.exe main.py`

### Option C: Right-Click Menu
1. Right-click on `main.py`
2. Select "Run Python File in Terminal"

---

## 🐛 Debugging

To debug your code:

1. **Set breakpoints** by clicking left of line numbers
2. **Press `F5`** to start debugging
3. **Use debug controls:**
   - `F5` - Continue
   - `F10` - Step Over
   - `F11` - Step Into
   - `Shift+F11` - Step Out
   - `Shift+F5` - Stop

---

## ⚙️ Terminal Settings

If VSCode opens PowerShell instead of Command Prompt:

1. **Press `Ctrl+Shift+P`**
2. **Type:** "Terminal: Select Default Profile"
3. **Choose:** "Command Prompt"

Or add to settings:
```json
"terminal.integrated.defaultProfile.windows": "Command Prompt"
```

---

## 📋 Quick Commands

| Action | Shortcut | Command |
|--------|----------|---------|
| **Run** | `F5` | Debug with breakpoints |
| **Run (no debug)** | `Ctrl+F5` | Run without debugging |
| **Terminal** | `` Ctrl+` `` | Open terminal |
| **Select Interpreter** | `Ctrl+Shift+P` → "Python: Select Interpreter" | Choose Python version |

---

## 🔍 Verify Setup

1. **Check Python Interpreter:**
   - Look at bottom-right of VSCode
   - Should show: `Python 3.x.x ('spaceenv': venv)`

2. **Test Run:**
   - Open `main.py`
   - Press `F5`
   - Should run without errors!

---

## 💡 Tips

- **Always use Command Prompt terminal** (not PowerShell) to avoid execution policy issues
- **The ▶️ Run button** is the easiest way to run
- **Set breakpoints** to debug your code
- **Check terminal output** for any error messages

---

## 🎯 Recommended Workflow

1. **Open VSCode** in your project folder
2. **Open `main.py`**
3. **Click ▶️ Run** or press `F5`
4. **View output** in terminal
5. **Open results:** `output/collision_scenario.html`

---

**That's it! VSCode makes it super easy to run Python programs! 🚀**
