import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.violation import Violation
from backend.app.repositories.violation import ViolationRepository
from backend.app.core.config import settings

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.violation_repo = ViolationRepository(db)

    async def ingest_csv(self) -> int:
        """
        Loads the CSV, cleans records, filters by boundary box, and writes to database.
        Returns the number of rows ingested.
        """
        csv_path = settings.DATA_CSV_PATH
        
        # 1. Check if database already has records
        if await self.violation_repo.has_records():
            print("Database already contains violations. Skipping ingestion.")
            return await self.violation_repo.get_total_count()

        # 2. Check if file exists
        if not os.path.exists(csv_path):
            # Fallback: seed synthetic violations so the demo always has data
            print(f"Data file not found at: {csv_path}. Seeding synthetic violations for demo.")
            await self._seed_synthetic_violations()
            return await self.violation_repo.get_total_count()

        print(f"Starting ingestion of {csv_path}...")
        
        # Bangalore geographic boundaries
        lat_min, lat_max = 12.8, 13.3
        lon_min, lon_max = 77.4, 77.8
        
        chunk_size = 10000
        total_ingested = 0

        # We will use pandas to read in chunks
        # This keeps the memory usage low
        for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size):
            violations_chunk = []
            
            # Drop rows with missing latitude or longitude
            chunk_df = chunk_df.dropna(subset=['latitude', 'longitude'])
            
            # Clean coordinates
            chunk_df['latitude'] = pd.to_numeric(chunk_df['latitude'], errors='coerce')
            chunk_df['longitude'] = pd.to_numeric(chunk_df['longitude'], errors='coerce')
            chunk_df = chunk_df.dropna(subset=['latitude', 'longitude'])
            
            # Filter rows inside Bangalore bounding box
            chunk_df = chunk_df[
                (chunk_df['latitude'] >= lat_min) & (chunk_df['latitude'] <= lat_max) &
                (chunk_df['longitude'] >= lon_min) & (chunk_df['longitude'] <= lon_max)
            ]
            
            if chunk_df.empty:
                continue

            for _, row in chunk_df.iterrows():
                # Parse created_datetime
                dt_str = str(row['created_datetime'])
                try:
                    # e.g., '2023-11-20 00:28:46+00'
                    if '+' in dt_str:
                        # Remove timezone suffix if python datetime doesn't support +00 format on old versions
                        # but Python 3.7+ supports fromisoformat with tz
                        dt = datetime.fromisoformat(dt_str)
                    else:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    dt = datetime.utcnow() # fallback

                # Standardize strings
                location_val = str(row['location']) if pd.notnull(row['location']) else "Unknown Location"
                vehicle_number_val = str(row['vehicle_number']) if pd.notnull(row['vehicle_number']) else "UNKNOWN"
                vehicle_type_val = str(row['vehicle_type']) if pd.notnull(row['vehicle_type']) else "UNKNOWN"
                police_station_val = str(row['police_station']) if pd.notnull(row['police_station']) else "No Police Station"
                junction_name_val = str(row['junction_name']) if pd.notnull(row['junction_name']) else "No Junction"
                
                # Format JSON arrays of violations and offense codes
                # Some violation types in CSV are serialized string arrays like: '["WRONG PARKING"]'
                violation_type_val = str(row['violation_type']) if pd.notnull(row['violation_type']) else "[]"
                offence_code_val = str(row['offence_code']) if pd.notnull(row['offence_code']) else "[]"
                
                violation = {
                    "id": str(row['id']),
                    "latitude": float(row['latitude']),
                    "longitude": float(row['longitude']),
                    "location": location_val,
                    "vehicle_number": vehicle_number_val,
                    "vehicle_type": vehicle_type_val,
                    "violation_type": violation_type_val,
                    "offence_code": offence_code_val,
                    "created_datetime": dt,
                    "police_station": police_station_val,
                    "junction_name": junction_name_val
                }
                violations_chunk.append(violation)

            if violations_chunk:
                await self.violation_repo.bulk_create(violations_chunk)
                await self.db.commit()
                total_ingested += len(violations_chunk)
                print(f"Ingested {total_ingested} records so far...")

        print(f"Ingestion completed. Total records saved: {total_ingested}")
        return total_ingested

    async def _seed_synthetic_violations(self) -> None:
        """
        Fallback seed: generates synthetic violations across known Bangalore junctions
        when the CSV dataset is unavailable. Guarantees a non-empty demo on fresh deployments.
        """
        import uuid
        from datetime import datetime, timedelta

        base_locations = [
            ("KR Market", 12.9716, 77.5946),
            ("MG Road", 12.9758, 77.6055),
            ("Indiranagar", 12.9784, 77.6376),
            ("Koramangala", 12.9352, 77.6245),
            ("Whitefield", 12.9698, 77.7500),
            ("Jayanagar", 12.9255, 77.5937),
            ("Malleshwaram", 13.0034, 77.5703),
            ("Hebbal", 13.0358, 77.5913),
        ]

        vehicle_types = ["CAR", "BIKE", "AUTO", "BUS", "TRUCK"]
        violation_types = [
            '["WRONG PARKING"]',
            '["NO PARKING"]',
            '["OBSTRUCTING TRAFFIC"]',
        ]

        now = datetime.utcnow()
        synthetic = []
        total = 800

        for i in range(total):
            loc_idx = i % len(base_locations)
            loc_name, base_lat, base_lon = base_locations[loc_idx]
            lat = base_lat + (i * 0.0007)
            lon = base_lon + (i * 0.0007)
            created = now - timedelta(minutes=int((total - i) * 17), hours=(i % 24))
            vehicle = vehicle_types[i % len(vehicle_types)]
            vtype = violation_types[i % len(violation_types)]
            synthetic.append({
                "id": str(uuid.uuid4()),
                "latitude": float(lat),
                "longitude": float(lon),
                "location": f"{loc_name}, Bengaluru",
                "vehicle_number": f"KA{50 + (i % 50)}-{1000 + i}",
                "vehicle_type": vehicle,
                "violation_type": vtype,
                "offence_code": "[101]",
                "created_datetime": created,
                "police_station": f"PS-{loc_name.split()[0]}",
                "junction_name": loc_name,
            })

        await self.violation_repo.bulk_create(synthetic)
        await self.db.commit()
        print(f"Seeded {len(synthetic)} synthetic violations.")
