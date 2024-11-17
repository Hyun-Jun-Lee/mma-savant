from domain.match import Match, MatchStatistics

class MatchService:
    def __init__(self, match_repo):
        self.match_repo = match_repo

    async def get_all_matches(self, event_id: int) -> list[Match]:
        return await self.match_repo.get_all_by_event_id(event_id)
    
    async def get_match(self, match_id: int) -> Match:
        return await self.match_repo.get_by_id(match_id)
    
    async def get_matches_by_fighter(self, fighter_id: int) -> list[Match]:
        return await self.match_repo.get_matches_by_fighter(fighter_id)

    async def get_punch_accuracy_by_result(self, fighter_id: int, result: str) -> tuple[int, int]:
        """Fighter의 경기 중 특정 결과에 따른 펀치 성공률 계산"""
        matches = await self.match_repo.get_matches_by_fighter(fighter_id)
        
        # 특정 결과에 해당하는 경기를 필터링
        filtered_matches = [
            match for match in matches if match["result"] == result
        ]
        
        # 펀치 성공률 계산
        total_punches = sum(match["total_punches"] for match in filtered_matches)
        landed_punches = sum(match["landed_punches"] for match in filtered_matches)

        return landed_punches, total_punches