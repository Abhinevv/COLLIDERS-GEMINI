# Satellite Database Curation Plan

## Current Status
- **Total Satellites**: 928
- **Performance Impact**: Slow collision analysis due to large dataset
- **Issue**: 614 generic "SATELLITE" entries (mostly Starlink constellation)

## Curation Strategy

### Satellites to Keep: 74 High-Priority Assets

#### Space Stations (3) - HIGHEST PRIORITY
- ISS (ZARYA)
- Tiangong Space Station
- Tiangong-2

#### Navigation Satellites (16)
- GPS constellation (multiple satellites)
- Critical infrastructure for global positioning

#### Weather Satellites (12)
- NOAA series (17, 18, 19, 20)
- GOES (16, 18)
- METOP (A, B, C)
- Fengyun (3A, 3B, 3D)

#### Earth Observation (10)
- Landsat 8, 9
- Sentinel 1A, 2A, 3A
- WorldView 1, 2, 3
- Aqua, Terra

#### Science & Telescopes (11)
- Hubble Space Telescope (HST)
- Chandra X-ray Observatory
- Fermi Gamma-ray Space Telescope
- Historic satellites (Vanguard, Explorer, TIROS)

#### Communication (6)
- Major GEO satellites (Intelsat, SES, Eutelsat, Astra)

#### Representative Constellations (9)
- Starlink: 6 representative satellites (not all 600+)
- Kuiper: 3 representative satellites

#### Other Notable (7)
- Military/reconnaissance satellites
- Test spacecraft
- Dragon capsule

### Satellites to Remove: 854

- **614 generic SATELLITE entries** - Mostly Starlink duplicates
- **211 Communication satellites** - Excess Starlink/constellation satellites
- **29 Satellite entries** - Excess Kuiper and other duplicates

## Benefits

### Performance Improvements
- **92% reduction** in satellite count (928 → 74)
- **Faster collision analysis** - fewer satellite-debris pairs to check
- **Better UX** - quicker response times
- **Lower computational cost** - Monte Carlo simulations scale with satellite count

### Better User Experience
- Curated list of important satellites
- Focus on high-value assets
- Easier to navigate and select satellites
- More meaningful collision alerts

### Maintained Coverage
- All orbital regimes covered (LEO, MEO, GEO)
- All satellite types represented
- Critical infrastructure protected
- Scientific missions included

## Execution Steps

### 1. Dry Run (Already Done)
```bash
python curate_satellites.py
```
Shows what will be changed without modifying database.

### 2. Backup Database
Automatic backup created before execution:
```
data/astrocleanai_backup_YYYYMMDD_HHMMSS.db
```

### 3. Execute Curation
```bash
python curate_satellites.py --execute
```

### 4. Verify Results
- Check satellite count: should be ~74
- Test collision analysis: should be much faster
- Verify all priority satellites present

## Future Enhancements

### User-Managed Satellites
Allow users to:
- Add custom satellites by NORAD ID
- Create personal watchlists
- Subscribe to specific satellite alerts

### Dynamic Priority
- Auto-prioritize satellites with recent close approaches
- Highlight satellites in crowded orbital regions
- Flag satellites with degrading orbits

### Constellation Representatives
- Keep 1-2 satellites per constellation for analysis
- Show constellation-wide statistics
- Allow users to expand to full constellation if needed

## Rollback Plan

If issues occur:
1. Stop the application
2. Restore from backup:
   ```bash
   copy data\astrocleanai_backup_YYYYMMDD_HHMMSS.db data\astrocleanai.db
   ```
3. Restart application

## Next Steps

1. ✅ Review curation plan
2. ⏳ Execute curation with `--execute` flag
3. ⏳ Test collision analysis performance
4. ⏳ Update frontend to show curated satellite list
5. ⏳ Add "Add Custom Satellite" feature for users
