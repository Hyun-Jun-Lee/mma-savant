"""
Supported Charts 동적 로딩 유틸리티

JSON 파일에서 지원되는 차트 정보를 실시간으로 로드하여
런타임 중 변경사항을 반영할 수 있도록 합니다.
"""

import json
from typing import Dict, Any
from pathlib import Path

def get_supported_charts() -> Dict[str, Any]:
    """
    지원되는 차트 정보를 JSON 파일에서 동적으로 로드
    
    Returns:
        Dict[str, Any]: 차트 ID를 키로 하는 차트 정보 딕셔너리
    """
    try:
        # 현재 파일 위치 기준으로 JSON 파일 경로 구성
        current_dir = Path(__file__).parent
        json_path = current_dir / "supported_charts.json"
        
        with open(json_path, 'r', encoding='utf-8') as f:
            charts = json.load(f)
            
        return charts
        
    except FileNotFoundError:
        # Fallback: 기본 차트 설정 반환
        return {
            "text_summary": {
                "description": "요약 및 인사이트 텍스트",
                "best_for": "복잡한 분석 결과, 텍스트 기반 답변",
                "data_requirements": "임의의 분석 데이터"
            }
        }
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        # Fallback 반환
        return {
            "text_summary": {
                "description": "요약 및 인사이트 텍스트",
                "best_for": "복잡한 분석 결과, 텍스트 기반 답변", 
                "data_requirements": "임의의 분석 데이터"
            }
        }

def get_chart_info(chart_id: str) -> Dict[str, str]:
    """
    특정 차트 ID에 대한 정보 반환
    
    Args:
        chart_id: 차트 식별자
        
    Returns:
        Dict[str, str]: 해당 차트의 정보 딕셔너리
    """
    charts = get_supported_charts()
    return charts.get(chart_id, {})

def get_chart_list() -> list[str]:
    """
    지원되는 모든 차트 ID 목록 반환
    
    Returns:
        list[str]: 차트 ID 리스트
    """
    charts = get_supported_charts()
    return list(charts.keys())

def validate_chart_id(chart_id: str) -> bool:
    """
    차트 ID가 지원되는지 검증
    
    Args:
        chart_id: 검증할 차트 ID
        
    Returns:
        bool: 지원 여부
    """
    return chart_id in get_chart_list()

def get_charts_for_prompt() -> str:
    """
    프롬프트에 포함할 차트 목록을 문자열로 반환
    
    Returns:
        str: 프롬프트용 차트 설명 문자열
    """
    charts = get_supported_charts()
    
    chart_descriptions = []
    for chart_id, info in charts.items():
        description = f"**{chart_id}**: {info['description']}"
        best_for = f"  - 최적 사용: {info['best_for']}"
        data_req = f"  - 데이터 요구사항: {info['data_requirements']}"
        
        chart_descriptions.append(f"{description}\n{best_for}\n{data_req}")
    
    return "\n\n".join(chart_descriptions)

def reload_charts() -> Dict[str, Any]:
    """
    차트 설정을 강제로 다시 로드 (디버깅/테스트용)
    
    Returns:
        Dict[str, Any]: 새로 로드된 차트 정보
    """
    return get_supported_charts()