"""
스트림 프로세서 유닛 테스트
stream_processor.py의 모든 함수에 대한 포괄적인 테스트
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from llm.stream_processor import (
    extract_safe_text_content,
    process_agent_chunk,
    extract_tool_results,
    clean_response_content,
    create_final_result,
    create_error_response,
    create_streaming_chunk,
    validate_streaming_chunk,
    get_chunk_statistics,
)


# ==============================================================================
# extract_safe_text_content 테스트 (10개)
# ==============================================================================

def test_extract_safe_text_content_string_input():
    """문자열 입력은 그대로 반환"""
    # Given: 단순 문자열
    content = "Simple string content"

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 그대로 반환
    assert result == "Simple string content"


def test_extract_safe_text_content_dict_with_content_field():
    """딕셔너리의 'content' 필드에서 텍스트 추출"""
    # Given: content 필드를 가진 딕셔너리
    content = {"content": "Text from content field"}

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: content 필드 값 반환
    assert result == "Text from content field"


def test_extract_safe_text_content_dict_with_text_field():
    """딕셔너리의 'text' 필드에서 텍스트 추출"""
    # Given: text 필드를 가진 딕셔너리
    content = {"text": "Text from text field"}

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: text 필드 값 반환
    assert result == "Text from text field"


def test_extract_safe_text_content_dict_with_message_field():
    """딕셔너리의 'message' 필드에서 텍스트 추출"""
    # Given: message 필드를 가진 딕셔너리
    content = {"message": "Text from message field"}

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: message 필드 값 반환
    assert result == "Text from message field"


def test_extract_safe_text_content_tool_use_type_returns_empty():
    """type이 'tool_use'인 딕셔너리는 빈 문자열 반환"""
    # Given: tool_use 타입의 딕셔너리
    content = {"type": "tool_use", "id": "tool_123"}

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 빈 문자열 반환
    assert result == ""


def test_extract_safe_text_content_input_json_delta_type_returns_empty():
    """type이 'input_json_delta'인 딕셔너리는 빈 문자열 반환"""
    # Given: input_json_delta 타입의 딕셔너리
    content = {"type": "input_json_delta", "delta": "some_data"}

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 빈 문자열 반환
    assert result == ""


def test_extract_safe_text_content_tool_id_starting_with_toolu_returns_empty():
    """id가 'toolu_'로 시작하는 딕셔너리는 빈 문자열 반환"""
    # Given: toolu_로 시작하는 id를 가진 딕셔너리
    content = {"id": "toolu_abc123xyz"}

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 빈 문자열 반환
    assert result == ""


def test_extract_safe_text_content_list_input_joins_text():
    """리스트 입력은 각 항목의 텍스트를 추출하여 합침"""
    # Given: 여러 타입의 항목을 가진 리스트
    content = ["First", {"content": "Second"}, "Third"]

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 모든 텍스트가 합쳐짐
    assert result == "FirstSecondThird"


def test_extract_safe_text_content_none_input_returns_empty():
    """None 입력은 빈 문자열 반환"""
    # Given: None 값
    content = None

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 빈 문자열 반환
    assert result == ""


def test_extract_safe_text_content_integer_converts_to_string():
    """정수 입력은 문자열로 변환"""
    # Given: 정수 값
    content = 42

    # When: 텍스트 추출
    result = extract_safe_text_content(content)

    # Then: 문자열로 변환
    assert result == "42"


# ==============================================================================
# process_agent_chunk 테스트 (5개)
# ==============================================================================

def test_process_agent_chunk_with_output_key():
    """'output' 키를 가진 청크는 type='content' 반환"""
    # Given: output 키를 가진 청크
    chunk = {"output": "Agent output text"}

    # When: 청크 처리
    result = process_agent_chunk(chunk)

    # Then: type이 'content'이고 올바른 내용 반환
    assert result["type"] == "content"
    assert result["content"] == "Agent output text"
    assert result["metadata"]["has_output"] is True


def test_process_agent_chunk_with_intermediate_steps_key():
    """'intermediate_steps' 키를 가진 청크는 type='intermediate_steps' 반환"""
    # Given: intermediate_steps 키를 가진 청크
    mock_steps = [("action1", "observation1"), ("action2", "observation2")]
    chunk = {"intermediate_steps": mock_steps}

    # When: 청크 처리
    result = process_agent_chunk(chunk)

    # Then: type이 'intermediate_steps'이고 올바른 메타데이터 반환
    assert result["type"] == "intermediate_steps"
    assert result["content"] == ""
    assert result["metadata"]["steps_count"] == 2
    assert result["metadata"]["steps"] == mock_steps


def test_process_agent_chunk_with_other_dict():
    """기타 딕셔너리 청크는 type='raw_chunk' 반환"""
    # Given: output/intermediate_steps가 아닌 딕셔너리
    chunk = {"some_key": "some_value", "another_key": 123}

    # When: 청크 처리
    result = process_agent_chunk(chunk)

    # Then: type이 'raw_chunk'
    assert result["type"] == "raw_chunk"
    assert "some_key" in result["metadata"]["keys"]
    assert "another_key" in result["metadata"]["keys"]


def test_process_agent_chunk_with_non_dict():
    """딕셔너리가 아닌 청크는 type='raw_content' 반환"""
    # Given: 문자열 청크
    chunk = "Simple string chunk"

    # When: 청크 처리
    result = process_agent_chunk(chunk)

    # Then: type이 'raw_content'
    assert result["type"] == "raw_content"
    assert result["content"] == "Simple string chunk"
    assert result["metadata"]["original_type"] == "str"


def test_process_agent_chunk_includes_original_type_in_metadata():
    """메타데이터에 original_type 포함"""
    # Given: output을 가진 딕셔너리
    chunk = {"output": {"content": "nested content"}}

    # When: 청크 처리
    result = process_agent_chunk(chunk)

    # Then: metadata에 original_type 포함
    assert "original_type" in result["metadata"]
    assert result["metadata"]["original_type"] == "dict"


# ==============================================================================
# extract_tool_results 테스트 (4개)
# ==============================================================================

@patch('llm.stream_processor.remove_timestamps_from_tool_result')
def test_extract_tool_results_valid_steps(mock_remove_timestamps):
    """유효한 intermediate_steps에서 tool_results 올바르게 추출"""
    # Given: 유효한 intermediate_steps
    mock_remove_timestamps.side_effect = lambda x: x  # 그대로 반환

    class MockAction:
        def __init__(self, tool, tool_input):
            self.tool = tool
            self.tool_input = tool_input

    steps = [
        (MockAction("search_tool", "query1"), "observation1"),
        (MockAction("analyze_tool", {"param": "value"}), "observation2")
    ]

    # When: tool_results 추출
    results = extract_tool_results(steps)

    # Then: 올바른 tool_results 반환
    assert len(results) == 2
    assert results[0]["tool"] == "search_tool"
    assert results[0]["input"] == "query1"
    assert results[0]["result"] == "observation1"
    assert results[1]["tool"] == "analyze_tool"


@patch('llm.stream_processor.remove_timestamps_from_tool_result')
def test_extract_tool_results_empty_list(mock_remove_timestamps):
    """빈 리스트는 빈 리스트 반환"""
    # Given: 빈 intermediate_steps
    steps = []

    # When: tool_results 추출
    results = extract_tool_results(steps)

    # Then: 빈 리스트 반환
    assert results == []


@patch('llm.stream_processor.remove_timestamps_from_tool_result')
def test_extract_tool_results_invalid_step_continues_processing(mock_remove_timestamps):
    """잘못된 형식의 step이 있어도 처리 계속"""
    # Given: 일부 유효하지 않은 step을 포함한 리스트
    mock_remove_timestamps.side_effect = lambda x: x

    class MockAction:
        def __init__(self, tool, tool_input):
            self.tool = tool
            self.tool_input = tool_input

    steps = [
        (MockAction("valid_tool", "input1"), "observation1"),
        ("invalid_step",),  # 잘못된 형식
        (MockAction("another_tool", "input2"), "observation2")
    ]

    # When: tool_results 추출
    results = extract_tool_results(steps)

    # Then: 유효한 step들만 처리
    assert len(results) == 2
    assert results[0]["tool"] == "valid_tool"
    assert results[1]["tool"] == "another_tool"


@patch('llm.stream_processor.remove_timestamps_from_tool_result')
def test_extract_tool_results_step_with_less_than_two_elements(mock_remove_timestamps):
    """2개 미만의 요소를 가진 단계는 건너뜀"""
    # Given: 요소가 부족한 단계를 포함한 steps
    mock_remove_timestamps.side_effect = lambda x: x

    class MockAction:
        def __init__(self, tool, tool_input):
            self.tool = tool
            self.tool_input = tool_input

    steps = [
        (MockAction("tool1", "input1"), "result1"),
        ("single_element",),
        (MockAction("tool2", "input2"), "result2"),
    ]

    # When: tool_results 추출
    results = extract_tool_results(steps)

    # Then: 유효한 단계만 처리됨
    assert len(results) == 2


# ==============================================================================
# clean_response_content 테스트 (4개)
# ==============================================================================

def test_clean_response_content_string_is_stripped():
    """문자열 콘텐츠는 공백이 제거됨"""
    # Given: 앞뒤 공백이 있는 문자열
    content = "  Content with spaces  \n"

    # When: 콘텐츠 정리
    result = clean_response_content(content)

    # Then: 공백 제거됨
    assert result == "Content with spaces"


def test_clean_response_content_non_string_extracted():
    """문자열이 아닌 콘텐츠는 추출됨"""
    # Given: 딕셔너리 콘텐츠
    content = {"content": "Extracted text"}

    # When: 콘텐츠 정리
    result = clean_response_content(content)

    # Then: 텍스트 추출됨
    assert result == "Extracted text"


def test_clean_response_content_empty_string_returns_empty():
    """빈 문자열은 빈 문자열 반환"""
    # Given: 빈 문자열
    content = ""

    # When: 콘텐츠 정리
    result = clean_response_content(content)

    # Then: 빈 문자열 반환
    assert result == ""


def test_clean_response_content_none_returns_empty():
    """None은 빈 문자열 반환"""
    # Given: None
    content = None

    # When: 콘텐츠 정리
    result = clean_response_content(content)

    # Then: 빈 문자열 반환
    assert result == ""


# ==============================================================================
# create_final_result 테스트 (4개)
# ==============================================================================

@patch('llm.stream_processor.utc_now')
def test_create_final_result_with_required_fields(mock_time):
    """필수 필드를 포함한 최종 결과 생성"""
    # Given: 필수 파라미터들
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    content = "Final response content"
    tool_results = [{"tool": "search", "result": "found"}]
    message_id = "msg_123"
    conversation_id = 456
    execution_time = 1.5

    # When: 최종 결과 생성
    result = create_final_result(
        content=content,
        tool_results=tool_results,
        message_id=message_id,
        conversation_id=conversation_id,
        execution_time=execution_time
    )

    # Then: 모든 필수 필드 포함
    assert result["type"] == "final_result"
    assert result["content"] == content
    assert result["tool_results"] == tool_results
    assert result["message_id"] == message_id
    assert result["conversation_id"] == conversation_id
    assert result["execution_time"] == execution_time
    assert "timestamp" in result
    assert "metadata" in result


@patch('llm.stream_processor.utc_now')
def test_create_final_result_includes_user_id_when_provided(mock_time):
    """user_id가 제공되면 포함됨"""
    # Given: user_id를 포함한 파라미터들
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)

    # When: user_id와 함께 최종 결과 생성
    result = create_final_result(
        content="content",
        tool_results=[],
        message_id="msg_123",
        conversation_id=456,
        execution_time=1.0,
        user_id=789
    )

    # Then: user_id 포함
    assert result["user_id"] == 789


@patch('llm.stream_processor.utc_now')
def test_create_final_result_metadata_includes_correct_counts(mock_time):
    """메타데이터에 올바른 카운트 포함"""
    # Given: 콘텐츠와 tool_results
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    content = "Test content"
    tool_results = [{"tool": "tool1"}, {"tool": "tool2"}]

    # When: 최종 결과 생성
    result = create_final_result(
        content=content,
        tool_results=tool_results,
        message_id="msg_123",
        conversation_id=456,
        execution_time=1.0
    )

    # Then: 메타데이터에 올바른 카운트
    assert result["metadata"]["content_length"] == len(content)
    assert result["metadata"]["tools_used_count"] == 2
    assert result["metadata"]["has_tools"] is True


@patch('llm.stream_processor.utc_now')
def test_create_final_result_additional_kwargs_in_metadata(mock_time):
    """추가 kwargs가 메타데이터에 포함됨"""
    # Given: 추가 kwargs
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)

    # When: 추가 kwargs와 함께 최종 결과 생성
    result = create_final_result(
        content="content",
        tool_results=[],
        message_id="msg_123",
        conversation_id=456,
        execution_time=1.0,
        custom_field="custom_value",
        another_field=123
    )

    # Then: 메타데이터에 추가 kwargs 포함
    assert result["metadata"]["custom_field"] == "custom_value"
    assert result["metadata"]["another_field"] == 123


# ==============================================================================
# create_error_response 테스트 (4개)
# ==============================================================================

@patch('llm.stream_processor.utc_now')
def test_create_error_response_correct_structure(mock_time):
    """올바른 구조의 에러 응답 생성"""
    # Given: 에러와 기본 정보
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    error = ValueError("Test error message")
    message_id = "msg_123"
    conversation_id = 456

    # When: 에러 응답 생성
    result = create_error_response(
        error=error,
        message_id=message_id,
        conversation_id=conversation_id
    )

    # Then: 올바른 구조
    assert result["type"] == "error"
    assert result["error"] == "Test error message"
    assert result["message_id"] == message_id
    assert result["conversation_id"] == conversation_id
    assert "timestamp" in result
    assert result["metadata"]["error_type"] == "ValueError"


@patch('llm.stream_processor.utc_now')
def test_create_error_response_rate_limit_429_special_message(mock_time):
    """429 에러는 특별한 메시지 반환"""
    # Given: 429를 포함한 에러 메시지
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    error = Exception("Error 429: Too many requests")

    # When: 에러 응답 생성
    result = create_error_response(
        error=error,
        message_id="msg_123",
        conversation_id=456
    )

    # Then: 사용자 친화적 메시지
    assert result["error"] == "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."


@patch('llm.stream_processor.utc_now')
def test_create_error_response_rate_limit_error_text_special_message(mock_time):
    """'rate_limit_error' 텍스트를 포함한 에러는 특별한 메시지 반환"""
    # Given: rate_limit_error를 포함한 에러
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    error = Exception("rate_limit_error: exceeded quota")

    # When: 에러 응답 생성
    result = create_error_response(
        error=error,
        message_id="msg_123",
        conversation_id=456
    )

    # Then: 사용자 친화적 메시지
    assert result["error"] == "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."


@patch('llm.stream_processor.utc_now')
def test_create_error_response_context_included_in_metadata(mock_time):
    """context가 메타데이터에 포함됨"""
    # Given: context를 포함한 파라미터
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    error = Exception("Test error")
    context = {"user_action": "query", "attempt": 2}

    # When: context와 함께 에러 응답 생성
    result = create_error_response(
        error=error,
        message_id="msg_123",
        conversation_id=456,
        context=context
    )

    # Then: 메타데이터에 context 포함
    assert result["metadata"]["context"] == context


# ==============================================================================
# create_streaming_chunk 테스트 (3개)
# ==============================================================================

@patch('llm.stream_processor.utc_now')
def test_create_streaming_chunk_correct_structure(mock_time):
    """올바른 구조의 스트리밍 청크 생성"""
    # Given: 청크 정보
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)
    chunk_type = "content"
    content = "Streaming content"
    message_id = "msg_123"
    conversation_id = 456

    # When: 스트리밍 청크 생성
    result = create_streaming_chunk(
        chunk_type=chunk_type,
        content=content,
        message_id=message_id,
        conversation_id=conversation_id
    )

    # Then: 올바른 구조
    assert result["type"] == chunk_type
    assert result["content"] == content
    assert result["message_id"] == message_id
    assert result["conversation_id"] == conversation_id
    assert "timestamp" in result


@patch('llm.stream_processor.utc_now')
def test_create_streaming_chunk_includes_metadata_kwargs(mock_time):
    """메타데이터 kwargs 포함"""
    # Given: 추가 메타데이터
    mock_time.return_value = datetime(2024, 1, 15, 12, 0, 0)

    # When: 메타데이터와 함께 청크 생성
    result = create_streaming_chunk(
        chunk_type="content",
        content="test",
        message_id="msg_123",
        conversation_id=456,
        tool_name="search",
        step_number=1
    )

    # Then: 메타데이터에 kwargs 포함
    assert result["metadata"]["tool_name"] == "search"
    assert result["metadata"]["step_number"] == 1


@patch('llm.stream_processor.utc_now')
def test_create_streaming_chunk_timestamp_included(mock_time):
    """타임스탬프 포함"""
    # Given: 모킹된 시간
    mock_time.return_value = datetime(2024, 1, 15, 12, 30, 45)

    # When: 청크 생성
    result = create_streaming_chunk(
        chunk_type="content",
        content="test",
        message_id="msg_123",
        conversation_id=456
    )

    # Then: 타임스탬프 포함
    assert result["timestamp"] == "2024-01-15T12:30:45"


# ==============================================================================
# validate_streaming_chunk 테스트 (5개)
# ==============================================================================

def test_validate_streaming_chunk_valid_chunk_returns_true():
    """유효한 청크는 True 반환"""
    # Given: 유효한 청크
    chunk = {
        "type": "content",
        "content": "test content",
        "message_id": "msg_123",
        "conversation_id": 456,
        "timestamp": "2024-01-15T12:00:00"
    }

    # When: 청크 유효성 검사
    result = validate_streaming_chunk(chunk)

    # Then: True 반환
    assert result is True


def test_validate_streaming_chunk_missing_required_field_returns_false():
    """필수 필드 누락 시 False 반환"""
    # Given: message_id가 누락된 청크
    chunk = {
        "type": "content",
        "content": "test",
        "conversation_id": 456,
        "timestamp": "2024-01-15T12:00:00"
    }

    # When: 청크 유효성 검사
    result = validate_streaming_chunk(chunk)

    # Then: False 반환
    assert result is False


def test_validate_streaming_chunk_non_dict_returns_false():
    """딕셔너리가 아닌 청크는 False 반환"""
    # Given: 문자열 청크
    chunk = "not a dict"

    # When: 청크 유효성 검사
    result = validate_streaming_chunk(chunk)

    # Then: False 반환
    assert result is False


def test_validate_streaming_chunk_content_type_with_non_string_content_returns_false():
    """type='content'이지만 content가 문자열이 아니면 False 반환"""
    # Given: content가 정수인 청크
    chunk = {
        "type": "content",
        "content": 123,  # 문자열이 아님
        "message_id": "msg_123",
        "conversation_id": 456,
        "timestamp": "2024-01-15T12:00:00"
    }

    # When: 청크 유효성 검사
    result = validate_streaming_chunk(chunk)

    # Then: False 반환
    assert result is False


def test_validate_streaming_chunk_content_type_with_string_content_returns_true():
    """type='content'이고 content가 문자열이면 True 반환"""
    # Given: 유효한 content 청크
    chunk = {
        "type": "content",
        "content": "valid string content",
        "message_id": "msg_123",
        "conversation_id": 456,
        "timestamp": "2024-01-15T12:00:00"
    }

    # When: 청크 유효성 검사
    result = validate_streaming_chunk(chunk)

    # Then: True 반환
    assert result is True


# ==============================================================================
# get_chunk_statistics 테스트 (5개)
# ==============================================================================

def test_get_chunk_statistics_empty_list_returns_zero():
    """빈 리스트는 total_chunks=0 반환"""
    # Given: 빈 청크 리스트
    chunks = []

    # When: 통계 생성
    stats = get_chunk_statistics(chunks)

    # Then: total_chunks만 0으로 반환
    assert stats == {"total_chunks": 0}


def test_get_chunk_statistics_counts_chunk_types_correctly():
    """청크 타입별 카운트 올바르게 계산"""
    # Given: 다양한 타입의 청크들
    chunks = [
        {"type": "content", "content": "text1"},
        {"type": "content", "content": "text2"},
        {"type": "tool_start", "content": ""},
        {"type": "tool_end", "content": ""},
        {"type": "content", "content": "text3"}
    ]

    # When: 통계 생성
    stats = get_chunk_statistics(chunks)

    # Then: 타입별 카운트 올바름
    assert stats["total_chunks"] == 5
    assert stats["chunk_types"]["content"] == 3
    assert stats["chunk_types"]["tool_start"] == 1
    assert stats["chunk_types"]["tool_end"] == 1


def test_get_chunk_statistics_calculates_total_content_length():
    """전체 콘텐츠 길이 계산"""
    # Given: 콘텐츠를 가진 청크들
    chunks = [
        {"type": "content", "content": "12345"},      # 5자
        {"type": "content", "content": "abcdefg"},    # 7자
        {"type": "content", "content": "xyz"}         # 3자
    ]

    # When: 통계 생성
    stats = get_chunk_statistics(chunks)

    # Then: 전체 길이 올바름
    assert stats["total_content_length"] == 15


def test_get_chunk_statistics_calculates_average_chunk_size():
    """평균 청크 크기 계산"""
    # Given: 다양한 크기의 청크들
    chunks = [
        {"type": "content", "content": "12345"},      # 5자
        {"type": "content", "content": "abcdefghij"}, # 10자
        {"type": "content", "content": "xyz"}         # 3자
    ]

    # When: 통계 생성
    stats = get_chunk_statistics(chunks)

    # Then: 평균 크기 올바름 (5+10+3)/3 = 6
    assert stats["average_chunk_size"] == 6.0


def test_get_chunk_statistics_tracks_first_and_last_chunk_times():
    """첫 번째와 마지막 청크 시간 추적"""
    # Given: 타임스탬프를 가진 청크들
    chunks = [
        {"type": "content", "content": "a", "timestamp": "2024-01-15T12:00:00"},
        {"type": "content", "content": "b", "timestamp": "2024-01-15T12:00:05"},
        {"type": "content", "content": "c", "timestamp": "2024-01-15T12:00:10"}
    ]

    # When: 통계 생성
    stats = get_chunk_statistics(chunks)

    # Then: 첫 번째와 마지막 시간 올바름
    assert stats["first_chunk_time"] == "2024-01-15T12:00:00"
    assert stats["last_chunk_time"] == "2024-01-15T12:00:10"
