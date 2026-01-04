import { EventEmitter } from 'events'

export interface MockSocketEvents {
  connect: () => void
  disconnect: () => void
  message: (data: { content: string; role: 'assistant'; timestamp: Date }) => void
  typing: (data: { isTyping: boolean }) => void
  error: (error: string) => void
}

class MockSocket extends EventEmitter {
  private connected = false
  private typingTimeout: NodeJS.Timeout | null = null

  connect() {
    setTimeout(() => {
      this.connected = true
      this.emit('connect')
      console.log('🔌 Mock Socket connected')
    }, 500)
  }

  disconnect() {
    this.connected = false
    this.emit('disconnect')
    console.log('🔌 Mock Socket disconnected')
  }

  sendMessage(message: string) {
    if (!this.connected) {
      this.emit('error', 'Not connected to server')
      return
    }

    console.log('📤 Sending message:', message)

    // 타이핑 상태 시뮬레이션
    this.emit('typing', { isTyping: true })

    // Mock AI 응답 생성
    setTimeout(() => {
      const mockResponse = this.generateMockResponse(message)
      
      // 스트리밍 응답 시뮬레이션
      this.simulateStreamingResponse(mockResponse)
    }, 1000 + Math.random() * 2000) // 1-3초 랜덤 딜레이
  }

  private generateMockResponse(userMessage: string): string {
    const lowerMessage = userMessage.toLowerCase()
    
    // MMA 관련 키워드 기반 응답
    if (lowerMessage.includes('존 존스') || lowerMessage.includes('jon jones')) {
      return `존 존스(Jon Jones)는 UFC 라이트 헤비급의 전설적인 파이터입니다. 

주요 특징:
• **리치**: 84.5인치의 긴 리치로 상대를 압도
• **클린치 게임**: 엘보우와 니킥이 특기
• **레슬링**: 강력한 테이크다운과 그라운드 컨트롤
• **창의적인 기술**: 스피닝 엘보우, 오블리크 킥 등

주요 승리: 다니엘 코미에, 라시드 에반스, 쇼군 루아 등을 상대로 압승을 거두었습니다.`
    }
    
    if (lowerMessage.includes('기술') || lowerMessage.includes('technique')) {
      return `MMA의 주요 기술 카테고리를 설명해드리겠습니다:

**스트라이킹 (타격)**
• 복싱: 잽, 훅, 어퍼컷
• 킥복싱: 로우킥, 하이킥, 니킥
• 무에타이: 엘보우, 클린치

**그래플링 (그라운드)**
• 브라질리안 주짓수: 서브미션, 가드
• 레슬링: 테이크다운, 컨트롤
• 사모: 던지기 기술

**혼합 기술**
• 클린치 워크
• 케이지 컨트롤
• 트랜지션`
    }

    if (lowerMessage.includes('ufc') || lowerMessage.includes('이벤트')) {
      return `UFC는 세계 최대의 MMA 조직입니다.

**최근 주요 이벤트:**
• UFC 300: 역대급 카드로 화제
• UFC 299: 숀 오말리 vs 치토 베라
• UFC 298: 일리야 토포우리아의 페더급 벨트 획득

**체급별 현재 챔피언:**
• 헤비급: 존 존스
• 라이트헤비급: 알렉스 페레이라  
• 미들급: 드리커스 두 플레시스
• 웰터급: 벨랄 무하마드

더 구체적인 이벤트나 파이터에 대해 궁금한 것이 있으시면 언제든 물어보세요!`
    }

    // 기본 응답
    const defaultResponses = [
      `"${userMessage}"에 대한 흥미로운 질문이네요! MMA에서 이와 관련된 다양한 측면을 고려해볼 수 있습니다.`,
      `좋은 질문입니다! MMA는 복합격투기로서 다양한 무술이 융합된 스포츠입니다. 더 구체적인 질문을 해주시면 더 자세한 답변을 드릴 수 있어요.`,
      `MMA Savant로서 "${userMessage}"에 대해 설명드리겠습니다. 파이터, 기술, 이벤트 중 어떤 부분을 더 자세히 알고 싶으신가요?`
    ]
    
    return defaultResponses[Math.floor(Math.random() * defaultResponses.length)]
  }

  private simulateStreamingResponse(fullResponse: string) {
    const words = fullResponse.split(' ')
    let currentResponse = ''
    
    words.forEach((word, index) => {
      setTimeout(() => {
        currentResponse += (index === 0 ? word : ` ${word}`)
        
        this.emit('message', {
          content: currentResponse,
          role: 'assistant' as const,
          timestamp: new Date(),
        })

        // 마지막 단어면 타이핑 중지
        if (index === words.length - 1) {
          this.emit('typing', { isTyping: false })
        }
      }, index * 100 + Math.random() * 50) // 100ms + 랜덤 딜레이
    })
  }

  isConnected() {
    return this.connected
  }
}

// 싱글톤 인스턴스
let mockSocketInstance: MockSocket | null = null

export const getMockSocket = (): MockSocket => {
  if (!mockSocketInstance) {
    mockSocketInstance = new MockSocket()
  }
  return mockSocketInstance
}