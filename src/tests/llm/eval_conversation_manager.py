"""Conversation Manager 노드 — LangSmith Evaluation

실행: uv run python tests/llm/eval_conversation_manager.py  (직접 실행)

사전 조건:
  - .env에 LANGSMITH_API_KEY, LANGSMITH_TRACING="true" 설정
  - MAIN_MODEL 또는 SUB_MODEL 환경변수 설정

평가 모드:
  - EVAL_MODE = "rule"      → 규칙 기반 키워드 매칭 (빠름, 비용 없음)
  - EVAL_MODE = "llm_judge" → LLM이 0~1점 채점 (정확, LLM 비용 발생)
  - EVAL_MODE = "both"      → 두 방식 모두 실행
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
from langsmith.evaluation import evaluate, aevaluate

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import Config
from llm.graph.nodes.conversation_manager import conversation_manager_node


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
# 평가 모드 설정
# =============================================================================

EVAL_MODE = "llm_judge"  # "rule" | "llm_judge" | "both"


# =============================================================================
# 1. 데이터셋 정의
# =============================================================================

DATASET_NAME = "cm-test-dataset"

EVAL_CASES = [
    # =========================================================================
    # A. 대명사 해소 (규칙 1: 대명사/생략 → 구체적 이름/조건)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "코너 맥그리거 전적 알려줘"},
                {"role": "ai", "content": "코너 맥그리거는 UFC에서 22승 6패입니다."},
                {"role": "human", "content": "승률은?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["코너 맥그리거", "승률"],
            "must_not_include": ["그 선수"],
            "description": "생략된 주어 해소: '승률은?' → '코너 맥그리거의 승률'",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "존 존스 최근 경기 알려줘"},
                {"role": "ai", "content": "존 존스의 최근 경기는 2023년 UFC 285입니다."},
                {"role": "human", "content": "상대는 누구였어?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["존 존스"],
            "must_not_include": [],
            "description": "암시적 참조: '상대는 누구였어?' → 존 존스의 경기 맥락 포함",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "하빕 누르마고메도프 전적 알려줘"},
                {"role": "ai", "content": "하빕 누르마고메도프는 29승 0패입니다."},
                {"role": "human", "content": "그 선수 마지막 경기는?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["하빕", "누르마고메도프"],
            "must_not_include": ["그 선수"],
            "description": "명시적 대명사 '그 선수' → 하빕 누르마고메도프로 해소",
        },
    },
    # =========================================================================
    # B. 복합 대명사 (여러 선수 참조)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "이슬람 마카체프 vs 찰스 올리베이라 비교해줘"},
                {"role": "ai", "content": "두 선수의 비교 결과입니다..."},
                {"role": "human", "content": "둘 중 테이크다운 성공률이 높은 선수는?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["마카체프", "올리베이라", "테이크다운"],
            "must_not_include": [],
            "description": "'둘 중' → 두 선수명 모두 해소",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "알렉산더 볼카노프스키 vs 맥스 할로웨이 전적 비교"},
                {"role": "ai", "content": "볼카노프스키 3승, 할로웨이 0승입니다."},
                {"role": "human", "content": "첫 번째 경기는 언제였어?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["볼카노프스키", "할로웨이"],
            "must_not_include": [],
            "description": "'첫 번째 경기' → 두 선수 간 첫 대결 시점으로 해소",
        },
    },
    # =========================================================================
    # C. 주제 전환 감지 (규칙 5: 주제 전환 시 이전 맥락 무시)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "코너 맥그리거 전적 알려줘"},
                {"role": "ai", "content": "코너 맥그리거는 22승 6패입니다."},
                {"role": "human", "content": "헤비급 챔피언은 누구야?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["헤비급", "챔피언"],
            "must_not_include": ["맥그리거"],
            "description": "완전한 주제 전환 — 맥그리거 맥락 제거, 헤비급 질문 그대로",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "라이트급 랭킹 알려줘"},
                {"role": "ai", "content": "라이트급 랭킹: 1. 마카체프 2. 올리베이라..."},
                {"role": "human", "content": "UFC 역대 최다 KO 기록은?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["KO"],
            "must_not_include": ["라이트급", "마카체프"],
            "description": "체급 → 역대 기록으로 주제 전환, 이전 맥락 제거",
        },
    },
    # =========================================================================
    # D. 부분 주제 전환 (같은 선수, 다른 카테고리)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "존 존스 타격 통계 알려줘"},
                {"role": "ai", "content": "존 존스의 분당 타격 수는 4.29입니다."},
                {"role": "human", "content": "그래플링 통계도 알려줘"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["존 존스", "그래플링"],
            "must_not_include": [],
            "description": "같은 선수 유지, 카테고리만 전환 — 선수 맥락 보존",
        },
    },
    # =========================================================================
    # E. sql_context ID 참조 (규칙 3: 엔티티 id 명시)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "서브미션 Top 5 알려줘"},
                {"role": "ai", "content": "1. charles oliveira (15회)\n2. ..."},
                {"role": "human", "content": "1등 선수의 최근 10경기"},
            ],
            "sql_context": [
                {
                    "query": "SELECT ...",
                    "data": [{"id": 123, "name": "charles oliveira", "submissions": 15}],
                },
            ],
        },
        "expected": {
            "must_include": ["charles oliveira"],
            "must_not_include": [],
            "description": "sql_context에서 선수명과 ID를 참조하여 '1등 선수' 해소",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "라이트급 KO 승리 Top 3"},
                {"role": "ai", "content": "1. dustin poirier 2. justin gaethje 3. ..."},
                {"role": "human", "content": "2등 선수의 최근 5경기 상대는?"},
            ],
            "sql_context": [
                {
                    "query": "SELECT ...",
                    "data": [
                        {"id": 200, "name": "dustin poirier", "ko_wins": 12},
                        {"id": 301, "name": "justin gaethje", "ko_wins": 10},
                    ],
                },
            ],
        },
        "expected": {
            "must_include": ["justin gaethje"],
            "must_not_include": ["dustin poirier"],
            "description": "'2등 선수' → sql_context 순서 기반으로 gaethje 해소",
        },
    },
    # =========================================================================
    # F. 히스토리 없음 → 패스스루 (규칙 4: 독립 질문은 그대로)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "존 존스 전적 알려줘"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["존 존스"],
            "must_not_include": [],
            "description": "히스토리 없음 — 원본 질문 그대로 반환",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "UFC 밴텀급 랭킹 Top 10 알려줘"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["밴텀급", "랭킹"],
            "must_not_include": [],
            "description": "히스토리 없음, 독립 질문 — 그대로 반환",
        },
    },
    # =========================================================================
    # G. 다턴 대화 (3턴 이상 히스토리)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "이슬람 마카체프 전적 알려줘"},
                {"role": "ai", "content": "이슬람 마카체프는 25승 1패입니다."},
                {"role": "human", "content": "KO 승리 몇 번이야?"},
                {"role": "ai", "content": "KO 승리는 4회입니다."},
                {"role": "human", "content": "서브미션은?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["마카체프", "서브미션"],
            "must_not_include": [],
            "description": "3턴 연속 같은 선수 — '서브미션은?' → 마카체프의 서브미션 승리",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "아만다 누네스 전적"},
                {"role": "ai", "content": "아만다 누네스는 21승 5패입니다."},
                {"role": "human", "content": "타이틀 방어 몇 번 했어?"},
                {"role": "ai", "content": "밴텀급 7회, 페더급 2회 방어했습니다."},
                {"role": "human", "content": "마지막 방어전 상대는?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["아만다 누네스"],
            "must_not_include": [],
            "description": "3턴 대화 후 '마지막 방어전 상대' → 누네스의 타이틀 방어 맥락 유지",
        },
    },
    # =========================================================================
    # H. 조건 필터 해소 (체급, 연도 등 조건 맥락)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "2024년 UFC 경기 중 1라운드 KO가 가장 많은 체급은?"},
                {"role": "ai", "content": "라이트급이 12건으로 가장 많습니다."},
                {"role": "human", "content": "2023년은?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["2023", "1라운드", "KO", "체급"],
            "must_not_include": [],
            "description": "연도만 변경 — 나머지 조건(1라운드 KO, 체급별) 유지",
        },
    },
    {
        "input": {
            "messages": [
                {"role": "human", "content": "웰터급 선수 중 테이크다운 성공률 Top 5"},
                {"role": "ai", "content": "1. 카마루 우스만 2. ..."},
                {"role": "human", "content": "미들급은?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["미들급", "테이크다운"],
            "must_not_include": ["웰터급"],
            "description": "체급만 변경 — 테이크다운 성공률 Top 5 조건 유지, 웰터급 제거",
        },
    },
    # =========================================================================
    # I. 히스토리 있지만 독립적인 새 질문 (규칙 4)
    # =========================================================================
    {
        "input": {
            "messages": [
                {"role": "human", "content": "코너 맥그리거 전적 알려줘"},
                {"role": "ai", "content": "22승 6패입니다."},
                {"role": "human", "content": "카마루 우스만의 타이틀 방어 횟수는?"},
            ],
            "sql_context": [],
        },
        "expected": {
            "must_include": ["카마루 우스만", "타이틀"],
            "must_not_include": ["맥그리거"],
            "description": "히스토리 있지만 완전히 다른 선수 질문 — 독립 질문으로 처리",
        },
    },
]


# =============================================================================
# 2. 데이터셋 업로드
# =============================================================================

def get_or_create_dataset():
    """데이터셋이 있으면 읽고, 없으면 새로 생성"""
    client = Client()

    try:
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"기존 데이터셋 사용: '{DATASET_NAME}' (id={dataset.id})")
        return dataset
    except Exception:
        pass

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Conversation Manager 대명사 해소 평가 데이터셋",
    )

    for case in EVAL_CASES:
        client.create_example(
            dataset_id=dataset.id,
            inputs=case["input"],
            outputs=case["expected"],
        )

    print(f"데이터셋 생성 완료: '{DATASET_NAME}' ({len(EVAL_CASES)}개 케이스)")
    return dataset


# =============================================================================
# 3. 평가 대상 함수 (target)
# =============================================================================

def _build_messages(raw_messages: list[dict]) -> list:
    """dict 형태의 메시지를 LangChain 메시지 객체로 변환"""
    result = []
    for msg in raw_messages:
        if msg["role"] == "human":
            result.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "ai":
            result.append(AIMessage(content=msg["content"]))
    return result


async def cm_target(inputs: dict) -> dict:
    """conversation_manager_node를 직접 호출하는 래퍼

    LangSmith evaluate가 데이터셋의 inputs를 이 함수에 전달.
    노드와 동일한 state 구조로 변환하여 호출.
    """
    llm = _get_llm()

    state = {
        "messages": _build_messages(inputs["messages"]),
        "sql_context": inputs.get("sql_context", []),
    }

    result = await conversation_manager_node(state, llm)
    return {"resolved_query": result.get("resolved_query", "")}


# =============================================================================
# 4. 평가자 (Evaluators)
# =============================================================================

def must_include_check(run, example) -> dict:
    """resolved_query에 필수 키워드가 포함되어 있는지 검사"""
    resolved = run.outputs.get("resolved_query", "").lower()
    must_include = example.outputs.get("must_include", [])

    if not must_include:
        return {"key": "must_include", "score": 1.0}

    found = sum(1 for kw in must_include if kw.lower() in resolved)
    score = found / len(must_include)

    missing = [kw for kw in must_include if kw.lower() not in resolved]
    comment = f"missing: {missing}" if missing else "all keywords found"

    return {"key": "must_include", "score": score, "comment": comment}


def must_not_include_check(run, example) -> dict:
    """resolved_query에 불필요한 키워드가 없는지 검사"""
    resolved = run.outputs.get("resolved_query", "").lower()
    must_not_include = example.outputs.get("must_not_include", [])

    if not must_not_include:
        return {"key": "must_not_include", "score": 1.0}

    violations = [kw for kw in must_not_include if kw.lower() in resolved]
    score = 1.0 if not violations else 0.0
    comment = f"violations: {violations}" if violations else "no violations"

    return {"key": "must_not_include", "score": score, "comment": comment}


def is_not_empty(run, example) -> dict:
    """resolved_query가 비어있지 않은지 검사"""
    resolved = run.outputs.get("resolved_query", "")
    score = 1.0 if resolved.strip() else 0.0
    return {"key": "is_not_empty", "score": score}


def is_standalone_query(run, example) -> dict:
    """resolved_query가 독립적으로 이해 가능한 완전한 질문인지 검사

    대명사("그", "그 선수", "이 선수", "걔")가 해소되지 않고 남아있으면 실패
    """
    resolved = run.outputs.get("resolved_query", "").lower()

    unresolved_pronouns = ["그 선수", "이 선수", "그의", "걔", "저 선수"]
    found = [p for p in unresolved_pronouns if p in resolved]

    score = 1.0 if not found else 0.0
    comment = f"unresolved: {found}" if found else "standalone query"

    return {"key": "is_standalone", "score": score, "comment": comment}


RULE_EVALUATORS = [
    must_include_check,
    must_not_include_check,
    is_not_empty,
    is_standalone_query,
]


# =============================================================================
# 4-B. LLM-as-Judge 평가자
# =============================================================================

LLM_JUDGE_PROMPT = """당신은 MMA 대화 시스템의 대명사 해소(coreference resolution) 품질을 평가하는 심사관입니다.

## 평가 대상
사용자의 대화 히스토리와 최신 질문이 주어졌을 때, 시스템이 최신 질문을 독립적으로 이해 가능한 완전한 질문으로 재작성한 결과를 평가합니다.

## 평가 기준 (각 항목 동일 가중치)

1. **대명사 해소 (Coreference Resolution)**
   - 대명사("그 선수", "걔", "둘 중" 등)가 구체적인 이름으로 대체되었는가
   - 생략된 맥락이 복원되었는가 ("승률은?" → "XXX의 승률은?")

2. **독립성 (Standalone)**
   - 대화 히스토리 없이 재작성된 질문만 읽어도 의미가 명확한가
   - 다른 시스템이 이 질문만 받아도 정확히 처리할 수 있는가

3. **정확성 (Accuracy)**
   - 히스토리에 없는 정보를 임의로 추가하지 않았는가 (hallucination)
   - 선수명, 체급 등 고유명사가 정확한가

4. **주제 전환 감지 (Topic Switch)**
   - 사용자가 주제를 바꿨을 때 이전 맥락을 적절히 무시했는가
   - 새로운 주제의 질문을 왜곡 없이 전달했는가

## 입력 정보
- 대화 히스토리: {conversation}
- 최신 질문: {latest_query}
- 재작성 결과: {resolved_query}
- 기대 설명: {description}

## 출력 형식 (JSON만 출력, 다른 텍스트 없이)
{{"score": 0.0~1.0, "reason": "채점 근거를 1~2문장으로"}}"""


async def llm_judge(run, example) -> dict:
    """LLM이 resolved_query의 품질을 0~1점으로 채점"""
    resolved = run.outputs.get("resolved_query", "")
    messages = example.inputs.get("messages", [])
    description = example.outputs.get("description", "")

    # 대화 히스토리 포맷
    conversation_lines = []
    for msg in messages[:-1]:
        role = "사용자" if msg["role"] == "human" else "어시스턴트"
        conversation_lines.append(f"[{role}]: {msg['content']}")
    conversation = "\n".join(conversation_lines) if conversation_lines else "(히스토리 없음)"

    latest_query = messages[-1]["content"] if messages else ""

    judge_input = LLM_JUDGE_PROMPT.format(
        conversation=conversation,
        latest_query=latest_query,
        resolved_query=resolved,
        description=description,
    )

    llm = _get_llm()
    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are a strict evaluator. Output only valid JSON."),
            HumanMessage(content=judge_input),
        ])

        content = response.content.strip()
        # JSON 블록 추출
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        parsed = json.loads(content)
        score = max(0.0, min(1.0, float(parsed["score"])))
        reason = parsed.get("reason", "")

        return {"key": "llm_judge", "score": score, "comment": reason}

    except Exception as e:
        return {"key": "llm_judge", "score": 0.0, "comment": f"Judge error: {e}"}


LLM_EVALUATORS = [llm_judge]


# =============================================================================
# 5. 평가 실행
# =============================================================================

def _get_evaluators() -> list:
    """EVAL_MODE에 따라 평가자 목록 반환"""
    if EVAL_MODE == "rule":
        return RULE_EVALUATORS
    elif EVAL_MODE == "llm_judge":
        return LLM_EVALUATORS
    elif EVAL_MODE == "both":
        return RULE_EVALUATORS + LLM_EVALUATORS
    else:
        raise ValueError(f"Unknown EVAL_MODE: {EVAL_MODE}. Use 'rule', 'llm_judge', or 'both'")


async def run_evaluation():
    """전체 평가 파이프라인 실행"""
    evaluators = _get_evaluators()
    evaluator_names = [e.__name__ for e in evaluators]
    print(f"평가 모드: {EVAL_MODE}")
    print(f"평가자: {evaluator_names}")

    # 데이터셋 생성
    get_or_create_dataset()

    # 비동기 평가 실행
    results = await aevaluate(
        cm_target,
        data=DATASET_NAME,
        evaluators=evaluators,
        experiment_prefix=f"cm-eval-{EVAL_MODE}",
        max_concurrency=2,
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print(f"Evaluation Results (mode={EVAL_MODE})")
    print("=" * 60)
    async for result in results:
        run = result["run"]
        inputs = run.inputs or {}
        messages = inputs.get("messages", [])
        last_msg = messages[-1]["content"] if messages else "(unknown)"
        resolved = (run.outputs or {}).get("resolved_query", "")
        print(f"\n질문: {last_msg}")
        print(f"해소: {resolved}")
        for ev in result["evaluation_results"]["results"]:
            status = "PASS" if ev.score == 1.0 else f"{ev.score:.2f}"
            print(f"  [{status}] {ev.key}: {ev.score:.2f} — {ev.comment or ''}")


if __name__ == "__main__":
    asyncio.run(run_evaluation())
