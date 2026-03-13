# Daily Debris Database Update Setup

This guide explains how to set up automatic daily updates for the debris database.

## Prerequisites

1. **Space-Track.org Account**
   - Register at https://www.space-track.org/auth/createAccount
   - Free account with rate limits (20 queries per minute, 200 per hour)

2. **Environment Variables**
   - Set `SPACETRACK_USERNAME` to your Space-Track username
   - Set `SPACETRACK_PASSWORD` to your Space-Track password

## Setting Environment Variables (Windows)

1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables" or "System variables", click "New"
5. Add:
   - Variable name: `SPACETRACK_USERNAME`
   - Variable value: `your_username`
6. Click "New" again and add:
   - Variable name: `SPACETRACK_PASSWORD`
   - Variable value: `your_password`
7. Click OK to save

## Setup Automatic Daily Updates

### Option 1: Using Task Scheduler (Recommended)

1. **Right-click** `setup_daily_update.bat` and select **"Run as administrator"**
2. The script will create a scheduled task that runs daily at 3:00 AM
3. Done! The debris database will update automatically every day

### Option 2: Manual Setup

1. Open Task Scheduler (`taskschd.msc`)
2. Click "Create Basic Task"
3. Name: `AstroCleanAI Daily Debris Update`
4. Trigger: Daily at 3:00 AM
5. Action: Start a program
6. Program: `C:\path\to\AstroCleanAI\update_debris_daily.bat`
7. Finish

## Manual Update

To update the debris database manually at any time:

```bash
# Run the update script
update_debris_daily.bat

# Or run Python directly
.\spaceenv\Scripts\python.exe populate_db.py
```

## Verify Updates

Check the database update status:

```bash
# Check debris count
.\spaceenv\Scripts\python.exe -c "from database.db_manager import get_db_manager; from database.models import DebrisObject; db = get_db_manager(); session = db.get_session(); print(f'Total debris: {session.query(DebrisObject).count()}'); session.close()"
```

## Update Schedule

- **Frequency**: Daily at 3:00 AM
- **Duration**: 5-15 minutes (depending on network speed)
- **Data Source**: Space-Track.org
- **Rate Limits**: Respects Space-Track API limits

## Troubleshooting

### Task Not Running

1. Open Task Scheduler
2. Find "AstroCleanAI Daily Debris Update"
3. Check "Last Run Result" - should be 0x0 (success)
4. Check "Last Run Time"

### Authentication Errors

- Verify environment variables are set correctly
- Check Space-Track credentials at https://www.space-track.org
- Ensure account is active and not rate-limited

### Database Errors

- Check disk space (debris database can grow to 100+ MB)
- Verify database file permissions
- Check `astrocleanai.db` is not locked by another process

## Logs

The update script outputs to console. To save logs:

```bash
update_debris_daily.bat > logs\debris_update_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1
```

## Disable Automatic Updates

To stop automatic updates:

1. Open Task Scheduler
2. Find "AstroCleanAI Daily Debris Update"
3. Right-click and select "Disable" or "Delete"

## Notes

- Updates run in the background (no window appears)
- First update may take longer (downloading full catalog)
- Subsequent updates are incremental (only new/changed debris)
- TLE data expires after ~7 days, so daily updates are recommended
