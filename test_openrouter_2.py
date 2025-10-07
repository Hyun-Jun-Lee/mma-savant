
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from langchain.tools import Tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from database.connection.postgres_conn import get_readonly_db_context
from config import Config
from common.logging_config import get_logger
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from llm.prompts.two_phase_prompts import get_phase1_prompt

LOGGER = get_logger(__name__)

# 테스트할 모델 (실제 Two-Phase 시스템과 동일한 구조로 테스트)
TEST_MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"

# 실제 Two-Phase 시스템에서 사용하는 테스트 쿼리
TEST_QUERIES = [
    "KO/TKO 승리가 가장 많은 파이터 상위 3명을 차트로 보여줘"
]

async def test_readonly_database_connection():
    """
    읽기 전용 데이터베이스 연결 테스트
    """
    print(f"🔍 Testing readonly database connection...")

    try:
        # 읽기 전용 계정으로 간단한 테스트 쿼리
        with get_readonly_db_context() as session:
            result = session.execute(text("SELECT COUNT(*) as fighter_count FROM fighter"))
            row = result.fetchone()

            print(f"✅ Readonly database connection successful!")
            print(f"   📊 Fighter count: {row.fighter_count}")
            return True

    except Exception as e:
        print(f"❌ Readonly database connection failed: {e}")
        return False

def create_real_database_tools():
    """실제 데이터베이스 연결을 사용하는 LangChain 도구 생성"""
    print(f"🔧 [TOOLS] Creating database tools...")

    def sync_execute_sql_query(query: str) -> str:
        """
        읽기 전용 DB 연결을 사용하는 단순화된 SQL 실행
        DB 레벨에서 권한 제어하므로 복잡한 보안 검증 불필요
        """
        print(f"🔧 [READONLY DB] Called with query: {query}")

        # JSON 형식으로 잘못 전달된 경우 처리
        if query.startswith("{") and query.endswith("}"):
            try:
                query_data = json.loads(query)
                if "query" in query_data:
                    query = query_data["query"]
                    print(f"🔧 [READONLY DB] Extracted SQL from JSON")
            except:
                pass

        # 간단한 래퍼 제거 (마크다운 코드 블록 형식들)
        query = query.strip()

        # ```sql ... ``` 형태 제거
        if query.startswith("```") and query.endswith("```"):
            import re
            query = re.sub(r'^```\w*\n?', '', query)
            query = re.sub(r'\n?```$', '', query)
            query = query.strip()
            print(f"🔧 [READONLY DB] Removed markdown wrapper")

        # $ ... $ 형태 제거
        elif query.startswith("$") and query.endswith("$"):
            query = query.strip("$").strip()
            print(f"🔧 [READONLY DB] Removed $ wrapper")

        # 결과 제한 (옵션)
        limit = 100
        query_upper = query.upper()
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        try:
            # 읽기 전용 데이터베이스 연결 사용
            # DB 레벨에서 SELECT만 허용하므로 추가 검증 불필요
            with get_readonly_db_context() as session:
                print(f"🔧 [READONLY DB] Executing with readonly connection")
                result = session.execute(text(query))
                rows = result.fetchall()

                # 결과를 딕셔너리 형태로 변환
                if rows:
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                else:
                    data = []

                print(f"🔧 [READONLY DB] Success: {len(data)} rows returned")
                return json.dumps({
                    "success": True,
                    "query": query,
                    "row_count": len(data),
                    "data": data,
                    "columns": list(result.keys()) if rows else []
                })

        except SQLAlchemyError as e:
            # DB 레벨 권한 오류 발생 시 (INSERT, DELETE 시도 등)
            print(f"🔧 [READONLY DB] SQL Error (권한 또는 구문 오류): {e}")
            return json.dumps({
                "error": f"쿼리 실행 실패: {str(e)}",
                "query": query,
                "success": False,
                "hint": "읽기 전용 계정이므로 SELECT만 가능합니다"
            })
        except Exception as e:
            print(f"🔧 [READONLY DB] Unexpected Error: {e}")
            return json.dumps({
                "error": f"예상치 못한 오류: {str(e)}",
                "query": query,
                "success": False
            })

    tools = [
        Tool(
            name="execute_raw_sql_query",
            func=sync_execute_sql_query,
            description="""UFC 데이터베이스에서 읽기 전용 SQL 쿼리를 실행합니다.

            중요한 테이블명 규칙 (단수형 사용):
            - 'fighter' (파이터 정보)
            - 'match' (매치 정보)
            - 'fighter_match' (파이터-매치 관계)
            - 'event' (이벤트 정보)
            - 'ranking' (랭킹 정보)
            - 'weight_class' (체급 정보)

            읽기 전용 계정이므로 SELECT만 가능합니다.

            올바른 쿼리 예시:
            SELECT f.name, COUNT(*) as ko_wins FROM fighter f JOIN fighter_match fm ON f.id = fm.fighter_id JOIN match m ON fm.match_id = m.id WHERE m.method ILIKE '%ko%' GROUP BY f.name ORDER BY ko_wins DESC LIMIT 3;

            Args:
                query (str): 실행할 SQL 쿼리 (읽기 전용)
            """
        )
    ]

    print(f"🔧 [TOOLS] Created {len(tools)} tools: {[tool.name for tool in tools]}")
    return tools

async def test_langchain_with_real_db(model_name: str, query: str):
    """실제 데이터베이스를 사용한 LangChain 도구 테스트"""
    print(f"{'='*80}")

    try:
        # 1. 실제 데이터베이스 도구 생성
        tools = create_real_database_tools()

        # 2. 공식 LangChain ChatOpenAI로 OpenRouter 사용
        llm = ChatOpenAI(
            model=model_name,
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
            default_headers={
                "HTTP-Referer": "https://mma-savant.com",
                "X-Title": "MMA Savant Test"
            }
        )

        print(f"🤖 OpenRouter LLM created (using ChatOpenAI): {model_name}")

        # 3. 실제 Two-Phase 시스템의 Phase 1 프롬프트 사용
        phase1_prompt_text = get_phase1_prompt()
        prompt = ChatPromptTemplate.from_messages([
            ("system", phase1_prompt_text),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        print(f"📝 Prompt template created")

        start_time = asyncio.get_event_loop().time()

        # 4. 에이전트 생성 시도
        # Mistral 모델은 tool calling보다 ReAct가 더 잘 작동할 수 있음
        use_react = True  # 강제로 ReAct 사용

        if not use_react:
            try:
                agent = create_tool_calling_agent(llm, tools, prompt)
                agent_type = "tool_calling"
                print(f"✅ Tool calling agent created successfully!")
            except Exception as e:
                print(f"⚠️ Tool calling failed: {e}")
                print(f"🔄 Trying ReAct agent...")

        if use_react:
            from langchain.agents import create_react_agent
            print(f"🔄 Using ReAct agent for better tool execution")

            # 실제 Phase 1 프롬프트에 ReAct 형식만 추가
            react_prompt = ChatPromptTemplate.from_template(f"""{phase1_prompt_text}

## ReAct Tool Usage Format
You have access to the following tools:
{{tools}}

The available tool names are: {{tool_names}}

📌 SQL 쿼리 작성 규칙:
- 읽기 전용 계정이므로 SELECT만 가능 (INSERT/UPDATE/DELETE 불가)
- Action Input에는 SQL 쿼리만 작성 (마크다운 래핑 불필요)
- 예시: Action Input: SELECT name FROM fighter LIMIT 5

Use this exact format:

Thought: [Your reasoning about what needs to be done]
Action: execute_raw_sql_query
Action Input: [PLAIN SQL query without any markdown formatting]
Observation: [The result will appear here]
... (this Thought/Action/Action Input/Observation can repeat as needed)
Thought: [Your final reasoning]
Final Answer: [Your response with collected data]

Begin!

Question: {{input}}
Thought: {{agent_scratchpad}}""")

            agent = create_react_agent(llm, tools, react_prompt)
            agent_type = "react"
            print(f"✅ ReAct agent created successfully!")

        # 5. AgentExecutor 생성 및 실행
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )

        print(f"🚀 Running {agent_type} agent with real database query...")

        result = await agent_executor.ainvoke({"input": query})

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # 결과 분석
        print(f"\n📊 Real Database Test Results:")
        print(f"   📝 Output: {result.get('output', 'No output')}")

        # 중간 단계 분석
        intermediate_steps = result.get('intermediate_steps', [])
        print(f"   🔧 Total Intermediate Steps: {len(intermediate_steps)}")

        if intermediate_steps:
            print(f"   🔧 Database Queries Executed: {len(intermediate_steps)}")
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                print(f"      Step {i}:")
                print(f"        Tool: {getattr(action, 'tool', 'unknown')}")
                print(f"        Input: {str(getattr(action, 'tool_input', 'unknown'))}")
                print(f"        Output: {str(observation)}")
        else:
            print(f"   ⚠️  No intermediate steps found - tools may not have been called!")
            print(f"   🤔 Agent may have answered directly without using tools")

        return {
            "model": model_name,
            "query": query,
            "success": True,
            "duration": duration,
            "agent_type": agent_type,
            "output": result.get('output', ''),
            "intermediate_steps": len(intermediate_steps),
            "database_queries": len([s for s in intermediate_steps if hasattr(s[0], 'tool') and s[0].tool == 'execute_sql_query'])
        }

    except Exception as e:
        print(f"❌ Real database test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_name,
            "query": query,
            "success": False,
            "error": str(e),
            "duration": 0
        }


async def main():
    """메인 테스트 함수"""
    print("🧪 OpenRouter API Test with Real Database v2")
    print("=" * 60)

    # 환경 설정 확인
    print("🔧 Configuration Check:")
    print(f"   API Key: {'✅ Set' if Config.OPENROUTER_API_KEY else '❌ Missing'}")
    print(f"   Base URL: https://openrouter.ai/api/v1")
    print(f"   Test Model: {TEST_MODEL}")

    if not Config.OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY is not set in environment variables")
        return

    # 읽기 전용 데이터베이스 연결 테스트
    print(f"\n🗄️ Readonly Database Connection Test:")
    db_connected = await test_readonly_database_connection()

    if not db_connected:
        print("❌ Readonly database connection failed. Cannot proceed with test.")
        return

    # 실제 데이터베이스를 사용한 LangChain 도구 테스트
    try:
        query = TEST_QUERIES[0]
        print(f"\n🧪 Testing with Readonly Database & LangChain Tools")
        result = await test_langchain_with_real_db(TEST_MODEL, query)

        # 결과 출력
        print(f"\n{'='*60}")
        print("📊 FINAL TEST RESULT")
        print(f"{'='*60}")

        if result["success"]:
            print(f"✅ Success: {TEST_MODEL}")
            print(f"   🤖 Agent Type: {result['agent_type']}")
            print(f"   📝 Intermediate Steps: {result['intermediate_steps']}")
            print(f"   🗄️  Database Queries: {result['database_queries']}")
            print(f"   💬 Output: {result['output']}")

            print(f"\n🎯 테스트 성공!")
            print(f"   ✅ OpenRouter 모델이 읽기 전용 DB와 안전하게 연동")
            print(f"   ✅ LangChain Tool 사용 가능")
            print(f"   ✅ Two-Phase 시스템 호환 가능성 높음")
        else:
            print(f"❌ Failed: {TEST_MODEL}")
            print(f"   Error: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error with {TEST_MODEL}: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n🎯 테스트 완료! 위 결과를 확인하여 실제 시스템 적용 가능성을 평가하세요.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Script interrupted by user")
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()