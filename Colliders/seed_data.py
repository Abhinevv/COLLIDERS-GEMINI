"""
COLLIDERS - Seed Data Generator
Populates colliders.db and local TLE cache with:
1. Complete Indian Space Mission Catalog (49 Active Satellites across 5 categories)
   - Weather & Meteorology
   - Earth Observation & Radar Imaging
   - Navigation & Positioning (NavIC)
   - Space Science & Solar Observation
   - Communication & Relay (GSAT / CMS)
2. Realistic Orbital Debris Catalog (760+ Debris Objects)
   - PSLV debris & upper stages
   - Mission Shakti ASAT (Microsat-R) fragmentation cloud
   - GSLV / LVM3 upper stages & GTO/GEO drift debris
   - Major LEO/SSO orbital collision debris intersecting Indian satellite orbits
"""

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
    """Calculate standard NORAD TLE checksum modulo 10."""
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
    """Construct TLE line 1 with proper field spacing and checksum."""
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
    """Construct TLE line 2 with orbital elements and checksum."""
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
    """Compute orbital eccentricity, mean motion (rev/day), and orbital period (minutes)."""
    Re = 6378.137
    mu = 398600.4418
    ra = Re + apogee_km
    rp = Re + perigee_km
    a  = (ra + rp) / 2.0
    e  = max(1e-7, min((ra - rp) / (ra + rp), 0.2))
    n_rads = math.sqrt(mu / (a ** 3))
    n_revday = n_rads * 86400.0 / (2.0 * math.pi)
    period_min = 1440.0 / n_revday
    return e, n_revday, period_min


def make_bstar(alt_km: float) -> float:
    """Estimate atmospheric drag BSTAR parameter based on altitude."""
    if alt_km > 20000:
        return 0.0
    elif alt_km > 1200:
        return random.uniform(1e-6, 5e-6)
    elif alt_km > 800:
        return random.uniform(1e-5, 5e-5)
    elif alt_km > 500:
        return random.uniform(5e-5, 3e-4)
    else:
        return random.uniform(2e-4, 1e-3)


# =============================================================================
# 49 SATELLITES ACROSS 5 OPERATIONAL CATEGORIES
# =============================================================================
INDIAN_SATELLITE_CATALOG = [
    # -------------------------------------------------------------------------
    # 1. Weather & Meteorology (GEO / GSO ~35786 km)
    # -------------------------------------------------------------------------
    ('58955', 'INSAT-3DS', 'Weather & Meteorology', 'ISRO/IMD',
     'Advanced third-generation meteorological satellite in geostationary orbit with 6-channel optical imager and 19-channel sounder for severe storm tracking.',
     35786, 0.10, 2024),
    ('41752', 'INSAT-3DR', 'Weather & Meteorology', 'ISRO/IMD',
     'Operational meteorological satellite in geostationary orbit (74° E) with multi-spectral optical radiometer and atmospheric sounder for weather forecasting.',
     35786, 0.05, 2016),
    ('39216', 'INSAT-3D', 'Weather & Meteorology', 'ISRO/IMD',
     'Dedicated geostationary meteorological satellite (82° E) providing continuous vertical atmospheric profiling and cyclone tracking.',
     35786, 0.12, 2013),

    # -------------------------------------------------------------------------
    # 2. Earth Observation & Radar Imaging (LEO / Sun-Synchronous Orbit)
    # -------------------------------------------------------------------------
    ('60465', 'EOS-08', 'Earth Observation & Radar Imaging', 'ISRO',
     'New-generation Earth Observation micro-satellite (SSLV-D3) carrying Electro-Optical Infrared Payload (EOIR) and UV dosimeter in ~475 km orbit.',
     475, 37.40, 2024),
    ('55562', 'EOS-07', 'Earth Observation & Radar Imaging', 'ISRO',
     'Technology demonstration Earth observation micro-satellite (SSLV-D2) in ~450 km circular orbit with mm-Wave payload and spectrum monitoring.',
     450, 37.20, 2023),
    ('54361', 'EOS-06 (Oceansat-3)', 'Earth Observation & Radar Imaging', 'ISRO',
     'Third-generation oceanographic monitoring satellite in ~742 km SSO carrying Ocean Color Monitor (OCM-3), Ku-band Scatterometer, and SSTM.',
     742, 98.30, 2022),
    ('51656', 'EOS-04 (RISAT-1A)', 'Earth Observation & Radar Imaging', 'ISRO',
     'Heavy C-band Synthetic Aperture Radar (SAR) all-weather Earth imaging satellite in ~529 km sun-synchronous orbit for agriculture and disaster management.',
     529, 97.50, 2022),
    ('46905', 'EOS-01', 'Earth Observation & Radar Imaging', 'ISRO',
     'Advanced X-band Synthetic Aperture Radar (SAR) satellite in ~575 km orbit providing 24/7 all-weather surveillance and natural resource mapping.',
     575, 37.00, 2020),
    ('44804', 'Cartosat-3', 'Earth Observation & Radar Imaging', 'ISRO',
     'Advanced third-generation agile high-resolution optical imaging satellite (0.28m resolution) in ~505 km sun-synchronous polar orbit.',
     505, 97.50, 2019),
    ('43111', 'Cartosat-2F', 'Earth Observation & Radar Imaging', 'ISRO',
     'High-resolution Earth observation satellite in Cartosat-2 series carrying panchromatic and 4-band multispectral sensors in ~505 km SSO.',
     505, 97.50, 2018),
    ('42767', 'Cartosat-2E', 'Earth Observation & Radar Imaging', 'ISRO',
     'Sub-meter high-resolution optical reconnaissance and cartographic satellite in ~505 km sun-synchronous polar orbit.',
     505, 97.50, 2017),
    ('41948', 'Cartosat-2D', 'Earth Observation & Radar Imaging', 'ISRO',
     'Dedicated high-resolution cartographic satellite providing high-agility spot scene imaging in ~505 km polar orbit.',
     505, 97.50, 2017),
    ('41877', 'Resourcesat-2A', 'Earth Observation & Radar Imaging', 'ISRO',
     'Three-tier multi-spectral optical remote sensing satellite carrying LISS-4 (5.8m), LISS-3 (23.5m), and AWiFS (56m) sensors in ~817 km SSO.',
     817, 98.70, 2016),
    ('37387', 'Resourcesat-2', 'Earth Observation & Radar Imaging', 'ISRO',
     'Multi-spectral resource monitoring satellite in ~817 km SSO with enhanced radiometric performance for agricultural and hydrological surveys.',
     817, 98.70, 2011),
    ('44857', 'RISAT-2BR1', 'Earth Observation & Radar Imaging', 'ISRO',
     'Active X-band Synthetic Aperture Radar reconnaissance satellite with 0.35m spatial resolution in ~576 km inclination 37° orbit.',
     576, 37.00, 2019),
    ('44262', 'RISAT-2B', 'Earth Observation & Radar Imaging', 'ISRO',
     'Indian radar reconnaissance satellite carrying an indigenous 3.6-meter radial rib antenna X-band SAR in ~556 km orbit.',
     556, 37.00, 2019),
    ('39086', 'SARAL', 'Earth Observation & Radar Imaging', 'ISRO/CNES',
     'Joint Indo-French oceanographic altimetry satellite in ~781 km SSO with Ka-band AltiKa altimeter for sea surface height and wave height monitoring.',
     781, 98.50, 2013),
    ('43719', 'HysIS', 'Earth Observation & Radar Imaging', 'ISRO',
     'Hyperspectral Imaging Satellite in ~636 km SSO carrying 55 VNIR and 165 SWIR continuous spectral bands for environmental and mineralogical mapping.',
     636, 97.90, 2018),
    ('44114', 'EMISAT', 'Earth Observation & Radar Imaging', 'ISRO/DRDO',
     'Electronic Intelligence (ELINT) satellite carrying the Kautilya radio frequency spectrum surveillance package in ~748 km SSO.',
     748, 98.40, 2019),

    # -------------------------------------------------------------------------
    # 3. Navigation & Positioning (NavIC / IRNSS - GEO & IGSO ~35786 km)
    # -------------------------------------------------------------------------
    ('56759', 'NVS-01', 'Navigation & Positioning', 'ISRO',
     'Second-generation NavIC constellation satellite equipped with an indigenous Space-Grade Rubidium Atomic Frequency Standard (RAFS) in GSO.',
     35786, 5.00, 2023),
    ('43286', 'IRNSS-1I', 'Navigation & Positioning', 'ISRO',
     'NavIC regional navigation constellation satellite operating in an inclined geosynchronous orbit (29.5° inclination, ~35786 km).',
     35786, 29.50, 2018),
    ('41384', 'IRNSS-1F', 'Navigation & Positioning', 'ISRO',
     'NavIC regional navigation satellite in geostationary orbit (32.5° E longitude slot, ~35786 km) broadcasting L5 and S-band navigation signals.',
     35786, 5.00, 2016),
    ('41241', 'IRNSS-1E', 'Navigation & Positioning', 'ISRO',
     'NavIC regional positioning satellite in inclined geosynchronous orbit (111.75° E crossing, 29.5° inclination, ~35786 km).',
     35786, 29.50, 2016),
    ('40547', 'IRNSS-1D', 'Navigation & Positioning', 'ISRO',
     'NavIC satellite in inclined geosynchronous orbit (111.75° E crossing, 29.5° inclination, ~35786 km) supporting aviation and maritime positioning.',
     35786, 29.50, 2015),
    ('40269', 'IRNSS-1C', 'Navigation & Positioning', 'ISRO',
     'NavIC navigation satellite in geostationary orbit (83° E longitude slot, ~35786 km) providing continuous timing and positioning across India.',
     35786, 5.00, 2014),
    ('39635', 'IRNSS-1B', 'Navigation & Positioning', 'ISRO',
     'NavIC constellation satellite operating in inclined geosynchronous orbit (55° E crossing, 29.5° inclination, ~35786 km).',
     35786, 29.50, 2014),

    # -------------------------------------------------------------------------
    # 4. Space Science & Solar Observation
    # -------------------------------------------------------------------------
    ('57735', 'Aditya-L1', 'Space Science & Solar Observation', 'ISRO',
     'India’s flagship solar coronagraphy and space weather observatory monitoring solar flares, CMEs, and magnetic fields from Sun-Earth L1 halo orbit proxy.',
     695, 19.30, 2023),
    ('58694', 'XPoSat', 'Space Science & Solar Observation', 'ISRO/RRI',
     'X-ray Polarimeter Satellite carrying POLIX and XSPECT instruments in ~650 km low-inclination (6°) orbit studying cosmic celestial sources.',
     650, 6.00, 2024),
    ('40930', 'AstroSat', 'Space Science & Solar Observation', 'ISRO',
     'India’s multi-wavelength astronomical observatory carrying UVIT, LAXPC, CZTI, and SXT instruments in ~650 km (6° inclination) near-equatorial orbit.',
     650, 6.00, 2015),
    ('44441', 'Chandrayaan-2 Orbiter', 'Space Science & Solar Observation', 'ISRO',
     'Advanced lunar exploration orbiter with ultra-high resolution camera (OHRC 0.25m), SAR, and infrared spectrometer (simulated high orbit tracker).',
     720, 90.00, 2019),

    # -------------------------------------------------------------------------
    # 5. Communication & Relay (GSAT & CMS - GEO ~35786 km)
    # -------------------------------------------------------------------------
    ('61850', 'GSAT-N2 (GSAT-20)', 'Communication & Relay', 'ISRO/NSIL',
     'High Throughput Satellite (HTS) providing 48 Gbps Ka-band broadband and in-flight connectivity across the Indian region in GEO.',
     35786, 0.05, 2024),
    ('52899', 'GSAT-24', 'Communication & Relay', 'ISRO/NSIL',
     'Dedicated 24 Ku-band transponder telecommunications satellite leased for Direct-to-Home (DTH) broadcast services across India in GEO (41.2° E).',
     35786, 0.05, 2022),
    ('44034', 'GSAT-31', 'Communication & Relay', 'ISRO',
     'High-reliability Ku-band telecommunications satellite in GEO (48° E) supporting VSAT networks, DTH, and disaster emergency communications.',
     35786, 0.05, 2019),
    ('45026', 'GSAT-30', 'Communication & Relay', 'ISRO',
     'High-power C-band and Ku-band communications satellite in GEO (83° E) replacing INSAT-4A for television broadcast and telecom.',
     35786, 0.05, 2020),
    ('43694', 'GSAT-29', 'Communication & Relay', 'ISRO',
     'Multi-beam Ka/Ku-band high-throughput communication satellite in GEO (55° E) connecting remote Jammu & Kashmir and North-East regions.',
     35786, 0.08, 2018),
    ('42744', 'GSAT-19', 'Communication & Relay', 'ISRO',
     'Next-generation experimental Ka/Ku-band communication satellite in GEO (74° E) launched on GSLV Mk III D1.',
     35786, 0.08, 2017),
    ('41793', 'GSAT-18', 'Communication & Relay', 'ISRO',
     'Heavy 3404 kg telecommunications satellite carrying 48 transponders in Normal C, Upper Extended C, and Ku bands in GEO (74° E).',
     35786, 0.05, 2016),
    ('42814', 'GSAT-17', 'Communication & Relay', 'ISRO',
     'Multi-mission communication satellite in GEO (93.5° E) carrying Normal C-band, Extended C-band, S-band mobile, and Search and Rescue (SAR) transponders.',
     35786, 0.05, 2017),
    ('40332', 'GSAT-16', 'Communication & Relay', 'ISRO',
     '48-transponder heavy communications satellite in GEO (55° E) augmenting satellite telecommunications and television broadcasting.',
     35786, 0.05, 2014),
    ('41028', 'GSAT-15', 'Communication & Relay', 'ISRO',
     'Ku-band communication satellite in GEO (93.5° E) carrying 24 Ku-band transponders and GAGAN navigation payload.',
     35786, 0.05, 2015),
    ('39498', 'GSAT-14', 'Communication & Relay', 'ISRO',
     'Communication satellite in GEO (74° E) carrying 6 Extended C-band and 6 Ku-band transponders powered by indigenous cryogenic stage.',
     35786, 0.05, 2014),
    ('43824', 'GSAT-11', 'Communication & Relay', 'ISRO',
     'India’s heaviest communication satellite (5854 kg) providing 16 Gbps high-throughput connectivity across 32 user beams in Ka/Ku bands in GEO (74° E).',
     35786, 0.05, 2018),
    ('38779', 'GSAT-10', 'Communication & Relay', 'ISRO',
     'Multi-mission communication satellite in GEO (83° E) with 30 transponders in C-band, Ku-band, and GAGAN navigation transponder.',
     35786, 0.05, 2012),
    ('42695', 'GSAT-9 (South Asia Sat)', 'Communication & Relay', 'ISRO',
     'Geostationary communications satellite in GEO (48° E) providing Ku-band connectivity and tele-education to South Asian neighboring nations.',
     35786, 0.05, 2017),
    ('37605', 'GSAT-8', 'Communication & Relay', 'ISRO',
     'High-power 3100 kg satellite in GEO (55° E) carrying 24 Ku-band transponders and the primary GAGAN SBAS payload.',
     35786, 0.05, 2011),
    ('43865', 'GSAT-7A', 'Communication & Relay', 'ISRO',
     'Dedicated military communication satellite in GEO providing secure real-time Ku-band network-centric connectivity for the Indian Air Force and Army.',
     35786, 0.05, 2018),
    ('39234', 'GSAT-7 (Rukmini)', 'Communication & Relay', 'ISRO',
     'India’s first dedicated naval multi-band defense communications satellite in GEO (74° E) enabling real-time naval command and maritime domain awareness.',
     35786, 0.05, 2013),
    ('40880', 'GSAT-6', 'Communication & Relay', 'ISRO',
     'Strategic multimedia communication satellite in GEO (83° E) equipped with a 6-meter unfurlable S-band antenna for handheld defense terminals.',
     35786, 0.05, 2015),
    ('47256', 'CMS-01 (GSAT-12R)', 'Communication & Relay', 'ISRO',
     'Dedicated Extended C-band communications satellite in GEO (83° E) providing coverage over Indian mainland, Andaman & Nicobar, and Lakshadweep.',
     35786, 0.05, 2020),
]


def generate_satellites():
    """Generate satellite model records with valid SGP4 TLEs for all 49 Indian satellites."""
    now = datetime.utcnow()
    epoch_yr = now.year % 100
    epoch_day = now.timetuple().tm_yday + (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    satellites = []
    rng = random.Random(1947)

    for idx, (norad_id, name, sat_type, operator, description, alt_km, inc_deg, launch_yr) in enumerate(INDIAN_SATELLITE_CATALOG):
        nid = int(norad_id)
        # Squeeze altitude dispersion
        alt_offset = rng.uniform(-2.0, 2.0)
        actual_alt = max(300.0, alt_km + alt_offset)

        ecc, mm, period_min = orbital_params_from_alt(actual_alt, actual_alt - rng.uniform(0.1, 2.0))
        raan = (idx * 360.0 / len(INDIAN_SATELLITE_CATALOG)) % 360.0
        argp = rng.uniform(0, 360)
        ma = rng.uniform(0, 360)
        ndot = rng.uniform(1e-7, 2e-5)
        bstar = make_bstar(actual_alt)
        elem_set = 100 + (idx % 800)
        rev = 500 + idx * 50
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


# =============================================================================
# REALISTIC DEBRIS FAMILIES THREATENING INDIAN SATELLITE ORBITAL REGIMES
# =============================================================================
DEBRIS_FAMILIES = [
    # 1. Indian Launch & ASAT Debris (LEO / SSO)
    ('PSLV C-45 DEB',      44120, 60, 'IND',  730,  760,  710,  745, 98.2, 98.6, 'DEBRIS',       'SMALL'),
    ('PSLV C-37 DEB',      41950, 50, 'IND',  490,  525,  470,  510, 97.3, 97.7, 'DEBRIS',       'SMALL'),
    ('MICROSAT-R DEB',     44100, 65, 'IND',  260,  550,  240,  460, 96.2, 96.8, 'DEBRIS',       'SMALL'),
    ('PSLV R/B STAGE-4',   44858, 25, 'IND',  560,  590,  540,  575, 36.8, 37.2, 'ROCKET BODY',  'LARGE'),
    ('GSLV MK-III R/B',    42745, 20, 'IND', 35600,35900,  250,  600, 19.0, 21.5, 'ROCKET BODY',  'LARGE'),
    ('RESOURCESAT-1 DEB',  28944, 30, 'IND',  800,  835,  790,  820, 98.4, 98.9, 'DEBRIS',       'SMALL'),

    # 2. Major LEO / SSO Collision & Breakup Clouds (Cross-cutting Indian SSO Orbits)
    ('COSMOS 2251 DEB',   33760, 85, 'CIS',  760,  820,  730,  790, 73.5, 74.5, 'DEBRIS',       'SMALL'),
    ('FENGYUN 1C DEB',    29500, 90, 'PRC',  820,  910,  780,  860, 98.2, 99.2, 'DEBRIS',       'SMALL'),
    ('IRIDIUM 33 DEB',    33430, 65, 'USA',  760,  810,  740,  790, 86.0, 86.8, 'DEBRIS',       'SMALL'),
    ('COSMOS 1408 DEB',   49250, 65, 'CIS',  420,  540,  350,  470, 82.3, 83.2, 'DEBRIS',       'SMALL'),
    ('CZ-4B DEB',         25900, 40, 'PRC',  680,  780,  640,  740, 98.0, 98.8, 'DEBRIS',       'MEDIUM'),
    ('SL-16 R/B & DEB',   23080, 35, 'CIS',  830,  865,  815,  845, 70.8, 71.4, 'ROCKET BODY',  'LARGE'),
    ('SL-8 R/B & DEB',    14820, 35, 'CIS',  950, 1000,  920,  970, 82.8, 83.5, 'ROCKET BODY',  'LARGE'),
    ('RESURS-O DEB',      36597, 25, 'CIS',  590,  635,  560,  610, 97.7, 98.3, 'DEBRIS',       'SMALL'),
    ('KOMPSAT-2 DEB',     29268, 20, 'ROK',  675,  715,  655,  695, 98.0, 98.5, 'DEBRIS',       'SMALL'),
    ('SPOT 1 DEB',        16613, 20, 'FR',   815,  850,  795,  835, 98.5, 99.0, 'DEBRIS',       'SMALL'),
    ('CERISE DEB',        23605, 15, 'FR',   650,  685,  630,  670, 98.0, 98.5, 'DEBRIS',       'SMALL'),

    # 3. Geostationary & Geosynchronous Drift Debris (Threatening INSAT, GSAT, NavIC)
    ('GEO GRAVEYARD DEB', 62100, 35, 'INT', 35900,36200,35800,36100,  0.0,  5.0, 'DEBRIS',       'SMALL'),
    ('GEO TITAN TRANSTAGE',18700, 20, 'USA', 35700,36050,35600,35950,  2.0, 12.0, 'ROCKET BODY',  'LARGE'),
    ('GEO ARIANE R/B',    24820, 25, 'ESA', 35750,36150,35700,36000,  0.5,  7.0, 'ROCKET BODY',  'LARGE'),
]


def generate_debris_objects(target_count=760):
    """Generate debris objects with realistic orbital distribution across LEO, SSO, and GEO."""
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
            perigee = rng.uniform(peri_min, min(peri_max, apogee - 2))
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

            ndot  = rng.uniform(1e-7, 3e-5)
            bstar = make_bstar((apogee + perigee) / 2)
            elem_set = rng.randint(100, 999)
            rev = rng.randint(500, 99999)
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
        norad_id = 92000 + k
        while norad_id in used_ids:
            norad_id += 1
        used_ids.add(norad_id)

        # Mix of SSO LEO debris and GSO drift debris
        if k % 5 == 0:
            apogee = rng.uniform(35800, 36200)
            perigee = rng.uniform(35700, apogee - 10)
            inc = rng.choice([0.1, 2.5, 5.0, 10.0, 15.0, 29.5])
        else:
            apogee = rng.uniform(450, 950)
            perigee = rng.uniform(400, apogee - 5)
            inc = rng.choice([37.0, 37.4, 96.6, 97.5, 98.3, 98.7])

        raan = rng.uniform(0, 360)
        argp = rng.uniform(0, 360)
        ma   = rng.uniform(0, 360)

        ecc, mm, period_min = orbital_params_from_alt(apogee, perigee)

        epoch_offset = rng.uniform(0, 180)
        epoch_dt  = now - timedelta(days=epoch_offset)
        epoch_yr  = epoch_dt.year % 100
        epoch_day = epoch_dt.timetuple().tm_yday + (
            epoch_dt.hour * 3600 + epoch_dt.minute * 60 + epoch_dt.second
        ) / 86400.0

        ndot  = rng.uniform(1e-7, 3e-5)
        bstar = make_bstar((apogee + perigee) / 2)
        elem_set = rng.randint(100, 999)
        rev = rng.randint(500, 99999)
        intl = f'{(1995 + k % 30):04d}{(k % 100):03d}L'
        country = rng.choice(['IND', 'USA', 'CIS', 'PRC', 'ESA'])

        try:
            l1 = build_tle_line1(norad_id, intl, epoch_yr, epoch_day, ndot, bstar, elem_set)
            l2 = build_tle_line2(norad_id, inc, raan, ecc, argp, ma, mm, rev)
        except Exception as e:
            print(f'  Extra TLE build error for {norad_id}: {e}')
            continue

        launch_yr = 1995 + (norad_id % 30)
        launch_dt = datetime(launch_yr, rng.randint(1, 12), rng.randint(1, 28))
        name = f'ORBITAL DEBRIS #{norad_id}'

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
    """Save all TLE data to disk cache data/sat_<id>.txt and data/debris_<id>.txt."""
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
    """Execute complete database seeding and cache population."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    db = get_db_manager(db_path='data/colliders.db')

    print("\n=== Seeding 49 Indian Operational Satellites ===")
    session = db.get_session()
    try:
        session.query(Satellite).delete()
        session.commit()

        satellites = generate_satellites()
        for sat in satellites:
            session.add(sat)
        session.commit()
        total_sats = session.query(Satellite).count()
        print(f"  [OK] Successfully seeded {total_sats} Indian satellites in DB")
    finally:
        session.close()

    print("\n=== Seeding 760+ Orbital Debris Objects ===")
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
        print(f"  [OK] Successfully seeded {total_debris} debris objects in DB")
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
