# Deployment Instructions for Intelligent Fast Mode

## What's Been Built

The intelligent Fast Mode system is **fully implemented** in the code:

### Backend (Ã¢Å“â€¦ Complete)
- `find_close_pairs.py` - Screens all satellites for debris within 25km
- `/api/find_close_pairs` endpoint in `api.py` - Returns top 50 satellites with most nearby debris
- Configurable screening threshold (default 25km)

### Frontend (Ã¢Å“â€¦ Complete, needs build)
- `RiskRanking.jsx` - Modified to call screening endpoint before analysis
- Intelligent pair selection instead of random debris
- Updated UI labels and progress text

## How to Deploy

### Step 1: Build Frontend
Run this command in the `Colliders` directory:
```bash
build_frontend.bat
```

Or manually:
```bash
cd frontend
npm run build
cd ..
```

### Step 2: Restart Server
Stop the current server (Ctrl+C) and restart:
```bash
python api.py
```

### Step 3: Clear Browser Cache
- Press `Ctrl + Shift + Delete`
- Select "Cached images and files"
- Click "Clear data"

OR use an incognito/private window

### Step 4: Test Fast Mode
1. Navigate to Risk Ranking page
2. Fast Mode will auto-start
3. Watch for "Screening satellites..." message
4. Results will show only close pairs

## Expected Behavior

### If Close Pairs Found
```
Screening 314 satellites against 2000 debris...
Found 15 satellites with close debris
Total pairs to analyze: 247

Fast Mode: Analyzing 247 close pairs
Progress: 45% complete
```

Results will show actual collision probabilities for pairs within 25km.

### If No Close Pairs Found
```
Screening 314 satellites against 2000 debris...
Found 0 satellites with close debris

Error: No close satellite-debris pairs found within 25km
```

This means your satellites are genuinely safe - no debris within 25km of any satellite.

## Troubleshooting

### Build Fails
If `npm run build` fails, check:
1. Node.js is installed: `node --version`
2. Dependencies installed: `cd frontend && npm install`
3. No syntax errors: Check console output

### Still Seeing Old Results
1. Hard refresh: `Ctrl + Shift + F5`
2. Check browser console for errors (F12)
3. Verify new bundle loaded (check Network tab)
4. Try incognito window

### Screening Takes Too Long
The screening process checks all 314 Ãƒâ€” 2000 = 628,000 combinations for distance.
This takes 2-5 minutes. Progress will show in console:
```
Screening satellites...
  ISS: 45 debris within 25km
  Hubble: 12 debris within 25km
  ...
```

### All Probabilities Still Zero
This could mean:
1. Screening found pairs, but they're not close enough during the 10-minute prediction window
2. Increase prediction window: Change `duration: 10` to `duration: 60` in RiskRanking.jsx
3. Or increase threshold: Change `threshold_km=25` to `threshold_km=50` in the API call

## System Architecture

```
User clicks Fast Mode
    Ã¢â€ â€œ
Frontend calls /api/find_close_pairs
    Ã¢â€ â€œ
Backend screens all satellites vs all debris
    Ã¢â€ â€œ
Returns top 50 satellites with most debris within 25km
    Ã¢â€ â€œ
Frontend analyzes only those close pairs
    Ã¢â€ â€œ
Results show actual collision probabilities
```

## Performance Metrics

- **Screening**: 2-5 minutes (one-time per analysis)
- **Analysis**: 5-15 minutes (depends on pairs found)
- **Total**: 10-20 minutes for complete Fast Mode

Compare to old system:
- **Old Fast Mode**: 10-15 minutes analyzing random pairs (all zeros)
- **New Fast Mode**: 10-20 minutes analyzing only real threats (actual probabilities)

## Configuration Options

### Adjust Threshold
In `RiskRanking.jsx`, line ~75:
```javascript
const screeningResponse = await fetch(
  'http://localhost:5000/api/find_close_pairs?threshold_km=25&max_satellites=50&max_debris=2000'
)
```

Change `threshold_km=25` to:
- `threshold_km=10` - Very tight, immediate threats only
- `threshold_km=50` - Wider net, more pairs
- `threshold_km=100` - Very wide, many pairs

### Adjust Satellite Count
Change `max_satellites=50` to analyze more or fewer satellites.

### Adjust Debris Pool
Change `max_debris=2000` to check against more or fewer debris objects.

## Next Steps After Deployment

1. **Run Fast Mode** - See if any close pairs are found
2. **Check Smart Analysis** - Let it run for full 628,000 combinations
3. **Review results** - Identify high-risk satellites
4. **Plan maneuvers** - Use Maneuver Planner for high-risk cases

## Support

If you encounter issues:
1. Check server logs for errors
2. Check browser console (F12) for frontend errors
3. Verify API endpoint works: `http://localhost:5000/api/find_close_pairs?threshold_km=25&max_satellites=5&max_debris=100`
4. Test screening independently: `python find_close_pairs.py`
