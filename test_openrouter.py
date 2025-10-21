import asyncio
import json
import sys
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

# 테스트 모드 활성화 (LangChain 도구 사용)
os.environ["USE_LANGCHAIN_TOOLS"] = "true"

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from llm.providers.openrouter_provider import get_openrouter_llm, get_model_info
from llm.callbacks.openrouter_callback import get_openrouter_callback_handler
from llm.agent_manager_v2 import AgentManagerV2
from llm.langchain_service_v2 import LangChainLLMService
from database.connection.postgres_conn import get_async_db_context
from config import Config
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

# 테스트할 모델 (하나씩 변경하면서 테스트)

# TEST_MODEL = "qwen/qwen3-30b-a3b:free"
# TEST_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
# TEST_MODEL = "meta-llama/llama-4-scout:free"
# TEST_MODEL = "meta-llama/llama-4-maverick:free"
# TEST_MODEL = "mistralai/mistral-7b-instruct:free"

# 실제 Two-Phase 시스템에서 사용하는 테스트 쿼리
TEST_QUERIES = [
    "KO/TKO 승리가 가장 많은 파이터 상위 3명을 차트로 보여줘"
]

async def test_langchain_tools_direct(model_name: str, query: str):
    """순수 LangChain 도구로 직접 테스트 (FastMCP 없이)"""
    print(f"\n{'='*80}")
    print(f"🤖 Testing Model: {model_name}")
    print(f"🔍 Query: {query}")
    print(f"🧪 Using PURE LangChain Tools (No FastMCP)")
    print(f"{'='*80}")

    try:
        from langchain.tools import Tool
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI  # 공식 LangChain import
        import json

        # 1. 순수 LangChain 도구 생성
        def execute_sql_dummy(query_text: str) -> str:
            """더미 SQL 실행 - 테스트용 KO/TKO 데이터 반환"""
            return json.dumps([
                {"fighter_name": "Francis Ngannou", "ko_tko_wins": 12},
                {"fighter_name": "Derrick Lewis", "ko_tko_wins": 11},
                {"fighter_name": "Junior dos Santos", "ko_tko_wins": 10}
            ])

        tools = [
            Tool(
                name="execute_sql_query",
                func=execute_sql_dummy,
                description="UFC 데이터베이스에서 SQL 쿼리를 실행합니다"
            )
        ]

        print(f"🔧 Created {len(tools)} pure LangChain tools")

        # 2. 공식 LangChain ChatOpenAI로 OpenRouter 사용
        llm = ChatOpenAI(
            model=model_name,  # OpenRouter 모델명
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",  # OpenRouter URL
            temperature=0.7,
            default_headers={
                "HTTP-Referer": "https://mma-savant.com",
                "X-Title": "MMA Savant Test"
            }
        )

        print(f"🤖 OpenRouter LLM created (using ChatOpenAI): {model_name}")

        # 3. 프롬프트 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful UFC data analyst. Use the SQL tool to get data, then create a summary."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        print(f"📝 Prompt template created")

        start_time = asyncio.get_event_loop().time()

        # 4. 에이전트 생성 시도
        try:
            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_type = "tool_calling"
            print(f"✅ Tool calling agent created successfully!")
        except Exception as e:
            print(f"⚠️ Tool calling failed: {e}")
            print(f"🔄 Trying ReAct agent...")

            from langchain.agents import create_react_agent
            react_prompt = ChatPromptTemplate.from_messages([
                ("system", """Answer questions about UFC data. You have access to these tools:

{tools}

Use this format:
Question: {input}
Thought: I need to get UFC data
Action: execute_sql_query
Action Input: query about KO/TKO wins
Observation: the result
Thought: Now I can answer
Final Answer: my response

Begin!

Question: {input}
Thought:{agent_scratchpad}""")
            ])

            agent = create_react_agent(llm, tools, react_prompt)
            agent_type = "react"
            print(f"✅ ReAct agent created successfully!")

        # 5. AgentExecutor 생성 및 실행
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3,
            return_intermediate_steps=True
        )

        print(f"🚀 Running {agent_type} agent with query...")

        result = await agent_executor.ainvoke({"input": query})

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # 결과 분석
        print(f"\n📊 LangChain Tools Test Results:")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   🤖 Agent Type: {agent_type}")
        print(f"   📝 Output: {result.get('output', 'No output')[:200]}...")

        return {
            "model": model_name,
            "query": query,
            "success": True,
            "duration": duration,
            "agent_type": agent_type,
            "output": result.get('output', ''),
            "intermediate_steps": len(result.get('intermediate_steps', []))
        }

    except Exception as e:
        print(f"❌ LangChain tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_name,
            "query": query,
            "success": False,
            "error": str(e),
            "duration": 0
        }

async def test_two_phase_system(model_name: str, query: str, db: AsyncSession):
    """Two-Phase 시스템으로 실제 테스트 (실제 환경과 동일)"""
    print(f"\n{'='*80}")
    print(f"🤖 Testing Model: {model_name}")
    print(f"🔍 Query: {query}")
    print(f"{'='*80}")

    # Config 백업
    original_model = Config.OPENROUTER_MODEL_NAME

    try:
        # OpenRouter 모델로 설정 (원래는 Claude 사용)
        Config.OPENROUTER_MODEL_NAME = model_name

        # OpenRouter 프로바이더로 LangChain 서비스 생성
        service = LangChainLLMService(provider="openrouter")

        print(f"📋 Model: {model_name}")
        print(f"🚀 Starting Two-Phase processing...")

        start_time = asyncio.get_event_loop().time()

        # 실제 스트리밍 응답 수집
        results = []
        visualization_data = None

        async for chunk in service.generate_streaming_chat_response(
            user_message=query,
            conversation_id="test_session",
            user_id=1
        ):
            results.append(chunk)
            print(f"📦 Chunk: {chunk['type']}")

            if chunk["type"] == "phase_start":
                print(f"   🔵 Phase {chunk.get('phase', '?')} started")
            elif chunk["type"] == "final_result":
                print(f"   🎯 Final result received")
                visualization_data = {
                    "content": chunk.get("content", ""),
                    "visualization_type": chunk.get("visualization_type"),
                    "visualization_data": chunk.get("visualization_data"),
                    "insights": chunk.get("insights", [])
                }

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # 결과 분석
        print(f"\n📊 Two-Phase System Results:")
        print(f"   ⏱️  Duration: {duration:.2f}s")
        print(f"   📝 Total Chunks: {len(results)}")

        # 청크 타입별 분석
        chunk_types = {}
        for chunk in results:
            chunk_type = chunk["type"]
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

        for chunk_type, count in chunk_types.items():
            print(f"   {chunk_type}: {count}")

        # 시각화 데이터 분석
        if visualization_data:
            print(f"\n📈 Visualization Analysis:")
            print(f"   📝 Content Length: {len(visualization_data['content'])}")
            print(f"   📊 Visualization Type: {visualization_data['visualization_type']}")
            print(f"   📋 Has Visualization Data: {bool(visualization_data['visualization_data'])}")
            print(f"   💡 Insights Count: {len(visualization_data['insights'])}")

            # 시각화 데이터 구조 확인
            if visualization_data['visualization_data']:
                viz_data = visualization_data['visualization_data']
                print(f"   🔍 Viz Data Keys: {list(viz_data.keys())}")
                if 'data' in viz_data:
                    print(f"   📈 Data Points: {len(viz_data['data'])}")
        else:
            print(f"\n❌ No visualization data generated")

        # Config 복원
        Config.OPENROUTER_MODEL_NAME = original_model

        return {
            "model": model_name,
            "query": query,
            "success": visualization_data is not None,
            "duration": duration,
            "chunk_count": len(results),
            "chunk_types": chunk_types,
            "visualization_data": visualization_data,
            "has_chart": visualization_data and visualization_data.get("visualization_type") not in [None, "text_summary"]
        }

    except Exception as e:
        # Config 복원
        Config.OPENROUTER_MODEL_NAME = original_model

        print(f"❌ Two-Phase test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_name,
            "query": query,
            "success": False,
            "error": str(e),
            "duration": 0,
            "chunk_count": 0
        }

async def compare_with_claude(query: str, db: AsyncSession):
    """Claude 모델과의 비교 테스트"""
    print(f"\n{'='*80}")
    print(f"🆚 CLAUDE COMPARISON TEST")
    print(f"🔍 Query: {query}")
    print(f"{'='*80}")

    # Claude로 기준 테스트
    claude_result = await test_two_phase_system("anthropic/claude-3.5-sonnet", query, db)

    return claude_result

async def main():
    """메인 테스트 함수"""
    print("🧪 OpenRouter API Test Script")
    print("=" * 60)

    # 환경 설정 확인
    print("🔧 Configuration Check:")
    print(f"   API Key: {'✅ Set' if Config.OPENROUTER_API_KEY else '❌ Missing'}")
    print(f"   Base URL: {Config.OPENROUTER_BASE_URL}")
    print(f"   Default Model: {Config.OPENROUTER_MODEL_NAME}")

    if not Config.OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY is not set in environment variables")
        return

    # 순수 LangChain 도구 테스트 실행 (데이터베이스 연결 불필요)
    try:
        query = TEST_QUERIES[0]  # 첫 번째 쿼리로 테스트
        print(f"\n🧪 Testing with PURE LangChain Tools (No FastMCP)")
        result = await test_langchain_tools_direct(TEST_MODEL, query)

        # 결과 출력
        print(f"\n{'='*60}")
        print("📊 TEST RESULT")
        print(f"{'='*60}")

        if result["success"]:
            print(f"✅ Success: {TEST_MODEL}")
            print(f"   ⏱️  Duration: {result['duration']:.2f}s")
            print(f"   🤖 Agent Type: {result['agent_type']}")
            print(f"   📝 Intermediate Steps: {result['intermediate_steps']}")
            print(f"   💬 Output: {result['output'][:200]}...")
        else:
            print(f"❌ Failed: {TEST_MODEL}")
            print(f"   Error: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error with {TEST_MODEL}: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n🎯 테스트 완료! 위 결과를 확인하여 모델 호환성을 평가하세요.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Script interrupted by user")
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()