from enum import Enum

class WeightClassEnum(str, Enum):
    """UFC 체급 Enum"""
    FLYWEIGHT = "flyweight"
    BANTAMWEIGHT = "bantamweight"
    FEATHERWEIGHT = "featherweight"
    LIGHTWEIGHT = "lightweight"
    WELTERWEIGHT = "welterweight"
    MIDDLEWEIGHT = "middleweight"
    LIGHT_HEAVYWEIGHT = "light heavyweight"
    HEAVYWEIGHT = "heavyweight"
    WOMENS_STRAWWEIGHT = "women's strawweight"
    WOMENS_FLYWEIGHT = "women's flyweight"
    WOMENS_BANTAMWEIGHT = "women's bantamweight"
    WOMENS_FEATHERWEIGHT = "women's featherweight"
    CATCH_WEIGHT = "catch weight"
    OPEN_WEIGHT = "open weight"
    MENS_POUND_FOR_POUND = "men's pound-for-pound"
    WOMENS_POUND_FOR_POUND = "women's pound-for-pound"

class LLMProvider(str, Enum):
    """지원되는 LLM 프로바이더"""
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    OPENAI = "openai"