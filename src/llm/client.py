"""
LLM API 클라이언트
Claude/OpenAI API 통합 처리
"""
import os
import json
import asyncio
from typing import AsyncGenerator, Dict, List, Any, Optional
from datetime import datetime

import httpx
from anthropic import AsyncAnthropic

from config import Config


class LLMConfig:
    """LLM 설정 클래스"""
    
    def __init__(self):
        self.anthropic_api_key = Config.ANTHROPIC_API_KEY
        
        # 기본 모델 설정
        self.default_model = Config.ANTHROPIC_MODEL_NAME
        self.max_tokens = 4000
        self.temperature = 0.7
        
        # 재시도 설정
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # 스트리밍 설정
        self.stream_chunk_size = 50  # 문자 단위로 청크 크기


class LLMClient:
    """LLM API 클라이언트"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        
        # Claude 클라이언트 초기화
        if self.config.anthropic_api_key:
            self.anthropic = AsyncAnthropic(api_key=self.config.anthropic_api_key)
        else:
            print("❌ Claude API key not configured")
            self.anthropic = None
            
        # 사용량 추적
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        LLM을 사용하여 응답 생성 (비스트리밍)
        """
        if not self.anthropic:
            raise ValueError("Claude API key not configured")
        
        model = model or self.config.default_model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        try:
            # Claude API 호출
            response = await self.anthropic.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                tools=tools if tools else []
            )
            
            # 사용량 추적
            self.usage_stats["total_requests"] += 1
            if hasattr(response, 'usage'):
                self.usage_stats["total_tokens"] += response.usage.input_tokens + response.usage.output_tokens
            
            return {
                "content": response.content[0].text if response.content else "",
                "model": model,
                "usage": {
                    "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                    "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                },
                "tool_calls": self._extract_tool_calls(response),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise LLMError(f"Failed to generate response: {str(e)}")
    
    async def generate_streaming_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        LLM을 사용하여 스트리밍 응답 생성
        """
        if not self.anthropic:
            raise ValueError("Claude API key not configured")
        
        model = model or self.config.default_model
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        try:
            print(f"🔄 Calling Claude API: model={model}, messages={len(messages)}, tools={len(tools) if tools else 0}")
            
            # Claude 스트리밍 API 호출
            async with self.anthropic.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages,
                tools=tools if tools else []
            ) as stream:
                
                async for chunk in stream:
                    # 실제 텍스트 내용
                    if chunk.type == "content_block_delta":
                        if chunk.delta.type == "text_delta":
                            yield {
                                "type": "content",
                                "content": chunk.delta.text,
                                "model": model,
                                "timestamp": datetime.now().isoformat()
                            }
                    
                    # 메시지 시작 신호
                    elif chunk.type == "message_start":
                        print(f"🚀 Claude response started")
                        yield {
                            "type": "start",
                            "model": model,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # 메시지 완료 신호
                    elif chunk.type == "message_stop":
                        print(f"✅ Claude response completed")
                        # 사용량 추적
                        self.usage_stats["total_requests"] += 1
                        yield {
                            "type": "end",
                            "model": model,
                            "timestamp": datetime.now().isoformat()
                        }
                        
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_with_retry(
        self,
        func,
        *args,
        max_retries: Optional[int] = None,
        **kwargs
    ):
        """
        재시도 로직을 포함한 함수 실행
        """
        max_retries = max_retries or self.config.max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                break
        
        raise LLMError(f"Failed after {max_retries + 1} attempts: {str(last_error)}")
    
    def _extract_tool_calls(self, response) -> List[Dict]:
        """
        응답에서 tool call 추출
        """
        tool_calls = []
        
        if hasattr(response, 'content'):
            for content_block in response.content:
                if hasattr(content_block, 'type') and content_block.type == "tool_use":
                    tool_calls.append({
                        "id": content_block.id,
                        "name": content_block.name,
                        "input": content_block.input
                    })
        
        return tool_calls
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        사용량 통계 반환
        """
        return self.usage_stats.copy()
    
    def reset_usage_stats(self):
        """
        사용량 통계 리셋
        """
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }


class LLMError(Exception):
    """LLM 관련 에러"""
    pass


# 글로벌 클라이언트 인스턴스
_llm_client = None

def get_llm_client() -> LLMClient:
    """
    글로벌 LLM 클라이언트 인스턴스 반환
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client