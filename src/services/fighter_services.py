from domain.fighter import Fighter, FighterRecord

class FighterService:
    def __init__(self, fighter_repo):
        self.fighter_repo = fighter_repo

    async def get_all_fighters(self, page: int, limit: int, order_by: str = "id", order: str = "asc") -> list[Fighter]:
        return await self.fighter_repo.get_all(page, limit, order_by, order)

    async def get_fighter_by_id(self, fighter_id: int) -> Fighter:
        """
        Fighter ID로 Fighter 객체를 생성하여 반환.
        """
        # 1. Fighter 기본 정보 조회
        fighter_data = await self.fighter_repo.get_fighter(fighter_id)
        if not fighter_data:
            raise ValueError(f"Fighter with ID {fighter_id} does not exist.")

        # 2. FighterRecord 정보 조회
        fighter_records_data = await self.fighter_repo.get_fighter_records(fighter_id)

        # 3. Fighter 객체 생성
        fighter = Fighter.from_dict(fighter_data)
        fighter.records = [FighterRecord.from_dict(record) for record in fighter_records_data]

        return fighter