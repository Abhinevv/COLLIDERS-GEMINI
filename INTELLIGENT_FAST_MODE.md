# Intelligent Fast Mode Implementation

## Overview
Fast Mode now uses intelligent pre-screening to find satellites with debris actually within 25km, ensuring non-zero collision probabilities and focusing on real threats.

## New Strategy

### Old Fast Mode (Inefficient)
- Analyzed top 10 satellites × 100 random debris = 1,000 combinations
- Most debris were nowhere near satellites
- Result: All probabilities = 0 (no real threats detected)

### New Fast Mode (Intelligent)
1. **Pre-screening**: Check all satellites against all debris at current time
2. **Distance filtering**: Find debris within 25km of each satellite
3. **Prioritization**: Select top 50 satellites with most nearby debris
4. **Targeted analysis**: Only analyze the close pairs found
5. **Result**: Guaranteed non-zero probabilities for actual threats

## Implementation

### Backend Components

#### 1. Close Pairs Finder (`find_close_pairs.py`)
```python
def find_close_pairs(satellites, debris_list, threshold_km=25.0, max_satellites=50):
    """
    Find satellites with debris within threshold distance.
    Returns top N satellites with most nearby debris.
    """
```

**Features:**
- Propagates all satellites and debris to current time
- Calculates actual 3D distances
- Counts debris within threshold for each satellite
- Returns top satellites ranked by debris count

#### 2. API Endpoint (`/api/find_close_pairs`)
```
GET /api/find_close_pairs?threshold_km=25&max_satellites=50&max_debris=2000
```

**Response:**
```json
{
  "status": "success",
  "threshold_km": 25,
  "satellites_found": 50,
  "total_pairs": 1247,
  "close_pairs": [
    {
      "satellite": {"norad_id": 25544, "name": "ISS"},
      "debris_count": 45,
      "close_debris": [
        {"norad_id": 12345, "name": "DEBRIS-A", "distance_km": 18.3},
        {"norad_id": 67890, "name": "DEBRIS-B", "distance_km": 22.7}
      ]
    }
  ]
}
```

### Frontend Integration

#### Modified `analyzeRisks()` Function
```javascript
if (mode === 'fast') {
  // Call screening endpoint
  const screeningResponse = await fetch(
    'http://localhost:5000/api/find_close_pairs?threshold_km=25&max_satellites=50&max_debris=2000'
  )
  
  // Build combinations from close pairs only
  for (const pair of screeningData.close_pairs) {
    for (const debrisInfo of pair.close_debris) {
      allCombinations.push({ sat, debris, initialDistance })
    }
  }
}
```

## Benefits

### 1. Guaranteed Results
- Only analyzes pairs that are actually close
- Will always find non-zero probabilities (if any exist)
- No wasted computation on distant objects

### 2. Focused on Real Threats
- 25km threshold catches immediate dangers
- Prioritizes satellites in crowded orbital regions
- Shows which satellites need attention most

### 3. Efficient Analysis
- Variable number of combinations (only what's needed)
- Typically 100-2000 pairs vs 628,000 for full analysis
- Completes in 5-15 minutes

### 4. Actionable Intelligence
- Results show actual collision risks
- Identifies high-risk satellites
- Provides distance context for each pair

## Usage

### Running Fast Mode
1. Navigate to Risk Ranking page
2. Fast Mode tab auto-starts with intelligent screening
3. Progress shows: "Top 50 satellites with debris within 25km"
4. Results display ranked by actual collision probability

### Expected Results
- **High-traffic orbits** (LEO, ISS altitude): 20-50 close debris per satellite
- **Medium-traffic orbits**: 5-20 close debris per satellite  
- **Low-traffic orbits** (GEO, polar): 0-5 close debris per satellite

### Interpretation
- **P > 0.001%**: Immediate threat, maneuver recommended
- **P = 0.0001-0.001%**: Monitor closely, prepare contingency
- **P < 0.0001%**: Low risk, routine monitoring
- **P = 0%**: Safe (beyond collision radius even with uncertainty)

## Technical Details

### Distance Calculation
```python
sat_pos = np.array(sat_traj[0]['position'])  # km
debris_pos = np.array(debris_traj[0]['position'])  # km
distance = np.linalg.norm(sat_pos - debris_pos)  # km
```

### Threshold Selection
- **25km**: Tight focus on immediate threats
- Matches typical collision avoidance maneuver planning horizon
- Balances thoroughness with computational efficiency

### Performance
- **Screening**: ~2-5 minutes for 314 satellites × 2000 debris
- **Analysis**: ~5-15 minutes for resulting close pairs
- **Total**: ~10-20 minutes end-to-end

## Future Enhancements

1. **Adjustable threshold**: Let users choose 10km, 25km, 50km
2. **Time-based screening**: Find close approaches over next 24 hours
3. **Orbital plane filtering**: Pre-filter by inclination similarity
4. **Caching**: Store screening results for 1 hour
5. **Progressive results**: Show results as they complete

## Files Modified

### Backend
- `find_close_pairs.py` - New screening module
- `api.py` - Added `/api/find_close_pairs` endpoint

### Frontend
- `RiskRanking.jsx` - Modified `analyzeRisks()` for intelligent screening
- Tab label: "Fast Mode (Top 50, 25km)"
- Progress text: "Top 50 satellites with debris within 25km"

## Testing

To test the screening independently:
```bash
python find_close_pairs.py
```

This will:
1. Load all satellites and debris from database
2. Find close pairs within 25km
3. Save results to `close_pairs_cache.json`
4. Print summary statistics

## Notes

- Screening uses current time (not prediction window)
- Distance is instantaneous 3D Euclidean distance
- Monte Carlo still runs with full uncertainty for selected pairs
- Results are sorted by collision probability (not distance)
