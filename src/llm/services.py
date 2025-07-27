"""
LLM 서비스 레이어
채팅 응답 생성 및 Tool 통합
"""
import json
import uuid
import importlib
import inspect
import os
import sys
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from llm.client import LLMClient, get_llm_client, LLMError
from llm.prompts.en_ver import get_en_system_prompt_with_tools, get_en_conversation_starter

# FastMCP 도구 로딩을 위한 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


class ChatMessage:
    """채팅 메시지 클래스"""
    
    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        message_id: Optional[str] = None
    ):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.message_id = message_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.message_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }


class LLMService:
    """LLM 서비스 클래스"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or get_llm_client()
        self.system_prompt = get_en_system_prompt_with_tools()
        self._tools_cache = None
        self._tool_functions_cache = None
    
    async def generate_chat_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 메시지에 대한 채팅 응답 생성 (비스트리밍)
        """
        try:
            # 메시지 히스토리 준비
            messages = self._prepare_messages(user_message, conversation_history)
            
            # LLM 응답 생성
            response = await self.llm_client.generate_response(
                messages=messages,
                system_prompt=self.system_prompt,
                tools=self._get_mcp_tools()
            )
            
            # Tool call 처리
            if response.get("tool_calls"):
                tool_results = await self._execute_tool_calls(response["tool_calls"])
                
                # Tool 결과를 포함하여 재요청
                messages.append({
                    "role": "assistant",
                    "content": response["content"],
                    "tool_calls": response["tool_calls"]
                })
                
                # Tool 결과 추가
                for tool_result in tool_results:
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(tool_result["result"]),
                        "tool_call_id": tool_result["call_id"]
                    })
                
                # 최종 응답 생성
                final_response = await self.llm_client.generate_response(
                    messages=messages,
                    system_prompt=self.system_prompt
                )
                
                return {
                    "content": final_response["content"],
                    "message_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "tool_calls": response["tool_calls"],
                    "tool_results": tool_results,
                    "usage": final_response.get("usage", {})
                }
            
            else:
                return {
                    "content": response["content"],
                    "message_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "usage": response.get("usage", {})
                }
                
        except Exception as e:
            raise LLMError(f"Failed to generate chat response: {str(e)}")
    
    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지에 대한 스트리밍 채팅 응답 생성
        """
        try:
            # 메시지 히스토리 준비
            messages = self._prepare_messages(user_message, conversation_history)
            
            message_id = str(uuid.uuid4())
            
            # 스트리밍 응답 생성
            async for chunk in self.llm_client.generate_streaming_response(
                messages=messages,
                system_prompt=self.system_prompt,
                tools=self._get_mcp_tools()
            ):
                
                if chunk["type"] == "content":
                    yield {
                        "type": "content",
                        "content": chunk["content"],
                        "message_id": message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    }
                
                elif chunk["type"] == "start":
                    yield {
                        "type": "start",
                        "message_id": message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    }
                
                elif chunk["type"] == "end":
                    yield {
                        "type": "end",
                        "message_id": message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    }
                
                elif chunk["type"] == "error":
                    yield {
                        "type": "error",
                        "error": chunk["error"],
                        "message_id": message_id,
                        "session_id": session_id,
                        "timestamp": chunk["timestamp"]
                    }
                    
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "message_id": str(uuid.uuid4()),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_messages(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """
        LLM API 호출을 위한 메시지 형식 준비
        """
        messages = []
        
        # 대화 히스토리 추가 (최근 10개만)
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # 현재 사용자 메시지 추가
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """
        FastMCP Tool 정의 동적 로딩
        """
        if self._tools_cache is not None:
            return self._tools_cache
        
        tools = []
        
        try:
            # tools 디렉토리의 모든 *_tools.py 파일에서 도구 로드
            tools_modules = [
                'tools.fighter_tools',
                'tools.event_tools', 
                'tools.match_tools',
                'tools.composition_tools'
            ]
            
            for module_name in tools_modules:
                try:
                    module = importlib.import_module(module_name)
                    
                    # @mcp.tool() 데코레이터가 붙은 함수들 찾기
                    for name, obj in inspect.getmembers(module):
                        if (inspect.iscoroutinefunction(obj) and 
                            hasattr(obj, '__wrapped__') and 
                            hasattr(obj, '_mcp_tool')):
                            
                            # 함수의 docstring과 type hints에서 스키마 생성
                            tool_schema = self._create_tool_schema(name, obj)
                            if tool_schema:
                                tools.append(tool_schema)

                except ImportError as e:
                    print(f"Warning: Could not import {module_name}: {e}")
                    continue
                except Exception as e:
                    print(f"Error loading tools from {module_name}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error loading MCP tools: {e}")
            raise ValueError("Failed to load MCP tools")
        
        self._tools_cache = tools
        print(f"✅ MCP tools loaded: {len(tools)} tools")
        return tools
    
    def _create_tool_schema(self, func_name: str, func: Any) -> Optional[Dict[str, Any]]:
        """
        함수에서 Claude API용 tool 스키마 생성
        """
        try:
            # 함수 시그니처 가져오기
            sig = inspect.signature(func)
            
            # docstring에서 description 추출
            doc = inspect.getdoc(func)
            description = ""
            if doc:
                # docstring의 첫 번째 줄을 description으로 사용
                lines = doc.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Args:') and not line.startswith('Returns:'):
                        description = line
                        break
            
            if not description:
                description = f"{func_name} 도구"
            
            # 파라미터 스키마 생성
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                # 타입 힌트 확인
                param_type = "string"  # 기본값
                
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif hasattr(param.annotation, '__origin__'):
                        # Optional, List 등 처리
                        if getattr(param.annotation, '__origin__', None) is list:
                            param_type = "array"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": f"{param_name} 파라미터"
                }
                
                # required 파라미터 확인 (기본값이 없으면 required)
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            return {
                "name": func_name,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
            
        except Exception as e:
            print(f"Error creating schema for {func_name}: {e}")
            return None
    
    def _load_tool_functions(self) -> Dict[str, Any]:
        """
        FastMCP 도구 함수들을 동적으로 로드하여 캐시
        """
        if self._tool_functions_cache is not None:
            return self._tool_functions_cache
        
        tool_functions = {}
        
        try:
            tools_modules = [
                'tools.fighter_tools',
                'tools.event_tools', 
                'tools.match_tools',
                'tools.composition_tools'
            ]
            
            for module_name in tools_modules:
                try:
                    module = importlib.import_module(module_name)
                    
                    # 모든 async 함수들을 도구 함수로 등록
                    for name, obj in inspect.getmembers(module):
                        if (inspect.iscoroutinefunction(obj) and 
                            not name.startswith('_')):
                            tool_functions[name] = obj
                            
                except ImportError as e:
                    print(f"Warning: Could not import {module_name}: {e}")
                    continue
                except Exception as e:
                    print(f"Error loading functions from {module_name}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error loading tool functions: {e}")
        
        self._tool_functions_cache = tool_functions
        return tool_functions

    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """
        FastMCP Tool call 실행
        """
        tool_results = []
        tool_functions = self._load_tool_functions()
        
        for tool_call in tool_calls:
            call_id = tool_call["id"]
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]
            
            try:
                # 실제 FastMCP 도구 함수 호출
                if tool_name in tool_functions:
                    tool_func = tool_functions[tool_name]
                    
                    # 함수 호출 (kwargs로 전달)
                    result = await tool_func(**tool_input)
                    
                    tool_results.append({
                        "call_id": call_id,
                        "tool_name": tool_name,
                        "result": result,
                        "success": True
                    })
                else:
                    # 도구를 찾을 수 없는 경우
                    tool_results.append({
                        "call_id": call_id,
                        "tool_name": tool_name,
                        "result": {"error": f"Tool '{tool_name}' not found"},
                        "success": False
                    })
                
            except Exception as e:
                print(f"Error executing tool {tool_name}: {e}")
                tool_results.append({
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "result": {"error": str(e)},
                    "success": False
                })
        
        return tool_results
    
    def get_conversation_starter(self) -> str:
        """
        대화 시작 메시지 반환
        """
        return get_conversation_starter()


# 글로벌 서비스 인스턴스
_llm_service = None

def get_llm_service() -> LLMService:
    """
    글로벌 LLM 서비스 인스턴스 반환
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service