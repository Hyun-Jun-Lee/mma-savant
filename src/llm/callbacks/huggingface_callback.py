import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import LLMResult

from common.utils import kr_time_now


class HuggingFaceCallbackHandler(AsyncCallbackHandler):
    """
    HuggingFace API를 위한 최적화된 콜백 핸들러
    HuggingFace Inference API를 통한 스트리밍 응답 처리
    """
    
    def __init__(self, message_id: str, session_id: str, model_name: str = "huggingface"):
        self.tokens = []
        self.message_id = message_id
        self.session_id = session_id
        self.model_name = model_name
        self.current_content = ""
        self.stream_queue = asyncio.Queue()
        self.is_streaming = False
        self.tool_calls = []
        self.start_time = None
        self.token_count = 0
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """새 토큰 생성 시 호출 - HuggingFace API 스트리밍 최적화"""
        try:
            # HuggingFace API 토큰 처리
            token_str = self._process_huggingface_api_token(token)
            
            if token_str and token_str.strip():  # 빈 토큰 필터링
                self.tokens.append(token_str)
                self.current_content += token_str
                self.token_count += 1
                
                # 스트리밍 큐에 토큰 추가
                await self.stream_queue.put({
                    "type": "content",
                    "content": token_str,
                    "message_id": self.message_id,
                    "session_id": self.session_id,
                    "model": self.model_name,
                    "token_count": self.token_count,
                    "timestamp": kr_time_now().isoformat()
                })
                
        except Exception as e:
            print(f"❌ Error in HuggingFace API token processing: {e}")
            print(f"🔍 Token: {type(token)} - {repr(token)}")
            # 에러가 발생해도 처리 계속
    
    def _process_huggingface_api_token(self, token: Any) -> str:
        """
        HuggingFace API 응답 토큰 처리
        API에서 받은 스트리밍 토큰을 문자열로 변환
        """
        if isinstance(token, str):
            # 가장 일반적인 경우: 문자열 토큰
            return token
        
        elif isinstance(token, dict):
            # API 응답에서 구조화된 데이터
            if 'token' in token:
                # {'token': {'text': '...'}} 형식
                token_data = token['token']
                if isinstance(token_data, dict) and 'text' in token_data:
                    return token_data['text']
                return str(token_data)
            
            elif 'generated_text' in token:
                return token['generated_text']
            elif 'text' in token:
                return token['text']
            elif 'content' in token:
                return token['content']
            elif 'choices' in token and len(token['choices']) > 0:
                # OpenAI 스타일 응답
                choice = token['choices'][0]
                if 'delta' in choice and 'content' in choice['delta']:
                    return choice['delta']['content']
                elif 'text' in choice:
                    return choice['text']
            
            # 다른 구조의 딕셔너리
            return str(token)
        
        elif isinstance(token, list) and len(token) > 0:
            # 배치 응답의 첫 번째 항목 처리
            return self._process_huggingface_api_token(token[0])
        
        elif token is None:
            return ""
        
        else:
            # 기타 타입은 문자열로 변환
            return str(token)
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM 시작"""
        self.tokens = []
        self.current_content = ""
        self.is_streaming = True
        self.start_time = time.time()
        self.token_count = 0
        
        await self.stream_queue.put({
            "type": "start",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 종료 - HuggingFace API 응답 완료 처리"""
        self.is_streaming = False
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        # API 응답에서 추가 정보 추출
        usage_info = self._extract_usage_info(response) if response else {}
        
        await self.stream_queue.put({
            "type": "end",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat(),
            "final_content": self.current_content,
            "duration": duration,
            "token_count": self.token_count,
            "tokens_per_second": self.token_count / duration if duration > 0 else 0,
            "usage": usage_info
        })
    
    def _extract_usage_info(self, response: LLMResult) -> Dict[str, Any]:
        """API 응답에서 사용량 정보 추출"""
        usage_info = {}
        
        if hasattr(response, 'llm_output') and response.llm_output:
            llm_output = response.llm_output
            
            # 토큰 사용량 정보
            if 'token_usage' in llm_output:
                usage_info['api_token_usage'] = llm_output['token_usage']
            
            # 모델 정보
            if 'model_name' in llm_output:
                usage_info['api_model'] = llm_output['model_name']
        
        return usage_info
    
    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """LLM 에러"""
        self.is_streaming = False
        
        await self.stream_queue.put({
            "type": "error",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat(),
            "error": str(error),
            "error_type": type(error).__name__
        })
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """툴 시작"""
        tool_name = serialized.get("name", "unknown")
        tool_start_time = time.time()
        
        tool_call = {
            "tool": tool_name,
            "input": input_str,
            "status": "started",
            "start_time": tool_start_time
        }
        self.tool_calls.append(tool_call)
        
        print(f"🔧 Tool '{tool_name}' started (HuggingFace: {self.model_name})")
        
        await self.stream_queue.put({
            "type": "tool_start",
            "tool_name": tool_name,
            "tool_input": input_str,
            "message_id": self.message_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """툴 종료"""
        tool_end_time = time.time()
        
        if self.tool_calls:
            tool_call = self.tool_calls[-1]
            tool_call["status"] = "completed"
            tool_call["result"] = output[:200] + "..." if len(output) > 200 else output
            tool_call["end_time"] = tool_end_time
            
            if "start_time" in tool_call:
                tool_duration = tool_end_time - tool_call["start_time"]
                tool_call["duration"] = tool_duration
                print(f"🔧 Tool '{tool_call['tool']}' completed in {tool_duration:.3f}s")
        
        await self.stream_queue.put({
            "type": "tool_end",
            "tool_result": output[:200] + "..." if len(output) > 200 else output,
            "message_id": self.message_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_agent_action(self, action, **kwargs) -> None:
        """에이전트 액션"""
        await self.stream_queue.put({
            "type": "thinking",
            "thought": f"Using tool: {action.tool}",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat()
        })
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 반환"""
        duration = time.time() - self.start_time if self.start_time else 0
        return {
            "model": self.model_name,
            "token_count": self.token_count,
            "content_length": len(self.current_content),
            "tool_calls_count": len(self.tool_calls),
            "duration": duration,
            "tokens_per_second": self.token_count / duration if duration > 0 else 0,
            "is_streaming": self.is_streaming,
            "tool_calls": self.tool_calls
        }


def get_huggingface_callback_handler(
    message_id: str, 
    session_id: str, 
    model_name: str = "huggingface"
) -> HuggingFaceCallbackHandler:
    """
    HuggingFace 콜백 핸들러 팩토리 함수
    
    Args:
        message_id: 메시지 ID
        session_id: 세션 ID  
        model_name: 모델 이름 (로깅용)
        
    Returns:
        HuggingFaceCallbackHandler 인스턴스
    """
    return HuggingFaceCallbackHandler(
        message_id=message_id,
        session_id=session_id, 
        model_name=model_name
    )