from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from typing import List, Optional
from backend.app.models.hotspot import Hotspot
from backend.app.repositories.base import BaseRepository

class HotspotRepository(BaseRepository[Hotspot]):
    def __init__(self, db: AsyncSession):
        super().__init__(Hotspot, db)

    async def get_all_ordered(self) -> List[Hotspot]:
        result = await self.db.execute(
            select(self.model).order_by(self.model.impact_score.desc())
        )
        return list(result.scalars().all())

    async def get_high_risk_count(self) -> int:
        # High and critical risk are scores >= 56 (recalibrated thresholds: High 56-65, Critical >= 66)
        result = await self.db.execute(
            select(func.count()).select_from(self.model).filter(self.model.impact_score >= 56)
        )
        return result.scalar() or 0

    async def get_total_count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0

    async def clear_all(self) -> None:
        await self.db.execute(delete(self.model))
        await self.db.commit()

    async def bulk_create(self, hotspots_list: List[Hotspot]) -> None:
        self.db.add_all(hotspots_list)
        await self.db.commit()
