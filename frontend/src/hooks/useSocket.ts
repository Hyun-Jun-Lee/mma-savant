"use client"

import { useEffect, useRef, useState, useCallback } from 'react'
import { getRealSocket } from '@/lib/realSocket'
import { useChatStore } from '@/store/chatStore'
import { processAssistantResponse } from '@/lib/visualizationParser'
import { VisualizationData } from '@/types/chat'
import { ChatApiService } from '@/services/chatApi'
import { ErrorResponse, getErrorMessage, logErrorDetails } from '@/types/error'

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const socketRef = useRef(getRealSocket())
  const { addMessage, updateMessage, setConnected, setTyping, currentSession, setCurrentSession, setSessions, openModal, setUsageLimit, setShowUsageLimitPopup, setErrorInfo, setShowErrorPopup, clearChat } = useChatStore()
  const currentStreamingMessage = useRef<{
    id: string;
    content: string;
    storeId?: string;
    visualizationData?: VisualizationData | null;
  } | null>(null)

  // 세션 목록 새로고침 함수
  const refreshSessions = useCallback(async () => {
    try {
      console.log('🔄 Refreshing sessions after AI response completion')
      const response = await ChatApiService.getSessions(20, 0)
      const convertedSessions = response.sessions.map(session => ({
        id: session.id,
        user_id: session.user_id,
        title: session.title,
        last_message_at: session.last_message_at ? new Date(session.last_message_at) : undefined,
        created_at: new Date(session.created_at),
        updated_at: new Date(session.updated_at),
      }))
      setSessions(convertedSessions)
      console.log('✅ Sessions refreshed, count:', convertedSessions.length)
    } catch (error) {
      console.error('❌ Failed to refresh sessions:', error)
    }
  }, [setSessions])

  // Zustand 스토어 함수들은 이미 안정적이므로 직접 사용

  useEffect(() => {
    const socket = socketRef.current
    

    // 연결 이벤트 처리
    socket.on('connect', () => {
      setIsConnected(true)
      setConnected(true)
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
      setConnected(false)
    })

    // 메시지 수신 처리 (환영 메시지 등 일반 메시지용)
    socket.on('message', (data: { content: string; role: 'assistant'; timestamp: Date; messageId?: string }) => {
      console.log('💪 Received message:', data)
      addMessage({
        content: data.content,
        role: data.role
      })
    })

    // 스트리밍 메시지 청크 처리 (백엔드는 response_chunk 이벤트 사용)
    socket.on('response_chunk', (data: {
      content: string;
      message_id: string;
      conversation_id: number;
      timestamp: string;
      type: string;
    }) => {
      console.log('📝 Received response_chunk:', data)
      console.log('📝 Current streaming message:', currentStreamingMessage.current?.id)

      // 스트리밍 메시지의 전체 내용을 누적
      let fullContent = ""

      if (!currentStreamingMessage.current || currentStreamingMessage.current.id !== data.message_id) {
        // 새로운 스트리밍 메시지 시작 - 즉시 타이핑 상태 해제
        console.log('🆕 Starting new streaming message:', data.message_id)
        console.log('⚡ Immediately stopping typing indicator')
        setIsTyping(false)
        setTyping(false)

        // 첫 번째 청크의 내용으로 시작
        fullContent = data.content

        // 시각화 데이터 파싱
        const { visualizationData, textContent } = processAssistantResponse(fullContent)

        // 새 메시지 추가
        const newMessage = {
          content: textContent || fullContent, // 파싱된 텍스트 또는 원본
          role: 'assistant' as const,
          isStreaming: true,
          visualizationData: visualizationData
        }

        const addedMessage = addMessage(newMessage)

        // 현재 스트리밍 메시지 정보 저장 (store ID 직접 사용)
        currentStreamingMessage.current = {
          id: data.message_id,
          content: fullContent,
          storeId: addedMessage.id, // addMessage에서 반환된 실제 ID 사용
          visualizationData: visualizationData
        }

        console.log('📝 New streaming message stored with store ID:', addedMessage.id, 'hasVisualization:', !!visualizationData)
      } else {
        // 기존 메시지 업데이트 - 새 청크를 기존 내용에 추가
        currentStreamingMessage.current.content += data.content
        fullContent = currentStreamingMessage.current.content

        console.log('🔄 Updating streaming message:', data.message_id, 'new length:', fullContent.length)

        // 시각화 데이터 재파싱 (스트리밍 중 JSON이 완성될 수 있음)
        const { visualizationData, textContent } = processAssistantResponse(fullContent)

        // 시각화 데이터가 새로 감지되었거나 변경되었으면 업데이트
        if (visualizationData !== currentStreamingMessage.current.visualizationData) {
          currentStreamingMessage.current.visualizationData = visualizationData
          console.log('📊 Visualization data updated:', !!visualizationData)
        }

        // store ID를 사용하여 직접 메시지 업데이트
        const storeId = currentStreamingMessage.current.storeId
        if (storeId) {
          console.log('📝 Updating message in store by store ID:', storeId)

          // 메시지가 실제로 존재하는지 먼저 확인
          const messages = useChatStore.getState().messages
          const targetMessage = messages.find(msg => msg.id === storeId)

          if (targetMessage) {
            console.log('✅ Target message found, updating:', storeId)
            updateMessage(storeId, textContent || fullContent, true, visualizationData)
          } else {
            console.log('❌ Target message not found in store:', storeId)
            // fallback으로 마지막 스트리밍 메시지 찾기
            const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.isStreaming)
            if (lastAssistantMessage) {
              console.log('📝 Using fallback message:', lastAssistantMessage.id)
              updateMessage(lastAssistantMessage.id, textContent || fullContent, true, visualizationData)
              currentStreamingMessage.current.storeId = lastAssistantMessage.id
            } else {
              console.log('❌ No streaming assistant message found in store at all')
            }
          }
        } else {
          console.log('❌ No storeId available, using fallback')
          // fallback: 마지막 스트리밍 메시지 찾기
          const messages = useChatStore.getState().messages
          const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.isStreaming)
          if (lastAssistantMessage) {
            console.log('📝 Updating message in store (fallback):', lastAssistantMessage.id)
            updateMessage(lastAssistantMessage.id, textContent || fullContent, true, visualizationData)
            // store ID 저장
            currentStreamingMessage.current.storeId = lastAssistantMessage.id
          } else {
            console.log('❌ No streaming assistant message found in store')
          }
        }
      }
    })

    // final_result 직접 처리 (Two-Phase 시스템의 완성된 결과)
    socket.on('final_result', (data: {
      content?: string;
      message_id: string;
      conversation_id: number;
      timestamp: string;
      visualization_type?: string;
      visualization_data?: Record<string, unknown>;
      insights?: string[];
      tool_results?: unknown[];
      intermediate_steps?: unknown[];
    }) => {
      console.log('🎯 Received final_result:', data.message_id)
      console.log('📊 Visualization type:', data.visualization_type)
      console.log('📊 Has visualization data:', !!data.visualization_data)

      // 즉시 타이핑 상태 해제
      setIsTyping(false)
      setTyping(false)

      // 직접 시각화 데이터 구성 (content 파싱 대신)
      let visualizationData: VisualizationData | null = null
      const validVisualizationTypes = ['table', 'bar_chart', 'pie_chart', 'line_chart', 'scatter_plot', 'text_summary'] as const
      if (
        data.visualization_type &&
        data.visualization_data &&
        data.visualization_type !== 'text_summary' &&
        validVisualizationTypes.includes(data.visualization_type as typeof validVisualizationTypes[number])
      ) {
        visualizationData = {
          selected_visualization: data.visualization_type as VisualizationData['selected_visualization'],
          visualization_data: {
            title: String(data.visualization_data.title || "분석 결과"),
            data: (data.visualization_data.data || data.visualization_data) as Record<string, string | number>[],
            x_axis: data.visualization_data.x_axis as string | undefined,
            y_axis: data.visualization_data.y_axis as string | undefined
          },
          insights: data.insights || []
        }
      }

      // 텍스트 content 처리 - JSON 제거하고 insights 조건부 추가
      let textContent = ""

      // content에서 JSON 제거 (디버깅 로그 추가)
      if (data.content) {
        console.log('🔍 Original content:', data.content)
        const { visualizationData: parsedViz, textContent: cleanText } = processAssistantResponse(data.content)
        console.log('🧹 Cleaned text:', cleanText)
        console.log('📊 Parsed visualization:', parsedViz)
        textContent = cleanText
      }

      // 시각화 데이터가 없을 때만 insights를 텍스트로 추가
      // (시각화가 있으면 ChartRenderer에서 이미 인사이트를 표시함)
      if (!visualizationData && data.insights && data.insights.length > 0) {
        if (textContent && textContent.trim().length > 0) {
          textContent += "\n\n"
        }
        textContent += "**주요 인사이트:**\n" + data.insights.map(insight => `• ${insight}`).join('\n')
      }

      console.log('✅ Final textContent:', textContent)
      console.log('📊 Has visualization:', !!visualizationData)

      // 완성된 메시지로 즉시 추가 (스트리밍 우회)
      const finalMessage = {
        content: textContent,
        role: 'assistant' as const,
        isStreaming: false,
        visualizationData: visualizationData
      }

      const addedMessage = addMessage(finalMessage)
      console.log('✅ Final message added immediately:', addedMessage.id, 'hasVisualization:', !!visualizationData)

      // 현재 스트리밍 메시지 정리
      currentStreamingMessage.current = null

      // AI 응답 완료 즉시 메시지 클리어 및 세션 목록 새로고침
      console.log('🧹 Clearing messages immediately after AI response completion')
      const conversationId = data.conversation_id
      setTimeout(async () => {
        const { clearChat } = useChatStore.getState()
        clearChat()
        await refreshSessions()
        // 세션 목록 새로고침 후 해당 세션의 모달 자동 열기
        if (conversationId) {
          console.log('🔓 Opening modal for session:', conversationId)
          openModal(conversationId)
        }
      }, 100) // 최소한의 지연으로 바로 클리어
    })

    // 스트리밍 완료 처리 (백엔드는 response_end 이벤트 사용)
    socket.on('response_end', (data: { message_id: string; conversation_id: number; timestamp: string; type: string }) => {
      console.log('✅ Response complete:', data.message_id)
      // 스트리밍 메시지를 완료 상태로 변경
      if (currentStreamingMessage.current && currentStreamingMessage.current.id === data.message_id) {
        console.log('📝 Finalizing streaming message:', data.message_id)

        const finalContent = currentStreamingMessage.current.content
        const finalVisualizationData = currentStreamingMessage.current.visualizationData

        // 최종 파싱 (완전한 메시지로 마지막 파싱)
        const { visualizationData, textContent } = processAssistantResponse(finalContent)
        const finalParsedVisualizationData = visualizationData || finalVisualizationData

        if (currentStreamingMessage.current.storeId) {
          // store ID를 사용하여 직접 완료 처리
          console.log('📝 Setting streaming message as completed by store ID:', currentStreamingMessage.current.storeId)
          updateMessage(
            currentStreamingMessage.current.storeId,
            textContent || finalContent,
            false,
            finalParsedVisualizationData
          )
        } else {
          // fallback: 마지막 스트리밍 메시지 찾기
          const messages = useChatStore.getState().messages
          const lastAssistantMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.isStreaming)
          if (lastAssistantMessage) {
            console.log('📝 Setting streaming message as completed (fallback):', lastAssistantMessage.id)
            updateMessage(
              lastAssistantMessage.id,
              textContent || finalContent,
              false,
              finalParsedVisualizationData
            )
          }
        }

        console.log('🎉 Message finalized with visualization:', !!finalParsedVisualizationData)
        const conversationId = data.conversation_id
        currentStreamingMessage.current = null

        // AI 응답 완료 후 메시지 클리어 및 세션 목록 새로고침
        setTimeout(async () => {
          console.log('🧹 Clearing messages after streaming completion')
          const { clearChat } = useChatStore.getState()
          clearChat()
          await refreshSessions()
          // 세션 목록 새로고침 후 해당 세션의 모달 자동 열기
          if (conversationId) {
            console.log('🔓 Opening modal for session:', conversationId)
            openModal(conversationId)
          }
        }, 100) // 최소한의 지연으로 바로 클리어
      }
    })

    // 타이핑 상태 처리
    socket.on('typing', (data: { isTyping: boolean }) => {
      setIsTyping(data.isTyping)
      setTyping(data.isTyping)
    })

    // 메시지 수신 확인 처리 (새 세션 생성 시 세션 정보 업데이트)
    socket.on('message_received', (data: {
      type: string;
      message_id: string;
      conversation_id: number;
      timestamp: string;
    }) => {
      console.log('📩 Message received confirmation:', data)

      // 현재 세션이 없거나 다른 세션이면 업데이트
      if (!currentSession || currentSession.id !== data.conversation_id) {
        console.log('🔄 Updating current session from WebSocket:', data.conversation_id)

        // 새 세션 정보 생성 (기본 정보만)
        const newSession = {
          id: data.conversation_id,
          user_id: 0, // 임시 user_id
          title: `채팅 ${new Date().toLocaleString()}`,
          created_at: new Date(),
          updated_at: new Date(),
          last_message_at: new Date(data.timestamp)
        }

        // ChatStore의 현재 세션 업데이트 (세션 목록은 AI 응답 완료 후 새로고침으로 처리)
        setCurrentSession(newSession)
        console.log('✅ Current session updated:', newSession)
      }
    })

    // 에러 처리 (기존 socket error)
    socket.on('error', (error: string) => {
      console.error('Socket error:', error)
    })

    // 백엔드 에러 응답 처리
    socket.on('error_response', (errorData: ErrorResponse) => {
      console.log('💥 Received error_response:', errorData)

      // 개발 모드에서 상세 로깅
      logErrorDetails(errorData)

      // 사용자 친화적 메시지 가져오기
      const userMessage = getErrorMessage(errorData.error_class)
      console.log('📝 User-friendly message:', userMessage)

      // 팝업으로 에러 표시
      setErrorInfo({ errorClass: errorData.error_class, message: userMessage })
      setShowErrorPopup(true)

      // 채팅에서 진행 중이던 질문 제거
      clearChat()

      // 타이핑 상태 해제
      setIsTyping(false)
      setTyping(false)

      // 현재 스트리밍 메시지 정리
      currentStreamingMessage.current = null
    })

    // 일일 사용량 제한 초과 처리
    socket.on('usage_limit_exceeded', (data: {
      error: string;
      daily_requests: number;
      daily_limit: number;
      remaining_requests: number;
      timestamp: string;
    }) => {
      console.log('🚫 Usage limit exceeded:', data)

      // 사용량 제한 상태 업데이트
      setUsageLimit({
        exceeded: true,
        dailyRequests: data.daily_requests,
        dailyLimit: data.daily_limit,
        remainingRequests: data.remaining_requests,
        error: data.error
      })

      // 팝업 표시
      setShowUsageLimitPopup(true)

      setIsTyping(false)
      setTyping(false)
      currentStreamingMessage.current = null
    })

    // 초기 연결만 수행 (세션 ID 없이)

    // 연결되지 않은 경우에만 연결 시도
    if (!socket.isConnected()) {
      socket.connect() // 세션 ID 없이 초기 연결
    }

    // 클린업
    return () => {
      // 소켓 연결 해제
      socket.disconnect()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // 마운트 시 한 번만 실행 (의존성 배열 비움)

  const sendMessage = async (message: string) => {
    console.log('🚀 sendMessage called, React isConnected:', isConnected)
    console.log('🚀 sendMessage called, Socket isConnected:', socketRef.current.isConnected())
    console.log('🚀 sendMessage called, Socket exists:', !!socketRef.current)
    
    // 실제 소켓 상태를 기준으로 판단
    const actuallyConnected = socketRef.current && socketRef.current.isConnected()
    
    // 연결되지 않은 경우 잠시 대기 후 재시도
    if (!actuallyConnected) {
      console.log('⏳ Socket not actually connected, waiting for connection...')
      
      // 최대 5초 동안 연결을 기다림
      let attempts = 0
      const maxAttempts = 50 // 5초 (100ms * 50)
      
      while ((!socketRef.current || !socketRef.current.isConnected()) && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100))
        attempts++
        console.log(`⏳ Waiting for connection... attempt ${attempts}/${maxAttempts}, socket exists: ${!!socketRef.current}, socket connected: ${socketRef.current?.isConnected()}`)
      }
      
      if (!socketRef.current || !socketRef.current.isConnected()) {
        console.log('❌ Connection timeout after waiting')
        return
      }
      
      console.log('✅ Connection established, sending message')
    }
    
    // 현재 conversation ID로 메시지 전송 (동적으로 conversation ID 설정)
    console.log('📤 Sending message with conversation:', currentSession?.id)
    socketRef.current.sendMessage(message, currentSession?.id)
  }

  return {
    isConnected,
    isTyping,
    sendMessage,
  }
}