"""
LLM 모델 및 콜백 핸들러 생성 팩토리
다양한 프로바이더를 지원하며 환경 변수를 통한 동적 모델 선택 제공
"""
from typing import List, Tuple, Dict, Any, Optional
from enum import Enum

from config import Config
from common.logging_config import get_logger
from llm.providers import get_anthropic_llm, get_huggingface_llm, get_chat_model_llm
from llm.callbacks import get_anthropic_callback_handler, get_huggingface_callback_handler

LOGGER = get_logger(__name__)


class LLMProvider(Enum):
    """지원되는 LLM 프로바이더"""
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"  # 향후 확장용


def create_llm_with_callbacks(
    message_id: str,
    session_id: str,
    provider: Optional[str] = None,
    **model_kwargs
) -> Tuple[Any, Any]:
    """
    프로바이더에 따른 LLM과 콜백 핸들러 생성
    
    Args:
        message_id: 메시지 ID
        session_id: 세션 ID  
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
            return get_anthropic_model_and_callback(message_id, session_id, **model_kwargs)
            
        elif selected_provider == LLMProvider.HUGGINGFACE.value:
            return get_huggingface_model_and_callback(message_id, session_id, **model_kwargs)
            
        elif selected_provider == LLMProvider.OPENAI.value:
            return get_openai_model_and_callback(message_id, session_id, **model_kwargs)
            
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
    session_id: str,
    **kwargs
) -> Tuple[Any, Any]:
    """
    Anthropic 모델과 콜백 생성
    
    Args:
        message_id: 메시지 ID
        session_id: 세션 ID
        **kwargs: 추가 모델 파라미터 (온도, 최대 토큰 등)
        
    Returns:
        Tuple[AnthropicLLM, AnthropicCallbackHandler]
    """
    # 설정 검증
    if not validate_provider_config(LLMProvider.ANTHROPIC.value):
        raise ValueError("Anthropic configuration is invalid. Check ANTHROPIC_API_KEY.")
    
    try:
        # 콜백 핸들러 생성
        callback_handler = get_anthropic_callback_handler(message_id, session_id)
        
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
    session_id: str, 
    model_name: Optional[str] = None,
    **kwargs
) -> Tuple[Any, Any]:
    """
    HuggingFace 모델과 콜백 생성
    
    Args:
        message_id: 메시지 ID
        session_id: 세션 ID
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
            session_id, 
            model_name=final_model_name
        )
        
        # API 토큰 검증
        if not validate_huggingface_api_config():
            LOGGER.warning("⚠️ HuggingFace API token not configured, using public models only")
        
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


def get_openai_model_and_callback(
    message_id: str, 
    session_id: str,
    **kwargs
) -> Tuple[Any, Any]:
    """
    OpenAI 모델과 콜백 생성 (향후 확장용)
    
    Args:
        message_id: 메시지 ID
        session_id: 세션 ID
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
        
        # API 토큰은 선택사항 (public 모델 사용 가능)
        return True
        
    elif provider == LLMProvider.OPENAI.value:
        valid = bool(Config.OPENAI_API_KEY and Config.OPENAI_API_KEY.strip())
        if not valid:
            LOGGER.warning("⚠️ OpenAI API key not configured")
        return valid
        
    else:
        LOGGER.warning(f"⚠️ Unknown provider: {provider}")
        return False


def get_provider_info() -> Dict[str, Dict[str, Any]]:
    """
    모든 프로바이더의 상세 정보 반환
    
    Returns:
        Dict: 프로바이더별 정보 (설정 상태, 사용 가능 여부 등)
    """
    info = {}
    
    for provider in LLMProvider:
        provider_name = provider.value
        is_available = provider_name in get_available_providers()
        is_configured = validate_provider_config(provider_name)
        
        provider_info = {
            "available": is_available,
            "configured": is_configured,
            "description": _get_provider_description(provider_name)
        }
        
        # 프로바이더별 추가 정보
        if provider_name == LLMProvider.ANTHROPIC.value:
            provider_info.update({
                "model_name": getattr(Config, 'ANTHROPIC_MODEL_NAME', 'Not configured'),
                "api_key_configured": bool(getattr(Config, 'ANTHROPIC_API_KEY', None))
            })
        elif provider_name == LLMProvider.HUGGINGFACE.value:
            provider_info.update({
                "model_name": Config.HUGGINGFACE_MODEL_NAME,
                "api_token_configured": bool(Config.HUGGINGFACE_API_TOKEN),
                "max_tokens": Config.HUGGINGFACE_MAX_TOKENS,
                "temperature": Config.HUGGINGFACE_TEMPERATURE,
                "api_mode": "inference_api"
            })
        elif provider_name == LLMProvider.OPENAI.value:
            provider_info.update({
                "model_name": getattr(Config, 'OPENAI_MODEL_NAME', 'Not configured'),
                "api_key_configured": bool(getattr(Config, 'OPENAI_API_KEY', None))
            })
            
        info[provider_name] = provider_info
    
    return info


def validate_huggingface_api_config() -> bool:
    """
    HuggingFace API 설정 유효성 검사
    
    Returns:
        bool: API 토큰이 설정되어 있는지 여부
    """
    return bool(Config.HUGGINGFACE_API_TOKEN and Config.HUGGINGFACE_API_TOKEN.strip())


def _get_provider_description(provider: str) -> str:
    """프로바이더 설명 반환"""
    descriptions = {
        LLMProvider.ANTHROPIC.value: "Claude models from Anthropic - high quality reasoning and analysis",
        LLMProvider.HUGGINGFACE.value: "Open source models from HuggingFace Inference API - cloud-based execution",
        LLMProvider.OPENAI.value: "GPT models from OpenAI - powerful general purpose AI (coming soon)"
    }
    return descriptions.get(provider, "Unknown provider")


if __name__ == "__main__":
    """테스트 및 디버깅용"""
    print("🏭 Model Factory Test")
    print("=" * 50)
    
    print("\n📋 Available Providers:")
    available = get_available_providers()
    for provider in available:
        print(f"  ✅ {provider}")
    
    # print(f"\n🎯 Recommended Provider: {get_recommended_provider()}")  # 함수가 없어서 주석처리
    
    print(f"\n🔧 Current Configuration:")
    print(f"  LLM_PROVIDER: {Config.LLM_PROVIDER}")
    print(f"  ANTHROPIC_API_KEY configured: {bool(getattr(Config, 'ANTHROPIC_API_KEY', None))}")
    print(f"  HUGGINGFACE_MODEL_NAME: {Config.HUGGINGFACE_MODEL_NAME}")
    
    print("\n📊 Provider Details:")
    info = get_provider_info()
    for provider, details in info.items():
        print(f"  {provider}:")
        for key, value in details.items():
            print(f"    {key}: {value}")