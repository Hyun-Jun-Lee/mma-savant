from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class BaseRepository(ABC):
    """
    Repository의 기본 인터페이스를 정의하는 추상 클래스
    """
    
    @abstractmethod
    def upsert(self, data: Dict) -> bool:
        """
        데이터를 생성하거나 업데이트
        
        Args:
            data: 저장할 데이터
            
        Returns:
            bool: 성공 여부
        """
        pass
    
    @abstractmethod
    def bulk_upsert(self, data_list: List[Dict]) -> bool:
        """
        여러 데이터를 한번에 생성하거나 업데이트
        
        Args:
            data_list: 저장할 데이터 리스트
            
        Returns:
            bool: 성공 여부
        """
        pass
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[Dict]:
        """
        ID로 데이터 조회
        
        Args:
            id: 조회할 데이터의 ID
            
        Returns:
            Optional[Dict]: 조회된 데이터 또는 None
        """
        pass
    
    @abstractmethod
    def find_all(self, is_active: bool = True) -> List[Dict]:
        """
        모든 데이터 조회
        
        Args:
            is_active: 활성화된 데이터만 조회할지 여부
            
        Returns:
            List[Dict]: 조회된 데이터 리스트
        """
        pass
