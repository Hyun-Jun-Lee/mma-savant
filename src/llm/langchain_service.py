"""
LangChain 기반 LLM 서비스
단일 MCP 서버용 최적화된 구현
"""
import asyncio
import uuid
import time
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from traceback import format_exc
from contextlib import asynccontextmanager

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import LLMResult

# 단일 MCP 서버용 imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

from config import Config
from llm.prompts.en_ver import get_en_system_prompt_with_tools, get_en_conversation_starter


class StreamingCallbackHandler(AsyncCallbackHandler):
    """실제 스트리밍을 위한 콜백 핸들러"""
    
    def __init__(self, message_id: str, session_id: str):
        self.tokens = []
        self.message_id = message_id
        self.session_id = session_id
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
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat()
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
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 종료 시 호출"""
        self.is_streaming = False
        
        # 스트리밍 종료 신호
        await self.stream_queue.put({
            "type": "end",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
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
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
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
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_agent_action(self, action, **kwargs) -> None:
        """에이전트 액션 시 호출"""
        await self.stream_queue.put({
            "type": "thinking",
            "thought": f"Using tool: {action.tool}",
            "message_id": self.message_id,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        })


class LangChainLLMService:
    """LangChain 기반 LLM 서비스 - 단일 MCP 서버 최적화"""
    
    def __init__(self):
        # Anthropic LLM 초기화
        self.llm = ChatAnthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            model=Config.ANTHROPIC_MODEL_NAME,
            temperature=0.7,
            max_tokens=4000,
            streaming=True
        )
        
        # 단일 MCP 서버 설정
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        mcp_server_path = os.path.join(src_dir, "tools", "mcp_server.py")
        
        self.server_params = StdioServerParameters(
            command="python",
            args=[mcp_server_path],
        )
    
    @asynccontextmanager
    async def _get_mcp_tools(self):
        """
        단일 MCP 서버에서 도구를 가져오는 최적화된 context manager
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 연결 초기화
                await session.initialize()
                
                # 도구 로드
                tools = await load_mcp_tools(session)
                print(f"✅ MCP Tools loaded: {len(tools)} tools")
                
                yield tools

    async def generate_streaming_chat_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None
        ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지에 대한 실제 스트리밍 채팅 응답 생성
        """
        message_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # 메시지 히스토리 준비
            prep_start = time.time()
            messages = self._prepare_messages(user_message, conversation_history)
            prep_time = time.time() - prep_start

            print("-"*50)
            print("check message :")
            print(messages)
            print("-"*50)
            
            # 단일 MCP 서버에서 도구 로드
            mcp_start = time.time()
            async with self._get_mcp_tools() as tools:
                mcp_time = time.time() - mcp_start
                print(f"⏱️ MCP tools loading took: {mcp_time:.3f}s")
                
                # 스트리밍 콜백 핸들러 생성
                callback_handler = StreamingCallbackHandler(message_id, session_id)
                
                # 프롬프트 템플릿 생성
                prompt = ChatPromptTemplate.from_messages([
                    ("system", get_en_system_prompt_with_tools()),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ])
                
                # 스트리밍을 지원하는 LLM 생성
                streaming_llm = ChatAnthropic(
                    api_key=Config.ANTHROPIC_API_KEY,
                    model=Config.ANTHROPIC_MODEL_NAME,
                    temperature=0.7,
                    max_tokens=4000,
                    streaming=True,
                    callbacks=[callback_handler]  
                )
                
                # 에이전트 생성 (스트리밍 LLM 사용)
                agent = create_tool_calling_agent(streaming_llm, tools, prompt)

                agent_executor = AgentExecutor(
                    agent=agent, 
                    tools=tools, 
                    verbose=True,
                    return_intermediate_steps=True,  
                    callbacks=[callback_handler]  
                )
                
                print(f"🤖 Agent created with {len(tools)} tools")
                
                # 비동기 에이전트 실행을 별도 태스크로 시작
                async def run_agent():
                    try:
                        print("🚀 Starting agent execution...")
                        
                        agent_exec_start = time.time()
                        
                        invoke_start = time.time()
                        
                        result = await agent_executor.ainvoke({
                            "input": user_message,
                            "chat_history": messages[:-1]
                        })
                        
                        invoke_time = time.time() - invoke_start
                        agent_exec_time = time.time() - agent_exec_start
                        
                        print("✅ Agent execution completed")
                        print(f"⏱️ ainvoke() call took: {invoke_time:.3f}s")
                        print(f"⏱️ Total agent execution took: {agent_exec_time:.3f}s")
                        
                        # 결과 분석
                        if "intermediate_steps" in result:
                            steps = result["intermediate_steps"]
                            print(f"📊 Agent used {len(steps)} intermediate steps")
                            for i, step in enumerate(steps):
                                if hasattr(step, '__len__') and len(step) >= 2:
                                    action, observation = step
                                    tool_name = getattr(action, 'tool', 'unknown')
                                    print(f"   Step {i+1}: Used tool '{tool_name}'")
                        
                        # 출력 분석
                        output = result.get("output", "")
                        
                        # 최종 결과 큐에 추가
                        await callback_handler.stream_queue.put({
                            "type": "final_result",
                            "content": result["output"],
                            "intermediate_steps": result.get("intermediate_steps", []),
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        print(f"❌ Agent execution failed: {e}")
                        
                        # Rate limit 에러 특별 처리
                        error_message = str(e)
                        if "rate_limit_error" in error_message or "429" in error_message:
                            print("🚫 Rate limit exceeded - reducing token usage recommended")
                            error_message = "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
                        
                        await callback_handler.stream_queue.put({
                            "type": "error",
                            "error": error_message,
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        })
                    finally:
                        # 종료 신호
                        await callback_handler.stream_queue.put(None)
                
                # 에이전트 실행 태스크 시작
                agent_task = asyncio.create_task(run_agent())
                
                # 스트리밍 이벤트를 실시간으로 yield
                first_chunk_time = None
                chunk_count = 0
                while True:
                    try:
                        # 타임아웃을 두어 무한 대기 방지
                        chunk = await asyncio.wait_for(
                            callback_handler.stream_queue.get(), 
                            timeout=60.0
                        )
                        
                        if chunk is None:  # 종료 신호
                            break
                        
                        # 첫 번째 응답 청크 시간 측정
                        if first_chunk_time is None and chunk.get("type") == "content":
                            first_chunk_time = time.time() - start_time
                            print(f"⏱️ First response chunk took: {first_chunk_time:.3f}s")
                        
                        chunk_count += 1
                        
                        yield chunk
                        
                    except asyncio.TimeoutError:
                        print("⚠️ Streaming timeout - sending error")
                        yield {
                            "type": "error",
                            "error": "Streaming timeout",
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        break
                    except Exception as e:
                        print(f"❌ Error in streaming: {e}")
                        yield {
                            "type": "error",
                            "error": str(e),
                            "message_id": message_id,
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        break
                
                # 에이전트 태스크 완료 대기
                try:
                    await agent_task
                except Exception as e:
                    print(f"❌ Agent task error: {e}")
                
                total_time = time.time() - start_time
                print(f"⏱️ Total streaming function took: {total_time:.3f}s")
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "message_id": message_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_messages(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ):
        """LangChain 메시지 형식으로 변환"""
        messages = []
        
        # 시스템 메시지 추가
        messages.append(SystemMessage(content=get_en_system_prompt_with_tools()))
        
        # 대화 히스토리 추가
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    content = msg["content"]
                    
                    # tool 결과가 포함된 경우 파싱
                    if "<!-- TOOL_RESULTS:" in content:
                        # 사용자에게 보이는 부분과 tool 정보 분리
                        parts = content.split("<!-- TOOL_RESULTS:")
                        user_visible_content = parts[0].strip()
                        
                        if len(parts) > 1:
                            try:
                                tool_part = parts[1].split(" -->")[0].strip()
                                tool_results = json.loads(tool_part)
                                
                                # tool 결과를 포함한 확장된 메시지 생성
                                enhanced_content = user_visible_content + "\n\n[Previous tool results:\n"
                                for tool_info in tool_results:
                                    enhanced_content += f"- {tool_info['tool']}: {tool_info['input']} → {tool_info['result'][:200]}...\n"
                                enhanced_content += "]"
                                
                                messages.append(AIMessage(content=enhanced_content))
                            except:
                                # JSON 파싱 실패 시 원본 사용
                                messages.append(AIMessage(content=user_visible_content))
                        else:
                            messages.append(AIMessage(content=user_visible_content))
                    else:
                        messages.append(AIMessage(content=content))
        
        # 현재 사용자 메시지 추가
        messages.append(HumanMessage(content=user_message))
        
        return messages
    
    def get_conversation_starter(self) -> str:
        """대화 시작 메시지 반환"""
        return get_conversation_starter()
    
    async def cleanup(self):
        """리소스 정리 - MCP context manager가 자동으로 처리"""
        print("✅ LLM service cleanup completed")


# 글로벌 서비스 인스턴스 - 간단한 싱글톤
_langchain_service = None

async def get_langchain_service() -> LangChainLLMService:
    """글로벌 LangChain 서비스 인스턴스 반환"""
    global _langchain_service
    
    if _langchain_service is None:
        _langchain_service = LangChainLLMService()
        print("✅ Single MCP server LangChain service created")
    
    return _langchain_service