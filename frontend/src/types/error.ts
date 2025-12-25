/**
 * Backend Error Response Types and Message Mapping
 */

export interface ErrorResponse {
  error: boolean
  error_class: string
  traceback: string
}

export const ERROR_MESSAGES: Record<string, string> = {
  // Phase 1 Errors - 데이터 수집 단계
  'AIReasoningException': 'AI가 질문을 분석하는 중 문제가 발생했습니다. 더 구체적으로 질문해주세요.',
  'IntermediateStepsException': '분석 과정에서 문제가 발생했습니다. 다시 시도해주세요.',
  'SQLExecutionException': '데이터 조회 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
  'SQLResultExtractionException': '조회 결과를 처리하는 중 문제가 발생했습니다.',

  // Phase 2 Errors - 시각화 단계
  'LLMResponseException': 'AI 응답 생성 중 문제가 발생했습니다. 다시 시도해주세요.',
  'JSONParsingException': '응답 데이터 처리 중 문제가 발생했습니다.',
  'VisualizationValidationException': '시각화 생성 중 문제가 발생했습니다. 텍스트로 결과를 표시합니다.',

  // System Errors
  'UnexpectedException': '예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
  'ConfigurationException': '시스템 설정 오류가 발생했습니다. 관리자에게 문의해주세요.',
  'RetryExhaustedException': '여러 번 시도했지만 실패했습니다. 나중에 다시 시도해주세요.',
}

/**
 * Get user-friendly error message from error class
 */
export function getErrorMessage(errorClass: string): string {
  return ERROR_MESSAGES[errorClass] || ERROR_MESSAGES['UnexpectedException']
}

/**
 * Log error details in development mode
 */
export function logErrorDetails(errorData: ErrorResponse): void {
  if (process.env.NODE_ENV === 'development') {
    console.group(`🚨 Error: ${errorData.error_class}`)
    console.error('Traceback:', errorData.traceback)
    console.groupEnd()
  } else {
    // Production에서는 간단한 로그만
    console.error(`Error occurred: ${errorData.error_class}`)
  }
}