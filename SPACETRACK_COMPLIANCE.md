# Space-Track.org API Compliance Plan

## Issue
Account suspended for violating API usage policy:
- Accessing same GP ephemerides more than once per hour
- Fetching individual TLEs instead of bulk queries

## Space-Track Requirements
1. **Fetch all TLEs maximum once per hour**
2. **Use bulk query** instead of individual requests
3. **Time queries 10-20 min off busy periods** (e.g., 09:19, 09:38 - NOT 09:00, 09:30)
4. **Use recommended bulk query:**
   ```
   https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/CREATION_DATE/>now-0.042/format/tle
   ```

## Solution Implementation

### 1. Local TLE Cache
- Cache all TLE data locally in `data/tle_cache/`
- Refresh cache maximum once per hour
- Use cached data for all analyses

### 2. Bulk Fetch Strategy
- Fetch ALL active objects in one query (not individual)
- Store with timestamp
- Check cache age before any Space-Track request

### 3. Rate Limiting
- Enforce 1-hour minimum between Space-Track queries
- Log all API calls with timestamps
- Reject requests if cache is fresh

### 4. Scheduled Updates
- Run bulk update at off-peak times (e.g., 3:17 AM, 3:47 AM)
- Never query during busy periods (top/bottom of hour)

## Response to Space-Track Team

**Subject:** Acknowledgement and Mitigation Plan - Account Reinstatement Request

Dear Space-Track.org Team,

I acknowledge the violation of your API usage policy and apologize for the excessive individual TLE queries. I have immediately disabled all automatic scripts.

**Mitigation Plan:**

1. **Bulk Query Implementation**
   - Will use only the recommended bulk query:
     `https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/CREATION_DATE/>now-0.042/format/tle`
   - Fetches all active objects in single request

2. **Query Schedule**
   - Maximum once per hour
   - Scheduled at off-peak times: 3:17 AM and 3:47 PM local time
   - Never during busy periods (XX:00 or XX:30)

3. **Local Caching**
   - All TLE data cached locally for 1 hour minimum
   - Application uses cached data exclusively
   - No individual object queries

4. **Rate Limiting**
   - Enforced 1-hour minimum between any Space-Track requests
   - Timestamp logging for all API calls
   - Automatic rejection of requests if cache is fresh

**Timeline:**
- Immediate: All scripts disabled
- Day 1: Implement caching and rate limiting
- Day 2: Test with manual queries only
- Day 3+: Enable scheduled bulk updates at off-peak times

I understand the importance of responsible API usage and will ensure full compliance going forward.

Thank you for your consideration.

Best regards,
[Your Name]

---

## Current Status
⚠️ **ACCOUNT SUSPENDED** - Awaiting reinstatement
🔧 **SCRIPTS DISABLED** - No automatic queries
📝 **PLAN SUBMITTED** - Awaiting approval

## Next Steps
1. Email response to Space-Track team
2. Wait for account reinstatement
3. Implement caching system
4. Test with manual queries only
5. Enable scheduled updates after verification
