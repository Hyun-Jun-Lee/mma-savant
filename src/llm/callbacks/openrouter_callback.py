import asyncio
import time
from typing import Dict, Any, List

from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import LLMResult

from common.utils import kr_time_now

class OpenRouterCallbackHandler(AsyncCallbackHandler):
    """OpenRouter 스트리밍 콜백 핸들러"""
    
    def __init__(self, message_id: str, conversation_id : int, model_name: str = "unknown"):
        self.tokens = []
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.model_name = model_name
        self.current_content = ""
        self.stream_queue = asyncio.Queue()
        self.is_streaming = False
        self.tool_calls = []
        self.start_time = None
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """새 토큰 스트리밍"""
        try:
            if isinstance(token, str) and token.strip():
                self.tokens.append(token)
                self.current_content += token
                
                await self.stream_queue.put({
                    "type": "content",
                    "content": token,
                    "message_id": self.message_id,
                    "conversation_id": self.conversation_id,
                    "model": self.model_name,
                    "timestamp": kr_time_now().isoformat()
                })
        except Exception as e:
            print(f"Error in OpenRouter token streaming: {e}")
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM 시작"""
        self.tokens = []
        self.current_content = ""
        self.is_streaming = True
        self.start_time = time.time()
        
        await self.stream_queue.put({
            "type": "start",
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "model": self.model_name,
            "provider": "openrouter",
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 종료"""
        self.is_streaming = False
        
        # 토큰 사용량 정보 (OpenRouter에서 제공하는 경우)
        usage_info = {}
        if hasattr(response, 'llm_output') and response.llm_output:
            usage_info = response.llm_output.get('token_usage', {})
        
        await self.stream_queue.put({
            "type": "end",
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "model": self.model_name,
            "final_content": self.current_content,
            "usage": usage_info,
            "duration": time.time() - self.start_time if self.start_time else None,
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """툴 시작"""
        tool_name = serialized.get("name", "unknown")
        tool_start_time = time.time()
        
        self.tool_calls.append({
            "tool": tool_name,
            "input": input_str,
            "status": "started",
            "start_time": tool_start_time
        })
        
        await self.stream_queue.put({
            "type": "tool_start",
            "tool_name": tool_name,
            "tool_input": input_str,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """툴 종료"""
        tool_end_time = time.time()
        
        if self.tool_calls:
            tool_call = self.tool_calls[-1]
            tool_call["status"] = "completed"
            tool_call["result"] = output
            tool_call["end_time"] = tool_end_time
            
            if "start_time" in tool_call:
                tool_call["duration"] = tool_end_time - tool_call["start_time"]
        
        await self.stream_queue.put({
            "type": "tool_end",
            "tool_result": output,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": kr_time_now().isoformat()
        })
    
    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """에러 처리"""
        error_message = str(error)
        
        # OpenRouter/DeepSeek 특화 에러 메시지
        if "rate limit" in error_message.lower() or "429" in error_message:
            user_friendly_error = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        elif "402" in error_message:
            user_friendly_error = "크레딧이 부족합니다. OpenRouter 계정을 확인해주세요."
        elif "model not found" in error_message.lower():
            user_friendly_error = f"모델 '{self.model_name}'을 찾을 수 없습니다."
        else:
            user_friendly_error = f"API 호출 중 오류가 발생했습니다: {error_message}"
        
        await self.stream_queue.put({
            "type": "error",
            "error": user_friendly_error,
            "raw_error": error_message,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "model": self.model_name,
            "timestamp": kr_time_now().isoformat()
        })

def get_openrouter_callback_handler(message_id: str, conversation_id : int, model_name: str = "unknown"):
    """OpenRouter 콜백 핸들러 생성"""
    return OpenRouterCallbackHandler(
        message_id=message_id, 
        conversation_id=conversation_id,
        model_name=model_name
    )