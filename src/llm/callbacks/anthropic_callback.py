import asyncio
import time
from typing import Dict, Any, List
from datetime import datetime

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

from common.utils import utc_now

class AnthropicCallbackHandler(AsyncCallbackHandler):
    """실제 스트리밍을 위한 콜백 핸들러"""
    
    def __init__(self, message_id: str, conversation_id : int):
        self.tokens = []
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.current_content = ""
        self.stream_queue = asyncio.Queue()
        self.is_streaming = False
        self.tool_calls = []
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """새 토큰이 생성될 때 호출 - 실제 스트리밍"""
        try:
            token_str = ""
            
            # Anthropic의 토큰 형식 처리 및 툴 호출 토큰 필터링
            if isinstance(token, dict):
                # 툴 호출 관련 토큰들 필터링
                tool_types = ['tool_use', 'input_json_delta', 'tool_call', 'function_call']
                if token.get('type') in tool_types:
                    return  # 툴 관련 토큰은 스트리밍하지 않음
                
                # 툴 호출 ID나 이름이 포함된 토큰 필터링
                if 'id' in token and token.get('id', '').startswith('toolu_'):
                    return
                
                # {'text': 'content', 'type': 'text', 'index': 0} 형식
                if 'text' in token:
                    token_str = token['text']
                else:
                    return  # text가 없는 토큰은 스트리밍하지 않음
                    
            elif isinstance(token, list):
                # 리스트인 경우 각 요소에서 text 추출
                texts = []
                for item in token:
                    if isinstance(item, dict):
                        # 툴 관련 토큰 필터링
                        tool_types = ['tool_use', 'input_json_delta', 'tool_call', 'function_call']
                        if item.get('type') in tool_types:
                            continue
                        # 툴 ID 토큰 필터링
                        if 'id' in item and item.get('id', '').startswith('toolu_'):
                            continue
                        if 'text' in item:
                            texts.append(item['text'])
                    else:
                        texts.append(str(item))
                token_str = ''.join(texts)
                if not token_str:
                    return  # 빈 문자열인 경우 스트리밍하지 않음
            else:
                token_str = str(token)
            
            if token_str:  # 빈 문자열이 아닌 경우만 처리
                self.tokens.append(token_str)
                self.current_content += token_str
                
                # 스트리밍 큐에 토큰 추가
                await self.stream_queue.put({
                    "type": "content",
                    "content": token_str,
                    "message_id": self.message_id,
                    "conversation_id": self.conversation_id,
                    "timestamp": utc_now().isoformat()
                })
                
        except Exception as e:
            print(f"❌ Error in on_llm_new_token: {e}")
            print(f"🔍 Token type: {type(token)}, value: {token}")
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM 시작 시 호출"""
        self.tokens = []
        self.current_content = ""
        self.is_streaming = True
        
        # 스트리밍 시작 신호
        await self.stream_queue.put({
            "type": "start",
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": utc_now().isoformat()
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 종료 시 호출"""
        self.is_streaming = False
        
        # 스트리밍 종료 신호
        await self.stream_queue.put({
            "type": "end",
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": utc_now().isoformat(),
            "final_content": self.current_content
        })
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """툴 시작 시 호출"""
        tool_name = serialized.get("name", "unknown")
        tool_start_time = time.time()
        self.tool_calls.append({
            "tool": tool_name,
            "input": input_str,
            "status": "started",
            "start_time": tool_start_time
        })
        
        print(f"🔧 Tool '{tool_name}' started at {tool_start_time}")
        
        # 툴 사용 알림
        await self.stream_queue.put({
            "type": "tool_start",
            "tool_name": tool_name,
            "tool_input": input_str,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": utc_now().isoformat()
        })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """툴 종료 시 호출"""
        tool_end_time = time.time()
        
        if self.tool_calls:
            tool_call = self.tool_calls[-1]
            tool_call["status"] = "completed"
            tool_call["result"] = output[:200] + "..." if len(output) > 200 else output
            tool_call["end_time"] = tool_end_time
            
            # 툴 실행 시간 계산
            if "start_time" in tool_call:
                tool_duration = tool_end_time - tool_call["start_time"]
                tool_call["duration"] = tool_duration
                print(f"🔧 Tool '{tool_call['tool']}' completed in {tool_duration:.3f}s")
            else:
                print(f"🔧 Tool completed at {tool_end_time}")
        
        # 툴 완료 알림
        await self.stream_queue.put({
            "type": "tool_end",
            "tool_result": output[:200] + "..." if len(output) > 200 else output,
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": utc_now().isoformat()
        })
    
    async def on_agent_action(self, action, **kwargs) -> None:
        """에이전트 액션 시 호출"""
        await self.stream_queue.put({
            "type": "thinking",
            "thought": f"Using tool: {action.tool}",
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "timestamp": utc_now().isoformat()
        })

def get_anthropic_callback_handler(message_id: str, conversation_id : int):
    return AnthropicCallbackHandler(message_id=message_id, conversation_id=conversation_id)
