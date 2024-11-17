from exceptions.base_exception import BaseException

class FighterNotFoundException(BaseException):
    status_code = 404

    def __init__(self, fighter_id: int):
        super().__init__(f"Fighter with id {fighter_id} not found")