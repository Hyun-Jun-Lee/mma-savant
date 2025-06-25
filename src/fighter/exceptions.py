from typing import List

class FighterDomainError(Exception):
    """Fighter 도메인 최상위 예외"""
    pass

class FighterNotFoundError(FighterDomainError):
    """Fighter를 찾을 수 없는 경우"""
    def __init__(self, fighter_identifier: str):
        self.fighter_identifier = fighter_identifier
        super().__init__(f"Fighter not found: {fighter_identifier}")

class InvalidWeightClassError(FighterDomainError):
    """잘못된 체급인 경우"""
    def __init__(self, weight_class_name: str):
        self.weight_class_name = weight_class_name
        super().__init__(f"Invalid weight class: {weight_class_name}")