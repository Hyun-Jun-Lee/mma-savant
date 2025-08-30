import json
import asyncio
from typing import Callable, Dict, Any, AsyncGenerator, Optional, List

from openai import AsyncOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import LLMResult, Generation, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.prompt_values import ChatPromptValue, StringPromptValue
from pydantic import Field

from config import Config
from common.logging_config import get_logger
from common.utils import kr_time_now

LOGGER = get_logger(__name__)


class OpenRouterLLM(BaseChatModel):
    """OpenRouter를 사용하는 LangChain 호환 LLM 클래스 (공식 문서 방식)"""
    
    # Pydantic 필드 정의
    model_name: str = Field(...)
    api_key: str = Field(...)
    base_url: str = Field(default="https://openrouter.ai/api/v1")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4000)
    callback_handler: Optional[Any] = Field(default=None)  # Any 타입으로 변경하여 콜백 핸들러 객체 허용
    
    # OpenAI 클라이언트는 런타임에 생성
    _client: Optional[AsyncOpenAI] = None
    
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False  # 할당 시 검증 비활성화
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # OpenAI 클라이언트 생성 (공식 문서 방식)
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
    
    @property
    def _llm_type(self) -> str:
        return "openrouter"
    
    def _generate(
        self,
        messages: List[List[BaseMessage]],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> LLMResult:
        """동기 생성 메서드 (LangChain 요구사항)"""
        # 동기 메서드는 구현하지 않음
        raise NotImplementedError("Use agenerate for async operations")
    
    async def _agenerate(
        self,
        messages: List[List[BaseMessage]],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> LLMResult:
        """LangChain 호환 비동기 생성 메서드"""
        
        # 모델별 특화 파라미터 가져오기
        model_params = get_model_specific_params(self.model_name)
        
        # 첫 번째 메시지 시퀀스 사용
        message_list = messages[0] if messages else []
        
        # LangChain 메시지를 OpenAI 형식으로 변환
        openai_messages = []
        for msg in message_list:
            if isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                # 기타 메시지 타입은 system으로 처리
                openai_messages.append({"role": "system", "content": msg.content})
        
        # 요청 파라미터 구성 (공식 문서 방식)
        request_params = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": model_params.get("temperature", self.temperature),
            "max_tokens": model_params.get("max_tokens", self.max_tokens),
            "extra_headers": {
                "HTTP-Referer": "https://mma-savant.com",
                "X-Title": "MMA Savant"
            },
            "extra_body": {}
        }
        
        # 바인딩된 도구들이 있는 경우 tools 파라미터 추가
        bound_tools = getattr(self, '_bound_tools', [])
        if bound_tools:
            # LangChain 도구를 OpenAI function calling 형식으로 변환
            openai_tools = []
            for tool in bound_tools:
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    tool_def = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                        }
                    }
                    # args_schema가 있는 경우 파라미터 스키마 추가
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        try:
                            tool_def["function"]["parameters"] = tool.args_schema.model_json_schema()
                        except:
                            pass  # 스키마 변환 실패 시 무시
                    openai_tools.append(tool_def)
            
            if openai_tools:
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"
        
        # 모델별 특화 파라미터를 extra_body에 추가
        for key, value in model_params.items():
            if key not in ["temperature", "max_tokens"]:
                request_params["extra_body"][key] = value
        
        LOGGER.info(f"🚀 OpenRouter API call with tools: {len(bound_tools)} tools, extra_body: {request_params['extra_body']}")
        
        try:
            # API 호출 (공식 문서 방식)
            response = await self.client.chat.completions.create(**request_params)
            
            # 응답 처리
            choice = response.choices[0]
            message = choice.message
            
            # 도구 호출이 있는 경우
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # 도구 호출 정보를 포함한 ChatGeneration 생성
                ai_message = AIMessage(
                    content=message.content or "",
                    additional_kwargs={
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in message.tool_calls
                        ]
                    }
                )
                generation = ChatGeneration(message=ai_message)
            else:
                # 일반 텍스트 응답도 ChatGeneration으로 생성
                ai_message = AIMessage(content=message.content or "")
                generation = ChatGeneration(message=ai_message)
            
            return LLMResult(generations=[[generation]])
            
        except Exception as e:
            LOGGER.error(f"❌ OpenRouter API call failed: {e}")
            raise
    
    # LangChain 필수 추상 메서드들 구현
    def generate_prompt(self, prompts, stop=None, callbacks=None, **kwargs):
        """동기 프롬프트 생성"""
        raise NotImplementedError("Use agenerate_prompt for async operations")
    
    async def agenerate_prompt(self, prompts, stop=None, callbacks=None, **kwargs):
        """비동기 프롬프트 생성"""
        prompt_strings = [p.to_string() for p in prompts]
        return await self._agenerate(prompt_strings, stop, callbacks, **kwargs)
    
    def predict(self, text: str, **kwargs) -> str:
        """동기 예측"""
        raise NotImplementedError("Use apredict for async operations")
    
    async def apredict(self, text: str, **kwargs) -> str:
        """비동기 예측"""
        result = await self._agenerate([text], **kwargs)
        return result.generations[0][0].text
    
    def predict_messages(self, messages, **kwargs):
        """동기 메시지 예측"""
        raise NotImplementedError("Use apredict_messages for async operations")
    
    async def apredict_messages(self, messages, **kwargs):
        """비동기 메시지 예측"""
        # 메시지를 프롬프트로 변환
        prompt = messages[-1].content if messages else ""
        return await self.apredict(prompt, **kwargs)
    
    def invoke(self, input_data, config=None, **kwargs):
        """동기 호출"""
        raise NotImplementedError("Use ainvoke for async operations")
    
    async def ainvoke(self, input_data, config=None, **kwargs):
        """비동기 호출"""
        if isinstance(input_data, str):
            return await self.apredict(input_data, **kwargs)
        elif isinstance(input_data, list):
            return await self.apredict_messages(input_data, **kwargs)
        elif isinstance(input_data, ChatPromptValue):
            # ChatPromptValue를 메시지로 변환
            messages = input_data.to_messages()
            return await self._agenerate_from_messages(messages, **kwargs)
        elif isinstance(input_data, StringPromptValue):
            # StringPromptValue를 문자열로 변환
            return await self.apredict(input_data.text, **kwargs)
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
    
    async def _agenerate_from_messages(self, messages: List[BaseMessage], **kwargs) -> str:
        """메시지 리스트로부터 응답 생성"""
        # 모델별 특화 파라미터 가져오기
        model_params = get_model_specific_params(self.model_name)
        
        # LangChain 메시지를 OpenAI 형식으로 변환
        openai_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
            else:
                # 기타 메시지 타입은 system으로 처리
                openai_messages.append({"role": "system", "content": msg.content})
        
        # 요청 파라미터 구성
        request_params = {
            "model": self.model_name,
            "messages": openai_messages,
            "temperature": model_params.get("temperature", self.temperature),
            "max_tokens": model_params.get("max_tokens", self.max_tokens),
            "extra_headers": {
                "HTTP-Referer": "https://mma-savant.com",
                "X-Title": "MMA Savant"
            },
            "extra_body": {}
        }
        
        # 바인딩된 도구들이 있는 경우 tools 파라미터 추가
        bound_tools = getattr(self, '_bound_tools', [])
        if bound_tools:
            openai_tools = []
            for tool in bound_tools:
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    tool_def = {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                        }
                    }
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        try:
                            tool_def["function"]["parameters"] = tool.args_schema.model_json_schema()
                        except:
                            pass
                    openai_tools.append(tool_def)
            
            if openai_tools:
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"
        
        # 모델별 특화 파라미터를 extra_body에 추가
        for key, value in model_params.items():
            if key not in ["temperature", "max_tokens"]:
                request_params["extra_body"][key] = value
        
        try:
            # API 호출
            response = await self.client.chat.completions.create(**request_params)
            
            # 응답 처리
            choice = response.choices[0]
            message = choice.message
            
            return message.content or ""
            
        except Exception as e:
            LOGGER.error(f"❌ OpenRouter API call failed: {e}")
            raise
    
    def bind_tools(self, tools, **kwargs):
        """도구 바인딩 (LangChain tool calling agent 요구사항)"""
        # 도구 정보를 저장하고 자기 자신을 반환 (체이닝 패턴)
        bound_llm = self.__class__(
            model_name=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            callback_handler=self.callback_handler
        )
        # 도구 정보 저장
        bound_llm._bound_tools = tools
        bound_llm._bind_kwargs = kwargs
        return bound_llm
    
    def get_bound_tools(self):
        """바인딩된 도구들 반환"""
        return getattr(self, '_bound_tools', [])


def get_model_specific_params(model_name: str) -> Dict[str, Any]:
    """
    모델별 특화 파라미터 반환
    
    Args:
        model_name: 모델 이름
        
    Returns:
        Dict: 모델에 특화된 파라미터들
    """
    model_params = {}
    
    # Llama-4-scout 모델 - extra_body로 특화 파라미터 전달
    if "llama-4-scout" in model_name.lower():
        model_params.update({
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "min_rounds": 1,
            "max_rounds": 10
        })
    
    # Llama-3 계열 모델들
    elif "llama-3" in model_name.lower():
        model_params.update({
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        })
    
    # DeepSeek 모델들
    elif "deepseek" in model_name.lower():
        model_params.update({
            "top_p": 0.95,
            "temperature": 0.6
        })
    
    # GPT-4 계열 모델들
    elif "gpt-4" in model_name.lower():
        model_params.update({
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        })
    
    # Claude 계열 모델들
    elif "claude" in model_name.lower():
        model_params.update({
            "top_p": 0.9,
            "temperature": 0.7
        })
    
    # Mixtral 모델들
    elif "mixtral" in model_name.lower():
        model_params.update({
            "top_p": 0.9,
            "temperature": 0.7
        })
    
    # Gemini 모델들
    elif "gemini" in model_name.lower():
        model_params.update({
            "top_p": 0.95,
            "temperature": 0.7
        })
    
    return model_params


def get_model_info(model_name: str) -> Dict[str, Any]:
    """
    모델 정보 및 권장 설정 반환
    
    Args:
        model_name: 모델 이름
        
    Returns:
        Dict: 모델 정보
    """
    if "llama-4-scout" in model_name.lower():
        return {
            "provider": "Meta",
            "type": "chat",
            "context_length": 8192,
            "description": "Meta의 최신 Llama-4 스카우트 모델",
            "strengths": ["reasoning", "code", "math"],
            "recommended_temp": 0.7
        }
    
    elif "deepseek" in model_name.lower():
        return {
            "provider": "DeepSeek",
            "type": "chat",
            "context_length": 32768,
            "description": "DeepSeek의 고성능 추론 모델",
            "strengths": ["reasoning", "code", "analysis"],
            "recommended_temp": 0.6
        }
    
    elif "gpt-4" in model_name.lower():
        return {
            "provider": "OpenAI",
            "type": "chat",
            "context_length": 128000 if "turbo" in model_name.lower() else 8192,
            "description": "OpenAI의 고성능 GPT-4 모델",
            "strengths": ["general", "creative", "analysis"],
            "recommended_temp": 0.7
        }
    
    else:
        return {
            "provider": "Unknown",
            "type": "chat", 
            "context_length": 4096,
            "description": "일반 채팅 모델",
            "strengths": ["general"],
            "recommended_temp": 0.7
        }


def get_openrouter_llm(
    callback_handler: Callable,
    model_name: str = Config.OPENROUTER_MODEL_NAME,
    api_key: str = Config.OPENROUTER_API_KEY,
    temperature: float = 0.7,
    max_tokens: int = None,
    **kwargs
):
    """
    OpenRouter LLM 생성 (공식 문서 방식 사용)
    
    Args:
        callback_handler: 콜백 핸들러
        model_name: 사용할 모델 (예: deepseek/deepseek-r1-0528-qwen3-8b:free)
        api_key: OpenRouter API 키
        temperature: 생성 온도
        max_tokens: 최대 토큰 수
        **kwargs: 추가 파라미터
    
    Returns:
        OpenRouterLLM: OpenRouter LLM 인스턴스
    """
    LOGGER.info(f"🔧 Creating OpenRouter LLM with model: {model_name}")
    
    # Pydantic 모델에 맞게 키워드 인자로 전달
    return OpenRouterLLM(
        model_name=model_name,
        api_key=api_key,
        base_url=Config.OPENROUTER_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens or 4000,
        callback_handler=callback_handler
    )