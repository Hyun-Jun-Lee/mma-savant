from domain.match import Match, MatchStatistics

class MatchService:
    def __init__(self, match_repo):
        self.match_repo = match_repo

    async def get_all_matches(self, event_id: int) -> list[Match]:
        return await self.match_repo.get_all_by_event_id(event_id)
    
    async def get_match_with_statistics(self, match_id: int) -> Match:
        match = await self.match_repo.get_by_id(match_id)

        match_statics = await self.match_repo.get_statistics_by_match_id(match_id)

        match.statistics = match_statics

        return match
        
    async def get_matches_by_fighter(self, fighter_id: int) -> list[Match]:
        """단순히 Match 데이터를 조회"""
        return await self.match_repo.get_matches_by_fighter(fighter_id)

    async def get_matches_with_statistics_by_fighter(self, fighter_id: int) -> list[dict]:
        """
        Fighter와 관련된 모든 Match와 각 Match에서 Fighter의 통계만 반환.
        """
        matches = await self.get_matches_by_fighter(fighter_id)

        matches_with_statistics = []
        
        for match in matches:
            statistics = await self.match_repo.get_statistics_by_match_id(match.id)

            fighter_statistics = [
                stat for stat in statistics if stat.fighter_id == fighter_id
            ]

            matches_with_statistics.append({
                "match": match,
                "statistics": fighter_statistics[0],
            })
        
        return matches_with_statistics
        

    async def get_stat_by_result(self, fighter_id: int, result: str) -> tuple[int, int]:
        
        matches = await self.match_repo.get_matches_by_fighter(fighter_id)
        
        if result == "win":
            matches = [match for match in matches if match.winner_fighter_id == fighter_id]
        elif result == "loss":
            matches = [match for match in matches if match.loser_fighter_id == fighter_id]
        elif result == "draw":
            pass
        else:
            raise ValueError("Invalid result type. Expected 'win', 'loss' or 'draw'.")

        total_statistics = {
            "total_strike_landed": 0,
            "total_strike_attempted": 0,
            "total_takedown_landed": 0,
            "total_takedown_attempted": 0,
        }

        for match in matches:
            statistics = await self.match_repo.get_statistics_by_match_id(match.id)

            fighter_statistics = [
                stat for stat in statistics if stat.fighter_id == fighter_id
            ]

            for stat in fighter_statistics:
                total_statistics["total_strike_landed"] += stat.get_total_strike_landed()
                total_statistics["total_strike_attempted"] += stat.get_total_strike_attempted()
                total_statistics["total_takedown_landed"] += stat.get_total_takedown_landed()
                total_statistics["total_takedown_attempted"] += stat.get_total_takedown_attempted()

        return total_statistics

    async def get_detail_stats_by_result(self, fighter_id: int, result: str) -> dict:
        """
        특정 Fighter의 승리/패배 경기에서 MatchStatistics의 모든 속성 합계를 반환.
        Args:
            fighter_id (int): 통계를 확인할 Fighter ID.
            result (str): "win" 또는 "loss" (승리/패배 조건).
        Returns:
            dict: MatchStatistics의 모든 속성 합계.
        """
        # 1. Fighter와 관련된 모든 경기 조회
        matches = await self.match_repo.get_matches_by_fighter(fighter_id)

        # 2. 승리/패배 조건에 맞는 경기 필터링
        if result == "win":
            matches = [match for match in matches if match.winner_fighter_id == fighter_id]
        elif result == "loss":
            matches = [match for match in matches if match.loser_fighter_id == fighter_id]
        elif result == "draw":
            pass
        else:
            raise ValueError("Invalid result type. Expected 'win' or 'loss'.")

        # 3. 통계 초기화
        detail_statistics = {
            "head_strikes_landed": 0,
            "head_strikes_attempts": 0,
            "body_strikes_landed": 0,
            "body_strikes_attempts": 0,
            "leg_strikes_landed": 0,
            "leg_strikes_attempts": 0,
            "takedowns_landed": 0,
            "takedowns_attempts": 0,
            "clinch_strikes_landed": 0,
            "clinch_strikes_attempts": 0,
            "ground_strikes_landed": 0,
            "ground_strikes_attempts": 0,
        }

        # 4. 각 경기의 통계 수집
        for match in matches:
            statistics = await self.match_repo.get_statistics_by_match_id(match.id)

            # 해당 Fighter의 통계만 필터링
            fighter_statistics = [
                stat for stat in statistics if stat.fighter_id == fighter_id
            ]

            for stat in fighter_statistics:
                # 각 통계 속성 합계 계산
                detail_statistics["head_strikes_landed"] += stat.head_strikes_landed or 0
                detail_statistics["head_strikes_attempts"] += stat.head_strikes_attempts or 0
                detail_statistics["body_strikes_landed"] += stat.body_strikes_landed or 0
                detail_statistics["body_strikes_attempts"] += stat.body_strikes_attempts or 0
                detail_statistics["leg_strikes_landed"] += stat.leg_strikes_landed or 0
                detail_statistics["leg_strikes_attempts"] += stat.leg_strikes_attempts or 0
                detail_statistics["takedowns_landed"] += stat.takedowns_landed or 0
                detail_statistics["takedowns_attempts"] += stat.takedowns_attempts or 0
                detail_statistics["clinch_strikes_landed"] += stat.clinch_strikes_landed or 0
                detail_statistics["clinch_strikes_attempts"] += stat.clinch_strikes_attempts or 0
                detail_statistics["ground_strikes_landed"] += stat.ground_strikes_landed or 0
                detail_statistics["ground_strikes_attempts"] += stat.ground_strikes_attempts or 0

        return detail_statistics