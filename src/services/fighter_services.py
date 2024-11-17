from domain.fighter import Fighter, FighterRecord

class FighterService:
    def __init__(self, fighter_repo):
        self.fighter_repo = fighter_repo

    async def get_all_fighters(self, page: int, limit: int, order_by: str = "id", order: str = "asc") -> list[Fighter]:
        return await self.fighter_repo.get_all(page, limit, order_by, order)

    async def get_fighter(self, fighter_id: int) -> Fighter:
        return await self.fighter_repo.get_by_id(fighter_id)