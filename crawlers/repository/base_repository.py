from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseRepository(ABC):
    """
    Repository의 기본 인터페이스를 정의하는 추상 클래스
    """
    
    @abstractmethod
    def upsert(self, data: Dict) -> Dict[int,str]:
        """
        데이터를 생성하거나 업데이트
        """
        pass
    
    @abstractmethod
    def bulk_upsert(self, data_list: List[Dict]) -> bool:
        """
        여러 데이터를 한번에 생성하거나 업데이트
        """
        pass
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[Dict]:
        """
        ID로 데이터 조회
        """
        pass
    
    @abstractmethod
    def find_all(self, is_active: bool = True) -> List[Dict]:
        """
        모든 데이터 조회
        """
        pass
