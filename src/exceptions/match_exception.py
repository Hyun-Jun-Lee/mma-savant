from exceptions.base_exception import BaseException

class MatchNotFoundException(BaseException):
    status_code = 404

    def __init__(self, match_id: int):
        super().__init__(f"Match with id {match_id} not found")