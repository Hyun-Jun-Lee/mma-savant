#!/usr/bin/env python3
"""
AgentManagerV3 + OpenRouter + ReAct 통합 테스트
"""
import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from llm.agent_manager_v3 import AgentManagerV2
from llm.providers.openrouter_provider import get_openrouter_llm
from llm.callbacks.openrouter_callback import get_openrouter_callback_handler
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

# 테스트 모델과 쿼리
TEST_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
TEST_QUERY = "KO/TKO 승리가 가장 많은 파이터 상위 3명을 보여줘"

async def test_openrouter_integration():
    """OpenRouter + ReAct + AgentManagerV3 통합 테스트"""
    print("🚀 Testing AgentManagerV3 with OpenRouter + ReAct")
    print("=" * 70)

    try:
        # 1. 콜백 핸들러 생성
        callback = get_openrouter_callback_handler(
            message_id="test_v3_001",
            session_id="test_session_v3",
            model_name=TEST_MODEL
        )
        print(f"✅ Callback handler created: {type(callback).__name__}")

        # 2. OpenRouter LLM 생성 (단순화된 방식)
        llm = get_openrouter_llm(
            callback_handler=callback,
            model_name=TEST_MODEL
        )
        print(f"✅ OpenRouter LLM created: {type(llm).__name__}")
        print(f"   Model: {TEST_MODEL}")
        print(f"   Streaming: {getattr(llm, 'streaming', False)}")

        # 3. AgentManagerV3 생성
        agent_manager = AgentManagerV2()
        print(f"✅ AgentManagerV3 created")

        # 4. 상태 확인
        health = await agent_manager.health_check()
        print(f"✅ Health check: {health.get('agent_manager', 'unknown')}")
        print(f"   MCP server: {health.get('mcp_server_exists', False)}")

        # 5. 통합 테스트 실행
        print(f"\n🎯 Testing Two-Phase processing with ReAct...")
        print(f"Query: {TEST_QUERY}")

        try:
            result = await agent_manager.process_two_step(
                user_query=TEST_QUERY,
                llm=llm,
                callback_handler=callback
            )

            # 결과 분석
            if result.get("error"):
                print(f"❌ Processing failed: {result['error']}")
                return False
            else:
                print(f"✅ Processing completed successfully!")
                print(f"   Processing ID: {result.get('processing_id', 'unknown')}")
                print(f"   SQL Query: {result.get('sql_query', 'none')[:100]}...")
                print(f"   Row Count: {result.get('row_count', 0)}")
                print(f"   Visualization: {result.get('visualization_type', 'unknown')}")
                print(f"   Content Length: {len(result.get('content', ''))}")
                return True

        except Exception as e:
            print(f"❌ Two-Phase processing failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def test_react_prompt_generation():
    """ReAct 프롬프트 생성 테스트"""
    print(f"\n📝 Testing ReAct prompt generation...")
    print("=" * 50)

    try:
        from llm.prompts.two_phase_prompts import get_phase1_prompt
        from llm.providers.openrouter_provider import create_react_prompt_template

        # Phase 1 기본 프롬프트 가져오기
        base_prompt = get_phase1_prompt()
        print(f"✅ Base Phase 1 prompt loaded ({len(base_prompt)} chars)")

        # ReAct 템플릿 생성
        react_prompt = create_react_prompt_template(base_prompt)
        print(f"✅ ReAct prompt template created")
        print(f"   Input variables: {react_prompt.input_variables}")

        # 샘플 포맷팅 테스트
        sample_format = react_prompt.format(
            tools="execute_raw_sql_query",
            tool_names=["execute_raw_sql_query"],
            input="Show top fighters",
            agent_scratchpad=""
        )
        print(f"✅ Sample formatting successful ({len(sample_format)} chars)")

        # ReAct 형식 확인
        required_elements = ["Thought:", "Action:", "Action Input:", "Observation:", "Final Answer:"]
        for element in required_elements:
            if element in sample_format:
                print(f"   ✓ Contains '{element}'")
            else:
                print(f"   ✗ Missing '{element}'")

        return True

    except Exception as e:
        print(f"❌ ReAct prompt test failed: {e}")
        return False

async def test_mcp_tools_compatibility():
    """MCP tools와 ReAct 호환성 테스트"""
    print(f"\n🔧 Testing MCP tools with ReAct agent...")
    print("=" * 50)

    try:
        agent_manager = AgentManagerV2()

        # MCP tools 로드 테스트
        async with agent_manager.get_mcp_tools() as tools:
            print(f"✅ MCP tools loaded: {len(tools)} tools")

            for i, tool in enumerate(tools[:3]):  # 처음 3개만 확인
                tool_name = getattr(tool, 'name', 'unknown')
                tool_desc = getattr(tool, 'description', 'no description')
                print(f"   {i+1}. {tool_name}: {tool_desc[:50]}...")

            # ReAct에 필요한 SQL 도구 확인
            sql_tools = [tool for tool in tools if 'sql' in getattr(tool, 'name', '').lower()]
            if sql_tools:
                print(f"✅ SQL tools found: {len(sql_tools)} tools")
                for tool in sql_tools:
                    print(f"   - {getattr(tool, 'name', 'unknown')}")
            else:
                print(f"⚠️ No SQL tools found - check MCP server")

        return True

    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

async def main():
    """메인 테스트 실행"""
    print("🧪 AgentManagerV3 + OpenRouter + ReAct Integration Test")
    print("=" * 80)

    tests = [
        ("ReAct Prompt Generation", test_react_prompt_generation),
        ("MCP Tools Compatibility", test_mcp_tools_compatibility),
        ("OpenRouter Integration", test_openrouter_integration)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # 결과 요약
    print(f"\n{'='*80}")
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! AgentManagerV3 with OpenRouter + ReAct is ready!")
        print("\n📋 Next Steps:")
        print("   1. Update API endpoints to use AgentManagerV3")
        print("   2. Configure OpenRouter API key in .env")
        print("   3. Test with real user queries")
    else:
        print("⚠️ Some tests failed. Please review the issues before deployment.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Tests failed with error: {e}")