"""
스트리밍 응답 처리 및 텍스트 추출
LangChain Agent의 출력을 안전하게 처리하고 정제하는 함수들
"""
from typing import Dict, Any, List, Union, Optional
from datetime import datetime

from common.logging_config import get_logger
from common.utils import remove_timestamps_from_tool_result, kr_time_now

LOGGER = get_logger(__name__)


def extract_safe_text_content(content: Any) -> str:
    """
    LangChain Agent 출력에서 안전하게 텍스트 추출
    Anthropic 토큰 형태와 기타 구조화된 데이터를 필터링
    
    Args:
        content: 추출할 콘텐츠 (str, dict, list 등)
        
    Returns:
        str: 추출된 텍스트 콘텐츠
    """
    if isinstance(content, str):
        return content
    
    elif isinstance(content, dict):
        # Anthropic 토큰 형태 필터링
        if content.get('type') in ['tool_use', 'input_json_delta', 'tool_call', 'function_call']:
            LOGGER.debug(f"🔧 Filtered tool-related token: {content.get('type')}")
            return ""
        
        # 툴 ID 토큰 필터링
        if 'id' in content and str(content.get('id', '')).startswith('toolu_'):
            LOGGER.debug(f"🔧 Filtered tool ID token: {content.get('id')}")
            return ""
        
        # 표준 텍스트 필드들 확인 (우선순위 순)
        for text_field in ['content', 'text', 'message']:
            if text_field in content:
                text_value = content[text_field]
                if isinstance(text_value, str):
                    return text_value
                else:
                    # 재귀적으로 처리
                    return extract_safe_text_content(text_value)
        
        # 알려진 구조화된 형태들 로깅
        if 'type' in content and 'index' in content:
            LOGGER.debug(f"🔍 Skipped structured token: {content}")
            return ""
        
        # 기타 딕셔너리는 문자열로 변환 (마지막 수단)
        LOGGER.debug(f"⚠️ Unknown dict structure converted to string: {content}")
        return str(content)
    
    elif isinstance(content, list):
        # 리스트인 경우 각 항목에서 텍스트 추출하여 합침
        texts = []
        for item in content:
            extracted = extract_safe_text_content(item)
            if extracted:
                texts.append(extracted)
        return ''.join(texts)
    
    else:
        # 기타 타입은 문자열로 변환
        return str(content) if content is not None else ""


def process_agent_chunk(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    에이전트 청크 처리 및 정규화
    
    Args:
        chunk: Agent executor에서 받은 청크
        
    Returns:
        Dict: 처리된 청크 정보
    """
    processed_chunk = {
        "type": "unknown",
        "content": "",
        "metadata": {}
    }
    
    try:
        if isinstance(chunk, dict):
            # 출력 청크 처리
            if "output" in chunk:
                content = chunk["output"]
                extracted_text = extract_safe_text_content(content)
                processed_chunk.update({
                    "type": "content",
                    "content": extracted_text,
                    "metadata": {
                        "original_type": type(content).__name__,
                        "has_output": True
                    }
                })
            
            # 중간 단계 처리
            elif "intermediate_steps" in chunk:
                steps = chunk["intermediate_steps"]
                processed_chunk.update({
                    "type": "intermediate_steps",
                    "content": "",
                    "metadata": {
                        "steps_count": len(steps),
                        "steps": steps
                    }
                })
            
            # 기타 청크 타입
            else:
                processed_chunk.update({
                    "type": "raw_chunk",
                    "content": extract_safe_text_content(chunk),
                    "metadata": {
                        "keys": list(chunk.keys()) if isinstance(chunk, dict) else [],
                        "original_type": type(chunk).__name__
                    }
                })
        
        else:
            # 비-딕셔너리 청크 처리
            processed_chunk.update({
                "type": "raw_content",
                "content": extract_safe_text_content(chunk),
                "metadata": {
                    "original_type": type(chunk).__name__
                }
            })
    
    except Exception as e:
        LOGGER.error(f"❌ Error processing chunk: {e}")
        processed_chunk.update({
            "type": "error",
            "content": "",
            "metadata": {
                "error": str(e),
                "original_chunk": str(chunk)[:100] + "..." if len(str(chunk)) > 100 else str(chunk)
            }
        })
    
    return processed_chunk


def extract_tool_results(intermediate_steps: List[Any]) -> List[Dict[str, Any]]:
    """
    중간 단계에서 도구 결과 추출
    v1 호환성을 위해 단순화된 로직 사용
    
    Args:
        intermediate_steps: Agent executor의 intermediate_steps
        
    Returns:
        List[Dict]: 추출된 도구 결과들
    """
    tool_results = []
    
    try:
        LOGGER.info(f"🔧 Found intermediate_steps: {len(intermediate_steps)} steps")
        
        for step in intermediate_steps:
            try:
                if len(step) >= 2:
                    action, observation = step
                    
                    # v1과 동일한 로직으로 간단하게 처리
                    tool_result = {
                        "tool": getattr(action, 'tool', 'unknown'),
                        "input": str(action.tool_input),
                        "result": str(remove_timestamps_from_tool_result(observation))
                    }
                    tool_results.append(tool_result)
                    
            except Exception as e:
                LOGGER.error(f"❌ Error processing individual step: {e}")
                # 에러가 있어도 계속 처리
                continue
        
        LOGGER.info(f"✅ Extracted {len(tool_results)} tool results")
        return tool_results
        
    except Exception as e:
        LOGGER.error(f"❌ Error extracting tool results: {e}")
        return []


def clean_response_content(content: Any) -> str:
    """
    응답 콘텐츠 정리 및 검증
    
    Args:
        content: 정리할 콘텐츠
        
    Returns:
        str: 정리된 텍스트 콘텐츠
    """
    try:
        if isinstance(content, str):
            cleaned = content.strip()
        else:
            LOGGER.warning(f"⚠️ Non-string response_content: {type(content)} - {content}")
            cleaned = extract_safe_text_content(content)
        
        # 빈 콘텐츠 확인
        if not cleaned:
            LOGGER.warning("⚠️ Empty response content after cleaning")
            return ""
        
        # 콘텐츠 길이 로깅
        LOGGER.debug(f"📝 Cleaned content length: {len(cleaned)} characters")
        
        return cleaned
        
    except Exception as e:
        LOGGER.error(f"❌ Error cleaning response content: {e}")
        return ""


def create_final_result(
    content: str,
    tool_results: List[Dict[str, Any]],
    message_id: str,
    conversation_id : int,
    execution_time: float,
    user_id: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    최종 결과 객체 생성
    
    Args:
        content: 최종 응답 콘텐츠
        tool_results: 도구 실행 결과들
        message_id: 메시지 ID
        conversation_id: 세션 ID
        execution_time: 실행 시간 (초)
        **kwargs: 추가 메타데이터
        
    Returns:
        Dict: 최종 결과 객체
    """
    result = {
        "type": "final_result",
        "content": content,
        "tool_results": tool_results,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "timestamp": kr_time_now().isoformat(),
        "execution_time": execution_time,
        "metadata": {
            "content_length": len(content),
            "tools_used_count": len(tool_results),
            "has_tools": len(tool_results) > 0,
            **kwargs
        }
    }
    
    # user_id가 있으면 포함
    if user_id is not None:
        result["user_id"] = user_id
    
    return result


def create_error_response(
    error: Exception,
    message_id: str,
    conversation_id : int,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    에러 응답 객체 생성
    
    Args:
        error: 발생한 에러
        message_id: 메시지 ID
        conversation_id: 세션 ID  
        context: 에러 발생 컨텍스트
        **kwargs: 추가 메타데이터
        
    Returns:
        Dict: 에러 응답 객체
    """
    error_message = str(error)
    
    # 특별한 에러 타입 처리
    if "rate_limit_error" in error_message or "429" in error_message:
        LOGGER.warning("🚫 Rate limit exceeded")
        user_friendly_message = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
    else:
        user_friendly_message = error_message
    
    return {
        "type": "error",
        "error": user_friendly_message,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "timestamp": kr_time_now().isoformat(),
        "metadata": {
            "error_type": type(error).__name__,
            "original_error": error_message,
            "context": context or {},
            **kwargs
        }
    }


def create_streaming_chunk(
    chunk_type: str,
    content: str,
    message_id: str,
    conversation_id : int,
    **metadata
) -> Dict[str, Any]:
    """
    스트리밍 청크 객체 생성
    
    Args:
        chunk_type: 청크 타입 (content, tool_start, tool_end 등)
        content: 청크 콘텐츠
        message_id: 메시지 ID
        conversation_id: 세션 ID
        **metadata: 추가 메타데이터
        
    Returns:
        Dict: 스트리밍 청크 객체
    """
    return {
        "type": chunk_type,
        "content": content,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "timestamp": kr_time_now().isoformat(),
        "metadata": metadata
    }


def validate_streaming_chunk(chunk: Dict[str, Any]) -> bool:
    """
    스트리밍 청크 유효성 검사
    
    Args:
        chunk: 검사할 청크
        
    Returns:
        bool: 유효한 청크인지 여부
    """
    required_fields = ["type", "message_id", "conversation_id", "timestamp"]
    
    if not isinstance(chunk, dict):
        return False
    
    for field in required_fields:
        if field not in chunk:
            LOGGER.warning(f"⚠️ Missing required field in chunk: {field}")
            return False
    
    # 타입별 특별 검증
    chunk_type = chunk.get("type")
    if chunk_type == "content" and not isinstance(chunk.get("content"), str):
        LOGGER.warning("⚠️ Content chunk must have string content")
        return False
    
    return True


def get_chunk_statistics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    청크 통계 정보 생성
    
    Args:
        chunks: 분석할 청크 리스트
        
    Returns:
        Dict: 통계 정보
    """
    if not chunks:
        return {"total_chunks": 0}
    
    stats = {
        "total_chunks": len(chunks),
        "chunk_types": {},
        "total_content_length": 0,
        "average_chunk_size": 0,
        "first_chunk_time": None,
        "last_chunk_time": None
    }
    
    content_lengths = []
    timestamps = []
    
    for chunk in chunks:
        # 타입별 카운트
        chunk_type = chunk.get("type", "unknown")
        stats["chunk_types"][chunk_type] = stats["chunk_types"].get(chunk_type, 0) + 1
        
        # 콘텐츠 길이
        content = chunk.get("content", "")
        if isinstance(content, str):
            length = len(content)
            content_lengths.append(length)
            stats["total_content_length"] += length
        
        # 타임스탬프
        timestamp = chunk.get("timestamp")
        if timestamp:
            timestamps.append(timestamp)
    
    # 통계 계산
    if content_lengths:
        stats["average_chunk_size"] = sum(content_lengths) / len(content_lengths)
    
    if timestamps:
        stats["first_chunk_time"] = min(timestamps)
        stats["last_chunk_time"] = max(timestamps)
    
    return stats


if __name__ == "__main__":
    """테스트 및 디버깅용"""
    print("🔄 Stream Processor Test")
    print("=" * 50)
    
    # 테스트 콘텐츠들
    test_contents = [
        "Simple string content",
        {"content": "Dict with content field"},
        {"type": "tool_use", "id": "toolu_123"},  # 필터링되어야 함
        {"text": "Dict with text field"},
        ["List", "of", "strings"],
        None,
        42
    ]
    
    print("\n📝 Text Extraction Test:")
    for i, content in enumerate(test_contents):
        extracted = extract_safe_text_content(content)
        print(f"  {i+1}. {type(content).__name__}: '{extracted}'")
    
    # 가상 도구 결과 테스트
    print("\n🔧 Tool Results Test:")
    class MockAction:
        def __init__(self, tool, tool_input):
            self.tool = tool
            self.tool_input = tool_input
    
    mock_steps = [
        (MockAction("search", "MMA fighters"), "Found 10 fighters"),
        (MockAction("analyze", {"fighter": "Jon Jones"}), "Analysis complete")
    ]
    
    tool_results = extract_tool_results(mock_steps)
    for result in tool_results:
        print(f"  Tool: {result['tool']}, Input: {result['input']}")
    
    print(f"\n✅ Stream Processor module loaded successfully")