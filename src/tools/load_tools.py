from fastmcp import FastMCP
import sys
import os
import importlib
import inspect
from typing import List, Union

# 현재 파일이 있는 디렉토리의 상위 디렉토리(src)를 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

mcp = FastMCP("mma-savant")

def load_tools_from_module(module_path: str, tool_names: List[str] = None):
    """모듈에서 지정된 도구들을 로드하거나 @mcp.tool() 데코레이터가 붙은 모든 함수를 자동 로드"""
    try:
        module = importlib.import_module(module_path)
        
        if tool_names:
            # 기존 방식: 지정된 도구들만 로드
            for tool_name in tool_names:
                if hasattr(module, tool_name):
                    tool_func = getattr(module, tool_name)
                    mcp.add_tool(tool_func)
                    print(f"✅ {tool_name} 로드됨")
                else:
                    print(f"❌ {tool_name}을 {module_path}에서 찾을 수 없음")
        else:
            # 새로운 방식: @mcp.tool() 데코레이터가 붙은 모든 함수 자동 로드
            loaded_count = 0
            loaded_tools = set()  # 중복 방지를 위한 툴 이름 추적
            
            for name, obj in inspect.getmembers(module):
                if (inspect.isfunction(obj) and 
                    hasattr(obj, '__wrapped__') and 
                    hasattr(obj, '_mcp_tool') and 
                    name not in loaded_tools):
                    try:
                        mcp.add_tool(obj)
                        loaded_tools.add(name)
                        print(f"✅ {name} 자동 로드됨")
                        loaded_count += 1
                    except Exception as e:
                        print(f"⚠️ {name} 로드 실패: {e}")
            
            print(f"📊 {module_path}에서 총 {loaded_count}개 도구 로드됨")
            
    except Exception as e:
        print(f"❌ {module_path} 로드 실패: {e}")


def auto_load_all_tools():
    """tools 디렉토리의 모든 *_tools.py 파일에서 도구들을 자동 로드"""
    tools_dir = os.path.dirname(__file__)
    global_loaded_tools = set()  # 전역 중복 방지
    total_tools = 0
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('_tools.py') and filename != '__init__.py':
            module_name = filename[:-3]  # .py 제거
            module_path = f"tools.{module_name}"
            print(f"\n🔄 {module_path} 로딩 중...")
            
            # 모듈별 로딩 전 도구 개수 확인
            before_count = len(mcp._tools) if hasattr(mcp, '_tools') else 0
            
            load_tools_from_module(module_path)
            
            # 모듈별 로딩 후 도구 개수 확인
            after_count = len(mcp._tools) if hasattr(mcp, '_tools') else 0
            module_tools = after_count - before_count
            total_tools += module_tools
            
            print(f"✅ {module_name}: {module_tools}개 도구 추가됨")
    
    print(f"\n📊 전체 로딩 완료: 총 {total_tools}개 도구")