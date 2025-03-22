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
        
        Args:
            events: 저장할 이벤트 스키마 리스트
            
        Returns:
            성공한 이벤트의 스키마 리스트
        """
        result = []
        try:
            # 단일 트랜잭션 내에서 처리
            # 기존 이벤트 이름 목록을 한 번에 조회
            event_names = [e.name for e in events if e.name]
            
            # 이름으로 먼저 기존 이벤트 조회
            name_to_events = {}
            if event_names:
                stmt = select(EventModel).where(EventModel.name.in_(event_names))
                for event in self.session.execute(stmt).scalars().all():
                    if event.name not in name_to_events:
                        name_to_events[event.name] = []
                    name_to_events[event.name].append(event)
            
            # URL로 조회할 이벤트 목록 준비
            events_to_query_by_url = []
            for event in events:
                if not event.name or event.name not in name_to_events:
                    # 이름이 없거나 이름으로 찾을 수 없는 경우
                    if event.url:
                        events_to_query_by_url.append(event)
                    continue
                
                # 이름으로 찾은 결과가 여러 개인 경우
                if len(name_to_events[event.name]) > 1 and event.url:
                    events_to_query_by_url.append(event)
            
            # URL로 추가 조회가 필요한 경우
            url_to_event = {}
            if events_to_query_by_url:
                event_urls = [e.url for e in events_to_query_by_url if e.url]
                if event_urls:
                    stmt = select(EventModel).where(EventModel.url.in_(event_urls))
                    for event in self.session.execute(stmt).scalars().all():
                        if event.url:
                            url_to_event[event.url] = event
            
            # 일괄 처리
            for event in events:
                existing_event = None
                
                # 1. 이름으로 찾기
                if event.name and event.name in name_to_events:
                    if len(name_to_events[event.name]) == 1:
                        # 이름으로 찾은 결과가 하나만 있는 경우
                        existing_event = name_to_events[event.name][0]
                    elif event.url and event.url in url_to_event:
                        # 이름으로 찾은 결과가 여러 개인 경우, URL로 필터링
                        existing_event = url_to_event[event.url]
                
                # 2. URL로 찾기 (이름으로 찾지 못한 경우)
                elif event.url and event.url in url_to_event:
                    existing_event = url_to_event[event.url]
                
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
                    # 새로 생성된 이벤트는 ID가 없으므로 다시 조회
                    stmt = select(EventModel).where(
                        (EventModel.url == item.url) & 
                        (EventModel.name == item.name)
                    )
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

    def find_all(self, is_active: bool = True) -> List[Event]:
        """
        모든 이벤트를 조회합니다.
        
        Args:
            is_active: 활성 상태 여부 (기본값: True)
            
        Returns:
            조회된 이벤트 스키마 리스트
        """
        try:
            stmt = select(EventModel).where(EventModel.is_active == is_active)
            events = self.session.execute(stmt).scalars().all()
            return [event.to_schema() for event in events]
        except SQLAlchemyError as e:
            print(f"이벤트 목록 조회 중 오류 발생: {str(e)}")
            return []