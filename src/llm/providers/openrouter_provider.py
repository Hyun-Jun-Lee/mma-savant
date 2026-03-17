from typing import Callable, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from config import Config
from common.logging_config import get_logger

LOGGER = get_logger(__name__)




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


# create_react_prompt_template 함수는 llm.prompts.create_phase1_prompt_template()로 이동됨


def get_openrouter_llm(
    callback_handler: Callable,
    model_name: str = Config.OPENROUTER_MODEL_NAME,
    api_key: str = Config.OPENROUTER_API_KEY,
    temperature: float = 0.7,
    max_tokens: int = None,
    **kwargs
):
    """
    OpenRouter LLM 생성 - 표준 ChatOpenAI 사용 (ReAct 에이전트용)

    주요 기능:
    - test_openrouter_2.py에서 검증된 안정적인 표준 ChatOpenAI 사용
    - 모델별 특화 파라미터 자동 적용
    - 스트리밍 및 콜백 핸들러 완전 지원
    - OpenRouter 최적화 헤더 설정

    Args:
        callback_handler: 스트리밍용 콜백 핸들러
        model_name: 사용할 모델 (예: deepseek/deepseek-chat-v3-0324:free)
        api_key: OpenRouter API 키
        temperature: 생성 온도 (모델별 최적값 자동 적용)
        max_tokens: 최대 토큰 수

    Returns:
        ChatOpenAI: OpenRouter LLM 인스턴스

    Example:
        >>> from llm.callbacks.openrouter_callback import get_openrouter_callback_handler
        >>> callback = get_openrouter_callback_handler("msg_123", "session_456", "deepseek/deepseek-chat")
        >>> llm = get_openrouter_llm(callback, "deepseek/deepseek-chat")
        >>> # 항상 ReAct 에이전트와 함께 사용
    """
    LOGGER.info(f"🔧 Creating OpenRouter LLM with model: {model_name}")

    # 모델별 특화 파라미터 적용
    model_params = get_model_specific_params(model_name)
    effective_temperature = model_params.get("temperature", temperature)
    effective_max_tokens = model_params.get("max_tokens", max_tokens or 4000)

    LOGGER.info(f"📱 Using ChatOpenAI for ReAct agent with temp={effective_temperature}, max_tokens={effective_max_tokens}")

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=Config.OPENROUTER_BASE_URL,
        temperature=effective_temperature,
        max_tokens=effective_max_tokens,
        default_headers={
            "HTTP-Referer": "https://mma-savant.com",
            "X-Title": "MMA Savant"
        },
        streaming=True,
    )