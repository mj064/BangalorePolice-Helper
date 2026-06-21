from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Tuple
from backend.app.models.violation import Violation
from backend.app.repositories.base import BaseRepository

class ViolationRepository(BaseRepository[Violation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Violation, db)

    async def has_records(self) -> bool:
        result = await self.db.execute(select(func.count()).select_from(self.model))
        count = result.scalar() or 0
        return count > 0

    async def get_total_count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0

    async def get_coordinates(self) -> List[Tuple[float, float, str]]:
        # Returns latitude, longitude, vehicle_number for clustering
        # We need this to run DBSCAN on violations
        result = await self.db.execute(
            select(self.model.latitude, self.model.longitude, self.model.id)
        )
        return [(r[0], r[1], r[2]) for r in result.all()]

    async def get_all_coordinates_with_features(self) -> List[Violation]:
        # Returns all violations for feature computations
        result = await self.db.execute(select(self.model))
        return list(result.scalars().all())

    async def bulk_create(self, violations_list: List[dict]) -> None:
        from sqlalchemy import insert
        await self.db.execute(insert(self.model), violations_list)
        # Session commit is handled by database manager or caller
