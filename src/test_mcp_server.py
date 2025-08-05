# test_mcp_server.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server_standalone():
    """MCP 서버만 단독으로 테스트"""
    print("🧪 MCP 서버 단독 테스트 시작...")
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "tools.load_tools"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            print("✅ MCP 서버 프로세스 시작 성공")
            
            async with ClientSession(read, write) as session:
                print("✅ 세션 생성 완료")
                
                # 서버 초기화
                init_result = await session.initialize()
                print(f"✅ 서버 초기화 완료: {init_result}")
                
                # 사용 가능한 도구 목록 확인
                tools_result = await session.list_tools()
                print(f"✅ 사용 가능한 도구 개수: {len(tools_result.tools)}")
                
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # 도구 직접 호출 테스트 (예시)
                if tools_result.tools:
                    first_tool = tools_result.tools[0]
                    print(f"\n🔧 '{first_tool.name}' 도구 테스트 호출...")
                    
                    try:
                        # 도구 호출 (실제 파라미터는 도구에 따라 조정 필요)
                        call_result = await session.call_tool(
                            first_tool.name,
                            arguments={"fighter_id": 14000}  # 예시 파라미터
                        )
                        print(f"✅ 도구 호출 성공: {call_result}")
                    except Exception as tool_error:
                        print(f"❌ 도구 호출 실패: {tool_error}")
                        print(f"도구 스키마: {first_tool.inputSchema}")
                
                return True
                
    except Exception as e:
        print(f"❌ MCP 서버 테스트 실패: {e}")
        import traceback
        print(f"상세 에러:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mcp_server_standalone())