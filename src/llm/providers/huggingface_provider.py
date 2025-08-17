from typing import Callable, Dict, Any, Optional

from langchain_huggingface import HuggingFacePipeline
from config import Config


def get_huggingface_llm(
    callback_handler: Callable,
    model_name: str = "microsoft/DialoGPT-medium",
    temperature: float = 0.7,
    max_tokens: int = 4000,
    device: int = -1,  # -1 for CPU, 0+ for GPU
    task: str = "text-generation",
    **kwargs
) -> HuggingFacePipeline:
    """
    HuggingFace LLM provider - 모든 주요 LLM 모델들을 지원
    
    주요 모델 예시:
    - "microsoft/DialoGPT-medium": 대화형 모델
    - "meta-llama/Llama-2-7b-chat-hf": Meta의 Llama 모델
    - "google/flan-t5-large": Google의 T5 모델
    - "openai-gpt": OpenAI 스타일 모델
    - "EleutherAI/gpt-neo-2.7B": EleutherAI GPT
    
    Args:
        callback_handler: 스트리밍을 위한 콜백 핸들러
        model_name: HuggingFace Hub의 모델 이름
        temperature: 생성 온도 (0.0-1.0)
        max_tokens: 최대 토큰 수
        device: 추론 디바이스 (-1=CPU, 0+=GPU)
        task: HuggingFace 파이프라인 태스크
        **kwargs: 추가 모델 파라미터
        
    Returns:
        설정된 HuggingFacePipeline 인스턴스
    """
    from transformers import pipeline
    
    # 모델별 기본 설정
    model_configs = {
        "microsoft/DialoGPT-medium": {
            "task": "text-generation",
            "pad_token_id": 50256
        },
        "meta-llama/Llama-2-7b-chat-hf": {
            "task": "text-generation",
            "do_sample": True,
            "top_p": 0.9
        },
        "google/flan-t5-large": {
            "task": "text2text-generation",
            "do_sample": True
        },
        "EleutherAI/gpt-neo-2.7B": {
            "task": "text-generation",
            "do_sample": True
        }
    }
    
    # 모델별 설정 적용
    config = model_configs.get(model_name, {"task": task})
    final_task = config.get("task", task)
    
    # 모델 파라미터 설정
    model_kwargs = {
        "temperature": temperature,
        "max_length": max_tokens,
        **config,
        **kwargs
    }
    
    # task 제거 (pipeline 파라미터이므로)
    model_kwargs.pop("task", None)
    
    try:
        # HuggingFace 파이프라인 생성
        hf_pipeline = pipeline(
            final_task,
            model=model_name,
            device=device,
            model_kwargs=model_kwargs
        )
        
        # LangChain 래퍼 생성
        return HuggingFacePipeline(
            pipeline=hf_pipeline,
            callbacks=[callback_handler]
        )
        
    except Exception as e:
        print(f"❌ Error loading HuggingFace model '{model_name}': {e}")
        print(f"💡 Falling back to default model...")
        
        # 기본 모델로 폴백
        fallback_pipeline = pipeline(
            "text-generation",
            model="microsoft/DialoGPT-medium",
            device=device,
            model_kwargs={
                "temperature": temperature,
                "max_length": max_tokens,
                "pad_token_id": 50256
            }
        )
        
        return HuggingFacePipeline(
            pipeline=fallback_pipeline,
            callbacks=[callback_handler]
        )


def get_chat_model_llm(
    callback_handler: Callable,
    model_type: str = "llama",
    size: str = "7b",
    **kwargs
) -> HuggingFacePipeline:
    """
    채팅 특화 모델들을 위한 편의 함수
    
    Args:
        callback_handler: 콜백 핸들러
        model_type: 모델 타입 (llama, flan-t5, dialogpt)
        size: 모델 크기 (7b, 13b, large, medium 등)
        **kwargs: 추가 파라미터
    """
    
    model_map = {
        "llama": {
            "7b": "meta-llama/Llama-2-7b-chat-hf",
            "13b": "meta-llama/Llama-2-13b-chat-hf"
        },
        "flan-t5": {
            "small": "google/flan-t5-small",
            "base": "google/flan-t5-base", 
            "large": "google/flan-t5-large",
            "xl": "google/flan-t5-xl"
        },
        "dialogpt": {
            "small": "microsoft/DialoGPT-small",
            "medium": "microsoft/DialoGPT-medium",
            "large": "microsoft/DialoGPT-large"
        },
        "gpt-neo": {
            "1.3b": "EleutherAI/gpt-neo-1.3B",
            "2.7b": "EleutherAI/gpt-neo-2.7B"
        }
    }
    
    model_name = model_map.get(model_type, {}).get(size)
    if not model_name:
        print(f"❌ Unknown model combination: {model_type}/{size}")
        model_name = "microsoft/DialoGPT-medium"  # 기본값
    
    return get_huggingface_llm(
        callback_handler=callback_handler,
        model_name=model_name,
        **kwargs
    )


def list_popular_models() -> Dict[str, Dict[str, str]]:
    """인기 있는 HuggingFace 모델들 목록 반환"""
    return {
        "chat_models": {
            "llama2_7b": "meta-llama/Llama-2-7b-chat-hf",
            "llama2_13b": "meta-llama/Llama-2-13b-chat-hf", 
            "dialogpt_medium": "microsoft/DialoGPT-medium",
            "dialogpt_large": "microsoft/DialoGPT-large"
        },
        "instruction_models": {
            "flan_t5_large": "google/flan-t5-large",
            "flan_t5_xl": "google/flan-t5-xl",
            "alpaca": "tatsu-lab/alpaca-7b-wdiff"
        },
        "general_models": {
            "gpt_neo_2.7b": "EleutherAI/gpt-neo-2.7B",
            "gpt_j_6b": "EleutherAI/gpt-j-6B",
            "opt_2.7b": "facebook/opt-2.7b"
        },
        "lightweight_models": {
            "distilgpt2": "distilgpt2",
            "gpt2_medium": "gpt2-medium",
            "dialogpt_small": "microsoft/DialoGPT-small"
        }
    }