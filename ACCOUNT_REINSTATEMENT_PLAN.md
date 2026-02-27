# Space-Track Account Reinstatement Plan

## Current Status
🔴 **ACCOUNT SUSPENDED** - Violated API usage policy
⏸️ **ALL SCRIPTS DISABLED** - No automatic queries active
✅ **COMPLIANCE SYSTEM IMPLEMENTED** - Ready for testing after reinstatement

## What Happened
The system was querying individual TLE data for each debris object, violating Space-Track's policy of:
- Maximum 1 query per hour for GP ephemerides
- Must use bulk queries, not individual object requests

## Immediate Actions Taken
1. ✅ Disabled all automatic Space-Track queries
2. ✅ Implemented TLE caching system
3. ✅ Added rate limiting (1-hour minimum between queries)
4. ✅ Added off-peak time enforcement
5. ✅ Created bulk query endpoint

## Email Response to Space-Track Team

**To:** support@space-track.org
**Subject:** Acknowledgement and Mitigation Plan - Account Reinstatement Request

---

Dear Space-Track.org Team,

I acknowledge the violation of your API usage policy and sincerely apologize for the excessive individual TLE queries. I have immediately disabled all automatic scripts and implemented a comprehensive compliance system.

**What Caused the Violation:**
My application was fetching individual TLE data for each debris object during collision analysis, resulting in multiple queries per hour to the GP endpoint.

**Mitigation Plan Implemented:**

1. **Bulk Query Only**
   - Implemented the recommended bulk query:
     ```
     /basicspacedata/query/class/gp/decay_date/null-val/CREATION_DATE/>now-0.042/format/json
     ```
   - Fetches ALL active objects in a single request
   - No individual object queries

2. **Local Caching System**
   - All TLE data cached locally for minimum 1 hour
   - Application uses cached data exclusively
   - Cache automatically expires after 1 hour

3. **Rate Limiting**
   - Enforced 1-hour minimum between any Space-Track requests
   - Automatic rejection if cache is fresh
   - Timestamp logging for all API calls

4. **Off-Peak Timing**
   - Queries only allowed 10-20 minutes past the hour
   - Blocked during busy periods (XX:00-XX:05, XX:25-XX:35, XX:55-XX:59)
   - Prevents load during peak times

5. **Manual Control**
   - All queries require manual approval
   - No automatic/scheduled queries
   - Admin-only refresh endpoint

**Query Schedule (After Reinstatement):**
- **Frequency:** Maximum once per hour
- **Timing:** Off-peak only (e.g., XX:17, XX:38, XX:47)
- **Method:** Single bulk query for all objects
- **URL:** `/basicspacedata/query/class/gp/decay_date/null-val/CREATION_DATE/>now-0.042/format/json`

**Testing Plan:**
1. Day 1-2: Manual testing only, verify cache system
2. Day 3-4: Single manual refresh per day at off-peak time
3. Day 5+: Maximum 2 refreshes per day (morning/evening off-peak)

**Monitoring:**
- Daily query count tracking
- Cache age monitoring
- Rate limit enforcement logs
- Off-peak time compliance verification

I understand the importance of responsible API usage and the impact of excessive queries on your infrastructure. I have implemented multiple safeguards to ensure this violation never occurs again.

Thank you for your consideration in reinstating my account. I am committed to being a responsible member of the Space-Track community.

Best regards,
[Your Name]
[Your Email]

---

## Files Created

### 1. `tle_cache_manager.py`
- Manages local TLE cache
- Enforces 1-hour minimum between queries
- Checks off-peak timing
- Tracks daily query count

### 2. `refresh_tle_cache.py`
- Manual cache refresh script
- Checks rate limits before querying
- Uses bulk query only
- Requires user confirmation

### 3. API Endpoints
- `GET /api/tle_cache/status` - Check cache status
- `POST /api/tle_cache/refresh` - Manual refresh (admin only)

## After Account Reinstatement

### Step 1: Initial Cache Population
```bash
cd AstroCleanAI
python refresh_tle_cache.py
```

This will:
- Check if query is allowed (rate limit + timing)
- Fetch ALL active objects in one bulk query
- Save to local cache
- Display cache statistics

### Step 2: Verify Cache
```bash
python -c "from tle_cache_manager import get_cache_manager; import json; print(json.dumps(get_cache_manager().get_cache_stats(), indent=2))"
```

### Step 3: Test Application
- Start server: `start_with_spacetrack.bat`
- Use Satellite Risk Profile
- Should use cached data only
- No Space-Track queries during analysis

### Step 4: Monitor Compliance
- Check cache age before any refresh
- Only refresh during off-peak times
- Maximum once per hour
- Log all queries

## Compliance Checklist

Before ANY Space-Track query:
- [ ] Cache is older than 60 minutes
- [ ] Current time is off-peak (10-20 min past hour)
- [ ] Less than 24 queries today
- [ ] Using bulk query endpoint
- [ ] Manual approval obtained

## Long-Term Strategy

### Daily Refresh Schedule (After Proven Compliance)
- **Morning:** 3:17 AM (off-peak, low usage)
- **Evening:** 3:47 PM (off-peak, low usage)
- **Maximum:** 2 queries per day

### Cache Management
- 1-hour minimum cache lifetime
- Automatic expiration
- No automatic refresh (manual only)
- Cache statistics dashboard

## Support Contact
If you have questions about this plan, please contact:
- Email: [Your Email]
- Space-Track Username: RIDDHESHMORANKAR@GMAIL.COM

---

**Status:** ⏳ Awaiting account reinstatement
**Last Updated:** 2026-02-27
**Compliance Level:** ✅ FULL COMPLIANCE IMPLEMENTED
