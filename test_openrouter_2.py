#!/usr/bin/env python3
"""
OpenRouter API 테스트 스크립트 v2
실제 데이터베이스 연결을 사용한 순수 LangChain Tool 테스트
"""

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

from database.connection.postgres_conn import get_async_db_context
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

async def execute_real_sql_query(query: str, limit: int = 100) -> str:
    """
    실제 데이터베이스에서 SQL 쿼리 실행
    database_tools.py의 execute_raw_sql_query 함수를 기반으로 구현
    """
    print(f"🔧 [TOOL CALLED] execute_real_sql_query with query: {query[:100]}...")
    LOGGER.info(f"Tool execute_real_sql_query called with query: {query}")

    # 보안 검증: SELECT 문만 허용
    query_stripped = query.strip().upper()
    if not query_stripped.startswith('SELECT'):
        return json.dumps({
            "error": "보안상 SELECT 문만 허용됩니다",
            "allowed_operations": ["SELECT"]
        })

    # 위험한 키워드 차단
    dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
    for keyword in dangerous_keywords:
        if keyword in query_stripped:
            return json.dumps({
                "error": f"보안상 '{keyword}' 문은 허용되지 않습니다",
                "query": query
            })

    # 결과 제한
    limit = min(max(1, limit), 1000)

    # LIMIT 절이 없으면 추가
    if 'LIMIT' not in query_stripped:
        query = f"{query.rstrip(';')} LIMIT {limit}"

    try:
        async with get_async_db_context() as session:
            result = await session.execute(text(query))
            rows = result.fetchall()

            # 결과를 딕셔너리 형태로 변환
            if rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                data = []

            return json.dumps({
                "success": True,
                "query": query,
                "row_count": len(data),
                "data": data,
                "columns": list(result.keys()) if rows else []
            })

    except SQLAlchemyError as e:
        return json.dumps({
            "error": f"SQL 실행 오류: {str(e)}",
            "query": query,
            "success": False
        })
    except Exception as e:
        return json.dumps({
            "error": f"예상치 못한 오류: {str(e)}",
            "query": query,
            "success": False
        })

def create_real_database_tools():
    """실제 데이터베이스 연결을 사용하는 LangChain 도구 생성"""
    print(f"🔧 [TOOLS] Creating database tools...")

    def sync_execute_sql_query(query: str) -> str:
        """
        동기 래퍼 함수 - LangChain Tool이 async 함수를 직접 처리하지 못함
        """
        print(f"🔧 [SYNC WRAPPER] Called with query: {query[:100]}...")

        # JSON 형식으로 잘못 전달된 경우 처리
        if query.startswith("{") and query.endswith("}"):
            try:
                query_data = json.loads(query)
                if "query" in query_data:
                    query = query_data["query"]
                    print(f"🔧 [SYNC WRAPPER] Extracted SQL from JSON: {query[:100]}...")
            except:
                pass

        try:
            import nest_asyncio
            nest_asyncio.apply()

            # 현재 이벤트 루프를 사용
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    print(f"🔧 [SYNC WRAPPER] Using existing event loop with nest_asyncio")
                    # nest_asyncio를 사용하여 중첩 실행
                    result = loop.run_until_complete(execute_real_sql_query(query))
                else:
                    print(f"🔧 [SYNC WRAPPER] Creating new event loop")
                    result = asyncio.run(execute_real_sql_query(query))
            except RuntimeError:
                print(f"🔧 [SYNC WRAPPER] Creating new event loop (RuntimeError)")
                result = asyncio.run(execute_real_sql_query(query))

            print(f"🔧 [SYNC WRAPPER] Query executed successfully")
            return result
        except Exception as e:
            print(f"🔧 [SYNC WRAPPER] Error: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({
                "error": f"동기 래퍼 실행 오류: {str(e)}",
                "success": False
            })

    tools = [
        Tool(
            name="execute_raw_sql_query",
            func=sync_execute_sql_query,
            description="""UFC 데이터베이스에서 SQL 쿼리를 실행합니다.

            중요한 테이블명 규칙 (단수형 사용):
            - 'match' (매치 정보)
            - 'fighter' (파이터 정보)
            - 'event' (이벤트 정보)
            - 'ranking' (랭킹 정보)

            SELECT 문만 허용되며, 보안상 다른 SQL 명령어는 차단됩니다.
            KO/TKO 승리 관련 쿼리 예시:
            SELECT fighter_name, ko_tko_wins FROM fighter ORDER BY ko_tko_wins DESC LIMIT 3;

            Args:
                query (str): 실행할 SQL 쿼리 (SELECT 문만 허용)
                description (str, optional): 쿼리 목적 설명
                limit (int): 최대 반환 행 수 (기본값: 100)
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
            # ReAct 에이전트용 프롬프트 - 필수 변수 포함
            react_prompt = ChatPromptTemplate.from_template("""You are MMA Savant Phase 1 - analyze queries and execute SQL queries to collect data.

        You have access to the following tools:
        {tools}

        The available tool names are: {tool_names}

        ## Database Schema
        Use SINGULAR table names (match, fighter, event, ranking)
        All text data in database is stored in lowercase

        ## How to use tools
        To use a tool, please use the following format:

        Thought: I need to analyze the query and execute SQL
        Action: execute_raw_sql_query
        Action Input: SELECT query here
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now have the data
        Final Answer: the final answer with the collected data

        ## Examples
        Question: KO/TKO 승리가 가장 많은 파이터 3명
        Thought: I need to query fighter data for KO/TKO wins
        Action: execute_raw_sql_query
        Action Input: SELECT name, ko_tko_wins FROM fighter ORDER BY ko_tko_wins DESC LIMIT 3
        Observation: [result will be shown here]
        Thought: I have the data for top 3 fighters
        Final Answer: Here are the results...

        Begin!

        Question: {input}
        Thought: {agent_scratchpad}""")

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
                print(f"        Input: {str(getattr(action, 'tool_input', 'unknown'))[:100]}...")
                print(f"        Output: {str(observation)[:200]}...")
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

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    print(f"🔍 Testing database connection...")

    try:
        # 간단한 테스트 쿼리
        result = await execute_real_sql_query("SELECT COUNT(*) as fighter_count FROM fighter LIMIT 1")
        result_data = json.loads(result)

        if result_data.get("success"):
            print(f"✅ Database connection successful!")
            print(f"   📊 Fighter count: {result_data['data'][0]['fighter_count']}")
            return True
        else:
            print(f"❌ Database query failed: {result_data.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

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

    # 데이터베이스 연결 테스트
    print(f"\n🗄️ Database Connection Test:")
    db_connected = await test_database_connection()

    if not db_connected:
        print("❌ Database connection failed. Cannot proceed with real database test.")
        return

    # 실제 데이터베이스를 사용한 LangChain 도구 테스트
    try:
        query = TEST_QUERIES[0]
        print(f"\n🧪 Testing with REAL Database & PURE LangChain Tools")
        result = await test_langchain_with_real_db(TEST_MODEL, query)

        # 결과 출력
        print(f"\n{'='*60}")
        print("📊 FINAL TEST RESULT")
        print(f"{'='*60}")

        if result["success"]:
            print(f"✅ Success: {TEST_MODEL}")
            print(f"   ⏱️  Duration: {result['duration']:.2f}s")
            print(f"   🤖 Agent Type: {result['agent_type']}")
            print(f"   📝 Intermediate Steps: {result['intermediate_steps']}")
            print(f"   🗄️  Database Queries: {result['database_queries']}")
            print(f"   💬 Output: {result['output'][:300]}...")

            print(f"\n🎯 테스트 성공!")
            print(f"   ✅ OpenRouter 모델이 실제 데이터베이스와 연동 가능")
            print(f"   ✅ 순수 LangChain Tool 사용 가능")
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