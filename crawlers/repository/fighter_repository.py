from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repository.base_repository import BaseRepository
from models.fighter_model import FighterModel
from schemas import Fighter

class FighterRepository(BaseRepository):
    """
    파이터 데이터에 대한 저장소 클래스
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, fighter: Fighter) -> Optional[Fighter]:
        """
        파이터를 생성하거나 업데이트합니다.
        
        Args:
            fighter: 저장할 파이터 스키마
            
        Returns:
            저장된 파이터 스키마 또는 None (실패 시)
        """
        try:
            # 기존 파이터 확인 (이름과 detail_url로 검색)
            stmt = select(FighterModel).where(
                (FighterModel.name == fighter.name) | 
                (FighterModel.detail_url == fighter.detail_url)
            )
            existing_fighter = self.session.execute(stmt).scalars().first()
            
            if existing_fighter:
                # 기존 파이터 업데이트
                for key, value in fighter.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                    setattr(existing_fighter, key, value)
                self.session.commit()
                return existing_fighter.to_schema()
            else:
                # 새 파이터 생성
                new_fighter = FighterModel.from_schema(fighter)
                self.session.add(new_fighter)
                self.session.commit()
                return new_fighter.to_schema()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"파이터 저장 중 오류 발생: {str(e)}")
            return None

    def bulk_upsert(self, fighters: List[Fighter]) -> List[Fighter]:
        """
        여러 파이터를 일괄 생성하거나 업데이트합니다.
        
        Args:
            fighters: 저장할 파이터 스키마 리스트
            
        Returns:
            성공한 파이터의 스키마 리스트
        """
        result = []
        try:
            # 입력 리스트에서 중복 제거 (동일 이름 파이터 중 마지막 항목만 유지)
            unique_fighters = {}
            for fighter in fighters:
                if fighter.name:  # 이름이 있는 경우만 처리
                    if fighter.name not in unique_fighters:
                        unique_fighters[fighter.name] = fighter
            
            # 중복 제거된 고유 파이터 리스트 생성
            unique_fighter_list = list(unique_fighters.values())
            
            # 기존 파이터 이름 목록을 한 번에 조회
            name_to_fighters = {}
            fighter_names = [f.name for f in unique_fighter_list if f.name]
            if fighter_names:
                stmt = select(FighterModel).where(FighterModel.name.in_(fighter_names))
                for fighter in self.session.execute(stmt).scalars().all():
                    if fighter.name not in name_to_fighters:
                        name_to_fighters[fighter.name] = fighter

            # 일괄 처리
            for fighter in unique_fighter_list:
                existing_fighter = None
                
                # 이름으로만 찾기
                if fighter.name and fighter.name in name_to_fighters:
                    existing_fighter = name_to_fighters[fighter.name]
                
                if existing_fighter:
                    # 기존 파이터 업데이트
                    for key, value in fighter.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                        setattr(existing_fighter, key, value)
                    result.append(existing_fighter.to_schema())
                else:
                    # 새 파이터 생성
                    new_fighter = FighterModel.from_schema(fighter)
                    self.session.add(new_fighter)
                    # 커밋 전에는 ID가 없으므로 임시로 저장
                    result.append(fighter)
            
            # 모든 변경사항을 한 번에 커밋
            self.session.commit()
            
            # 새로 생성된 파이터의 스키마 업데이트 (ID 포함)
            updated_result = []
            for item in result:
                if not getattr(item, 'id', None):
                    # 새로 생성된 파이터는 ID가 없으므로 다시 조회
                    stmt = select(FighterModel).where(FighterModel.name == item.name)
                    new_fighter = self.session.execute(stmt).scalars().first()
                    if new_fighter:
                        updated_result.append(new_fighter.to_schema())
                else:
                    updated_result.append(item)
            
            return updated_result
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"파이터 일괄 저장 중 오류 발생: {str(e)}")
            return result

    def find_by_id(self, id: int) -> Optional[Fighter]:
        """
        ID로 파이터를 조회합니다.
        
        Args:
            id: 조회할 파이터 ID
            
        Returns:
            조회된 파이터 스키마 또는 None (없을 경우)
        """
        try:
            stmt = select(FighterModel).where(FighterModel.id == id)
            fighter = self.session.execute(stmt).scalars().first()
            return fighter.to_schema() if fighter else None
        except SQLAlchemyError as e:
            print(f"파이터 조회 중 오류 발생: {str(e)}")
            return None

    def find_by_name(self, name: str) -> Optional[Fighter]:
        """
        이름으로 파이터를 조회합니다.
        
        Args:
            name: 조회할 파이터 이름
            
        Returns:
            조회된 파이터 스키마 또는 None (없을 경우)
        """
        try:
            stmt = select(FighterModel).where(FighterModel.name == name)
            fighter = self.session.execute(stmt).scalars().first()
            return fighter.to_schema() if fighter else None
        except SQLAlchemyError as e:
            print(f"파이터 조회 중 오류 발생: {str(e)}")
            return None

    def find_by_detail_url(self, detail_url: str) -> Optional[Fighter]:
        """
        상세 URL로 파이터를 조회합니다.
        
        Args:
            detail_url: 조회할 파이터의 상세 URL
            
        Returns:
            조회된 파이터 스키마 또는 None (없을 경우)
        """
        try:
            stmt = select(FighterModel).where(FighterModel.detail_url == detail_url)
            fighter = self.session.execute(stmt).scalars().first()
            return fighter.to_schema() if fighter else None
        except SQLAlchemyError as e:
            print(f"파이터 조회 중 오류 발생: {str(e)}")
            return None

    def find_all(self) -> List[Fighter]:
        """
        모든 파이터를 조회합니다.
        
        Args:
            is_active: 활성 상태 여부 (기본값: True)
            
        Returns:
            조회된 파이터 스키마 리스트
        """
        try:
            stmt = select(FighterModel)
            fighters = self.session.execute(stmt).scalars().all()
            return [fighter.to_schema() for fighter in fighters]
        except SQLAlchemyError as e:
            print(f"파이터 목록 조회 중 오류 발생: {str(e)}")
            return []