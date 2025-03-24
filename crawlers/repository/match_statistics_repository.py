from sqlalchemy.orm import Session
from typing import Optional, List

from models.match_model import MatchStatisticsModel
from schemas.match import MatchStatistics

class MatchStatisticsRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def upsert(self, match_statistics: MatchStatistics) -> MatchStatistics:
        """매치 통계 정보를 업서트합니다."""
        # 이미 존재하는 매치 통계인지 확인
        existing_stats = self.find_by_fighter_match_id(match_statistics.fighter_match_id)
        
        if existing_stats:
            # 기존 매치 통계 업데이트
            stats_model = self.session.query(MatchStatisticsModel).filter(
                MatchStatisticsModel.fighter_match_id == match_statistics.fighter_match_id
            ).first()
            
            # 필드 업데이트
            stats_model.knockdowns = match_statistics.knockdowns
            stats_model.control_time_seconds = match_statistics.control_time_seconds
            stats_model.submission_attempts = match_statistics.submission_attempts
            stats_model.sig_str_landed = match_statistics.sig_str_landed
            stats_model.sig_str_attempted = match_statistics.sig_str_attempted
            stats_model.total_str_landed = match_statistics.total_str_landed
            stats_model.total_str_attempted = match_statistics.total_str_attempted
            stats_model.td_landed = match_statistics.td_landed
            stats_model.td_attempted = match_statistics.td_attempted
            
            self.session.commit()
            return stats_model.to_schema()
        else:
            # 새 매치 통계 생성
            stats_model = MatchStatisticsModel.from_schema(match_statistics)
            self.session.add(stats_model)
            self.session.commit()
            return stats_model.to_schema()
    
    def bulk_upsert(self, match_statistics_list: List[MatchStatistics]) -> List[MatchStatistics]:
        """여러 매치 통계 정보를 업서트합니다."""
        result = []
        for match_statistics in match_statistics_list:
            result.append(self.upsert(match_statistics))
        return result
    
    def find_by_fighter_match_id(self, fighter_match_id: int) -> Optional[MatchStatistics]:
        """파이터 매치 ID로 매치 통계 정보를 조회합니다."""
        stats_model = self.session.query(MatchStatisticsModel).filter(
            MatchStatisticsModel.fighter_match_id == fighter_match_id
        ).first()
        
        if stats_model:
            return stats_model.to_schema()
        return None
    
    def find_all_by_fighter_match_id(self, fighter_match_id: int) -> List[MatchStatistics]:
        """파이터 매치 ID로 모든 매치 통계 정보를 조회합니다."""
        stats_models = self.session.query(MatchStatisticsModel).filter(
            MatchStatisticsModel.fighter_match_id == fighter_match_id
        ).all()
        
        return [stats_model.to_schema() for stats_model in stats_models]
