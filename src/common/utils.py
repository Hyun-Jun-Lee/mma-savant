import re
import json
import logging
import os
from typing import Callable, Dict
from functools import wraps
from unidecode import unidecode
from datetime import datetime, timezone, timedelta

def kr_time_now() -> datetime:
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).replace(tzinfo=None)

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

def remove_timestamps_from_tool_result(tool_result):
    """Tool 결과에서 created_at, updated_at 타임스탬프 필드를 제거한 정리된 데이터 반환
    
    Args:
        tool_result: dict, list[dict], 또는 JSON 문자열 - Tool 결과 데이터
        
    Returns:
        dict, list[dict], 또는 정리된 JSON 문자열 - 타임스탬프가 제거된 정리된 데이터
    """
    # 문자열인 경우 JSON 파싱 시도
    if isinstance(tool_result, str):
        try:
            parsed_data = json.loads(tool_result)
            # 파싱된 데이터를 정리 후 다시 JSON 문자열로 변환
            cleaned_data = remove_timestamps_from_tool_result(parsed_data)
            return json.dumps(cleaned_data, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            # JSON이 아닌 일반 문자열은 그대로 반환
            return tool_result
    
    elif isinstance(tool_result, list):
        # 리스트인 경우: 각 딕셔너리에서 타임스탬프 제거
        cleaned_results = []
        for item in tool_result:
            if isinstance(item, dict):
                item_copy = item.copy()
                item_copy.pop('created_at', None)
                item_copy.pop('updated_at', None)
                cleaned_results.append(item_copy)
            else:
                cleaned_results.append(item)
        return cleaned_results
    
    elif isinstance(tool_result, dict):
        # 딕셔너리인 경우: 타임스탬프 필드 제거
        tool_result_copy = tool_result.copy()
        tool_result_copy.pop('created_at', None)
        tool_result_copy.pop('updated_at', None)
        return tool_result_copy
    
    else:
        # 기타 타입인 경우 그대로 반환
        return tool_result


def load_schema_prompt() -> str:
    """
    프롬프트용 스키마 정보를 로드합니다. 전체 schema.json을 사용하여 포괄적인 데이터베이스 정보 제공.
    
    Returns:
        str: 프롬프트용 스키마 텍스트, 로드 실패 시 fallback 텍스트
    """
    try:
        # src/schema.json 경로 계산 (현재 파일 기준)
        current_dir = os.path.dirname(__file__)  # src/common
        schema_path = os.path.join(current_dir, '..', 'schema.json')  # src/schema.json
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
            
        # schema.json을 프롬프트용 텍스트로 변환
        return format_schema_for_prompt(schema_data)
        
    except Exception as e:
        logging.error(f"Error loading schema prompt: {e}")
        raise e


def format_schema_for_prompt(schema_data: Dict) -> str:
    """
    schema.json 데이터를 프롬프트용 텍스트로 변환합니다.
    
    Args:
        schema_data: schema.json의 파싱된 데이터
    
    Returns:
        str: 프롬프트용으로 포맷된 스키마 정보
    """
    lines = []
    
    # Database info section
    db_info = schema_data.get('database_info', {})
    lines.append("## Database Schema Information")
    lines.append("")
    lines.append(f"**Database**: {db_info.get('name', 'MMA Database')}")
    lines.append(f"**Naming Convention**: {db_info.get('naming_convention', 'singular_table_names')}")
    lines.append("")
    
    # Important notes
    important_notes = db_info.get('important_notes', [])
    if important_notes:
        lines.append("**Critical Rules**:")
        for note in important_notes:
            lines.append(f"- {note}")
        lines.append("- **DATA CASE SENSITIVITY**: All text data stored in lowercase")
        lines.append("")
    
    # Tables section
    tables = schema_data.get('tables', {})
    lines.append("### Tables and Relationships:")
    lines.append("")
    
    for table_name, table_info in tables.items():
        lines.append(f"**{table_name}**: {table_info.get('description', 'No description')}")
        
        # Relationships
        relationships = table_info.get('relationships', {})
        if relationships:
            lines.append("  - Relationships:")
            for rel_table, rel_desc in relationships.items():
                lines.append(f"    - {rel_table}: {rel_desc}")
        
        # All columns
        columns = table_info.get('columns', [])
        all_columns = []
        for col in columns:
            col_name = col.get('column', '')
            col_type = col.get('type', '')
            nullable = col.get('nullable', True)
            description = col.get('description', '')
            
            # Include all columns with complete information
            nullable_text = " (NOT NULL)" if not nullable else ""
            all_columns.append(f"{col_name} ({col_type}){nullable_text} - {description}")
        
        if all_columns:
            lines.append("  - Columns:")
            for col_desc in all_columns:
                lines.append(f"    - {col_desc}")
        
        lines.append("")
    
    lines.append("**Remember**: Always use SINGULAR table names (match, fighter, event, NOT matches, fighters, events)")
    
    return '\n'.join(lines)