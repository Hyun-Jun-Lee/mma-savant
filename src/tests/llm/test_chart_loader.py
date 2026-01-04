"""
Chart Loader 유틸리티에 대한 단위 테스트

chart_loader.py의 모든 함수에 대한 포괄적인 테스트를 제공합니다.
"""

import pytest
from unittest.mock import patch, mock_open
from llm.chart_loader import (
    get_supported_charts,
    get_chart_info,
    get_chart_list,
    validate_chart_id,
    get_charts_for_prompt,
    reload_charts
)


# =============================================================================
# get_supported_charts() 테스트
# =============================================================================

def test_get_supported_charts_returns_dict_with_expected_charts():
    """지원되는 모든 차트 타입을 포함한 딕셔너리를 반환한다"""
    # Given: 차트 정보를 로드할 때
    # When: get_supported_charts를 호출하면
    result = get_supported_charts()

    # Then: 모든 예상 차트 타입이 포함되어야 한다
    expected_charts = {
        "table", "bar_chart", "pie_chart",
        "line_chart", "scatter_plot", "text_summary"
    }
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_charts


def test_get_supported_charts_each_chart_has_required_fields():
    """각 차트는 필수 필드(description, best_for, data_requirements)를 가진다"""
    # Given: 차트 정보를 로드할 때
    # When: get_supported_charts를 호출하면
    result = get_supported_charts()

    # Then: 각 차트는 필수 필드를 모두 포함해야 한다
    required_fields = {"description", "best_for", "data_requirements"}
    for chart_id, chart_info in result.items():
        assert isinstance(chart_info, dict), f"{chart_id}의 정보가 딕셔너리가 아님"
        assert set(chart_info.keys()) == required_fields, \
            f"{chart_id}에 필수 필드가 누락됨: {required_fields - set(chart_info.keys())}"


def test_get_supported_charts_file_not_found_returns_fallback():
    """JSON 파일이 없으면 text_summary만 포함한 fallback을 반환한다"""
    # Given: JSON 파일이 존재하지 않을 때
    with patch("builtins.open", side_effect=FileNotFoundError()):
        # When: get_supported_charts를 호출하면
        result = get_supported_charts()

        # Then: text_summary만 포함한 fallback이 반환되어야 한다
        assert "text_summary" in result
        assert len(result) == 1
        assert "description" in result["text_summary"]
        assert "best_for" in result["text_summary"]
        assert "data_requirements" in result["text_summary"]


def test_get_supported_charts_json_decode_error_returns_fallback():
    """JSON 파싱 오류 시 text_summary만 포함한 fallback을 반환한다"""
    # Given: 잘못된 JSON 형식의 파일이 있을 때
    with patch("builtins.open", mock_open(read_data="invalid json {")):
        # When: get_supported_charts를 호출하면
        result = get_supported_charts()

        # Then: text_summary만 포함한 fallback이 반환되어야 한다
        assert "text_summary" in result
        assert len(result) == 1
        assert "description" in result["text_summary"]


# =============================================================================
# get_chart_info() 테스트
# =============================================================================

def test_get_chart_info_returns_correct_info_for_table():
    """table 차트 ID로 조회하면 올바른 정보를 반환한다"""
    # Given: table 차트 정보를 조회할 때
    # When: get_chart_info를 호출하면
    result = get_chart_info("table")

    # Then: table의 정보가 반환되어야 한다
    assert isinstance(result, dict)
    assert result["description"] == "행과 열로 구성된 데이터 테이블"
    assert "best_for" in result
    assert "data_requirements" in result


def test_get_chart_info_returns_correct_info_for_bar_chart():
    """bar_chart 차트 ID로 조회하면 올바른 정보를 반환한다"""
    # Given: bar_chart 차트 정보를 조회할 때
    # When: get_chart_info를 호출하면
    result = get_chart_info("bar_chart")

    # Then: bar_chart의 정보가 반환되어야 한다
    assert isinstance(result, dict)
    assert result["description"] == "카테고리별 수치를 막대로 표현"
    assert "best_for" in result
    assert "data_requirements" in result


def test_get_chart_info_returns_empty_dict_for_nonexistent_chart():
    """존재하지 않는 차트 ID로 조회하면 빈 딕셔너리를 반환한다"""
    # Given: 존재하지 않는 차트 ID로 조회할 때
    # When: get_chart_info를 호출하면
    result = get_chart_info("nonexistent_chart")

    # Then: 빈 딕셔너리가 반환되어야 한다
    assert result == {}


# =============================================================================
# get_chart_list() 테스트
# =============================================================================

def test_get_chart_list_returns_list():
    """차트 목록을 리스트 타입으로 반환한다"""
    # Given: 차트 목록을 조회할 때
    # When: get_chart_list를 호출하면
    result = get_chart_list()

    # Then: 리스트 타입이 반환되어야 한다
    assert isinstance(result, list)


def test_get_chart_list_contains_all_expected_charts():
    """모든 예상 차트 타입을 포함한다"""
    # Given: 차트 목록을 조회할 때
    # When: get_chart_list를 호출하면
    result = get_chart_list()

    # Then: 모든 예상 차트가 포함되어야 한다
    expected_charts = {
        "table", "bar_chart", "pie_chart",
        "line_chart", "scatter_plot", "text_summary"
    }
    assert set(result) == expected_charts


def test_get_chart_list_has_correct_length():
    """차트 목록의 길이가 예상 개수(6개)와 일치한다"""
    # Given: 차트 목록을 조회할 때
    # When: get_chart_list를 호출하면
    result = get_chart_list()

    # Then: 6개의 차트가 있어야 한다
    assert len(result) == 6


# =============================================================================
# validate_chart_id() 테스트
# =============================================================================

def test_validate_chart_id_returns_true_for_table():
    """table 차트 ID는 유효하다고 반환한다"""
    # Given: table 차트 ID를 검증할 때
    # When: validate_chart_id를 호출하면
    result = validate_chart_id("table")

    # Then: True가 반환되어야 한다
    assert result is True


def test_validate_chart_id_returns_true_for_text_summary():
    """text_summary 차트 ID는 유효하다고 반환한다"""
    # Given: text_summary 차트 ID를 검증할 때
    # When: validate_chart_id를 호출하면
    result = validate_chart_id("text_summary")

    # Then: True가 반환되어야 한다
    assert result is True


def test_validate_chart_id_returns_false_for_nonexistent_chart():
    """존재하지 않는 차트 ID는 유효하지 않다고 반환한다"""
    # Given: 존재하지 않는 차트 ID를 검증할 때
    # When: validate_chart_id를 호출하면
    result = validate_chart_id("nonexistent_chart")

    # Then: False가 반환되어야 한다
    assert result is False


def test_validate_chart_id_returns_false_for_empty_string():
    """빈 문자열 차트 ID는 유효하지 않다고 반환한다"""
    # Given: 빈 문자열로 검증할 때
    # When: validate_chart_id를 호출하면
    result = validate_chart_id("")

    # Then: False가 반환되어야 한다
    assert result is False


# =============================================================================
# get_charts_for_prompt() 테스트
# =============================================================================

def test_get_charts_for_prompt_returns_string():
    """프롬프트용 차트 설명을 문자열로 반환한다"""
    # Given: 프롬프트용 차트 설명을 조회할 때
    # When: get_charts_for_prompt를 호출하면
    result = get_charts_for_prompt()

    # Then: 문자열이 반환되어야 한다
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_charts_for_prompt_contains_all_chart_ids():
    """모든 차트 ID가 프롬프트 문자열에 포함된다"""
    # Given: 프롬프트용 차트 설명을 조회할 때
    # When: get_charts_for_prompt를 호출하면
    result = get_charts_for_prompt()

    # Then: 모든 차트 ID가 포함되어야 한다
    expected_charts = [
        "table", "bar_chart", "pie_chart",
        "line_chart", "scatter_plot", "text_summary"
    ]
    for chart_id in expected_charts:
        assert f"**{chart_id}**" in result, f"{chart_id}가 프롬프트에 포함되지 않음"


def test_get_charts_for_prompt_contains_best_for_text():
    """프롬프트에 '최적 사용:' 텍스트가 포함된다"""
    # Given: 프롬프트용 차트 설명을 조회할 때
    # When: get_charts_for_prompt를 호출하면
    result = get_charts_for_prompt()

    # Then: '최적 사용:' 텍스트가 포함되어야 한다
    assert "최적 사용:" in result


def test_get_charts_for_prompt_contains_data_requirements_text():
    """프롬프트에 '데이터 요구사항:' 텍스트가 포함된다"""
    # Given: 프롬프트용 차트 설명을 조회할 때
    # When: get_charts_for_prompt를 호출하면
    result = get_charts_for_prompt()

    # Then: '데이터 요구사항:' 텍스트가 포함되어야 한다
    assert "데이터 요구사항:" in result


# =============================================================================
# reload_charts() 테스트
# =============================================================================

def test_reload_charts_returns_dict():
    """reload_charts는 딕셔너리를 반환한다"""
    # Given: 차트를 다시 로드할 때
    # When: reload_charts를 호출하면
    result = reload_charts()

    # Then: 딕셔너리가 반환되어야 한다
    assert isinstance(result, dict)


def test_reload_charts_returns_same_data_as_get_supported_charts():
    """reload_charts는 get_supported_charts와 동일한 데이터를 반환한다"""
    # Given: 차트를 다시 로드할 때
    # When: reload_charts와 get_supported_charts를 각각 호출하면
    reload_result = reload_charts()
    get_result = get_supported_charts()

    # Then: 두 결과가 동일해야 한다
    assert reload_result == get_result
    assert set(reload_result.keys()) == set(get_result.keys())
