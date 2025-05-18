from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from repository.base_repository import BaseRepository
from models.event_model import EventModel
from schemas import Event

class EventRepository(BaseRepository):
    """
    이벤트 데이터에 대한 저장소 클래스
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, event: Event) -> Optional[Event]:
        """
        이벤트를 생성하거나 업데이트합니다.
        
        Args:
            event: 저장할 이벤트 스키마
            
        Returns:
            저장된 이벤트 스키마 또는 None (실패 시)
        """
        try:
            # 기존 이벤트 확인 (URL로 검색)
            stmt = select(EventModel).where(EventModel.url == event.url)
            existing_event = self.session.execute(stmt).scalars().first()
            
            if existing_event:
                # 기존 이벤트 업데이트
                for key, value in event.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                    setattr(existing_event, key, value)
                self.session.commit()
                return existing_event.to_schema()
            else:
                # 새 이벤트 생성
                new_event = EventModel.from_schema(event)
                self.session.add(new_event)
                self.session.commit()
                return new_event.to_schema()
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"이벤트 저장 중 오류 발생: {str(e)}")
            return None

    def bulk_upsert(self, events: List[Event]) -> List[Event]:
        """
        여러 이벤트를 일괄 생성하거나 업데이트합니다.
        URL을 기본 식별자로 사용하여 기존 이벤트를 찾습니다.
        
        Args:
            events: 저장할 이벤트 스키마 리스트
            
        Returns:
            성공한 이벤트의 스키마 리스트
        """
        result = []
        try:
            # URL이 있는 이벤트만 URL로 조회
            event_urls = [e.url for e in events if e.url]
            url_to_event = {}
            
            # URL로 한 번에 기존 이벤트 조회
            if event_urls:
                stmt = select(EventModel).where(EventModel.url.in_(event_urls))
                for event in self.session.execute(stmt).scalars().all():
                    if event.url:
                        url_to_event[event.url] = event
            
            # 일괄 처리
            for event in events:
                # URL로만 기존 이벤트 찾기
                existing_event = None
                if event.url:
                    existing_event = url_to_event.get(event.url)
                
                if existing_event:
                    # 기존 이벤트 업데이트
                    for key, value in event.model_dump(exclude={'id', 'created_at', 'updated_at'}).items():
                        setattr(existing_event, key, value)
                    result.append(existing_event.to_schema())
                else:
                    # 새 이벤트 생성
                    new_event = EventModel.from_schema(event)
                    self.session.add(new_event)
                    # 커밋 전에는 ID가 없으므로 임시로 저장
                    result.append(event)
            
            # 모든 변경사항을 한 번에 커밋
            self.session.commit()
            
            # 새로 생성된 이벤트의 스키마 업데이트 (ID 포함)
            updated_result = []
            for item in result:
                if not getattr(item, 'id', None):
                    # 새로 생성된 이벤트는 ID가 없는 경우만 다시 조회
                    if item.url:  # URL이 있는 경우 URL로 조회
                        stmt = select(EventModel).where(EventModel.url == item.url)
                    else:  # URL이 없는 경우 이름으로 조회
                        stmt = select(EventModel).where(EventModel.name == item.name)
                    
                    new_event = self.session.execute(stmt).scalars().first()
                    if new_event:
                        updated_result.append(new_event.to_schema())
                else:
                    updated_result.append(item)
            
            return updated_result
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"이벤트 일괄 저장 중 오류 발생: {str(e)}")
            return result

    def find_by_id(self, id: int) -> Optional[Event]:
        """
        ID로 이벤트를 조회합니다.
        
        Args:
            id: 조회할 이벤트 ID
            
        Returns:
            조회된 이벤트 스키마 또는 None (없을 경우)
        """
        try:
            stmt = select(EventModel).where(EventModel.id == id)
            event = self.session.execute(stmt).scalars().first()
            return event.to_schema() if event else None
        except SQLAlchemyError as e:
            print(f"이벤트 조회 중 오류 발생: {str(e)}")
            return None

    def find_by_url(self, url: str) -> Optional[Event]:
        """
        URL로 이벤트를 조회합니다.
        
        Args:
            url: 조회할 이벤트 URL
            
        Returns:
            조회된 이벤트 스키마 또는 None (없을 경우)
        """
        try:
            stmt = select(EventModel).where(EventModel.url == url)
            event = self.session.execute(stmt).scalars().first()
            return event.to_schema() if event else None
        except SQLAlchemyError as e:
            print(f"이벤트 조회 중 오류 발생: {str(e)}")
            return None

    def find_all(self) -> List[Event]:
        """
        모든 이벤트를 조회합니다.
        
        Args:
            is_active: 활성 상태 여부 (기본값: True)
            
        Returns:
            조회된 이벤트 스키마 리스트
        """
        try:
            stmt = select(EventModel)
            events = self.session.execute(stmt).scalars().all()
            return [event.to_schema() for event in events]
        except SQLAlchemyError as e:
            print(f"이벤트 목록 조회 중 오류 발생: {str(e)}")
            return []