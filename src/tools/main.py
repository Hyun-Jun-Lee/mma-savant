from fastmcp import FastMCP
import sys
import os
import importlib
import inspect
from typing import List, Union

# 현재 파일이 있는 디렉토리의 상위 디렉토리(src)를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

mcp = FastMCP("mma-savant")

def load_tools_from_module(module_path: str, tool_names: List[str]):
    """모듈에서 지정된 도구들을 로드"""
    try:
        module = importlib.import_module(module_path)
        for tool_name in tool_names:
            if hasattr(module, tool_name):
                tool_func = getattr(module, tool_name)
                mcp.add_tool(tool_func)
                print(f"✅ {tool_name} 로드됨")
            else:
                print(f"❌ {tool_name}을 {module_path}에서 찾을 수 없음")
    except Exception as e:
        print(f"❌ {module_path} 로드 실패: {e}")

if __name__ == "__main__":
    load_tools_from_module("tools.fighter_tools", ["get_fighter_info_by_id", "get_fighter_info_by_name", "get_fighter_info_by_nickname"])
    mcp.run()
