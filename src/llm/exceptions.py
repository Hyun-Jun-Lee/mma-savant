"""
Custom exceptions for MMA Savant Two-Phase Reasoning System
All exceptions include detailed information in the message for traceback-based debugging
"""


class LLMException(Exception):
    """Base exception for MMA Savant application"""
    def __init__(self, message: str):
        self.message = message
        self.error_class = self.__class__.__name__
        super().__init__(self.message)


# =============================================================================
# Phase 1 Exceptions
# =============================================================================

class AIReasoningException(LLMException):
    """AI reasoning validation failures in Phase 1"""
    def __init__(self, reasoning_output: str):
        detailed_message = (
            f"AI reasoning validation failed\n"
            f"Reasoning output: '{reasoning_output}'\n"
        )
        super().__init__(detailed_message)


class IntermediateStepsException(LLMException):
    """Empty or missing intermediate steps in ReAct agent"""
    def __init__(self):
        detailed_message = (
            f"No intermediate steps recorded by ReAct agent\n"
        )
        super().__init__(detailed_message)


class SQLExecutionException(LLMException):
    """SQL execution failures in Phase 1"""
    def __init__(self, query: str, original_error: str):
        detailed_message = (
            f"SQL execution failed: {original_error}\n"
            f"Failed query: {query}"
        )
        super().__init__(detailed_message)


class SQLResultExtractionException(LLMException):
    """Failed to extract SQL results from intermediate steps"""
    def __init__(self, intermediate_steps_count: int):
        detailed_message = (
            f"Failed to extract SQL results from agent intermediate steps\n"
            f"Intermediate steps count: {intermediate_steps_count}\n"
        )
        super().__init__(detailed_message)


# =============================================================================
# Phase 2 Exceptions
# =============================================================================

class LLMResponseException(LLMException):
    """LLM response failures in Phase 2"""
    def __init__(self, response_content: str):
        detailed_message = (
            f"LLM response validation failed in Phase 2\n"
            f"Response content: '{response_content}'\n"
            f"Response length: {len(response_content)}\n"
        )
        super().__init__(detailed_message)


class JSONParsingException(LLMException):
    """JSON parsing failures in Phase 2"""
    def __init__(self, response_text: str, json_error: str):
        detailed_message = (
            f"JSON parsing failed in Phase 2\n"
            f"JSON error: {json_error}\n"
        )
        super().__init__(detailed_message)


class VisualizationValidationException(LLMException):
    """Unsupported visualization type selected"""
    def __init__(self, visualization_type: str, supported_types: list):
        detailed_message = (
            f"Unsupported visualization type selected\n"
            f"Selected type: {visualization_type}\n"
            f"Supported types: {', '.join(supported_types)}\n"
        )
        super().__init__(detailed_message)