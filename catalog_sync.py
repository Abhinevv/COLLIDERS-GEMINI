"""
Automatic live catalog synchronization for satellites and debris.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import requests

from database.db_manager import get_db_manager
from database.models import DebrisObject, Satellite

logger = logging.getLogger(__name__)


class CatalogSyncManager:
    """Synchronize live satellite and debris catalogs into the local database."""

    def __init__(self, space_track_api=None, state_file='data/catalog_sync_state.json'):
        self.space_track_api = space_track_api
        self.state_file = state_file
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.sync_interval_seconds = int(os.getenv('CATALOG_SYNC_INTERVAL_SECONDS', '10800'))
        self.satellite_limit = int(os.getenv('CATALOG_SYNC_SATELLITE_LIMIT', '250'))
        self.debris_limit = int(os.getenv('CATALOG_SYNC_DEBRIS_LIMIT', '500'))
        self.request_timeout = int(os.getenv('CATALOG_SYNC_TIMEOUT_SECONDS', '60'))
        self.enabled = os.getenv('CATALOG_SYNC_ENABLED', 'true').lower() == 'true'

    def get_status(self):
        state = self._load_state()
        state.setdefault('enabled', self.enabled)
        state.setdefault('running', self.running)
        state.setdefault('interval_seconds', self.sync_interval_seconds)
        state.setdefault('satellite_limit', self.satellite_limit)
        state.setdefault('debris_limit', self.debris_limit)
        state.setdefault('space_track_configured', self._space_track_available())
        return state

    def start_background_sync(self):
        if not self.enabled or self.thread is not None:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, name='catalog-sync', daemon=True)
        self.thread.start()
        logger.info("Catalog sync background thread started")

    def trigger_sync(self, force=False):
        return self.sync_all(force=force)

    def sync_all(self, force=False):
        if not self.enabled:
            return {
                'status': 'disabled',
                'message': 'Automatic catalog sync is disabled',
            }

        if not self.lock.acquire(blocking=False):
            return {
                'status': 'busy',
                'message': 'A catalog sync is already running',
            }

        started_at = datetime.now(timezone.utc)
        state = self.get_status()
        state.update({
            'running': True,
            'last_attempt_at': started_at.isoformat(),
            'last_force': force,
        })
        self._save_state(state)

        try:
            satellite_result = self.sync_satellites()
            debris_result = self.sync_debris()
            finished_at = datetime.now(timezone.utc)
            result = {
                'status': 'success',
                'started_at': started_at.isoformat(),
                'completed_at': finished_at.isoformat(),
                'satellites': satellite_result,
                'debris': debris_result,
            }
            state.update({
                'running': False,
                'last_sync_at': finished_at.isoformat(),
                'last_success_at': finished_at.isoformat(),
                'last_result': result,
                'last_error': None,
            })
            self._save_state(state)
            return result
        except Exception as exc:
            finished_at = datetime.now(timezone.utc)
            logger.exception("Catalog sync failed")
            state.update({
                'running': False,
                'last_sync_at': finished_at.isoformat(),
                'last_error': str(exc),
            })
            self._save_state(state)
            return {
                'status': 'error',
                'message': str(exc),
            }
        finally:
            self.lock.release()

    def sync_satellites(self):
        gp_objects = self._fetch_celestrak_gp(group='ACTIVE')
        satcat_objects = self._fetch_celestrak_satcat(group='ACTIVE', payloads=True, onorbit=True, active=True)
        satcat_by_id = {
            str(item.get('NORAD_CAT_ID') or item.get('CATNR')): item
            for item in satcat_objects
            if item.get('NORAD_CAT_ID') or item.get('CATNR')
        }

        session = get_db_manager().get_session()
        added = 0
        updated = 0

        try:
            for obj in gp_objects[:self.satellite_limit]:
                norad_id = str(obj.get('NORAD_CAT_ID') or '').strip()
                if not norad_id:
                    continue

                satcat = satcat_by_id.get(norad_id, {})
                managed_locally = os.path.exists(os.path.join('data', f'sat_{norad_id}.txt'))
                satellite = session.query(Satellite).filter_by(norad_id=norad_id).first()
                if satellite is None:
                    satellite = Satellite(norad_id=norad_id)
                    session.add(satellite)
                    added += 1
                else:
                    updated += 1

                satellite.name = obj.get('OBJECT_NAME') or satcat.get('OBJECT_NAME') or f'SAT-{norad_id}'
                satellite.type = obj.get('OBJECT_TYPE') or 'PAYLOAD'
                if managed_locally and satellite.description:
                    satellite.description = satellite.description
                else:
                    sync_description = satcat.get('COMMENT') or satcat.get('OPS_STATUS') or 'Synced from live catalog'
                    satellite.description = f'[CATALOG_SYNC] {sync_description}'
                satellite.operator = satcat.get('OWNER') or satcat.get('OWNER_CODE')
                satellite.launch_date = self._parse_datetime(satcat.get('LAUNCH'))
                satellite.tle_line1 = obj.get('TLE_LINE1')
                satellite.tle_line2 = obj.get('TLE_LINE2')
                satellite.tle_epoch = self._parse_datetime(obj.get('EPOCH'))
                satellite.active = managed_locally

            session.commit()
            total = session.query(Satellite).count()
            return {
                'source': 'celestrak-active',
                'fetched': min(len(gp_objects), self.satellite_limit),
                'added': added,
                'updated': updated,
                'total': total,
            }
        finally:
            session.close()

    def sync_debris(self):
        if self._space_track_available():
            return self._sync_debris_from_space_track()
        return self._sync_debris_from_celestrak()

    def _sync_debris_from_space_track(self):
        combined = []
        seen = set()

        for object_type in ('DEBRIS', 'ROCKET BODY'):
            items = self.space_track_api.search_debris(object_type=object_type, limit=self.debris_limit)
            for item in items:
                norad_id = str(item.get('NORAD_CAT_ID') or '').strip()
                if not norad_id or norad_id in seen:
                    continue
                seen.add(norad_id)
                combined.append(item)
                if len(combined) >= self.debris_limit:
                    break
            if len(combined) >= self.debris_limit:
                break

        return self._upsert_debris_records(combined, source='space-track')

    def _sync_debris_from_celestrak(self):
        gp_objects = []
        satcat_objects = []

        for name_query in ('DEB', 'R/B'):
            gp_objects.extend(self._fetch_celestrak_gp(name=name_query))
            satcat_objects.extend(self._fetch_celestrak_satcat(name=name_query, onorbit=True))
            if len(gp_objects) >= self.debris_limit:
                break

        satcat_by_id = {
            str(item.get('NORAD_CAT_ID') or item.get('CATNR')): item
            for item in satcat_objects
            if item.get('NORAD_CAT_ID') or item.get('CATNR')
        }

        merged = []
        seen = set()
        for obj in gp_objects:
            norad_id = str(obj.get('NORAD_CAT_ID') or '').strip()
            if not norad_id or norad_id in seen:
                continue
            seen.add(norad_id)
            satcat = satcat_by_id.get(norad_id, {})
            merged.append({
                **satcat,
                **obj,
            })
            if len(merged) >= self.debris_limit:
                break

        if not merged:
            return {
                'source': 'celestrak-fallback',
                'fetched': 0,
                'added': 0,
                'updated': 0,
                'total': self._count_rows(DebrisObject),
            }

        return self._upsert_debris_records(merged, source='celestrak-fallback')

    def _upsert_debris_records(self, records, source):
        session = get_db_manager().get_session()
        added = 0
        updated = 0

        try:
            for obj in records[:self.debris_limit]:
                norad_id = str(obj.get('NORAD_CAT_ID') or obj.get('CATNR') or '').strip()
                if not norad_id:
                    continue

                debris = session.query(DebrisObject).filter_by(norad_id=norad_id).first()
                if debris is None:
                    debris = DebrisObject(norad_id=norad_id)
                    session.add(debris)
                    added += 1
                else:
                    updated += 1

                debris.name = obj.get('OBJECT_NAME') or obj.get('SATNAME') or f'DEBRIS-{norad_id}'
                debris.type = obj.get('OBJECT_TYPE') or obj.get('OBJECT_TYPE_DESC') or 'DEBRIS'
                debris.country = obj.get('COUNTRY') or obj.get('OWNER') or obj.get('OWNER_CODE') or 'LIVE'
                debris.launch_date = self._parse_datetime(obj.get('LAUNCH_DATE') or obj.get('LAUNCH'))
                debris.decay_date = self._parse_datetime(obj.get('DECAY_DATE') or obj.get('DECAY'))
                debris.apogee_km = self._as_float(obj.get('APOGEE') or obj.get('APOAPSIS'))
                debris.perigee_km = self._as_float(obj.get('PERIGEE') or obj.get('PERIAPSIS'))
                debris.inclination_deg = self._as_float(obj.get('INCLINATION') or obj.get('INCLINATION_DEG'))
                debris.period_minutes = self._as_float(obj.get('PERIOD') or obj.get('PERIOD_MINUTES'))
                debris.tle_line1 = obj.get('TLE_LINE1')
                debris.tle_line2 = obj.get('TLE_LINE2')
                debris.tle_epoch = self._parse_datetime(obj.get('EPOCH'))
                debris.rcs_size = obj.get('RCS_SIZE') or debris.rcs_size or 'MEDIUM'

            session.commit()
            total = session.query(DebrisObject).count()
            return {
                'source': source,
                'fetched': min(len(records), self.debris_limit),
                'added': added,
                'updated': updated,
                'total': total,
            }
        finally:
            session.close()

    def _fetch_celestrak_gp(self, group=None, name=None, special=None):
        params = {'FORMAT': 'JSON'}
        if group:
            params['GROUP'] = group
        if name:
            params['NAME'] = name
        if special:
            params['SPECIAL'] = special

        try:
            response = requests.get(
                'https://celestrak.org/NORAD/elements/gp.php',
                params=params,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except (requests.RequestException, ValueError) as exc:
            logger.warning("CelesTrak GP fetch failed for params=%s: %s", params, exc)
            return []

    def _fetch_celestrak_satcat(self, group=None, name=None, payloads=None, onorbit=None, active=None):
        params = {'FORMAT': 'JSON', 'MAX': str(self.debris_limit if name else self.satellite_limit)}
        if group:
            params['GROUP'] = group
        if name:
            params['NAME'] = name
        if payloads is not None:
            params['PAYLOADS'] = '1' if payloads else '0'
        if onorbit is not None:
            params['ONORBIT'] = '1' if onorbit else '0'
        if active is not None:
            params['ACTIVE'] = '1' if active else '0'

        try:
            response = requests.get(
                'https://celestrak.org/satcat/records.php',
                params=params,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []
        except (requests.RequestException, ValueError) as exc:
            logger.warning("CelesTrak SATCAT fetch failed for params=%s: %s", params, exc)
            return []

    def _run_loop(self):
        while self.running:
            self.sync_all()
            time.sleep(self.sync_interval_seconds)

    def _space_track_available(self):
        return bool(
            self.space_track_api and
            getattr(self.space_track_api, 'username', None) and
            getattr(self.space_track_api, 'password', None)
        )

    def _count_rows(self, model_cls):
        session = get_db_manager().get_session()
        try:
            return session.query(model_cls).count()
        finally:
            session.close()

    def _load_state(self):
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, 'r', encoding='utf-8') as handle:
                return json.load(handle)
        except Exception:
            return {}

    def _save_state(self, state):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        temp_file = f'{self.state_file}.tmp'
        with open(temp_file, 'w', encoding='utf-8') as handle:
            json.dump(state, handle, indent=2)
        os.replace(temp_file, self.state_file)

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError:
            for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S'):
                try:
                    return datetime.strptime(text, fmt)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _as_float(value):
        if value in (None, ''):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
