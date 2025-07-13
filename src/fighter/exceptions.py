"""
Fighter 도메인 예외 클래스
"""
from typing import Optional, Any, List


class FighterException(Exception):
    """Fighter 도메인의 기본 예외 클래스"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class FighterNotFoundError(FighterException):
    """파이터를 찾을 수 없을 때 발생하는 예외"""
    
    def __init__(self, fighter_identifier: Any, search_type: str = "id"):
        message = f"Fighter not found with {search_type}: {fighter_identifier}"
        details = {"fighter_identifier": fighter_identifier, "search_type": search_type}
        super().__init__(message, details)


class FighterValidationError(FighterException):
    """파이터 데이터 검증 실패 시 발생하는 예외"""
    
    def __init__(self, field: str, value: Any, reason: str):
        message = f"Invalid fighter data for field '{field}': {reason}"
        details = {"field": field, "value": value, "reason": reason}
        super().__init__(message, details)


class FighterNameError(FighterException):
    """파이터 이름 관련 오류 시 발생하는 예외"""
    
    def __init__(self, name: str, reason: str):
        message = f"Invalid fighter name '{name}': {reason}"
        details = {"name": name, "reason": reason}
        super().__init__(message, details)


class FighterWeightError(FighterException):
    """파이터 체중 관련 오류 시 발생하는 예외"""
    
    def __init__(self, weight: Any, reason: str):
        message = f"Invalid fighter weight '{weight}': {reason}"
        details = {"weight": weight, "reason": reason}
        super().__init__(message, details)


class FighterHeightError(FighterException):
    """파이터 신장 관련 오류 시 발생하는 예외"""
    
    def __init__(self, height: Any, reason: str):
        message = f"Invalid fighter height '{height}': {reason}"
        details = {"height": height, "reason": reason}
        super().__init__(message, details)


class FighterReachError(FighterException):
    """파이터 리치 관련 오류 시 발생하는 예외"""
    
    def __init__(self, reach: Any, reason: str):
        message = f"Invalid fighter reach '{reach}': {reason}"
        details = {"reach": reach, "reason": reason}
        super().__init__(message, details)


class FighterNationalityError(FighterException):
    """파이터 국적 관련 오류 시 발생하는 예외"""
    
    def __init__(self, nationality: str, reason: str):
        message = f"Invalid fighter nationality '{nationality}': {reason}"
        details = {"nationality": nationality, "reason": reason}
        super().__init__(message, details)


class FighterRecordError(FighterException):
    """파이터 전적 관련 오류 시 발생하는 예외"""
    
    def __init__(self, record_data: dict, reason: str):
        message = f"Invalid fighter record: {reason}"
        details = {"record_data": record_data, "reason": reason}
        super().__init__(message, details)


class FighterStatsError(FighterException):
    """파이터 통계 관련 오류 시 발생하는 예외"""
    
    def __init__(self, fighter_id: int, stat_type: str, reason: str):
        message = f"Invalid fighter statistics for fighter {fighter_id}, type '{stat_type}': {reason}"
        details = {"fighter_id": fighter_id, "stat_type": stat_type, "reason": reason}
        super().__init__(message, details)


class FighterRankingError(FighterException):
    """파이터 랭킹 관련 오류 시 발생하는 예외"""
    
    def __init__(self, fighter_id: int, weight_class_id: int, reason: str):
        message = f"Invalid fighter ranking for fighter {fighter_id} in weight class {weight_class_id}: {reason}"
        details = {"fighter_id": fighter_id, "weight_class_id": weight_class_id, "reason": reason}
        super().__init__(message, details)


class FighterWeightClassError(FighterException):
    """파이터 체급 관련 오류 시 발생하는 예외"""
    
    def __init__(self, weight_class_id: Any, reason: str):
        message = f"Invalid weight class {weight_class_id}: {reason}"
        details = {"weight_class_id": weight_class_id, "reason": reason}
        super().__init__(message, details)


class FighterCreationError(FighterException):
    """파이터 생성 실패 시 발생하는 예외"""
    
    def __init__(self, fighter_data: dict, reason: str):
        message = f"Failed to create fighter: {reason}"
        details = {"fighter_data": fighter_data, "reason": reason}
        super().__init__(message, details)


class FighterUpdateError(FighterException):
    """파이터 업데이트 실패 시 발생하는 예외"""
    
    def __init__(self, fighter_id: int, update_data: dict, reason: str):
        message = f"Failed to update fighter {fighter_id}: {reason}"
        details = {"fighter_id": fighter_id, "update_data": update_data, "reason": reason}
        super().__init__(message, details)


class FighterDeleteError(FighterException):
    """파이터 삭제 실패 시 발생하는 예외"""
    
    def __init__(self, fighter_id: int, reason: str):
        message = f"Failed to delete fighter {fighter_id}: {reason}"
        details = {"fighter_id": fighter_id, "reason": reason}
        super().__init__(message, details)


class FighterDuplicateError(FighterException):
    """중복된 파이터 생성 시 발생하는 예외"""
    
    def __init__(self, name: str, ufc_url: str = None):
        if ufc_url:
            message = f"Duplicate fighter: '{name}' with URL '{ufc_url}' already exists"
            details = {"name": name, "ufc_url": ufc_url}
        else:
            message = f"Duplicate fighter: '{name}' already exists"
            details = {"name": name}
        super().__init__(message, details)


class FighterSearchError(FighterException):
    """파이터 검색 관련 오류 시 발생하는 예외"""
    
    def __init__(self, search_params: dict, reason: str):
        message = f"Fighter search failed: {reason}"
        details = {"search_params": search_params, "reason": reason}
        super().__init__(message, details)


class FighterPerformanceError(FighterException):
    """파이터 성과 분석 관련 오류 시 발생하는 예외"""
    
    def __init__(self, fighter_id: int, analysis_type: str, reason: str):
        message = f"Fighter performance analysis failed for fighter {fighter_id}, type '{analysis_type}': {reason}"
        details = {"fighter_id": fighter_id, "analysis_type": analysis_type, "reason": reason}
        super().__init__(message, details)


class FighterComparisonError(FighterException):
    """파이터 비교 관련 오류 시 발생하는 예외"""
    
    def __init__(self, fighter_ids: List[int], reason: str):
        message = f"Fighter comparison failed for fighters {fighter_ids}: {reason}"
        details = {"fighter_ids": fighter_ids, "reason": reason}
        super().__init__(message, details)


class FighterQueryError(FighterException):
    """파이터 쿼리 실행 오류 시 발생하는 예외"""
    
    def __init__(self, query_type: str, parameters: dict, reason: str):
        message = f"Fighter query '{query_type}' failed: {reason}"
        details = {"query_type": query_type, "parameters": parameters, "reason": reason}
        super().__init__(message, details)


class FighterBirthDateError(FighterException):
    """파이터 생년월일 관련 오류 시 발생하는 예외"""
    
    def __init__(self, birth_date: Any, reason: str):
        message = f"Invalid fighter birth date '{birth_date}': {reason}"
        details = {"birth_date": birth_date, "reason": reason}
        super().__init__(message, details)


class FighterUrlError(FighterException):
    """파이터 URL 관련 오류 시 발생하는 예외"""
    
    def __init__(self, url: str, reason: str):
        message = f"Invalid fighter URL '{url}': {reason}"
        details = {"url": url, "reason": reason}
        super().__init__(message, details)


# 하위 호환성을 위한 별칭
FighterDomainError = FighterException
InvalidWeightClassError = FighterWeightClassError