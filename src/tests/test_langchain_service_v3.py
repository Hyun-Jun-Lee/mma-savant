#!/usr/bin/env python3
"""
LangChain Service V3 + AgentManagerV3 + OpenRouter 통합 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from llm.langchain_service_v3 import get_langchain_service
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

# 테스트 설정
TEST_SESSION_ID = "test_session_v3"
TEST_USER_ID = 1
TEST_QUERY = "KO/TKO 승리가 가장 많은 파이터 상위 3명을 차트로 보여줘"

async def test_langchain_service_v3():
    """LangChain Service V3 + AgentManagerV3 통합 테스트"""
    print("🚀 Testing LangChain Service V3 with AgentManagerV3")
    print("=" * 70)

    try:
        # 1. 서비스 생성 및 상태 확인
        print("🔧 Creating LangChain Service V3...")
        service = await get_langchain_service()
        print(f"✅ Service created: {type(service).__name__}")

        # 2. 헬스 체크
        print("\n🏥 Health Check...")
        health = await service.health_check()
        print(f"✅ Service Status: {health.get('status', 'unknown')}")
        print(f"   Provider: {health.get('llm_provider', 'unknown')}")
        print(f"   Agent Manager: {health.get('agent_manager_version', 'unknown')}")
        print(f"   Two-Phase System: {health.get('two_phase_system', {}).get('agent_manager', 'unknown')}")

        # 3. 대화 시작 메시지 테스트
        print("\n💬 Conversation Starter...")
        starter = service.get_conversation_starter()
        print(f"✅ Starter: {starter}")

        # 4. 스트리밍 응답 테스트
        print(f"\n🎯 Testing streaming response...")
        print(f"Query: {TEST_QUERY}")
        print("=" * 50)

        chunk_count = 0
        phase_start_received = False
        final_result_received = False
        error_occurred = False

        async for chunk in service.generate_streaming_chat_response(
            user_message=TEST_QUERY,
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID
        ):
            chunk_count += 1
            chunk_type = chunk.get("type", "unknown")

            print(f"📦 Chunk {chunk_count}: {chunk_type}")

            if chunk_type == "phase_start":
                phase_start_received = True
                print(f"   🚀 Phase {chunk.get('phase', '?')}: {chunk.get('description', 'unknown')}")

            elif chunk_type == "final_result":
                final_result_received = True
                print(f"   ✅ Final Result:")
                print(f"      Processing ID: {chunk.get('processing_id', 'unknown')}")
                print(f"      Visualization: {chunk.get('visualization_type', 'unknown')}")
                print(f"      Row Count: {chunk.get('row_count', 0)}")
                print(f"      SQL Query: {chunk.get('sql_query', 'none')[:100]}...")
                print(f"      Content Length: {len(chunk.get('content', ''))}")
                print(f"      Execution Time: {chunk.get('total_execution_time', 'unknown')}s")

            elif chunk_type == "error":
                error_occurred = True
                print(f"   ❌ Error: {chunk.get('error', 'unknown')}")
                break

        # 5. 결과 분석
        print(f"\n📊 Test Results:")
        print(f"   Total Chunks: {chunk_count}")
        print(f"   Phase Start: {'✅' if phase_start_received else '❌'}")
        print(f"   Final Result: {'✅' if final_result_received else '❌'}")
        print(f"   Error Occurred: {'❌' if error_occurred else '✅'}")

        if phase_start_received and final_result_received and not error_occurred:
            print(f"\n🎉 SUCCESS: LangChain Service V3 + AgentManagerV3 integration working!")
            return True
        else:
            print(f"\n⚠️ PARTIAL: Some components may need attention")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 6. 클린업
        try:
            await service.cleanup()
            print(f"\n🧹 Cleanup completed")
        except Exception as e:
            print(f"\n⚠️ Cleanup error: {e}")

async def main():
    """메인 테스트 함수"""
    print("🧪 LangChain Service V3 + AgentManagerV3 Integration Test")
    print("=" * 80)

    # 환경 확인
    print("🔧 Environment Check:")
    print(f"   OpenRouter API Key: {'✅ Set' if Config.OPENROUTER_API_KEY else '❌ Missing'}")
    print(f"   Database URL: {'✅ Set' if hasattr(Config, 'DATABASE_URL') and Config.DATABASE_URL else '❌ Missing'}")

    if not Config.OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY is not set in environment variables")
        return

    # 통합 테스트 실행
    success = await test_langchain_service_v3()

    # 최종 결과
    print(f"\n{'='*80}")
    print("🎯 FINAL RESULT")
    print(f"{'='*80}")

    if success:
        print("✅ LangChain Service V3 + AgentManagerV3 + OpenRouter integration SUCCESSFUL!")
        print("\n📋 Ready for:")
        print("   1. API endpoint updates")
        print("   2. Production deployment")
        print("   3. Real user testing")
    else:
        print("❌ Integration test FAILED - review errors above")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")