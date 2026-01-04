import { VisualizationData } from "@/types/chat"

/**
 * 메시지 내용에서 JSON 형태의 시각화 데이터를 추출
 */
export function parseVisualizationData(content: string): VisualizationData | null {
  try {
    console.log('🔍 Parsing visualization data from:', content.substring(0, 200) + '...')

    let jsonString = ""

    // 먼저 전체 내용이 JSON인지 확인 (가장 일반적인 경우)
    const trimmed = content.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      try {
        // 바로 파싱 시도
        const testParse = JSON.parse(trimmed)
        if (testParse.selected_visualization || testParse.visualization_data) {
          jsonString = trimmed
          console.log('✅ Found JSON as full content')
        }
      } catch {
        console.log('⚠️ Full content looks like JSON but failed to parse')
      }
    }

    // 전체 JSON이 아니면 패턴으로 찾기
    if (!jsonString) {
      // JSON 블록을 찾기 위한 패턴들
      const jsonPatterns = [
        /```json\s*([\s\S]*?)\s*```/,  // ```json { ... } ``` 형태
        /```\s*([\s\S]*?)\s*```/,      // ``` { ... } ``` 형태
      ]

      for (const pattern of jsonPatterns) {
        const match = content.match(pattern)
        if (match) {
          jsonString = match[1]
          console.log('✅ Found JSON with code block pattern')
          break
        }
      }
    }

    if (!jsonString) {
      console.log('❌ No valid JSON found in content')
      return null
    }

    console.log('🔍 Attempting to parse JSON string length:', jsonString.length)

    // JSON 파싱 시도
    const parsed = JSON.parse(jsonString)

    // 시각화 데이터 구조 검증
    if (
      parsed.selected_visualization &&
      parsed.visualization_data &&
      parsed.insights &&
      Array.isArray(parsed.insights)
    ) {
      console.log('✅ Valid visualization data found')
      return parsed as VisualizationData
    }

    console.log('❌ Invalid visualization data structure')
    return null
  } catch (error) {
    console.log('❌ 시각화 데이터 파싱 실패:', error)
    return null
  }
}

/**
 * 메시지 내용에서 시각화 데이터를 제거하고 일반 텍스트만 반환
 */
export function removeVisualizationFromContent(content: string): string {
  console.log('🧹 Removing visualization from content:', content.substring(0, 200) + '...')

  let cleanContent = content

  // 전체 내용이 JSON인지 먼저 확인
  const trimmed = content.trim()
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const parsed = JSON.parse(trimmed)
      if (parsed.selected_visualization || parsed.visualization_data) {
        console.log('🗑️ Entire content is JSON - removing completely')
        return ""
      }
    } catch {
      // JSON 파싱 실패시 계속 진행
    }
  }

  // 코드 블록을 찾아서 제거하기 전에 로그
  const codeBlockMatches = cleanContent.match(/```[\s\S]*?```/gm)
  if (codeBlockMatches) {
    console.log('📝 Found code blocks to remove:', codeBlockMatches.length)
  }

  // JSON 블록 제거 (더 강력한 패턴)
  // 백틱 3개로 시작하고 끝나는 모든 코드 블록 제거
  cleanContent = cleanContent.replace(/```json[\s\S]*?```/gm, '')
  cleanContent = cleanContent.replace(/```[\s\S]*?```/gm, '')

  // 백틱이 개행과 함께 있는 경우도 처리
  cleanContent = cleanContent.replace(/```json\n[\s\S]*?\n```/gm, '')
  cleanContent = cleanContent.replace(/```\n[\s\S]*?\n```/gm, '')

  // 남아있을 수 있는 JSON 객체 직접 제거
  cleanContent = cleanContent
    .replace(/\{[\s\S]*?"selected_visualization"[\s\S]*?\}/g, '')
    .replace(/\{[\s\S]*?"visualization_data"[\s\S]*?\}/g, '')
    .replace(/\{[\s\S]*?"insights"[\s\S]*?\}/g, '')

  // 인사이트 중복 제거 (JSON에서 추출된 것과 중복될 수 있음)
  cleanContent = cleanContent
    .replace(/\*\*주요 인사이트:\*\*[\s\S]*?(?=\n\n|\n$|$)/g, '')
    .replace(/주요 인사이트:[\s\S]*?(?=\n\n|\n$|$)/g, '')

  // 남은 내용 정리
  cleanContent = cleanContent
    .replace(/\n\s*\n\s*\n/g, '\n\n')  // 연속된 빈 줄 정리
    .replace(/^\s*\n/g, '')  // 시작 부분 빈 줄 제거
    .replace(/\n\s*$/g, '')  // 끝 부분 빈 줄 제거
    .trim()

  console.log('✅ Cleaned content:', cleanContent)
  return cleanContent
}

/**
 * 백엔드 응답에서 시각화 데이터와 텍스트 내용을 분리
 */
export function processAssistantResponse(content: string): {
  visualizationData: VisualizationData | null
  textContent: string
} {
  // 먼저 시각화 데이터 파싱 시도
  const visualizationData = parseVisualizationData(content)

  // 시각화 데이터가 있든 없든 JSON 제거 시도
  // (파싱이 실패해도 JSON처럼 보이는 텍스트는 제거해야 함)
  const textContent = removeVisualizationFromContent(content)

  // 시각화 데이터가 있거나, 텍스트가 완전히 제거된 경우
  if (visualizationData) {
    return { visualizationData, textContent }
  }

  // 시각화 데이터는 없지만 텍스트 정리는 된 상태
  return { visualizationData: null, textContent }
}