import asyncio
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.tools import load_mcp_tools

load_dotenv()

async def test_ufc_chatbot():
    print("🔧 MCP 도구들 로딩 중...")

    server_params = StdioServerParameters(
        command="python",
        args=["-m", "tools.load_tools"]
    )

    # 시스템 프롬프트 정의
    system_prompt = """
    당신은 UFC 전문 어시스턴트입니다.
    
    중요 규칙:
    - 모든 선수 이름은 영어로 저장되어 있습니다, 한글 선수 이름 입력시 영어로 번역 후 검색하세요
    - 한국 선수는 영어로 번역시 "Hyunjun Lee"와 같이 이름-성 형식으로 번역 후 검색하세요.
    - 번역한 영문으로 검색이 되지 않는다면 사용자에게 영문 이름을 요청하세요.
    
    예시:
    - 톰 아스피날 = Tom Aspinall
    - 이현준 = Hyunjun Lee
    """
    
    # SystemMessage 생성
    system_message = SystemMessage(content=system_prompt)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            print(f"✅ {len(tools)}개의 도구 로드 완료:")

            # Claude LLM 설정
            llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0,
            )
            
            # 에이전트 생성
            agent = create_react_agent(llm, tools=tools)
            
            print("\n🥊 UFC MCP 챗봇 테스트 시작!")
            print("=" * 50)
            
            # 테스트 질문들
            test_questions = [
                "유주상의 선수 정보를 알려주세요",
                "유수영의 선수 정보를 알려주세요",
            ]
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n📝 테스트 {i}: {question}")
                print("-" * 30)
                
                try:
                    response = await agent.ainvoke({
                        "messages": [HumanMessage(content=question), system_message]
                    })
                    print(f"🤖 답변: {response['messages'][-1].content}")

                    # 메시지 히스토리 상세 분석
                    print(f"\n📊 메시지 히스토리 분석:")
                    for j, msg in enumerate(response['messages']):
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            print(f"     Tool calls: {[tc.name if hasattr(tc, 'name') else str(tc) for tc in msg.tool_calls]}")
                except Exception as e:
                    print(f"❌ 오류: {str(e)}")
                
                print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_ufc_chatbot())