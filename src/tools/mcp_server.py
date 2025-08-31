#!/usr/bin/env python3
"""
MCP 서버 스크립트
LangChain MCP adapters에서 사용할 독립적인 MCP 서버
"""
import sys
import os

# 현재 파일이 있는 디렉토리의 상위 디렉토리(src)를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from tools.load_tools import mcp, auto_load_all_tools

if __name__ == "__main__":
    print("🚀 MMA Savant MCP 서버 시작 중...")
    print("🔧 자동 도구 로딩 시작...")
    
    # 모든 *_tools.py 파일에서 @mcp.tool() 데코레이터가 붙은 함수들을 자동 로드
    # auto_load_all_tools()
    auto_load_all_tools(only_modules=['database_tools'])
    
    print("\n✨ 모든 도구 로딩 완료!")
    print("🎯 MCP 서버 실행 중...")
    
    # stdio 모드로 실행 (LangChain MCP adapter와 통신용)
    mcp.run(transport="stdio")