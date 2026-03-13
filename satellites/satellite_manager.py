"""
Satellite Manager for tracking and managing satellites
"""

from datetime import datetime, timezone
from database.db_manager import get_db_manager
from database.models import Satellite
from fetch_tle import TLEFetcher
import logging
import json
import csv
import io

logger = logging.getLogger(__name__)


def _parse_tle_file_lines(lines, fallback_name):
    """Support both 2-line and 3-line TLE files."""
    cleaned = [line.strip() for line in lines if line.strip()]

    if len(cleaned) >= 3:
        return cleaned[0], cleaned[1], cleaned[2]

    if len(cleaned) >= 2:
        return fallback_name, cleaned[0], cleaned[1]

    raise Exception("Invalid TLE format")


class SatelliteManager:
    """Service for managing tracked satellites"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.tle_fetcher = TLEFetcher()
    
    def add_satellite(self, norad_id, name=None, sat_type=None, description=None, operator=None):
        """
        Add a satellite to tracking
        
        Args:
            norad_id: NORAD catalog ID
            name: Satellite name (optional, will fetch if not provided)
            sat_type: Satellite type
            description: Description
            operator: Operator/owner
            
        Returns:
            Satellite object
        """
        session = self.db_manager.get_session()
        try:
            # Check if already exists
            existing = session.query(Satellite).filter(
                Satellite.norad_id == str(norad_id)
            ).first()
            
            if existing:
                existing.name = name or existing.name
                existing.type = sat_type or existing.type
                existing.description = description or existing.description
                existing.operator = operator or existing.operator
                existing.active = True
                existing.last_updated = datetime.now(timezone.utc)
                session.commit()
                logger.info(f"Satellite {norad_id} promoted to managed tracking")
                return existing.to_dict()
            
            # Fetch TLE data
            tle_file = f'data/sat_{norad_id}.txt'
            success = self.tle_fetcher.fetch_tle(norad_id, f'sat_{norad_id}.txt')
            
            if not success:
                raise Exception(f"Failed to fetch TLE for {norad_id}")
            
            # Read TLE
            with open(tle_file, 'r') as f:
                parsed_name, tle_line1, tle_line2 = _parse_tle_file_lines(
                    f.readlines(),
                    name or f"SAT-{norad_id}"
                )
                sat_name = name or parsed_name
            
            # Create satellite record
            satellite = Satellite(
                norad_id=str(norad_id),
                name=sat_name,
                type=sat_type,
                description=description,
                operator=operator,
                tle_line1=tle_line1,
                tle_line2=tle_line2,
                tle_epoch=datetime.now(timezone.utc),
                active=True
            )
            
            session.add(satellite)
            session.commit()
            
            logger.info(f"Added satellite: {sat_name} ({norad_id})")
            return satellite.to_dict()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding satellite {norad_id}: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def remove_satellite(self, norad_id):
        """
        Remove a satellite from tracking
        
        Args:
            norad_id: NORAD catalog ID
            
        Returns:
            bool: Success status
        """
        session = self.db_manager.get_session()
        try:
            satellite = session.query(Satellite).filter(
                Satellite.norad_id == str(norad_id)
            ).first()
            
            if not satellite:
                logger.warning(f"Satellite {norad_id} not found")
                return False
            
            session.delete(satellite)
            session.commit()
            
            logger.info(f"Removed satellite: {satellite.name} ({norad_id})")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing satellite {norad_id}: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def update_satellite_tle(self, norad_id):
        """
        Update TLE data for a satellite
        
        Args:
            norad_id: NORAD catalog ID
            
        Returns:
            Satellite object
        """
        session = self.db_manager.get_session()
        try:
            satellite = session.query(Satellite).filter(
                Satellite.norad_id == str(norad_id)
            ).first()
            
            if not satellite:
                raise Exception(f"Satellite {norad_id} not found")
            
            # Fetch new TLE
            tle_file = f'data/sat_{norad_id}.txt'
            success = self.tle_fetcher.fetch_tle(norad_id, f'sat_{norad_id}.txt')
            
            if not success:
                raise Exception(f"Failed to fetch TLE for {norad_id}")
            
            # Read TLE
            with open(tle_file, 'r') as f:
                _, satellite.tle_line1, satellite.tle_line2 = _parse_tle_file_lines(
                    f.readlines(),
                    satellite.name or f"SAT-{norad_id}"
                )
                satellite.tle_epoch = datetime.now(timezone.utc)
            
            session.commit()
            
            logger.info(f"Updated TLE for: {satellite.name} ({norad_id})")
            return satellite.to_dict()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating TLE for {norad_id}: {e}")
            raise
        finally:
            self.db_manager.close_session(session)
    
    def get_all_satellites(self, active_only=True):
        """
        Get all tracked satellites
        
        Args:
            active_only: Only return active satellites
            
        Returns:
            List of Satellite objects
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(Satellite)
            
            if active_only:
                query = query.filter(Satellite.active == True)
            
            satellites = query.order_by(Satellite.name).all()
            return [s.to_dict() for s in satellites]
            
        finally:
            self.db_manager.close_session(session)
    
    def get_satellite(self, norad_id):
        """
        Get a specific satellite
        
        Args:
            norad_id: NORAD catalog ID
            
        Returns:
            Satellite object or None
        """
        session = self.db_manager.get_session()
        try:
            satellite = session.query(Satellite).filter(
                Satellite.norad_id == str(norad_id)
            ).first()
            
            return satellite.to_dict() if satellite else None
            
        finally:
            self.db_manager.close_session(session)
    
    def import_from_json(self, json_data):
        """
        Import satellites from JSON
        
        Args:
            json_data: JSON string or dict with satellite list
            
        Returns:
            Number of satellites imported
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        count = 0
        for sat_data in data.get('satellites', []):
            try:
                self.add_satellite(
                    norad_id=sat_data['norad_id'],
                    name=sat_data.get('name'),
                    sat_type=sat_data.get('type'),
                    description=sat_data.get('description'),
                    operator=sat_data.get('operator')
                )
                count += 1
            except Exception as e:
                logger.error(f"Error importing satellite {sat_data.get('norad_id')}: {e}")
        
        logger.info(f"Imported {count} satellites")
        return count
    
    def export_to_json(self):
        """
        Export all satellites to JSON
        
        Returns:
            JSON string
        """
        satellites = self.get_all_satellites(active_only=False)
        return json.dumps({'satellites': satellites}, indent=2)
    
    def import_from_csv(self, csv_data):
        """
        Import satellites from CSV
        
        Args:
            csv_data: CSV string with columns: norad_id, name, type, description, operator
            
        Returns:
            Number of satellites imported
        """
        reader = csv.DictReader(io.StringIO(csv_data))
        count = 0
        
        for row in reader:
            try:
                self.add_satellite(
                    norad_id=row['norad_id'],
                    name=row.get('name'),
                    sat_type=row.get('type'),
                    description=row.get('description'),
                    operator=row.get('operator')
                )
                count += 1
            except Exception as e:
                logger.error(f"Error importing satellite {row.get('norad_id')}: {e}")
        
        logger.info(f"Imported {count} satellites from CSV")
        return count
    
    def export_to_csv(self):
        """
        Export all satellites to CSV
        
        Returns:
            CSV string
        """
        satellites = self.get_all_satellites(active_only=False)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['norad_id', 'name', 'type', 'description', 'operator', 'added_at', 'active'])
        
        # Data
        for sat in satellites:
            writer.writerow([
                sat['norad_id'],
                sat['name'],
                sat['type'] or '',
                sat['description'] or '',
                sat['operator'] or '',
                sat['added_at'],
                sat['active']
            ])
        
        return output.getvalue()
