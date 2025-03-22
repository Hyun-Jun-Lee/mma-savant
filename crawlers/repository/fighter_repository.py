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
            # 단일 트랜잭션 내에서 처리
            # 기존 파이터 이름 목록을 한 번에 조회
            fighter_names = [f.name for f in fighters if f.name]
            
            # 이름으로 먼저 기존 파이터 조회
            name_to_fighters = {}
            if fighter_names:
                stmt = select(FighterModel).where(FighterModel.name.in_(fighter_names))
                for fighter in self.session.execute(stmt).scalars().all():
                    if fighter.name not in name_to_fighters:
                        name_to_fighters[fighter.name] = []
                    name_to_fighters[fighter.name].append(fighter)
            
            # URL로 조회할 파이터 목록 준비
            fighters_to_query_by_url = []
            for fighter in fighters:
                if not fighter.name or fighter.name not in name_to_fighters:
                    # 이름이 없거나 이름으로 찾을 수 없는 경우
                    if fighter.detail_url:
                        fighters_to_query_by_url.append(fighter)
                    continue
                
                # 이름으로 찾은 결과가 여러 개인 경우
                if len(name_to_fighters[fighter.name]) > 1 and fighter.detail_url:
                    fighters_to_query_by_url.append(fighter)
            
            # URL로 추가 조회가 필요한 경우
            url_to_fighter = {}
            if fighters_to_query_by_url:
                fighter_urls = [f.detail_url for f in fighters_to_query_by_url if f.detail_url]
                if fighter_urls:
                    stmt = select(FighterModel).where(FighterModel.detail_url.in_(fighter_urls))
                    for fighter in self.session.execute(stmt).scalars().all():
                        if fighter.detail_url:
                            url_to_fighter[fighter.detail_url] = fighter
            
            # 일괄 처리
            for fighter in fighters:
                existing_fighter = None
                
                # 1. 이름으로 찾기
                if fighter.name and fighter.name in name_to_fighters:
                    if len(name_to_fighters[fighter.name]) == 1:
                        # 이름으로 찾은 결과가 하나만 있는 경우
                        existing_fighter = name_to_fighters[fighter.name][0]
                    elif fighter.detail_url and fighter.detail_url in url_to_fighter:
                        # 이름으로 찾은 결과가 여러 개인 경우, URL로 필터링
                        existing_fighter = url_to_fighter[fighter.detail_url]
                
                # 2. URL로 찾기 (이름으로 찾지 못한 경우)
                elif fighter.detail_url and fighter.detail_url in url_to_fighter:
                    existing_fighter = url_to_fighter[fighter.detail_url]
                
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
                    stmt = select(FighterModel).where(
                        (FighterModel.name == item.name) & 
                        (FighterModel.detail_url == item.detail_url)
                    )
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

    def find_all(self, is_active: bool = True) -> List[Fighter]:
        """
        모든 파이터를 조회합니다.
        
        Args:
            is_active: 활성 상태 여부 (기본값: True)
            
        Returns:
            조회된 파이터 스키마 리스트
        """
        try:
            stmt = select(FighterModel).where(FighterModel.is_active == is_active)
            fighters = self.session.execute(stmt).scalars().all()
            return [fighter.to_schema() for fighter in fighters]
        except SQLAlchemyError as e:
            print(f"파이터 목록 조회 중 오류 발생: {str(e)}")
            return []