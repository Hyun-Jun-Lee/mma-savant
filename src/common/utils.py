import re
import logging
from typing import Callable, Dict
from functools import wraps
from unidecode import unidecode


def _calculate_percentage(numerator: int, denominator: int) -> float:
    """
    백분율을 계산합니다. 분모가 0이면 0을 반환합니다.
    """
    if not denominator:
        return 0
    return round((numerator / denominator) * 100, 2)

def calculate_fighter_accuracy(basic_stats: Dict, sig_str_stats: Dict) -> Dict:
    """파이터 정확도 계산 헬퍼 함수"""
    return {
        "sig_str_accuracy": _calculate_percentage(basic_stats["sig_str_landed"], basic_stats["sig_str_attempted"]),
        "total_str_accuracy": _calculate_percentage(basic_stats["total_str_landed"], basic_stats["total_str_attempted"]),
        "td_accuracy": _calculate_percentage(basic_stats["td_landed"], basic_stats["td_attempted"]),
        "head_strikes_accuracy": _calculate_percentage(sig_str_stats["head_strikes_landed"], sig_str_stats["head_strikes_attempts"]),
        "body_strikes_accuracy": _calculate_percentage(sig_str_stats["body_strikes_landed"], sig_str_stats["body_strikes_attempts"]),
        "leg_strikes_accuracy": _calculate_percentage(sig_str_stats["leg_strikes_landed"], sig_str_stats["leg_strikes_attempts"]),
        "clinch_strikes_accuracy": _calculate_percentage(sig_str_stats["clinch_strikes_landed"], sig_str_stats["clinch_strikes_attempts"]),
        "ground_strikes_accuracy": _calculate_percentage(sig_str_stats["ground_strikes_landed"], sig_str_stats["ground_strikes_attempts"]),
    }

def with_retry(max_attempts: int = 3):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logging.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    logging.warning(f"Attempt {attempts} failed: {str(e)}. Retrying...")
            return None
        return wrapper
    return decorator

def convert_height(height_str: str) -> tuple[float, float]:
    """Convert height from '5' 11"' format to 5.11 and calculate cm"""
    if not height_str or height_str == '--':
        return 0.0, 0.0
    
    try:
        # Extract feet and inches using regex
        match = re.match(r"(\d+)'\s*(\d+)", height_str)
        if match:
            feet, inches = map(int, match.groups())
            # Convert to cm: 1 foot = 30.48 cm, 1 inch = 2.54 cm
            cm = round((feet * 30.48) + (inches * 2.54), 1)
            # Convert to decimal format (e.g., 5'11" -> 5.11)
            decimal_height = float(f"{feet}.{inches:02d}")
            return decimal_height, cm
    except (ValueError, AttributeError):
        pass
    return 0.0, 0.0

def convert_weight(weight_str: str) -> tuple[float, float]:
    """Convert weight from 'X lbs.' format to numeric values"""
    if not weight_str or weight_str == '--':
        return 0.0, 0.0
    
    try:
        # Extract numeric value
        lbs = float(weight_str.replace('lbs.', '').strip())
        # Convert to kg
        kg = round(lbs * 0.453592, 1)
        return lbs, kg
    except ValueError:
        return 0.0, 0.0

def convert_reach(reach_str: str) -> tuple[float, float]:
    """Convert reach from 'XX"' format to numeric values and calculate cm"""
    if not reach_str or reach_str == '--':
        return 0.0, 0.0
    
    try:
        # Extract numeric value (e.g., '72.0"' -> 72.0)
        inches = float(reach_str.replace('"', '').strip())
        # Convert to cm
        cm = round(inches * 2.54, 1)
        return inches, cm
    except ValueError:
        return 0.0, 0.0

def normalize_name(name: str) -> str:
    return unidecode(name).lower()