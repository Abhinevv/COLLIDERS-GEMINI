
import os
import sys
import math
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import get_db_manager
from database.models import Satellite, DebrisObject
from sgp4.api import Satrec

def tle_checksum(line: str) -> int:
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
    sn = f'{satnum:05d}'
    intl = f'{intl_desig:<8}'[:8]
    ey = f'{epoch_yr:02d}'
    ed = f'{epoch_day:012.8f}'

    if ndot >= 0:
        ndot_str = f' {ndot:8.8f}'
    else:
        ndot_str = f'-{abs(ndot):8.8f}'
    ndot_str = ndot_str[:10]

    bstar_abs = abs(bstar)
    if bstar_abs == 0:
        bstar_str = ' 00000-0'
    else:
        exp = int(math.floor(math.log10(bstar_abs))) + 1
        mant = int(round(bstar_abs / (10 ** (exp - 5))))
        sign = '+' if bstar >= 0 else '-'
        exp_sign = '-' if exp <= 0 else '+'
        bstar_str = f'{sign}{mant:05d}{exp_sign}{abs(exp):01d}'
    bstar_str = f'{bstar_str:>8}'[:8]

    elem_str = f'{elem_set:04d}'

    line = f'1 {sn}U {intl} {ey}{ed} {ndot_str}  00000-0 {bstar_str} 0 {elem_str}0'
    line = f'{line:<68}'[:68]
    return line + str(tle_checksum(line + '0'))

def build_tle_line2(satnum: int, inc: float, raan: float, ecc: float,
                    argp: float, ma: float, mm: float, rev: int) -> str:
    sn = f'{satnum:05d}'
    inc_s  = f'{inc:8.4f}'
    raan_s = f'{raan:8.4f}'
    ecc_s  = f'{int(round(ecc * 1e7)):07d}'
    argp_s = f'{argp:8.4f}'
    ma_s   = f'{ma:8.4f}'
    mm_s   = f'{mm:11.8f}'
    rev_s  = f'{rev:05d}'

    line = f'2 {sn} {inc_s} {raan_s} {ecc_s} {argp_s} {ma_s} {mm_s}{rev_s}0'
    line = f'{line:<68}'[:68]
    return line + str(tle_checksum(line + '0'))

def orbital_params_from_alt(apogee_km: float, perigee_km: float):
    Re = 6378.137
    mu = 398600.4418
    ra = Re + apogee_km
    rp = Re + perigee_km
    a  = (ra + rp) / 2.0
    e  = max(1e-7, min((ra - rp) / (ra + rp), 0.2))
    n_rads = math.sqrt(mu / a**3)
    n_revday = n_rads * 86400 / (2 * math.pi)
    period_min = 1440.0 / n_revday
    return e, n_revday, period_min

def make_bstar(alt_km: float) -> float:
    if alt_km > 1200:
        return random.uniform(1e-6, 5e-6)
    elif alt_km > 800:
        return random.uniform(1e-5, 5e-5)
    elif alt_km > 500:
        return random.uniform(5e-5, 3e-4)
    else:
        return random.uniform(2e-4, 1e-3)

RAW_LEO_SATELLITES = [
    ('25544', 'ISS (ZARYA)', 'Space Station', 'NASA/Roscosmos', 'International Space Station — crewed orbital laboratory ~408 km LEO.', 415, 51.64, 1998),
    ('20580', 'HST', 'Space Telescope', 'NASA', 'Hubble Space Telescope — 2.4-m UV/optical/NIR telescope at ~540 km.', 540, 28.47, 1990),
    ('43013', 'NOAA 20 (JPSS-1)', 'Weather Satellite', 'NOAA', 'NOAA 20 polar-orbiting environmental monitoring satellite ~824 km SSO.', 824, 98.72, 2017),
    ('34264', 'NOAA-19', 'Weather Satellite', 'NOAA', 'NOAA-19 polar-orbiting operational environmental satellite ~850 km SSO.', 850, 98.71, 2009),
    ('28654', 'NOAA-18', 'Weather Satellite', 'NOAA', 'NOAA-18 polar-orbiting weather satellite ~854 km SSO.', 854, 98.74, 2005),
    ('39084', 'LANDSAT 8', 'Earth Observation', 'USGS/NASA', 'Landsat 8 land-imaging satellite ~705 km sun-synchronous orbit.', 705, 98.22, 2013),
    ('49260', 'LANDSAT 9', 'Earth Observation', 'USGS/NASA', 'Landsat 9 land-imaging satellite ~705 km sun-synchronous orbit.', 705, 98.22, 2021),
    ('25338', 'RADARSAT-1', 'Earth Observation', 'CSA', 'Canadian synthetic aperture radar satellite ~798 km SSO.', 798, 98.59, 1995),
    ('32382', 'RADARSAT-2', 'Earth Observation', 'CSA/MDA', 'Canadian commercial SAR satellite ~798 km SSO.', 798, 98.58, 2007),
    ('39634', 'SENTINEL-1A', 'Earth Observation', 'ESA', 'Copernicus C-band Synthetic Aperture Radar satellite ~693 km SSO.', 693, 98.18, 2014),
    ('40697', 'SENTINEL-2A', 'Earth Observation', 'ESA', 'Copernicus high-resolution multispectral imaging satellite ~786 km SSO.', 786, 98.57, 2015),
    ('42063', 'SENTINEL-2B', 'Earth Observation', 'ESA', 'Copernicus multispectral optical Earth observation satellite ~786 km SSO.', 786, 98.57, 2017),
    ('41335', 'SENTINEL-3A', 'Earth Observation', 'ESA', 'Copernicus ocean and land topography / temperature sensor ~814 km SSO.', 814, 98.62, 2016),
    ('43226', 'SENTINEL-3B', 'Earth Observation', 'ESA/Eumetsat', 'Copernicus ocean-colour and sea-surface-temperature sensor ~814 km.', 814, 98.62, 2018),
    ('43641', 'SENTINEL-5P', 'Earth Observation', 'ESA', 'Copernicus atmospheric chemistry monitor (TROPOMI) ~824 km SSO.', 824, 98.74, 2017),
    ('46984', 'SENTINEL-6 MF', 'Earth Observation', 'NASA/ESA/EUMETSAT', 'Sentinel-6 Michael Freilich ocean radar altimetry satellite ~1336 km.', 1336, 66.04, 2020),
    ('48274', 'CSS (TIANHE)', 'Space Station', 'CNSA', 'Chinese Space Station core module ~390 km LEO.', 390, 41.47, 2021),
    ('53239', 'CSS (WENTIAN)', 'Space Station Module', 'CNSA', 'Chinese Space Station Wentian laboratory module ~390 km LEO.', 390, 41.47, 2022),
    ('54216', 'CSS (MENGTIAN)', 'Space Station Module', 'CNSA', 'Chinese Space Station Mengtian science experiment module ~390 km LEO.', 390, 41.47, 2022),
    ('25994', 'TERRA (EOS AM-1)', 'Earth Observation', 'NASA', 'Flagship NASA Earth observation satellite in morning orbit ~705 km SSO.', 705, 98.20, 1999),
    ('27424', 'AQUA (EOS PM-1)', 'Earth Observation', 'NASA', 'Flagship NASA Earth science satellite monitoring water cycle ~705 km SSO.', 705, 98.20, 2002),
    ('28376', 'AURA (EOS Chem-1)', 'Earth Observation', 'NASA', 'NASA atmospheric chemistry and ozone monitoring satellite ~705 km SSO.', 705, 98.20, 2004),
    ('37849', 'SUOMI NPP', 'Weather / Climate', 'NOAA/NASA', 'Suomi National Polar-orbiting Partnership weather satellite ~824 km SSO.', 824, 98.74, 2011),
    ('41240', 'JASON-3', 'Earth Observation', 'NASA/CNES/NOAA', 'High-precision ocean surface altimetry satellite ~1336 km.', 1336, 66.04, 2016),
    ('39452', 'SWARM A', 'Scientific', 'ESA', 'ESA constellation studying Earths magnetic field ~460 km polar orbit.', 460, 87.35, 2013),
    ('39453', 'SWARM B', 'Scientific', 'ESA', 'ESA magnetic field survey constellation satellite ~520 km polar orbit.', 520, 87.98, 2013),
    ('39451', 'SWARM C', 'Scientific', 'ESA', 'ESA magnetic field survey satellite paired with Swarm A ~460 km.', 460, 87.35, 2013),
    ('36508', 'CRYOSAT 2', 'Earth Observation', 'ESA', 'ESA environmental research satellite measuring ice sheet thickness ~717 km.', 717, 92.00, 2010),
    ('27386', 'ENVISAT', 'Earth Observation', 'ESA', 'Large European environmental research satellite (derelict) ~770 km SSO.', 770, 98.54, 2002),
    ('29499', 'METOP-A', 'Weather Satellite', 'EUMETSAT', 'European operational polar meteorological satellite ~820 km SSO.', 820, 98.70, 2006),
    ('38771', 'METOP-B', 'Weather Satellite', 'EUMETSAT', 'European operational polar meteorological satellite ~820 km SSO.', 820, 98.70, 2012),
    ('43689', 'METOP-C', 'Weather Satellite', 'EUMETSAT', 'European polar weather satellite with microwave sounding ~820 km SSO.', 820, 98.70, 2018),
    ('34602', 'GOCE', 'Scientific', 'ESA', 'Gravity Field and Steady-State Ocean Circulation Explorer ~260 km LEO.', 260, 96.70, 2009),
    ('43476', 'GRACE-FO 1', 'Scientific', 'NASA/GFZ', 'Gravity Recovery and Climate Experiment Follow-On twin satellite ~490 km.', 490, 89.00, 2018),
    ('43477', 'GRACE-FO 2', 'Scientific', 'NASA/GFZ', 'Gravity Recovery and Climate Experiment Follow-On twin satellite ~490 km.', 490, 89.00, 2018),
    ('36795', 'CARTOSAT-2B', 'Earth Observation', 'ISRO', 'Indian high-resolution panchromatic Earth observation satellite ~630 km.', 630, 97.90, 2010),
    ('44804', 'CARTOSAT-3', 'Earth Observation', 'ISRO', 'Advanced high-resolution Indian optical Earth imaging satellite ~505 km.', 505, 97.50, 2019),
    ('44262', 'RISAT-2B', 'Earth Observation', 'ISRO', 'Indian X-band radar reconnaissance and Earth observation satellite ~556 km.', 556, 37.00, 2019),
    ('47632', 'EOS-01', 'Earth Observation', 'ISRO', 'Indian synthetic aperture radar Earth imaging satellite ~575 km.', 575, 37.00, 2020),
    ('48858', 'EOS-04 (RISAT-1A)', 'Earth Observation', 'ISRO', 'Indian C-band radar imaging satellite for agriculture and disaster management ~529 km.', 529, 97.50, 2022),
    ('39766', 'ALOS-2 (DAICHI-2)', 'Earth Observation', 'JAXA', 'Japanese L-band synthetic aperture radar satellite ~628 km SSO.', 628, 97.90, 2014),
    ('38337', 'GCOM-W1 (SHIZUKU)', 'Earth Observation', 'JAXA', 'Global Change Observation Mission water cycle monitoring satellite ~700 km SSO.', 700, 98.20, 2012),
    ('43065', 'GCOM-C (SHIKISAI)', 'Earth Observation', 'JAXA', 'Global Change Observation Mission climate monitoring satellite ~800 km SSO.', 800, 98.60, 2017),
    ('44713', 'STARLINK-1007', 'Communication', 'SpaceX', 'Starlink broadband constellation satellite ~550 km LEO.', 550, 53.05, 2019),
    ('45044', 'STARLINK-1118', 'Communication', 'SpaceX', 'Starlink low-latency internet satellite ~550 km LEO.', 550, 53.05, 2020),
    ('45056', 'STARLINK-1130', 'Communication', 'SpaceX', 'Starlink broadband constellation satellite ~550 km LEO.', 550, 53.05, 2020),
    ('45360', 'STARLINK-1284', 'Communication', 'SpaceX', 'Starlink high-throughput communication satellite ~550 km LEO.', 550, 53.05, 2020),
    ('45727', 'STARLINK-1433', 'Communication', 'SpaceX', 'Starlink internet constellation satellite ~550 km LEO.', 550, 53.05, 2020),
    ('46140', 'STARLINK-1502', 'Communication', 'SpaceX', 'Starlink orbital broadband transmitter ~550 km LEO.', 550, 53.05, 2020),
    ('46532', 'STARLINK-1692', 'Communication', 'SpaceX', 'Starlink internet constellation node ~550 km LEO.', 550, 53.05, 2020),
    ('47149', 'STARLINK-1823', 'Communication', 'SpaceX', 'Starlink low-orbit communication relay ~550 km LEO.', 550, 53.05, 2020),
    ('44057', 'ONEWEB-0012', 'Communication', 'OneWeb', 'OneWeb global low-latency constellation satellite ~1200 km polar orbit.', 1200, 87.40, 2019),
    ('45133', 'ONEWEB-0028', 'Communication', 'OneWeb', 'OneWeb polar-orbit internet constellation satellite ~1200 km.', 1200, 87.40, 2020),
    ('45425', 'ONEWEB-0045', 'Communication', 'OneWeb', 'OneWeb broadband relay satellite ~1200 km polar orbit.', 1200, 87.40, 2020),
    ('45856', 'ONEWEB-0067', 'Communication', 'OneWeb', 'OneWeb broadband relay satellite ~1200 km polar orbit.', 1200, 87.40, 2020),
    ('46490', 'ONEWEB-0082', 'Communication', 'OneWeb', 'OneWeb global satellite constellation node ~1200 km.', 1200, 87.40, 2020),
    ('40069', 'IRIDIUM NEXT 102', 'Communication', 'Iridium Communications', 'Iridium NEXT LEO telecommunications satellite ~780 km polar orbit.', 780, 86.40, 2017),
    ('41918', 'IRIDIUM NEXT 103', 'Communication', 'Iridium Communications', 'Iridium NEXT cross-linked voice/data relay satellite ~780 km.', 780, 86.40, 2017),
    ('41921', 'IRIDIUM NEXT 106', 'Communication', 'Iridium Communications', 'Iridium NEXT satellite supporting global Aireon ADS-B tracking ~780 km.', 780, 86.40, 2017),
    ('42803', 'IRIDIUM NEXT 113', 'Communication', 'Iridium Communications', 'Iridium NEXT polar constellation satellite ~780 km.', 780, 86.40, 2017),
    ('43075', 'IRIDIUM NEXT 120', 'Communication', 'Iridium Communications', 'Iridium NEXT low-orbit global network satellite ~780 km.', 780, 86.40, 2017),
    ('47530', 'PLANETSCOPE-2212', 'Earth Observation', 'Planet Labs', 'PlanetScope 3U Dove optical imaging CubeSat constellation ~500 km SSO.', 500, 97.45, 2021),
    ('49810', 'PLANETSCOPE-2401', 'Earth Observation', 'Planet Labs', 'PlanetScope SuperDove high-resolution optical CubeSat ~500 km SSO.', 500, 97.45, 2022),
    ('43810', 'SPIRE LEMUR-2-88', 'Weather Satellite', 'Spire Global', 'Spire Lemur 3U CubeSat for maritime AIS and GNSS weather occultation ~505 km.', 505, 97.50, 2018),
]

def generate_satellites():
    now = datetime.utcnow()
    epoch_yr = now.year % 100
    epoch_day = now.timetuple().tm_yday + (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    satellites = []
    rng = random.Random(1337)

    for idx, (norad_id, name, sat_type, operator, description, alt_km, inc_deg, launch_yr) in enumerate(RAW_LEO_SATELLITES):
        nid = int(norad_id)
        ecc, mm, period_min = orbital_params_from_alt(alt_km + rng.uniform(0, 5), alt_km - rng.uniform(0, 5))
        raan = (idx * 360.0 / len(RAW_LEO_SATELLITES)) % 360.0
        argp = rng.uniform(0, 360)
        ma = rng.uniform(0, 360)
        ndot = rng.uniform(1e-6, 5e-5)
        bstar = make_bstar(alt_km)
        elem_set = 100 + (idx % 800)
        rev = 1000 + idx * 50
        intl = f'{(launch_yr % 100):02d}{(idx % 90 + 10):03d}A'

        l1 = build_tle_line1(nid, intl, epoch_yr, epoch_day, ndot, bstar, elem_set)
        l2 = build_tle_line2(nid, inc_deg, raan, ecc, argp, ma, mm, rev)

        sat_rec = Satrec.twoline2rv(l1, l2)
        if sat_rec.error != 0:
            print(f'Warning: SGP4 error {sat_rec.error} for satellite {name} ({norad_id})')

        launch_dt = datetime(launch_yr, 1 + (idx % 12), 1 + (idx % 28))

        satellites.append(Satellite(
            norad_id=str(norad_id),
            name=name,
            type=sat_type,
            description=description,
            operator=operator,
            launch_date=launch_dt,
            added_at=now,
            last_updated=now,
            active=True,
            tle_line1=l1,
            tle_line2=l2,
            tle_epoch=now,
        ))

    return satellites

DEBRIS_FAMILIES = [
    ('FENGYUN 1C DEB',    29500, 110, 'PRC',  840,  920,  790,  870, 97.5, 99.5, 'DEBRIS',       'SMALL'),
    ('COSMOS 2251 DEB',   33760, 100, 'CIS',  770,  820,  730,  790, 73.5, 74.5, 'DEBRIS',       'SMALL'),
    ('IRIDIUM 33 DEB',    33430,  80, 'USA',  770,  830,  740,  800, 86.0, 86.9, 'DEBRIS',       'SMALL'),
    ('COSMOS 1408 DEB',   49250,  75, 'CIS',  430,  560,  340,  470, 82.5, 83.5, 'DEBRIS',       'SMALL'),
    ('SL-16 R/B & DEB',   23080,  45, 'CIS',  840,  870,  820,  850, 70.8, 71.4, 'ROCKET BODY',  'LARGE'),
    ('SL-8 R/B & DEB',    14820,  45, 'CIS',  960, 1010,  930,  980, 82.9, 83.7, 'ROCKET BODY',  'LARGE'),
    ('DELTA 2 DEB',       20900,  40, 'USA',  820,  900,  780,  860, 28.3, 28.9, 'ROCKET BODY',  'MEDIUM'),
    ('ARIANE 4/5 DEB',    24820,  35, 'FR',   790,  870,  740,  810, 51.6, 52.4, 'ROCKET BODY',  'MEDIUM'),
    ('CZ-4 DEB',          25900,  35, 'PRC',  700,  800,  650,  750, 98.0, 99.0, 'DEBRIS',       'MEDIUM'),
    ('CZ-3B DEB',         43160,  30, 'PRC',  280,  450,  200,  350, 27.0, 28.5, 'ROCKET BODY',  'LARGE'),
    ('PEGASUS DEB',       22820,  30, 'USA',  740,  790,  680,  750, 28.2, 28.8, 'DEBRIS',       'SMALL'),
    ('STEP 2 DEB',        23450,  25, 'USA',  780,  830,  740,  790, 28.3, 29.0, 'DEBRIS',       'SMALL'),
    ('ATLAS CENTAUR DEB', 18700,  25, 'USA',  900, 1050,  850, 1000, 27.9, 28.5, 'ROCKET BODY',  'LARGE'),
    ('RESURS-O DEB',      36597,  25, 'CIS',  595,  640,  560,  610, 97.8, 98.4, 'DEBRIS',       'SMALL'),
    ('NIMBUS 4 DEB',       4461,  20, 'USA', 1080, 1120, 1040, 1080, 99.5,100.2, 'DEBRIS',       'SMALL'),
    ('OPS 4682 DEB',      19120,  20, 'USA',  830,  880,  790,  840, 82.3, 83.1, 'DEBRIS',       'SMALL'),
    ('SPOT 1 DEB',        16613,  20, 'FR',   820,  860,  800,  840, 98.6, 99.2, 'DEBRIS',       'SMALL'),
    ('ERS-1 DEB',         21574,  20, 'ESA',  780,  810,  760,  790, 98.4, 98.9, 'DEBRIS',       'SMALL'),
    ('METEOR 2 DEB',      12456,  20, 'CIS',  960,  990,  930,  960, 81.5, 82.3, 'DEBRIS',       'SMALL'),
    ('KOMPSAT-2 DEB',     29268,  15, 'ROK',  680,  720,  660,  700, 98.0, 98.6, 'DEBRIS',       'SMALL'),
    ('RESOURCESAT DEB',   28944,  15, 'IND',  815,  845,  795,  825, 97.8, 98.4, 'DEBRIS',       'SMALL'),
    ('CERISE DEB',        23605,  15, 'FR',   650,  690,  630,  670, 98.0, 98.6, 'DEBRIS',       'SMALL'),
    ('THOR ABLE DEB',      1500,  20, 'USA',  850,  920,  800,  880, 28.2, 28.8, 'DEBRIS',       'SMALL'),
    ('TOPEX DEB',         22076,  15, 'USA', 1330, 1360, 1310, 1340, 66.0, 66.1, 'DEBRIS',       'SMALL'),
    ('STARLINK DEB',      45900,  25, 'USA',  530,  560,  510,  540, 53.0, 53.1, 'DEBRIS',       'SMALL'),
]

def generate_debris_objects(target_count=760):
    rng = random.Random(2026)
    now = datetime.utcnow()
    objects = []
    used_ids = set()

    for (prefix, norad_base, count, country,
         apog_min, apog_max, peri_min, peri_max,
         inc_min, inc_max, obj_type, rcs) in DEBRIS_FAMILIES:

        for i in range(count):
            norad_id = norad_base + i
            if norad_id in used_ids:
                norad_id = norad_base + i + 10000
            used_ids.add(norad_id)

            apogee  = rng.uniform(apog_min, apog_max)
            perigee = rng.uniform(peri_min, min(peri_max, apogee - 5))
            inc     = rng.uniform(inc_min, inc_max)
            raan    = rng.uniform(0, 360)
            argp    = rng.uniform(0, 360)
            ma      = rng.uniform(0, 360)

            ecc, mm, period_min = orbital_params_from_alt(apogee, perigee)

            epoch_offset = rng.uniform(0, 365)
            epoch_dt = now - timedelta(days=epoch_offset)
            epoch_yr  = epoch_dt.year % 100
            epoch_day = epoch_dt.timetuple().tm_yday + (
                epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second
            ) / 86400.0

            ndot  = rng.uniform(1e-7, 5e-5)
            bstar = make_bstar((apogee + perigee) / 2)
            elem_set = rng.randint(100, 999)
            rev = rng.randint(1000, 99999)
            intl = f'{(1990 + (norad_id % 34)):04d}{(norad_id % 100):03d}D'

            try:
                l1 = build_tle_line1(norad_id, intl, epoch_yr, epoch_day, ndot, bstar, elem_set)
                l2 = build_tle_line2(norad_id, inc, raan, ecc, argp, ma, mm, rev)
            except Exception as e:
                print(f'  TLE build error for {norad_id}: {e}')
                continue

            launch_yr = 1980 + (norad_id % 44)
            launch_dt = datetime(launch_yr, rng.randint(1, 12), rng.randint(1, 28))
            name = f'{prefix} #{i+1:03d}'

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

    extra_needed = max(0, target_count - len(objects))
    for k in range(extra_needed):
        norad_id = 91000 + k
        while norad_id in used_ids:
            norad_id += 1
        used_ids.add(norad_id)

        apogee  = rng.uniform(350, 1250)
        perigee = rng.uniform(300, apogee - 10)
        inc     = rng.choice([28.5, 41.5, 51.6, 53.0, 66.0, 74.0, 82.5, 86.4, 97.5, 98.2])
        raan    = rng.uniform(0, 360)
        argp    = rng.uniform(0, 360)
        ma      = rng.uniform(0, 360)

        ecc, mm, period_min = orbital_params_from_alt(apogee, perigee)

        epoch_offset = rng.uniform(0, 180)
        epoch_dt  = now - timedelta(days=epoch_offset)
        epoch_yr  = epoch_dt.year % 100
        epoch_day = epoch_dt.timetuple().tm_yday + (
            epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second
        ) / 86400.0

        ndot  = rng.uniform(1e-7, 5e-5)
        bstar = make_bstar((apogee + perigee) / 2)
        elem_set = rng.randint(100, 999)
        rev = rng.randint(1000, 99999)
        intl = f'{(1995 + k % 30):04d}{(k % 100):03d}L'
        country = rng.choice(['USA', 'CIS', 'PRC', 'FR', 'IND', 'JPN', 'ESA'])

        try:
            l1 = build_tle_line1(norad_id, intl, epoch_yr, epoch_day, ndot, bstar, elem_set)
            l2 = build_tle_line2(norad_id, inc, raan, ecc, argp, ma, mm, rev)
        except Exception as e:
            print(f'  Extra TLE build error for {norad_id}: {e}')
            continue

        launch_yr = 1995 + (norad_id % 30)
        launch_dt = datetime(launch_yr, rng.randint(1, 12), rng.randint(1, 28))
        name = f'LEO DEBRIS OBJ-{norad_id}'

        objects.append(DebrisObject(
            norad_id=str(norad_id),
            name=name,
            type='DEBRIS',
            rcs_size=rng.choice(['SMALL', 'MEDIUM', 'LARGE']),
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

def write_tle_cache(satellites, debris_objects):
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/tle_cache', exist_ok=True)

    for sat in satellites:
        path = f'data/sat_{sat.norad_id}.txt'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(sat.name + '\n' + sat.tle_line1 + '\n' + sat.tle_line2 + '\n')

    for d in debris_objects:
        path = f'data/debris_{d.norad_id}.txt'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(d.name + '\n' + d.tle_line1 + '\n' + d.tle_line2 + '\n')
        path2 = f'data/sat_{d.norad_id}.txt'
        with open(path2, 'w', encoding='utf-8') as f:
            f.write(d.name + '\n' + d.tle_line1 + '\n' + d.tle_line2 + '\n')

def seed():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    db = get_db_manager(db_path='data/colliders.db')

    print("\n=== Seeding 64 LEO Satellites ===")
    session = db.get_session()
    try:
        session.query(Satellite).delete()
        session.commit()

        satellites = generate_satellites()
        for sat in satellites:
            session.add(sat)
        session.commit()
        total_sats = session.query(Satellite).count()
        print(f"  [OK] Successfully seeded {total_sats} LEO satellites in DB")
    finally:
        session.close()

    print("\n=== Seeding 700+ LEO Debris Objects ===")
    session = db.get_session()
    try:
        session.query(DebrisObject).delete()
        session.commit()

        all_debris = generate_debris_objects(target_count=760)
        BATCH = 100
        for start in range(0, len(all_debris), BATCH):
            batch = all_debris[start:start + BATCH]
            session.bulk_save_objects(batch)
            session.commit()
            print(f"  Inserted batch {start//BATCH + 1}: {len(batch)} objects")

        total_debris = session.query(DebrisObject).count()
        print(f"  [OK] Successfully seeded {total_debris} LEO debris objects in DB")
    finally:
        session.close()

    print("\n=== Writing local TLE file cache ===")
    session = db.get_session()
    try:
        all_sats = session.query(Satellite).all()
        all_deb = session.query(DebrisObject).all()
        write_tle_cache(all_sats, all_deb)
        print("  [OK] Local TLE cache populated for all satellites and debris")
    finally:
        session.close()

    print("\n=== Seeding Complete ===\n")

if __name__ == '__main__':
    seed()
