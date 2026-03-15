# Colliders - Build Guide Ã°Å¸â€ºÂ Ã¯Â¸Â

This guide will help you set up and build the Colliders project from scratch.

## Prerequisites

- **Python 3.8 or higher** (Python 3.9+ recommended)
- **pip** (Python package installer)
- **Internet connection** (for downloading dependencies and TLE data)

## Quick Build (Automated)

Run the build script:

```bash
python build.py
```

This will:
1. Ã¢Å“â€œ Create required directories (`data/`, `output/`)
2. Ã¢Å“â€œ Check Python version compatibility
3. Ã¢Å“â€œ Verify project structure
4. Ã¢Å“â€œ Optionally install dependencies

## Manual Build Steps

### Step 1: Create Virtual Environment

**Windows:**

**Option A: Use Command Prompt (Recommended - avoids PowerShell issues)**
```cmd
python -m venv spaceenv
spaceenv\Scripts\activate.bat
```

**Option B: Use the provided batch file**
```cmd
python -m venv spaceenv
activate_env.bat
```

**Option C: PowerShell (if you get execution policy error, see troubleshooting)**
```powershell
python -m venv spaceenv
spaceenv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv spaceenv
source spaceenv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- numpy >= 1.24.0
- scipy >= 1.10.0
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- plotly >= 5.14.0
- sgp4 >= 2.21
- requests >= 2.31.0
- streamlit >= 1.28.0

### Step 3: Verify Installation

Run the test script:

```bash
python test_system.py
```

This checks:
- Ã¢Å“â€œ Directory structure
- Ã¢Å“â€œ File structure
- Ã¢Å“â€œ Dependencies installed
- Ã¢Å“â€œ Module imports

### Step 4: Download TLE Data

```bash
python fetch_tle.py
```

This downloads satellite orbital data from Celestrak.

### Step 5: Run the System

```bash
python main.py
```

## Project Structure After Build

```
Colliders/
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ data/              # TLE files (downloaded)
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ iss.txt
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ debris1.txt
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ debris2.txt
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ output/            # Generated visualizations
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ collision_scenario.html
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ spaceenv/          # Virtual environment (created)
Ã¢â€â€š
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ [all source files]
```

## Troubleshooting

### Issue: "Module not found"

**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: "TLE file not found"

**Solution:** Download TLE data:
```bash
python fetch_tle.py
```

### Issue: "Permission denied" (Windows)

**Solution:** Run PowerShell/Command Prompt as Administrator, or use:
```bash
python -m venv spaceenv --without-pip
```

### Issue: PowerShell Execution Policy Error

**Error:** `cannot be loaded because running scripts is disabled on this system`

**Solutions:**

1. **Use Command Prompt instead of PowerShell** (Easiest):
   ```cmd
   spaceenv\Scripts\activate.bat
   ```
   Or use: `activate_env.bat`

2. **Fix PowerShell execution policy** (requires admin):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Bypass for this session only**:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   spaceenv\Scripts\activate
   ```

4. **Use Python directly** (no activation needed):
   ```cmd
   spaceenv\Scripts\python.exe -m pip install -r requirements.txt
   spaceenv\Scripts\python.exe main.py
   ```

See `ACTIVATION_FIX.md` for detailed solutions.

### Issue: Virtual environment not activating

**Windows:**
```bash
# If Scripts folder doesn't exist, try:
python -m venv spaceenv --clear
```

**Linux/Mac:**
```bash
# Make sure you're using the correct path:
source ./spaceenv/bin/activate
```

## Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows packages)
- [ ] `data/` directory exists
- [ ] `output/` directory exists
- [ ] TLE files downloaded (`data/iss.txt` exists)
- [ ] Test script passes (`python test_system.py`)

## Next Steps

After successful build:

1. **Explore the code:** Read `README.md` and `QUICKSTART.md`
2. **Run examples:** Try individual modules (see `QUICKSTART.md`)
3. **Customize:** Modify satellite IDs in `fetch_tle.py` or `main.py`
4. **Visualize:** Open `output/collision_scenario.html` in browser

## Getting Help

- Check `TECHNICAL_DOCS.md` for detailed technical information
- Review `ARCHITECTURE.md` for system design
- Run `python test_system.py` to diagnose issues

---

**Happy Building! Ã°Å¸Å¡â‚¬**
