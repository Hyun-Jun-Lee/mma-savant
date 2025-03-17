from typing import List, Dict, Optional

from repository.base_repository import BaseRepository

class FighterRepository(BaseRepository):

    # NOTE : find method return dict[name,id]
    
    def __init__(self, session) -> None:
        self.session = session

    def upsert(self, data: Dict) -> Dict[int,str]:
        pass

    def bulk_upsert(self, data_list: List[Dict]) -> Dict[int,str]:
        pass

    def find_by_id(self, id: str) -> Optional[Dict]:
        pass

    def find_all(self, is_active: bool = True) -> List[Dict]:
        pass