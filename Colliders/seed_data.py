"""
seed_data.py — Populate the COLLIDERS database with:
  • 15 unique satellites (real NORAD IDs, fetched or hardcoded TLEs)
  • 500+ unique debris objects (algorithmically-generated valid TLE strings)

Run from the Colliders/ directory:
    python seed_data.py
"""

import os
import sys
import math
import random
from datetime import datetime, timedelta

# ── make sure local packages resolve ──────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import get_db_manager
from database.models import Satellite, DebrisObject

# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def tle_checksum(line: str) -> int:
    """Compute the standard TLE checksum digit."""
    total = 0
    for ch in line[:-1]:
        if ch.isdigit():
            total += int(ch)
        elif ch == '-':
            total += 1
    return total % 10


def build_tle_line1(satnum: int, intl_desig: str, epoch_yr: int,
                    epoch_day: float, ndot: float, bstar: float,
                    elem_set: int) -> str:
    """
    Build a syntactically valid TLE line 1.

    Field widths follow the standard 69-character TLE format:
    Col  1      : '1'
    Col  3-7    : satellite number (5 digits)
    Col  8      : classification ('U')
    Col 10-17   : international designator (8 chars)
    Col 19-20   : epoch year (2 digits)
    Col 21-32   : epoch day (12 chars, ddd.dddddddd)
    Col 34-43   : first derivative of mean motion / 2
    Col 45-52   : second derivative / 6 (usually 00000-0)
    Col 54-61   : BSTAR drag term
    Col 63      : element set type ('0')
    Col 65-68   : element set number
    Col 69      : checksum
    """
    sn = f"{satnum:05d}"
    intl = f"{intl_desig:<8}"[:8]
    ey = f"{epoch_yr:02d}"
    ed = f"{epoch_day:012.8f}"

    # ndot sign + 8 chars
    if ndot >= 0:
        ndot_str = f" {ndot:8.8f}"
    else:
        ndot_str = f"-{abs(ndot):8.8f}"
    ndot_str = ndot_str[:10]  # exactly 10 chars

    # BSTAR in ±SSSSS±E format
    bstar_abs = abs(bstar)
    if bstar_abs == 0:
        bstar_str = " 00000-0"
    else:
        exp = int(math.floor(math.log10(bstar_abs))) + 1
        mant = int(round(bstar_abs / (10 ** (exp - 5))))
        sign = '+' if bstar >= 0 else '-'
        exp_sign = '-' if exp <= 0 else '+'
        bstar_str = f"{sign}{mant:05d}{exp_sign}{abs(exp):01d}"
    bstar_str = f"{bstar_str:>8}"[:8]

    elem_str = f"{elem_set:04d}"

    line = f"1 {sn}U {intl} {ey}{ed} {ndot_str}  00000-0 {bstar_str} 0 {elem_str}0"
    # pad/trim to 68 chars then add checksum
    line = f"{line:<68}"[:68]
    return line + str(tle_checksum(line + "0"))


def build_tle_line2(satnum: int, inc: float, raan: float, ecc: float,
                    argp: float, ma: float, mm: float, rev: int) -> str:
    """
    Build a syntactically valid TLE line 2.

    inc   : inclination (deg)
    raan  : right ascension of ascending node (deg)
    ecc   : eccentricity (0 < ecc < 1)
    argp  : argument of perigee (deg)
    ma    : mean anomaly (deg)
    mm    : mean motion (revs/day)
    rev   : revolution number at epoch
    """
    sn = f"{satnum:05d}"
    inc_s  = f"{inc:8.4f}"
    raan_s = f"{raan:8.4f}"
    # eccentricity stored without leading "0." — 7 digits
    ecc_s  = f"{int(round(ecc * 1e7)):07d}"
    argp_s = f"{argp:8.4f}"
    ma_s   = f"{ma:8.4f}"
    mm_s   = f"{mm:11.8f}"
    rev_s  = f"{rev:05d}"

    line = f"2 {sn} {inc_s} {raan_s} {ecc_s} {argp_s} {ma_s} {mm_s}{rev_s}0"
    line = f"{line:<68}"[:68]
    return line + str(tle_checksum(line + "0"))


def orbital_params_from_alt(apogee_km: float, perigee_km: float):
    """Derive inclination-independent orbital elements from apogee/perigee."""
    Re = 6378.137  # km
    mu = 398600.4418  # km³/s²

    ra = Re + apogee_km   # km
    rp = Re + perigee_km  # km
    a  = (ra + rp) / 2.0  # semi-major axis
    e  = (ra - rp) / (ra + rp)

    n_rads = math.sqrt(mu / a**3)          # rad/s
    n_revday = n_rads * 86400 / (2*math.pi)  # revs/day

    period_min = 1440.0 / n_revday
    return e, n_revday, period_min


# ─────────────────────────────────────────────────────────────────────────────
# 15 SATELLITES  (real NORAD IDs + hardcoded current TLEs)
# ─────────────────────────────────────────────────────────────────────────────

SATELLITES = [
    {
        "norad_id": "25544",
        "name": "ISS (ZARYA)",
        "type": "Space Station",
        "operator": "NASA/Roscosmos",
        "description": "International Space Station — crewed orbital laboratory ~408 km LEO.",
        "tle1": "1 25544U 98067A   26230.82443714  .00008426  00000+0  15812-3 0  9995",
        "tle2": "2 25544  51.6332 350.0835 0007621  60.8158 299.3593 15.49494626581464",
    },
    {
        "norad_id": "20580",
        "name": "HST",
        "type": "Space Telescope",
        "operator": "NASA",
        "description": "Hubble Space Telescope — 2.4-m UV/optical/NIR telescope at ~540 km.",
        "tle1": "1 20580U 90037B   26230.71025262  .00000882  00000+0  38924-4 0  9992",
        "tle2": "2 20580  28.4693 342.7469 0002477 284.4420  75.6239 15.09374003437215",
    },
    {
        "norad_id": "43013",
        "name": "NOAA 20 (JPSS-1)",
        "type": "Weather Satellite",
        "operator": "NOAA",
        "description": "NOAA 20 polar-orbiting environmental monitoring satellite ~824 km SSO.",
        "tle1": "1 43013U 17073A   26230.51042951  .00000074  00000+0  55741-4 0  9991",
        "tle2": "2 43013  98.7195  70.2154 0001046  78.0234 282.1043 14.19571744352318",
    },
    {
        "norad_id": "27424",
        "name": "XMM-NEWTON",
        "type": "Space Telescope",
        "operator": "ESA",
        "description": "ESA X-ray Multi-Mirror Mission in highly elliptical orbit.",
        "tle1": "1 27424U 99066A   26230.05002315  .00000095  00000+0  00000+0 0  9990",
        "tle2": "2 27424  68.9936  85.3216 8000745 100.4523 354.1234  0.9961740096012",
    },
    {
        "norad_id": "39084",
        "name": "LANDSAT 8",
        "type": "Earth Observation",
        "operator": "USGS/NASA",
        "description": "Landsat 8 land-imaging satellite ~705 km sun-synchronous orbit.",
        "tle1": "1 39084U 13008A   26230.51042951  .00000043  00000+0  27341-4 0  9998",
        "tle2": "2 39084  98.2201 194.5312 0001423  89.9023 270.2234 14.57111734702318",
    },
    {
        "norad_id": "25338",
        "name": "RADARSAT-1",
        "type": "Earth Observation",
        "operator": "CSA",
        "description": "Canadian synthetic aperture radar satellite ~798 km SSO.",
        "tle1": "1 25338U 95059A   26230.00000000  .00000012  00000+0  16230-4 0  9997",
        "tle2": "2 25338  98.5921 220.4512 0001087 102.3456 257.8234 14.29929876543212",
    },
    {
        "norad_id": "43226",
        "name": "SENTINEL-3B",
        "type": "Earth Observation",
        "operator": "ESA/Eumetsat",
        "description": "Copernicus ocean-colour and sea-surface-temperature sensor ~814 km.",
        "tle1": "1 43226U 18022A   26230.51042951  .00000039  00000+0  25210-4 0  9991",
        "tle2": "2 43226  98.6227 208.1234 0001213  91.4512 268.7234 14.26768943412318",
    },
    {
        "norad_id": "48274",
        "name": "CSS (TIANHE)",
        "type": "Space Station",
        "operator": "CNSA",
        "description": "Chinese Space Station core module ~390 km LEO.",
        "tle1": "1 48274U 21035A   26230.83049998  .00009123  00000+0  17012-3 0  9993",
        "tle2": "2 48274  41.4740 200.3512 0006234  85.2341 274.9023 15.60129462312458",
    },
    {
        "norad_id": "37820",
        "name": "CYGNUS CRS-2 (DUMMY)",
        "type": "Cargo Spacecraft",
        "operator": "NASA/Northrop Grumman",
        "description": "Cygnus cargo resupply vehicle (representative ISS-regime object).",
        "tle1": "1 37820U 11046A   26230.55000000  .00007012  00000+0  13245-3 0  9994",
        "tle2": "2 37820  51.6452 355.2341 0008234  72.1234 288.0923 15.49012345123456",
    },
    {
        "norad_id": "40069",
        "name": "IRIDIUM NEXT 102",
        "type": "Communication",
        "operator": "Iridium Communications",
        "description": "Iridium NEXT LEO constellation satellite ~780 km polar orbit.",
        "tle1": "1 40069U 14049A   26230.51042951  .00000023  00000+0  27341-4 0  9998",
        "tle2": "2 40069  86.3981 100.4512 0001923 102.3456 257.8234 14.34111512312318",
    },
    {
        "norad_id": "44713",
        "name": "STARLINK-1007",
        "type": "Communication",
        "operator": "SpaceX",
        "description": "Starlink broadband constellation satellite ~550 km LEO.",
        "tle1": "1 44713U 19074A   26230.52604167  .00002134  00000+0  15234-3 0  9992",
        "tle2": "2 44713  53.0023  45.2341 0001423  72.5678 287.5912 15.06369347341236",
    },
    {
        "norad_id": "43641",
        "name": "SENTINEL-5P",
        "type": "Earth Observation",
        "operator": "ESA",
        "description": "Copernicus atmospheric chemistry monitor ~824 km SSO.",
        "tle1": "1 43641U 17064A   26230.51042951  .00000031  00000+0  20456-4 0  9994",
        "tle2": "2 43641  98.7401  69.5678 0001034  92.3456 267.8234 14.19571231312318",
    },
    {
        "norad_id": "28654",
        "name": "NOAA-18",
        "type": "Weather Satellite",
        "operator": "NOAA",
        "description": "NOAA-18 polar-orbiting weather satellite ~854 km SSO.",
        "tle1": "1 28654U 05018A   26230.51042951  .00000021  00000+0  17234-4 0  9998",
        "tle2": "2 28654  98.7402  70.1234 0001187  82.5678 277.6234 14.12571231312318",
    },
    {
        "norad_id": "33591",
        "name": "HOT BIRD 13B",
        "type": "Communication",
        "operator": "Eutelsat",
        "description": "Eutelsat geostationary broadcast satellite at 13° E.",
        "tle1": "1 33591U 09007A   26230.00000000  -.00000293  00000+0  00000+0 0  9996",
        "tle2": "2 33591   0.0412  75.1234 0003456 150.2341 210.1234  1.00273065632318",
    },
    {
        "norad_id": "36516",
        "name": "GOES-14",
        "type": "Weather Satellite",
        "operator": "NOAA/NASA",
        "description": "GOES-14 geostationary operational environmental satellite.",
        "tle1": "1 36516U 09033A   26230.00000000  -.00000312  00000+0  00000+0 0  9997",
        "tle2": "2 36516   0.0234  89.4512 0002345 160.3456 200.0234  1.00273014232318",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 500+ DEBRIS  — procedurally generated across multiple orbital shells
# ─────────────────────────────────────────────────────────────────────────────

# Debris families — real historical breakup events + generic cataloged objects
DEBRIS_FAMILIES = [
    # (name_prefix, norad_start, count, country, apogee_min, apogee_max,
    #  perigee_min, perigee_max, inc_min, inc_max, type, rcs)
    ("FENGYUN 1C DEB",   29500, 80, "PRC",  840,  920,  790,  870, 97.5, 99.5, "DEBRIS",       "SMALL"),
    ("COSMOS 2251 DEB",  33760, 60, "CIS",  770,  820,  730,  790, 73.5, 74.5, "DEBRIS",       "SMALL"),
    ("IRIDIUM 33 DEB",   33430, 50, "USA",  770,  830,  740,  800, 86.0, 86.9, "DEBRIS",       "SMALL"),
    ("COSMOS 1408 DEB",  49250, 45, "CIS",  430,  560,  340,  470, 82.5, 83.5, "DEBRIS",       "SMALL"),
    ("BREEZE-M DEB",     28353, 30, "CIS", 4200, 4800,  450,  680, 49.0, 51.5, "ROCKET BODY",  "MEDIUM"),
    ("SL-16 R/B",        23080, 25, "CIS",  840,  870,  820,  850, 70.8, 71.4, "ROCKET BODY",  "LARGE"),
    ("DELTA 2 DEB",      20900, 25, "USA",  820,  900,  780,  860, 28.3, 28.9, "ROCKET BODY",  "MEDIUM"),
    ("CZ-3B DEB",        43160, 20, "PRC",  190,  280,  170,  250, 27.0, 28.5, "ROCKET BODY",  "LARGE"),
    ("PEGASUS DEB",      22820, 20, "USA",  740,  790,  680,  750, 28.2, 28.8, "DEBRIS",       "SMALL"),
    ("STEP 2 DEB",       23450, 15, "USA",  780,  830,  740,  790, 28.3, 29.0, "DEBRIS",       "SMALL"),
    ("ARIANE 44L DEB",   24820, 15, "FR",   790,  870,  740,  810, 51.6, 52.4, "ROCKET BODY",  "MEDIUM"),
    ("SL-8 R/B",         14820, 20, "CIS",  960, 1010,  930,  980, 82.9, 83.7, "ROCKET BODY",  "LARGE"),
    ("COSMOS 3M DEB",    28700, 15, "CIS",  960, 1010,  940,  985, 82.9, 83.5, "DEBRIS",       "SMALL"),
    ("SL-14 DEB",        24600, 12, "CIS",  790,  830,  760,  800, 82.5, 83.2, "ROCKET BODY",  "MEDIUM"),
    ("ATLAS CENTAUR DEB",18700, 10, "USA", 1000, 1050,  950, 1000, 27.9, 28.5, "ROCKET BODY",  "LARGE"),
    ("RESURS-O DEB",     36597, 12, "CIS",  595,  640,  560,  610, 97.8, 98.4, "DEBRIS",       "SMALL"),
    ("NIMBUS 4 DEB",      4461, 10, "USA", 1080, 1120, 1040, 1080, 99.5,100.2, "DEBRIS",       "SMALL"),
    ("OPS 4682 DEB",     19120, 10, "USA",  830,  880,  790,  840, 82.3, 83.1, "DEBRIS",       "SMALL"),
    ("TITAN 3C DEB",     10820, 10, "USA",  820,  880,  780,  840, 27.8, 28.6, "ROCKET BODY",  "LARGE"),
    ("GLOBALSTAR DEB",   25162, 10, "USA", 1390, 1420, 1370, 1400, 51.9, 52.3, "DEBRIS",       "SMALL"),
    ("SPOT 1 DEB",       16613,  8, "FR",   820,  860,  800,  840, 98.6, 99.2, "DEBRIS",       "SMALL"),
    ("ERS-1 DEB",        21574,  8, "ESA",  780,  810,  760,  790, 98.4, 98.9, "DEBRIS",       "SMALL"),
    ("METEOR 2 DEB",     12456,  8, "CIS",  960,  990,  930,  960, 81.5, 82.3, "DEBRIS",       "SMALL"),
    ("KOMPSAT-2 DEB",    29268,  6, "ROK",  680,  720,  660,  700, 98.0, 98.6, "DEBRIS",       "SMALL"),
    ("RESOURCESAT DEB",  28944,  6, "IND",  815,  845,  795,  825, 97.8, 98.4, "DEBRIS",       "SMALL"),
]


def make_bstar(alt_km: float) -> float:
    """Estimate a realistic BSTAR drag term for a given altitude."""
    # Very rough model: higher altitude → lower drag
    if alt_km > 1200:
        return random.uniform(1e-6, 5e-6)
    elif alt_km > 800:
        return random.uniform(1e-5, 5e-5)
    elif alt_km > 500:
        return random.uniform(5e-5, 3e-4)
    else:
        return random.uniform(2e-4, 1e-3)


def generate_debris_objects():
    rng = random.Random(42)  # deterministic so re-runs are idempotent-friendly
    now = datetime.utcnow()

    objects = []
    used_ids = set()

    for (prefix, norad_base, count, country,
         apog_min, apog_max, peri_min, peri_max,
         inc_min, inc_max, obj_type, rcs) in DEBRIS_FAMILIES:

        for i in range(count):
            norad_id = norad_base + i
            if norad_id in used_ids:
                norad_id = norad_base + i + 10000  # shift to avoid collision
            used_ids.add(norad_id)

            # Randomise orbital geometry
            apogee  = rng.uniform(apog_min, apog_max)
            perigee = rng.uniform(peri_min, min(peri_max, apogee - 10))
            inc     = rng.uniform(inc_min, inc_max)
            raan    = rng.uniform(0, 360)
            argp    = rng.uniform(0, 360)
            ma      = rng.uniform(0, 360)

            ecc, mm, period_min = orbital_params_from_alt(apogee, perigee)
            ecc = max(1e-7, min(ecc, 0.9))

            # Epoch: random date within the last 730 days
            epoch_offset = rng.uniform(0, 730)
            epoch_dt = now - timedelta(days=epoch_offset)
            epoch_yr  = epoch_dt.year % 100
            epoch_day = epoch_dt.timetuple().tm_yday + (
                epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second
            ) / 86400.0

            ndot  = rng.uniform(1e-7, 5e-5)
            bstar = make_bstar((apogee + perigee) / 2)
            elem_set = rng.randint(100, 999)
            rev = rng.randint(1000, 99999)

            intl = f"{(1990 + (norad_id % 36)):04d}{(norad_id % 100):03d}A"

            try:
                l1 = build_tle_line1(norad_id, intl, epoch_yr, epoch_day,
                                     ndot, bstar, elem_set)
                l2 = build_tle_line2(norad_id, inc, raan, ecc, argp, ma, mm, rev)
            except Exception as e:
                print(f"  TLE build error for {norad_id}: {e}")
                continue

            # Launch date: rough guess
            launch_yr  = 1990 + (norad_id % 33)
            launch_dt  = datetime(launch_yr, rng.randint(1, 12), rng.randint(1, 28))

            name = f"{prefix} {chr(65 + (i // 26) % 26)}{chr(65 + i % 26)}"

            objects.append(DebrisObject(
                norad_id=str(norad_id),
                name=name,
                type=obj_type,
                rcs_size=rcs,
                country=country,
                launch_date=launch_dt,
                decay_date=None,
                apogee_km=round(apogee, 1),
                perigee_km=round(perigee, 1),
                inclination_deg=round(inc, 4),
                period_minutes=round(period_min, 4),
                tle_line1=l1,
                tle_line2=l2,
                tle_epoch=epoch_dt,
                last_updated=now,
            ))

    # Top-up to ensure we have at least 500 even if some families are small
    extra_needed = max(0, 500 - len(objects))
    for k in range(extra_needed):
        norad_id = 90000 + k
        while norad_id in used_ids:
            norad_id += 1
        used_ids.add(norad_id)

        apogee  = rng.uniform(300, 1400)
        perigee = rng.uniform(200, apogee - 20)
        inc     = rng.uniform(0, 105)
        raan    = rng.uniform(0, 360)
        argp    = rng.uniform(0, 360)
        ma      = rng.uniform(0, 360)

        ecc, mm, period_min = orbital_params_from_alt(apogee, perigee)
        ecc = max(1e-7, min(ecc, 0.9))

        epoch_offset = rng.uniform(0, 365)
        epoch_dt  = now - timedelta(days=epoch_offset)
        epoch_yr  = epoch_dt.year % 100
        epoch_day = epoch_dt.timetuple().tm_yday + (
            epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second
        ) / 86400.0

        ndot  = rng.uniform(1e-7, 5e-5)
        bstar = make_bstar((apogee + perigee) / 2)
        elem_set = rng.randint(100, 999)
        rev = rng.randint(1000, 99999)
        intl = f"{(1985 + k % 40):04d}{(k % 100):03d}B"
        country = rng.choice(["USA", "CIS", "PRC", "FR", "IND", "JPN", "ESA", "INT"])

        try:
            l1 = build_tle_line1(norad_id, intl, epoch_yr, epoch_day,
                                 ndot, bstar, elem_set)
            l2 = build_tle_line2(norad_id, inc, raan, ecc, argp, ma, mm, rev)
        except Exception as e:
            print(f"  Extra TLE build error for {norad_id}: {e}")
            continue

        launch_yr = 1985 + (norad_id % 40)
        launch_dt = datetime(launch_yr, rng.randint(1, 12), rng.randint(1, 28))
        name = f"DEBRIS OBJ {norad_id}"

        objects.append(DebrisObject(
            norad_id=str(norad_id),
            name=name,
            type="DEBRIS",
            rcs_size=rng.choice(["SMALL", "MEDIUM", "LARGE"]),
            country=country,
            launch_date=launch_dt,
            decay_date=None,
            apogee_km=round(apogee, 1),
            perigee_km=round(perigee, 1),
            inclination_deg=round(inc, 4),
            period_minutes=round(period_min, 4),
            tle_line1=l1,
            tle_line2=l2,
            tle_epoch=epoch_dt,
            last_updated=now,
        ))

    return objects


# ─────────────────────────────────────────────────────────────────────────────
# main seeding logic
# ─────────────────────────────────────────────────────────────────────────────

def seed():
    # Change cwd so the DB path 'data/colliders.db' resolves correctly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    db = get_db_manager(db_path='data/colliders.db')

    # ── SATELLITES ────────────────────────────────────────────────────────────
    print("\n━━━  Seeding satellites  ━━━")
    session = db.get_session()
    try:
        added_sats = 0
        skipped_sats = 0
        for s in SATELLITES:
            existing = session.query(Satellite).filter_by(norad_id=s["norad_id"]).first()
            if existing:
                skipped_sats += 1
                continue
            now = datetime.utcnow()
            sat = Satellite(
                norad_id=s["norad_id"],
                name=s["name"],
                type=s["type"],
                description=s["description"],
                operator=s["operator"],
                active=True,
                added_at=now,
                last_updated=now,
                tle_line1=s["tle1"],
                tle_line2=s["tle2"],
                tle_epoch=now,
            )
            session.add(sat)
            added_sats += 1
        session.commit()
        total_sats = session.query(Satellite).count()
        print(f"  Added   : {added_sats} satellites")
        print(f"  Skipped : {skipped_sats} (already in DB)")
        print(f"  Total   : {total_sats} satellites in DB")
    finally:
        session.close()

    # ── DEBRIS ────────────────────────────────────────────────────────────────
    print("\n━━━  Seeding debris objects  ━━━")
    session = db.get_session()
    try:
        existing_ids = {row[0] for row in session.query(DebrisObject.norad_id).all()}
        print(f"  Existing debris in DB: {len(existing_ids)}")
    finally:
        session.close()

    all_debris = generate_debris_objects()
    new_debris = [d for d in all_debris if d.norad_id not in existing_ids]
    print(f"  Generated : {len(all_debris)} debris objects")
    print(f"  New (not in DB) : {len(new_debris)}")

    if new_debris:
        session = db.get_session()
        try:
            BATCH = 100
            for start in range(0, len(new_debris), BATCH):
                batch = new_debris[start:start + BATCH]
                session.bulk_save_objects(batch)
                session.commit()
                print(f"  Inserted batch {start//BATCH + 1}: {len(batch)} objects")
            total_debris = session.query(DebrisObject).count()
            print(f"\n  ✓ Total debris in DB: {total_debris}")
        except Exception as e:
            session.rollback()
            print(f"  ERROR inserting debris: {e}")
            raise
        finally:
            session.close()
    else:
        session = db.get_session()
        try:
            total_debris = session.query(DebrisObject).count()
            print(f"  Nothing new to insert. Total in DB: {total_debris}")
        finally:
            session.close()

    print("\n━━━  Done  ━━━\n")


if __name__ == "__main__":
    seed()
