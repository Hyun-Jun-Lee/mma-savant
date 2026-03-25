"""
LLM 모델 및 콜백 핸들러 생성 팩토리
다양한 프로바이더를 지원하며 환경 변수를 통한 동적 모델 선택 제공
"""
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum

from config import Config
from common.logging_config import get_logger
from common.enums import LLMProvider
from llm.providers import get_anthropic_llm, get_huggingface_llm, get_chat_model_llm
from llm.providers.openrouter_provider import get_openrouter_llm
from llm.callbacks import get_anthropic_callback_handler, get_huggingface_callback_handler
from llm.callbacks.openrouter_callback import get_openrouter_callback_handler

LOGGER = get_logger(__name__)





def create_llm_with_callbacks(
    message_id: str,
    conversation_id : int,
    provider: Optional[str] = None,
    **model_kwargs
) -> Tuple[Any, Any]:
    """
    프로바이더에 따른 LLM과 콜백 핸들러 생성
    
    Args:
        message_id: 메시지 ID
        conversation_id: 세션 ID  
        provider: LLM 프로바이더 (None이면 Config.LLM_PROVIDER 사용)
        **model_kwargs: 모델별 추가 파라미터
        
    Returns:
        Tuple[LLM, CallbackHandler]: 생성된 LLM과 콜백 핸들러
        
    Raises:
        ValueError: 지원하지 않는 프로바이더이거나 설정이 잘못된 경우
        ImportError: 필요한 라이브러리가 설치되지 않은 경우
    """
    # 프로바이더 결정
    selected_provider = provider or Config.LLM_PROVIDER
    
    LOGGER.info(f"🏭 Creating LLM with provider: {selected_provider}")
    
    try:
        if selected_provider == LLMProvider.ANTHROPIC.value:
            return get_anthropic_model_and_callback(message_id, conversation_id, **model_kwargs)
            
        elif selected_provider == LLMProvider.HUGGINGFACE.value:
            return get_huggingface_model_and_callback(message_id, conversation_id, **model_kwargs)
            
        elif selected_provider == LLMProvider.OPENROUTER.value:
            return get_openrouter_model_and_callback(message_id, conversation_id, **model_kwargs)
            
        elif selected_provider == LLMProvider.OPENAI.value:
            return get_openai_model_and_callback(message_id, conversation_id, **model_kwargs)
            
        else:
            available = [p.value for p in LLMProvider]
            raise ValueError(f"Unsupported provider: {selected_provider}. Available: {available}")
            
    except ImportError as e:
        LOGGER.error(f"❌ Missing required library for provider {selected_provider}: {e}")
        raise ImportError(f"Provider {selected_provider} requires additional libraries. {e}")
    except Exception as e:
        LOGGER.error(f"❌ Error creating LLM for provider {selected_provider}: {e}")
        raise


def get_anthropic_model_and_callback(
    message_id: str, 
    conversation_id : int,
    **kwargs
) -> Tuple[Any, Any]:
    """
    Anthropic 모델과 콜백 생성
    
    Args:
        message_id: 메시지 ID
        conversation_id: 세션 ID
        **kwargs: 추가 모델 파라미터 (온도, 최대 토큰 등)
        
    Returns:
        Tuple[AnthropicLLM, AnthropicCallbackHandler]
    """
    # 설정 검증
    if not validate_provider_config(LLMProvider.ANTHROPIC.value):
        raise ValueError("Anthropic configuration is invalid. Check ANTHROPIC_API_KEY.")
    
    try:
        # 콜백 핸들러 생성
        callback_handler = get_anthropic_callback_handler(message_id, conversation_id)
        
        # 모델별 파라미터 적용
        model_params = {
            "callback_handler": callback_handler,
            **kwargs
        }
        
        # LLM 생성
        llm = get_anthropic_llm(**model_params)
        
        LOGGER.info(f"✅ Anthropic LLM created successfully")
        return llm, callback_handler
        
    except ImportError as e:
        LOGGER.error(f"❌ Failed to import Anthropic modules: {e}")
        raise ImportError("Anthropic provider requires 'anthropic' package")
    except Exception as e:
        LOGGER.error(f"❌ Error creating Anthropic model: {e}")
        raise


def get_huggingface_model_and_callback(
    message_id: str,
    conversation_id : int, 
    model_name: Optional[str] = None,
    **kwargs
) -> Tuple[Any, Any]:
    """
    HuggingFace 모델과 콜백 생성
    
    Args:
        message_id: 메시지 ID
        conversation_id: 세션 ID
        model_name: 모델 이름 (None이면 Config.HUGGINGFACE_MODEL_NAME 사용)
        **kwargs: 추가 모델 파라미터
        
    Returns:
        Tuple[HuggingFaceEndpoint, HuggingFaceCallbackHandler]
    """
    # 모델 이름 결정
    final_model_name = model_name or Config.HUGGINGFACE_MODEL_NAME
    
    try:
        
        # 콜백 핸들러 생성
        callback_handler = get_huggingface_callback_handler(
            message_id, 
            conversation_id, 
            model_name=final_model_name
        )

        # 설정에서 기본 파라미터 가져오기 (API 방식)
        model_params = {
            "callback_handler": callback_handler,
            "model_name": final_model_name,
            "temperature": kwargs.get("temperature", Config.HUGGINGFACE_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", Config.HUGGINGFACE_MAX_TOKENS),
            "huggingface_api_token": kwargs.get("huggingface_api_token", Config.HUGGINGFACE_API_TOKEN),
            **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens", "huggingface_api_token"]}
        }
        
        # LLM 생성 (Chat 모델 사용)
        if kwargs.get("use_chat_model", True):
            # 채팅 최적화 모델 사용
            model_type = kwargs.get("model_type", "dialogpt")
            model_size = kwargs.get("model_size", "medium")
            llm = get_chat_model_llm(
                callback_handler=callback_handler,
                model_type=model_type,
                size=model_size,
                huggingface_api_token=model_params["huggingface_api_token"],
                temperature=model_params["temperature"],
                max_tokens=model_params["max_tokens"]
            )
        else:
            # 직접 모델 지정
            llm = get_huggingface_llm(**model_params)
        
        LOGGER.info(f"✅ HuggingFace LLM created: {final_model_name}")
        return llm, callback_handler
        
    except ImportError as e:
        LOGGER.error(f"❌ Failed to import HuggingFace modules: {e}")
        raise ImportError("HuggingFace provider requires 'langchain-huggingface' package")
    except Exception as e:
        LOGGER.error(f"❌ Error creating HuggingFace model: {e}")
        raise


def get_openrouter_model_and_callback(
    message_id: str,
    conversation_id : int,
    model_name: Optional[str] = None,
    **kwargs
) -> Tuple[Any, Any]:
    """
    OpenRouter 모델과 콜백 생성
    
    Args:
        message_id: 메시지 ID
        conversation_id: 세션 ID
        model_name: 모델 이름 (None이면 Config.OPENROUTER_MODEL_NAME 사용)
        **kwargs: 추가 모델 파라미터
        
    Returns:
        Tuple[ChatOpenAI, OpenRouterCallbackHandler]
    """
    # 설정 검증
    if not validate_provider_config(LLMProvider.OPENROUTER.value):
        raise ValueError("OpenRouter configuration is invalid. Check OPENROUTER_API_KEY.")
    
    # 모델 이름 결정
    final_model_name = model_name or Config.OPENROUTER_MODEL_NAME
    
    try:
        # 콜백 핸들러 생성
        callback_handler = get_openrouter_callback_handler(
            message_id=message_id,
            conversation_id=conversation_id,
            model_name=final_model_name
        )
        
        # 모델 파라미터 설정
        model_params = {
            "callback_handler": callback_handler,
            "model_name": final_model_name,
            "api_key": kwargs.get("api_key", Config.OPENROUTER_API_KEY),
            "temperature": kwargs.get("temperature", Config.DEFAULT_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", Config.DEFAULT_MAX_TOKENS),
            **{k: v for k, v in kwargs.items() if k not in ["api_key", "temperature", "max_tokens"]}
        }
        
        # LLM 생성
        llm = get_openrouter_llm(**model_params)
        
        LOGGER.info(f"✅ OpenRouter LLM created: {final_model_name}")
        return llm, callback_handler
        
    except ImportError as e:
        LOGGER.error(f"❌ Failed to import OpenRouter modules: {e}")
        raise ImportError("OpenRouter provider requires 'langchain-openai' package")
    except Exception as e:
        LOGGER.error(f"❌ Error creating OpenRouter model: {e}")
        raise


def get_openai_model_and_callback(
    message_id: str, 
    conversation_id : int,
    **kwargs
) -> Tuple[Any, Any]:
    """
    OpenAI 모델과 콜백 생성 (향후 확장용)
    
    Args:
        message_id: 메시지 ID
        conversation_id: 세션 ID
        **kwargs: 추가 모델 파라미터
        
    Returns:
        Tuple[OpenAILLM, OpenAICallbackHandler]
        
    Raises:
        NotImplementedError: 아직 구현되지 않음
    """
    # 설정 검증
    if not validate_provider_config(LLMProvider.OPENAI.value):
        raise ValueError("OpenAI configuration is invalid. Check OPENAI_API_KEY.")
    
    # TODO: OpenAI 구현
    raise NotImplementedError("OpenAI provider will be implemented in future versions")


def _parse_model_spec(spec: str) -> tuple[str, str]:
    """환경변수에서 프로바이더와 모델명을 분리

    'openrouter/google/gemini-3-flash-preview'
      -> ('openrouter', 'google/gemini-3-flash-preview')
    'anthropic/claude-sonnet-4-5-20250929'
      -> ('anthropic', 'claude-sonnet-4-5-20250929')
    """
    parts = spec.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid model spec: {spec}. Expected 'provider/model_name'")
    return parts[0], parts[1]


def _create_model_from_spec(provider: str, model_name: str):
    """프로바이더와 모델명으로 LLM 인스턴스 생성 (콜백 없는 순수 모델)"""
    if provider == LLMProvider.OPENROUTER.value:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            temperature=Config.DEFAULT_TEMPERATURE,
            max_tokens=Config.DEFAULT_MAX_TOKENS,
            default_headers={
                "HTTP-Referer": "https://mma-savant.com",
                "X-Title": "MMA Savant",
            },
            streaming=True,
        )
    elif provider == LLMProvider.ANTHROPIC.value:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=Config.ANTHROPIC_API_KEY,
            model=model_name,
            temperature=Config.DEFAULT_TEMPERATURE,
            max_tokens=Config.DEFAULT_MAX_TOKENS,
            streaming=True,
        )
    elif provider == LLMProvider.OPENAI.value:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=Config.OPENAI_API_KEY,
            temperature=Config.DEFAULT_TEMPERATURE,
            max_tokens=Config.DEFAULT_MAX_TOKENS,
            streaming=True,
        )
    else:
        available = [p.value for p in LLMProvider]
        raise ValueError(f"Unsupported provider: {provider}. Available: {available}")


def get_main_model():
    """MAIN_MODEL 환경변수로 모델 생성"""
    if not Config.MAIN_MODEL:
        raise ValueError("MAIN_MODEL environment variable is not set")
    provider, model_name = _parse_model_spec(Config.MAIN_MODEL)
    LOGGER.info(f"🏭 Creating MAIN model: {provider}/{model_name}")
    return _create_model_from_spec(provider, model_name)


def get_sub_model():
    """SUB_MODEL 환경변수로 모델 생성"""
    if not Config.SUB_MODEL:
        raise ValueError("SUB_MODEL environment variable is not set")
    provider, model_name = _parse_model_spec(Config.SUB_MODEL)
    LOGGER.info(f"🏭 Creating SUB model: {provider}/{model_name}")
    return _create_model_from_spec(provider, model_name)


def get_available_providers() -> List[str]:
    """
    사용 가능한 프로바이더 목록 반환
    
    설정이 올바르게 되어있고 필요한 라이브러리가 설치된 프로바이더만 반환
    
    Returns:
        List[str]: 사용 가능한 프로바이더 목록
    """
    available = []
    
    for provider in LLMProvider:
        try:
            if validate_provider_config(provider.value):
                # 실제 import 테스트
                if provider == LLMProvider.ANTHROPIC:
                    available.append(provider.value)
                    
                elif provider == LLMProvider.HUGGINGFACE:
                    available.append(provider.value)
                    
                elif provider == LLMProvider.OPENROUTER:
                    available.append(provider.value)
                    
                elif provider == LLMProvider.OPENAI:
                    # TODO: OpenAI import 테스트
                    pass
                    
        except ImportError:
            LOGGER.debug(f"Provider {provider.value} not available due to missing dependencies")
        except Exception as e:
            LOGGER.debug(f"Provider {provider.value} not available: {e}")
    
    LOGGER.info(f"🔍 Available providers: {available}")
    return available


def validate_provider_config(provider: str) -> bool:
    """
    프로바이더 설정 유효성 검사
    
    Args:
        provider: 프로바이더 이름
        
    Returns:
        bool: 설정이 유효한지 여부
    """
    if provider == LLMProvider.ANTHROPIC.value:
        valid = bool(Config.ANTHROPIC_API_KEY and Config.ANTHROPIC_API_KEY.strip())
        if not valid:
            LOGGER.warning("⚠️ Anthropic API key not configured")
        return valid
        
    elif provider == LLMProvider.HUGGINGFACE.value:
        # 모델 이름 설정 확인
        model_configured = bool(Config.HUGGINGFACE_MODEL_NAME and Config.HUGGINGFACE_MODEL_NAME.strip())
        if not model_configured:
            LOGGER.warning("⚠️ HuggingFace model name not configured")
            return False
        
        return True
        
    elif provider == LLMProvider.OPENROUTER.value:
        valid = bool(Config.OPENROUTER_API_KEY and Config.OPENROUTER_API_KEY.strip())
        if not valid:
            LOGGER.warning("⚠️ OpenRouter API key not configured")
        return valid
        
    elif provider == LLMProvider.OPENAI.value:
        valid = bool(Config.OPENAI_API_KEY and Config.OPENAI_API_KEY.strip())
        if not valid:
            LOGGER.warning("⚠️ OpenAI API key not configured")
        return valid
        
    else:
        LOGGER.warning(f"⚠️ Unknown provider: {provider}")
        return False