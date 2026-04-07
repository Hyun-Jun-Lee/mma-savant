from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, ToolMessage


def build_react_agent(model, tools: list, prompt: str | None = None):
    """
    StateGraph 기반 ReAct 에이전트를 컴파일하여 반환.

    Args:
        model: LangChain ChatModel (tool calling 지원)
        tools: 바인딩할 도구 리스트
        prompt: 시스템 프롬프트 (선택)

    Returns:
        CompiledGraph — .ainvoke({"messages": [...]}, config={...}) 로 호출
    """
    model_with_tools = model.bind_tools(tools)
    tools_by_name = {tool.name: tool for tool in tools}

    async def llm_call(state: MessagesState):
        messages = state["messages"]
        if prompt:
            messages = [SystemMessage(content=prompt)] + list(messages)
        return {"messages": [await model_with_tools.ainvoke(messages)]}

    async def tool_node(state: MessagesState):
        results = []
        for tc in state["messages"][-1].tool_calls:
            tool = tools_by_name.get(tc["name"])
            if tool is None:
                results.append(ToolMessage(
                    content=f"Error: tool '{tc['name']}' not found",
                    tool_call_id=tc["id"],
                ))
                continue
            try:
                observation = await tool.ainvoke(tc["args"])
            except Exception as e:
                observation = f"Error executing tool: {e}"
            results.append(ToolMessage(
                content=str(observation),
                tool_call_id=tc["id"],
            ))
        return {"messages": results}

    def should_continue(state: MessagesState):
        if state["messages"][-1].tool_calls:
            return "tool_node"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("llm_call", llm_call)
    graph.add_node("tool_node", tool_node)
    graph.add_edge(START, "llm_call")
    graph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    graph.add_edge("tool_node", "llm_call")

    return graph.compile()
