# 🚀 How to Run AstroCleanAI

## Quick Start (3 Steps)

### Step 1: Activate Virtual Environment

**Option A: Use Command Prompt (Recommended)**
```cmd
cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI
activate_env.bat
```

**Option B: Manual Activation**
```cmd
spaceenv\Scripts\activate.bat
```

**Option C: Use Python Directly (No Activation Needed)**
```cmd
spaceenv\Scripts\python.exe main.py
```

### Step 2: Install Dependencies (First Time Only)

If you haven't installed dependencies yet:
```cmd
pip install -r requirements.txt
```

### Step 3: Run the Program

```cmd
python main.py
```

That's it! The program will:
1. ✓ Automatically download satellite data (if needed)
2. ✓ Analyze collision scenarios
3. ✓ Generate 3D visualization
4. ✓ Save results to `output/collision_scenario.html`

## View Results

After running, open the visualization in your browser:
```
output/collision_scenario.html
```

## Complete Example

```cmd
REM Navigate to project folder
cd C:\Users\ASUS\OneDrive\Desktop\AstroCleanAI\AstroCleanAI

REM Activate environment (or skip if using Python directly)
activate_env.bat

REM Install dependencies (first time only)
pip install -r requirements.txt

REM Run the program
python main.py

REM Open results in browser
start output/collision_scenario.html
```

## Troubleshooting

### "Module not found" error
**Solution:** Install dependencies:
```cmd
pip install -r requirements.txt
```

### "TLE file not found" error
**Solution:** The program will auto-download, but you can manually download:
```cmd
python fetch_tle.py
```

### "No module named 'sgp4'" error
**Solution:** Make sure virtual environment is activated and dependencies are installed:
```cmd
activate_env.bat
pip install -r requirements.txt
```

### Want to verify everything works first?
```cmd
python test_system.py
```

## What the Program Does

When you run `python main.py`, it will:

1. **Check for satellite data** - Downloads TLE files if missing
2. **Load orbital data** - Reads ISS and debris trajectories
3. **Propagate orbits** - Predicts positions over 3 hours
4. **Detect close approaches** - Finds potential collisions
5. **Calculate collision probability** - Uses Monte Carlo simulation
6. **Optimize avoidance maneuvers** - If collision risk detected
7. **Generate 3D visualization** - Creates interactive HTML plot

## Output Files

After running, you'll find:
- `output/collision_scenario.html` - Interactive 3D visualization
- `data/iss.txt` - ISS satellite data (auto-downloaded)
- `data/debris1.txt` - Debris object data (auto-downloaded)

---

**That's all you need! Just run `python main.py` and watch it work! 🛰️**
