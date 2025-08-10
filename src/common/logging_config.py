"""
공통 로깅 설정 모듈
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler



def get_logger(name: str, level: int = logging.INFO, error_log_file: str = None, caller_file: str = None) -> logging.Logger:
    """
    로거 생성 함수 (에러만 파일 저장)
    
    Args:
        name: 로거 이름 (보통 파일명)
        level: 로그 레벨 (기본값: INFO)
        error_log_file: 에러 로그 파일 경로 (None이면 기본 경로 사용)
        caller_file: 호출한 파일의 __file__ 경로 (자동 감지용)
    
    Returns:
        설정된 Logger 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 중복 핸들러 추가 방지
    if not logger.handlers:
        # 호출한 파일 경로 자동 감지
        if caller_file is None:
            import inspect
            frame = inspect.currentframe().f_back
            caller_file = frame.f_globals.get('__file__')
        
        setup_logger_with_error_file(logger, level, error_log_file, caller_file)
    
    return logger


def setup_logger_with_error_file(logger: logging.Logger, level: int = logging.INFO, error_log_file: str = None, caller_file: str = None) -> None:
    """
    로거 설정 (에러만 파일 저장)
    
    Args:
        logger: 설정할 Logger 인스턴스
        level: 로그 레벨
        error_log_file: 에러 로그 파일 경로
        caller_file: 호출한 파일의 경로
    """
    logger.setLevel(level)
    
    # 콘솔 핸들러 생성 (모든 레벨)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 에러 전용 파일 핸들러 생성
    if error_log_file is None:
        # 호출한 파일이 있는 디렉토리에 logs 폴더 생성
        if caller_file:
            caller_dir = os.path.dirname(os.path.abspath(caller_file))
            log_dir = os.path.join(caller_dir, 'logs')
        else:
            # fallback: 현재 작업 디렉토리
            log_dir = os.path.join(os.getcwd(), 'logs')
        
        os.makedirs(log_dir, exist_ok=True)
        error_log_file = os.path.join(log_dir, 'error.log')
    
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)  # ERROR 레벨만 파일에 저장
    
    # 에러 파일용 상세 포맷터
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_file_handler.setFormatter(error_formatter)
    logger.addHandler(error_file_handler)
    
    # 루트 로거로의 전파 방지 (중복 로그 방지)
    logger.propagate = False


