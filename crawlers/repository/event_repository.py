from typing import List, Dict, Optional

from repository.base_repository import BaseRepository

class EventRepository(BaseRepository):

    
    
    def __init__(self, session) -> None:
        self.session = session

    def upsert(self, data: Dict) -> Dict[int,str]:
        # NOTE : return dict[date,id] or Dict[title, id]
        # NOTE : event랑 event_detail 구분 필요
        pass

    def bulk_upsert(self, data_list: List[Dict]) -> bool:
        pass

    def find_by_id(self, id: str) -> Optional[Dict]:
        pass

    def find_all(self, is_active: bool = True) -> List[Dict]:
        pass