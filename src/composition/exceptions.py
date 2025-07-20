"""
Composition domain specific exceptions.

The composition layer orchestrates cross-domain operations and may encounter
various types of errors from the underlying domains it coordinates.
"""
from typing import Optional, Dict, Any


class CompositionException(Exception):
    """Base exception for all composition layer errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CompositionValidationError(CompositionException):
    """Exception raised when composition operation input validation fails."""
    
    def __init__(self, parameter: str, value: Any, reason: str):
        self.parameter = parameter
        self.value = value
        self.reason = reason
        message = f"Validation failed for parameter '{parameter}': {reason}"
        super().__init__(message, {"parameter": parameter, "value": value, "reason": reason})


class CompositionNotFoundError(CompositionException):
    """Exception raised when composition operation cannot find required data."""
    
    def __init__(self, resource_type: str, identifier: Any, context: Optional[str] = None):
        self.resource_type = resource_type
        self.identifier = identifier
        self.context = context
        message = f"{resource_type} not found: {identifier}"
        if context:
            message += f" (Context: {context})"
        super().__init__(message, {"resource_type": resource_type, "identifier": identifier, "context": context})


class CompositionQueryError(CompositionException):
    """Exception raised when composition operation encounters database/query errors."""
    
    def __init__(self, operation: str, parameters: Dict[str, Any], original_error: str):
        self.operation = operation
        self.parameters = parameters
        self.original_error = original_error
        message = f"Composition query '{operation}' failed: {original_error}"
        super().__init__(message, {"operation": operation, "parameters": parameters, "original_error": original_error})


class CompositionDataIntegrityError(CompositionException):
    """Exception raised when composition operation encounters data integrity issues."""
    
    def __init__(self, operation: str, issue: str, data_context: Dict[str, Any]):
        self.operation = operation
        self.issue = issue
        self.data_context = data_context
        message = f"Data integrity issue in '{operation}': {issue}"
        super().__init__(message, {"operation": operation, "issue": issue, "data_context": data_context})


class CompositionDomainError(CompositionException):
    """Exception raised when underlying domain operations fail during composition."""
    
    def __init__(self, domain: str, operation: str, original_error: str):
        self.domain = domain
        self.operation = operation
        self.original_error = original_error
        message = f"Domain '{domain}' error in operation '{operation}': {original_error}"
        super().__init__(message, {"domain": domain, "operation": operation, "original_error": original_error})


class CompositionConfigurationError(CompositionException):
    """Exception raised when composition operation encounters configuration issues."""
    
    def __init__(self, configuration_key: str, issue: str):
        self.configuration_key = configuration_key
        self.issue = issue
        message = f"Configuration error for '{configuration_key}': {issue}"
        super().__init__(message, {"configuration_key": configuration_key, "issue": issue})


class CompositionResourceLimitError(CompositionException):
    """Exception raised when composition operation exceeds resource limits."""
    
    def __init__(self, resource_type: str, limit: int, requested: int):
        self.resource_type = resource_type
        self.limit = limit
        self.requested = requested
        message = f"Resource limit exceeded for '{resource_type}': requested {requested}, limit {limit}"
        super().__init__(message, {"resource_type": resource_type, "limit": limit, "requested": requested})


class CompositionTimeoutError(CompositionException):
    """Exception raised when composition operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message, {"operation": operation, "timeout_seconds": timeout_seconds})


class CompositionPermissionError(CompositionException):
    """Exception raised when composition operation lacks required permissions."""
    
    def __init__(self, operation: str, required_permission: str, context: Optional[str] = None):
        self.operation = operation
        self.required_permission = required_permission
        self.context = context
        message = f"Permission denied for operation '{operation}': requires '{required_permission}'"
        if context:
            message += f" (Context: {context})"
        super().__init__(message, {"operation": operation, "required_permission": required_permission, "context": context})


class FighterComparisonError(CompositionException):
    """Exception raised when fighter comparison operations fail."""
    
    def __init__(self, fighter1_id: int, fighter2_id: int, reason: str):
        self.fighter1_id = fighter1_id
        self.fighter2_id = fighter2_id
        self.reason = reason
        message = f"Fighter comparison failed between {fighter1_id} and {fighter2_id}: {reason}"
        super().__init__(message, {"fighter1_id": fighter1_id, "fighter2_id": fighter2_id, "reason": reason})


# Backward compatibility aliases if any existing code uses these
ComposerException = CompositionException
ComposerValidationError = CompositionValidationError
ComposerNotFoundError = CompositionNotFoundError
ComposerQueryError = CompositionQueryError