from typing import Callable, Dict, Any, Optional

from langchain_huggingface import HuggingFaceEndpoint
from config import Config


def get_huggingface_llm(
    callback_handler: Callable,
    model_name: str = None,
    temperature: float = None,
    max_tokens: int = None,
    huggingface_api_token: str = None,
    **kwargs
) -> HuggingFaceEndpoint:
    """
    HuggingFace API LLM provider - HuggingFace Inference API를 통해 모델 사용
    
    주요 모델 예시:
    - "microsoft/DialoGPT-medium": 대화형 모델
    - "meta-llama/Llama-2-7b-chat-hf": Meta의 Llama 모델
    - "google/flan-t5-large": Google의 T5 모델
    - "mistralai/Mistral-7B-Instruct-v0.1": Mistral 모델
    - "HuggingFaceH4/zephyr-7b-beta": Zephyr 모델
    
    Args:
        callback_handler: 스트리밍을 위한 콜백 핸들러
        model_name: HuggingFace Hub의 모델 이름 (기본값: Config에서 가져옴)
        temperature: 생성 온도 (0.0-1.0)
        max_tokens: 최대 토큰 수
        huggingface_api_token: HuggingFace API 토큰
        **kwargs: 추가 모델 파라미터
        
    Returns:
        설정된 HuggingFaceEndpoint 인스턴스
    """
    # 기본값 설정
    model_name = model_name or Config.HUGGINGFACE_MODEL_NAME
    temperature = temperature if temperature is not None else Config.HUGGINGFACE_TEMPERATURE
    max_tokens = max_tokens or Config.HUGGINGFACE_MAX_TOKENS
    api_token = huggingface_api_token or Config.HUGGINGFACE_API_TOKEN
    
    if not api_token:
        raise ValueError(
            "HuggingFace API token is required. "
            "Set HUGGINGFACE_API_TOKEN environment variable or pass huggingface_api_token parameter."
        )

    # 최종 모델 파라미터
    model_kwargs = {
        **kwargs
    }
    
    try:
        # HuggingFace Inference API 엔드포인트 생성
        return HuggingFaceEndpoint(
            endpoint_url=f"https://api-inference.huggingface.co/models/{model_name}",
            huggingfacehub_api_token=api_token,
            model_kwargs=model_kwargs,
            streaming=True,
        )

    except Exception as e:
        print(f"❌ Error connecting to HuggingFace API for model '{model_name}': {e}")
        print(f"💡 Falling back to default model...")

        # 기본 모델로 폴백
        return HuggingFaceEndpoint(
            endpoint_url="https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            huggingfacehub_api_token=api_token,
            model_kwargs=model_kwargs,
            streaming=True,
        )


def get_chat_model_llm(
    callback_handler: Callable,
    model_name: str,
    huggingface_api_token: str = None,
    **kwargs
) -> HuggingFaceEndpoint:
    """
    채팅 특화 모델들을 위한 편의 함수
    
    Args:
        callback_handler: 콜백 핸들러
        model_name: 모델 이름
        **kwargs: 추가 파라미터
    """
    
    return get_huggingface_llm(
        callback_handler=callback_handler,
        model_name=model_name,
        huggingface_api_token=huggingface_api_token,
        **kwargs
    )