# 🔧 Fix: Propagation Errors (Code 2)

## The Problem

You're seeing many "Propagation error code 2" warnings. This means:
- **SGP4 Error Code 2**: Invalid orbital elements (eccentricity or semi-major axis out of valid range)
- **Cause**: TLE data may be expired, corrupted, or the satellite has invalid orbital parameters

## ✅ What Happened

The program **still ran successfully** but:
- All propagations failed (0 trajectory points)
- This means the TLE data for one or both satellites is invalid
- The visualization was created but is empty

## 🔧 Solutions

### Solution 1: Download Fresh TLE Data (Recommended)

The TLE data might be expired. Download fresh data:

```cmd
spaceenv\Scripts\python.exe fetch_tle.py
```

Then run again:
```cmd
spaceenv\Scripts\python.exe main.py
```

### Solution 2: Use Different Satellites

Edit `main.py` to use different satellite IDs. Open `main.py` and find:

```python
satellites = {
    '25544': 'iss.txt',        # ISS
    '33591': 'debris1.txt',     # Debris 1
    '37820': 'debris2.txt',     # Debris 2
}
```

Try using active, well-tracked satellites:
- **25544** - ISS (International Space Station) ✅
- **25544** - ISS (use twice for testing)
- Or search Celestrak for active satellites

### Solution 3: Check TLE File Format

Open `data/debris1.txt` and verify it has 3 lines:
```
Line 1: Satellite name
Line 2: TLE line 1 (starts with "1 ")
Line 3: TLE line 2 (starts with "2 ")
```

If format is wrong, delete and re-download:
```cmd
del data\debris1.txt
spaceenv\Scripts\python.exe fetch_tle.py
```

### Solution 4: Use Test Mode

I've improved error handling. The new version will:
- ✅ Show only first 5 errors (not spam)
- ✅ Provide summary of total errors
- ✅ Give helpful error messages
- ✅ Fix deprecation warning

## 📋 Quick Fix Steps

1. **Delete old TLE files:**
   ```cmd
   del data\*.txt
   ```

2. **Download fresh TLE data:**
   ```cmd
   spaceenv\Scripts\python.exe fetch_tle.py
   ```

3. **Run program again:**
   ```cmd
   spaceenv\Scripts\python.exe main.py
   ```

## 🎯 Expected Output

After fixing, you should see:
```
✓ Generated 180 trajectory points
[3/5] Detecting Close Approaches...
Analyzing 180 time steps...
```

Instead of:
```
⚠ Propagation error at ...: code 2
✓ Generated 0 trajectory points
```

## 💡 Understanding SGP4 Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1-2 | Invalid orbital elements (eccentricity or semi-major axis) |
| 3 | Mean motion < 0 |
| 4 | Eccentricity out of range |
| 5 | Semi-latus rectum < 0 |
| 6 | Sub-orbital elements |

**Error 2** typically means:
- TLE data is expired (>30 days old)
- Satellite has decayed/re-entered
- TLE format is corrupted
- Satellite has unusual orbit (hyperbolic, etc.)

## ✅ What I Fixed

1. **Deprecation Warning**: Changed `datetime.utcnow()` to `datetime.now(timezone.utc)`
2. **Error Handling**: Limited error messages to first 5, then summary
3. **Better Messages**: Added human-readable error descriptions
4. **Warnings**: Added helpful suggestions when all propagations fail

---

**Try downloading fresh TLE data - that usually fixes it!** 🚀
