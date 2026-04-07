"""E2E Graph Evaluation — LangSmith LLM-as-Judge

전체 MMA 그래프(conversation_manager → supervisor → analysis → critic → text_response)를
실행하고 LLM이 결과 품질을 채점합니다.

실행: cd src && uv run python tests/llm/eval_e2e.py

사전 조건:
  - .env에 LANGSMITH_API_KEY, LANGSMITH_TRACING="true" 설정
  - OPENROUTER_MODEL_NAME, OPENROUTER_API_KEY 설정
  - PostgreSQL DB 접속 가능 (mma_analysis, fighter_comparison 노드가 SQL 실행)
  - LangSmith에 "E2E-test-dataset" 데이터셋 생성 완료
"""
import asyncio
import json
import os
import sys

# src/ 디렉토리를 path에 추가 (tests/llm/ → tests/ → src/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client
from langsmith.evaluation import aevaluate

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import Config
from llm.graph import build_mma_graph
from common.logging_config import get_logger

LOGGER = get_logger(__name__)

DATASET_NAME = "E2E-test-dataset"


# =============================================================================
# 1. LLM 생성
# =============================================================================

def _get_llm():
    """평가용 LLM 생성 (OPENROUTER_MODEL_NAME 환경변수 사용)"""
    return ChatOpenAI(
        model=Config.OPENROUTER_MODEL_NAME,
        api_key=Config.OPENROUTER_API_KEY,
        base_url=Config.OPENROUTER_BASE_URL,
        temperature=0.0,
        max_tokens=4000,
        default_headers={
            "HTTP-Referer": "https://mma-savant.com",
            "X-Title": "MMA Savant",
        },
    )


# =============================================================================
# 2. 그래프 컴파일 (모듈 레벨에서 한 번만)
# =============================================================================

_compiled_graph = None


def _get_compiled_graph():
    """그래프를 한 번만 컴파일하여 재사용"""
    global _compiled_graph
    if _compiled_graph is None:
        llm = _get_llm()
        _compiled_graph = build_mma_graph(llm)
        LOGGER.info("E2E eval: graph compiled")
    return _compiled_graph


# =============================================================================
# 3. 메시지 변환 유틸리티
# =============================================================================

def _build_messages(raw_messages: list[dict]) -> list:
    """데이터셋의 메시지를 LangChain 메시지 객체로 변환

    LangSmith 데이터셋의 메시지 형식:
      - {"type": "human", "content": "..."} (LangChain 직렬화 형식)
      - {"role": "human", "content": "..."} (CM eval 형식)
    두 형식 모두 지원.
    """
    result = []
    for msg in raw_messages:
        role = msg.get("type") or msg.get("role", "")
        content = msg.get("content", "")

        if role == "human":
            result.append(HumanMessage(content=content))
        elif role == "ai":
            result.append(AIMessage(content=content))
        elif role == "system":
            result.append(SystemMessage(content=content))
    return result


# =============================================================================
# 4. 평가 대상 함수 (target)
# =============================================================================

async def e2e_target(inputs: dict) -> dict:
    """전체 그래프를 실행하고 주요 출력을 반환

    LangSmith evaluate가 데이터셋의 inputs를 이 함수에 전달.
    그래프 ainvoke 결과에서 평가에 필요한 필드만 추출.
    """
    graph = _get_compiled_graph()

    messages = _build_messages(inputs.get("messages", []))
    sql_context = inputs.get("sql_context", [])
    user_id = inputs.get("user_id", 1)
    conversation_id = inputs.get("conversation_id", 0)

    result = await asyncio.wait_for(
        graph.ainvoke({
            "messages": messages,
            "sql_context": sql_context,
            "user_id": user_id,
            "conversation_id": conversation_id,
        }),
        timeout=120,
    )

    return {
        "final_response": result.get("final_response", ""),
        "route": result.get("route", ""),
        "visualization_type": result.get("visualization_type"),
        "needs_visualization": result.get("needs_visualization", False),
        "critic_passed": result.get("critic_passed", False),
        "resolved_query": result.get("resolved_query", ""),
    }


# =============================================================================
# 5. LLM-as-Judge 평가자
# =============================================================================

E2E_JUDGE_PROMPT = """당신은 MMA 데이터 분석 챗봇의 E2E 응답 품질을 평가하는 심사관입니다.

## 평가 대상
사용자의 질문에 대해 시스템이 생성한 최종 응답(final_response)의 품질을 평가합니다.

## 평가 기준 (각 항목 동일 가중치)

1. **관련성 (Relevance)**
   - 사용자의 질문에 직접적으로 답변하고 있는가
   - 질문의 핵심 의도를 파악하여 적절한 정보를 제공하는가

2. **정확성 (Accuracy)**
   - 응답에 명백한 오류나 모순이 없는가
   - MMA/UFC 관련 고유명사(선수명, 체급 등)가 정확한가

3. **완성도 (Completeness)**
   - 질문에서 요구한 정보를 빠짐없이 포함하는가
   - 숫자/통계 데이터가 포함되어야 하는 질문에 구체적인 수치가 있는가

4. **응답 형식 (Format)**
   - 마크다운 등 가독성 좋은 형식으로 구성되었는가
   - 불필요한 반복이나 장황한 설명 없이 핵심 전달이 되는가

## 입력 정보
- 사용자 질문: {user_query}
- 시스템 응답: {final_response}
- 기대 응답 (참고용): {reference_response}
- 라우팅: {route}
- 시각화 필요: {needs_visualization}

## 출력 형식 (JSON만 출력, 다른 텍스트 없이)
{{"score": 0.0~1.0, "reason": "채점 근거를 1~2문장으로"}}"""


async def e2e_llm_judge(run, example) -> dict:
    """LLM이 E2E 응답 품질을 0~1점으로 채점"""
    outputs = run.outputs or {}
    final_response = outputs.get("final_response", "")
    route = outputs.get("route", "")
    needs_visualization = outputs.get("needs_visualization", False)

    # 사용자 질문 추출
    messages = (run.inputs or {}).get("messages", [])
    user_query = ""
    for msg in reversed(messages):
        msg_type = msg.get("type") or msg.get("role", "")
        if msg_type == "human":
            user_query = msg.get("content", "")
            break

    # 기대 응답 (참고용)
    ref_outputs = example.outputs or {}
    reference_response = ref_outputs.get("final_response", "(없음)")

    judge_input = E2E_JUDGE_PROMPT.format(
        user_query=user_query,
        final_response=final_response,
        reference_response=reference_response,
        route=route,
        needs_visualization=needs_visualization,
    )

    llm = _get_llm()
    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are a strict evaluator. Output only valid JSON."),
            HumanMessage(content=judge_input),
        ])

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        parsed = json.loads(content)
        score = max(0.0, min(1.0, float(parsed["score"])))
        reason = parsed.get("reason", "")

        return {"key": "e2e_llm_judge", "score": score, "comment": reason}

    except Exception as e:
        return {"key": "e2e_llm_judge", "score": 0.0, "comment": f"Judge error: {e}"}


# =============================================================================
# 6. 라우팅 정확도 평가자 (규칙 기반)
# =============================================================================

def route_accuracy(run, example) -> dict:
    """기대 라우팅과 실제 라우팅이 일치하는지 검사"""
    actual_route = (run.outputs or {}).get("route", "")
    expected_route = (example.outputs or {}).get("route", "")

    if not expected_route:
        return {"key": "route_accuracy", "score": 1.0, "comment": "no expected route"}

    score = 1.0 if actual_route == expected_route else 0.0
    comment = f"expected={expected_route}, actual={actual_route}"
    return {"key": "route_accuracy", "score": score, "comment": comment}


def response_not_empty(run, example) -> dict:
    """final_response가 비어있지 않은지 검사"""
    final_response = (run.outputs or {}).get("final_response", "")
    score = 1.0 if final_response.strip() else 0.0
    return {"key": "response_not_empty", "score": score}


def critic_passed_check(run, example) -> dict:
    """critic을 통과했는지 검사"""
    critic_passed = (run.outputs or {}).get("critic_passed", False)
    score = 1.0 if critic_passed else 0.0
    return {"key": "critic_passed", "score": score}


# =============================================================================
# 7. 실행
# =============================================================================

EVALUATORS = [
    e2e_llm_judge,
    route_accuracy,
    response_not_empty,
    critic_passed_check,
]


async def run_evaluation():
    """E2E 평가 파이프라인 실행"""
    client = Client()

    # 데이터셋 존재 확인
    try:
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"데이터셋 확인: '{DATASET_NAME}' (id={dataset.id})")
    except Exception:
        print(f"데이터셋 '{DATASET_NAME}'을 찾을 수 없습니다.")
        print("LangSmith에서 먼저 데이터셋을 생성해주세요.")
        return

    # 그래프 사전 컴파일
    _get_compiled_graph()

    evaluator_names = [e.__name__ for e in EVALUATORS]
    print(f"평가자: {evaluator_names}")

    # 비동기 평가 실행
    results = await aevaluate(
        e2e_target,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix="e2e-eval",
        max_concurrency=1,  # DB 부하 방지
    )

    # 결과 출력
    print("\n" + "=" * 70)
    print("E2E Evaluation Results")
    print("=" * 70)
    async for result in results:
        run = result["run"]
        inputs = run.inputs or {}
        messages = inputs.get("messages", [])

        # 마지막 사용자 질문 추출
        user_query = ""
        for msg in reversed(messages):
            msg_type = msg.get("type") or msg.get("role", "")
            if msg_type == "human":
                user_query = msg.get("content", "")
                break

        outputs = run.outputs or {}
        final_response = outputs.get("final_response", "")
        route = outputs.get("route", "")

        print(f"\n질문: {user_query[:80]}...")
        print(f"라우팅: {route}")
        print(f"응답: {final_response[:120]}...")
        for ev in result["evaluation_results"]["results"]:
            status = "PASS" if ev.score == 1.0 else f"{ev.score:.2f}"
            print(f"  [{status}] {ev.key}: {ev.score:.2f} — {ev.comment or ''}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
