"""
Conversation Repository 통합 테스트
conversation/repositories.py의 데이터베이스 레이어 함수들에 대한 통합 테스트
실제 테스트 DB를 사용하여 채팅 세션 및 메시지 관리 검증
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from conversation import repositories as conversation_repo
from conversation.models import ChatSessionResponse, ChatMessageResponse, ChatHistoryResponse
from user.models import UserSchema
from user import repositories as user_repo


# =============================================================================
# 헬퍼 함수: 테스트용 사용자 생성
# =============================================================================

async def create_test_user(session: AsyncSession, suffix: str = "") -> object:
    """테스트용 고유 사용자 생성"""
    timestamp = datetime.now().strftime("%H%M%S%f")
    username = f"conv_test_{suffix}_{timestamp}"
    return await user_repo.create_user(
        session,
        UserSchema(
            username=username,
            password_hash="test_hash",
            is_active=True
        )
    )


# =============================================================================
# create_chat_session 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_create_chat_session_with_title(clean_test_session: AsyncSession):
    """제목이 있는 채팅 세션 생성 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "create_title")

    # When: 제목과 함께 세션 생성
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session,
        user_id=test_user.id,
        title="UFC 분석 대화"
    )

    # Then: 세션 생성 성공
    assert chat_session is not None
    assert isinstance(chat_session, ChatSessionResponse)
    assert chat_session.id is not None
    assert chat_session.user_id == test_user.id
    assert chat_session.title == "UFC 분석 대화"
    assert chat_session.created_at is not None


@pytest.mark.asyncio
async def test_create_chat_session_without_title(clean_test_session: AsyncSession):
    """제목 없이 채팅 세션 생성 시 기본 제목 생성 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "create_notitle")

    # When: 제목 없이 세션 생성
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session,
        user_id=test_user.id
    )

    # Then: 기본 제목이 생성됨
    assert chat_session is not None
    assert chat_session.title is not None
    assert "채팅" in chat_session.title  # 기본 제목 포맷 확인


@pytest.mark.asyncio
async def test_create_multiple_chat_sessions(clean_test_session: AsyncSession):
    """동일 사용자가 여러 채팅 세션 생성 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "create_multi")

    # When: 여러 세션 생성
    session1 = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="세션 1"
    )
    session2 = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="세션 2"
    )
    session3 = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="세션 3"
    )

    # Then: 각 세션은 고유한 ID를 가짐
    assert session1.id != session2.id != session3.id
    assert session1.user_id == session2.user_id == session3.user_id == test_user.id


# =============================================================================
# get_user_chat_sessions 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_chat_sessions_returns_list(clean_test_session: AsyncSession):
    """사용자의 채팅 세션 목록 조회 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "get_list")
    await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="첫 번째 대화"
    )
    await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="두 번째 대화"
    )

    # When: 세션 목록 조회
    sessions = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id
    )

    # Then: 생성한 세션들이 포함됨
    assert isinstance(sessions, list)
    assert len(sessions) >= 2
    assert all(isinstance(s, ChatSessionResponse) for s in sessions)


@pytest.mark.asyncio
async def test_get_user_chat_sessions_ordered_by_updated_at(clean_test_session: AsyncSession):
    """채팅 세션 목록이 최신순으로 정렬되는지 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "get_ordered")
    session1 = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="오래된 세션"
    )
    session2 = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="최신 세션"
    )

    # When: 세션 목록 조회
    sessions = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id
    )

    # Then: 최신 세션이 먼저 나옴
    assert len(sessions) >= 2
    assert sessions[0].id == session2.id  # 최신이 먼저


@pytest.mark.asyncio
async def test_get_user_chat_sessions_pagination(clean_test_session: AsyncSession):
    """채팅 세션 목록 페이지네이션 테스트"""
    # Given: 테스트 사용자와 5개 세션 생성
    test_user = await create_test_user(clean_test_session, "get_page")
    for i in range(5):
        await conversation_repo.create_chat_session(
            clean_test_session, user_id=test_user.id, title=f"세션 {i+1}"
        )

    # When: 2개씩 페이지네이션 조회
    page1 = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id, limit=2, offset=0
    )
    page2 = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id, limit=2, offset=2
    )

    # Then: 각 페이지에 2개씩
    assert len(page1) == 2
    assert len(page2) == 2

    # 중복 확인
    page1_ids = {s.id for s in page1}
    page2_ids = {s.id for s in page2}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_get_user_chat_sessions_empty(clean_test_session: AsyncSession):
    """세션이 없는 사용자 조회 테스트"""
    # Given: 세션 없는 새 사용자
    test_user = await create_test_user(clean_test_session, "get_empty")

    # When: 세션이 없는 사용자 조회
    sessions = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id
    )

    # Then: 빈 리스트 반환
    assert sessions == []


@pytest.mark.asyncio
async def test_get_user_chat_sessions_only_own_sessions(clean_test_session: AsyncSession):
    """다른 사용자의 세션은 조회되지 않는지 테스트"""
    # Given: 두 사용자 생성 및 각자 세션 생성
    test_user = await create_test_user(clean_test_session, "get_own1")
    another_user = await create_test_user(clean_test_session, "get_own2")

    await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="내 세션"
    )
    await conversation_repo.create_chat_session(
        clean_test_session, user_id=another_user.id, title="다른 사람 세션"
    )

    # When: 첫 번째 사용자의 세션만 조회
    sessions = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id
    )

    # Then: 자신의 세션만 포함
    assert len(sessions) == 1
    assert sessions[0].title == "내 세션"


# =============================================================================
# get_chat_session_by_id 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_chat_session_by_id_success(clean_test_session: AsyncSession):
    """채팅 세션 ID로 조회 성공 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "byid_success")
    created_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="조회할 세션"
    )

    # When: ID로 조회
    found_session = await conversation_repo.get_chat_session_by_id(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )

    # Then: 동일한 세션 반환
    assert found_session is not None
    assert found_session.id == created_session.id
    assert found_session.title == "조회할 세션"


@pytest.mark.asyncio
async def test_get_chat_session_by_id_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션 ID로 조회 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "byid_notfound")

    # When: 존재하지 않는 ID로 조회
    result = await conversation_repo.get_chat_session_by_id(
        clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_chat_session_by_id_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 조회 시 None 반환 (권한 확인)"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "byid_wrong1")
    another_user = await create_test_user(clean_test_session, "byid_wrong2")
    created_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="비공개 세션"
    )

    # When: another_user가 조회 시도
    result = await conversation_repo.get_chat_session_by_id(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=another_user.id
    )

    # Then: None 반환 (권한 없음)
    assert result is None


# =============================================================================
# delete_chat_session 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_delete_chat_session_success(clean_test_session: AsyncSession):
    """채팅 세션 삭제 성공 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "del_success")
    created_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="삭제할 세션"
    )

    # When: 세션 삭제
    result = await conversation_repo.delete_chat_session(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )

    # Then: 삭제 성공
    assert result is True

    # 삭제 확인
    deleted_session = await conversation_repo.get_chat_session_by_id(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )
    assert deleted_session is None


@pytest.mark.asyncio
async def test_delete_chat_session_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션 삭제 시 False 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "del_notfound")

    # When: 존재하지 않는 세션 삭제 시도
    result = await conversation_repo.delete_chat_session(
        clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: False 반환
    assert result is False


@pytest.mark.asyncio
async def test_delete_chat_session_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 삭제 시도 시 False 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "del_wrong1")
    another_user = await create_test_user(clean_test_session, "del_wrong2")
    created_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="남의 세션"
    )

    # When: another_user가 삭제 시도
    result = await conversation_repo.delete_chat_session(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=another_user.id
    )

    # Then: 삭제 실패
    assert result is False

    # 세션이 여전히 존재하는지 확인
    still_exists = await conversation_repo.get_chat_session_by_id(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )
    assert still_exists is not None


# =============================================================================
# update_chat_session_title 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_update_chat_session_title_success(clean_test_session: AsyncSession):
    """채팅 세션 제목 업데이트 성공 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "upd_success")
    created_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="원래 제목"
    )

    # When: 제목 업데이트
    updated_session = await conversation_repo.update_chat_session_title(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id,
        new_title="새로운 제목"
    )

    # Then: 제목이 변경됨
    assert updated_session is not None
    assert updated_session.title == "새로운 제목"
    assert updated_session.id == created_session.id


@pytest.mark.asyncio
async def test_update_chat_session_title_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션 제목 업데이트 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "upd_notfound")

    # When: 존재하지 않는 세션 업데이트 시도
    result = await conversation_repo.update_chat_session_title(
        clean_test_session,
        conversation_id=99999,
        user_id=test_user.id,
        new_title="새 제목"
    )

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_update_chat_session_title_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 제목 업데이트 시 None 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "upd_wrong1")
    another_user = await create_test_user(clean_test_session, "upd_wrong2")
    created_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="원래 제목"
    )

    # When: another_user가 업데이트 시도
    result = await conversation_repo.update_chat_session_title(
        clean_test_session,
        conversation_id=created_session.id,
        user_id=another_user.id,
        new_title="해킹 시도"
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# add_message_to_session 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_add_message_to_session_user_message(clean_test_session: AsyncSession):
    """사용자 메시지 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "msg_user")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="대화 세션"
    )

    # When: 사용자 메시지 추가
    message = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="UFC 챔피언에 대해 알려줘",
        role="user"
    )

    # Then: 메시지 생성 성공
    assert message is not None
    assert isinstance(message, ChatMessageResponse)
    assert message.content == "UFC 챔피언에 대해 알려줘"
    assert message.role == "user"
    assert message.conversation_id == chat_session.id
    assert message.id is not None  # UUID


@pytest.mark.asyncio
async def test_add_message_to_session_assistant_message(clean_test_session: AsyncSession):
    """어시스턴트 메시지 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "msg_asst")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="대화 세션"
    )

    # When: 어시스턴트 메시지 추가
    message = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="현재 UFC 챔피언은...",
        role="assistant"
    )

    # Then: 메시지 생성 성공
    assert message is not None
    assert message.role == "assistant"
    assert message.content == "현재 UFC 챔피언은..."


@pytest.mark.asyncio
async def test_add_message_with_tool_results(clean_test_session: AsyncSession):
    """tool_results가 포함된 메시지 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "msg_tool")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="대화 세션"
    )
    tool_results = [{"tool": "search", "result": "found 5 champions"}]

    # When: tool_results 포함 메시지 추가
    message = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="검색 결과입니다",
        role="assistant",
        tool_results=tool_results
    )

    # Then: tool_results 포함됨
    assert message is not None
    assert message.tool_results == tool_results


@pytest.mark.asyncio
async def test_add_message_to_nonexistent_session(clean_test_session: AsyncSession):
    """존재하지 않는 세션에 메시지 추가 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "msg_noexist")

    # When: 존재하지 않는 세션에 메시지 추가
    result = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=99999,
        user_id=test_user.id,
        content="테스트 메시지",
        role="user"
    )

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_add_message_to_wrong_user_session(clean_test_session: AsyncSession):
    """다른 사용자의 세션에 메시지 추가 시 None 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "msg_wrong1")
    another_user = await create_test_user(clean_test_session, "msg_wrong2")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="남의 세션"
    )

    # When: another_user가 메시지 추가 시도
    result = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=another_user.id,
        content="침입 시도",
        role="user"
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# get_chat_history 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_chat_history_success(clean_test_session: AsyncSession):
    """채팅 히스토리 조회 성공 테스트"""
    # Given: 테스트 사용자, 세션, 메시지 생성
    test_user = await create_test_user(clean_test_session, "hist_success")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="히스토리 테스트"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="첫 번째 메시지",
        role="user"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="두 번째 메시지",
        role="assistant"
    )

    # When: 히스토리 조회
    history = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id
    )

    # Then: 히스토리 반환
    assert history is not None
    assert isinstance(history, ChatHistoryResponse)
    assert history.conversation_id == chat_session.id
    assert len(history.messages) == 2
    assert history.total_messages == 2
    assert history.has_more is False


@pytest.mark.asyncio
async def test_get_chat_history_ordered_by_time(clean_test_session: AsyncSession):
    """채팅 히스토리가 시간순으로 정렬되는지 테스트"""
    # Given: 테스트 사용자, 세션, 메시지들 생성
    test_user = await create_test_user(clean_test_session, "hist_ordered")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="순서 테스트"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="첫 번째",
        role="user"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="두 번째",
        role="assistant"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        content="세 번째",
        role="user"
    )

    # When: 히스토리 조회
    history = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id
    )

    # Then: 시간순 정렬 확인
    assert len(history.messages) == 3
    assert history.messages[0].content == "첫 번째"
    assert history.messages[1].content == "두 번째"
    assert history.messages[2].content == "세 번째"


@pytest.mark.asyncio
async def test_get_chat_history_pagination(clean_test_session: AsyncSession):
    """채팅 히스토리 페이지네이션 테스트"""
    # Given: 테스트 사용자, 세션, 5개 메시지 생성
    test_user = await create_test_user(clean_test_session, "hist_page")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="페이지네이션 테스트"
    )
    for i in range(5):
        await conversation_repo.add_message_to_session(
            clean_test_session,
            conversation_id=chat_session.id,
            user_id=test_user.id,
            content=f"메시지 {i+1}",
            role="user" if i % 2 == 0 else "assistant"
        )

    # When: 2개씩 조회
    page1 = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        limit=2,
        offset=0
    )

    # Then: 첫 페이지 확인
    assert len(page1.messages) == 2
    assert page1.total_messages == 5
    assert page1.has_more is True

    # 두 번째 페이지
    page2 = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        limit=2,
        offset=2
    )
    assert len(page2.messages) == 2
    assert page2.has_more is True

    # 마지막 페이지
    page3 = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id,
        limit=2,
        offset=4
    )
    assert len(page3.messages) == 1
    assert page3.has_more is False


@pytest.mark.asyncio
async def test_get_chat_history_empty(clean_test_session: AsyncSession):
    """메시지가 없는 세션의 히스토리 조회"""
    # Given: 메시지 없는 세션 생성
    test_user = await create_test_user(clean_test_session, "hist_empty")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="빈 세션"
    )

    # When: 히스토리 조회
    history = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=test_user.id
    )

    # Then: 빈 메시지 리스트
    assert history is not None
    assert history.messages == []
    assert history.total_messages == 0
    assert history.has_more is False


@pytest.mark.asyncio
async def test_get_chat_history_nonexistent_session(clean_test_session: AsyncSession):
    """존재하지 않는 세션의 히스토리 조회 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "hist_noexist")

    # When: 존재하지 않는 세션 히스토리 조회
    result = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_chat_history_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 히스토리 조회 시 None 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "hist_wrong1")
    another_user = await create_test_user(clean_test_session, "hist_wrong2")
    chat_session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="비공개 히스토리"
    )

    # When: another_user가 히스토리 조회 시도
    result = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=chat_session.id,
        user_id=another_user.id
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# get_user_chat_sessions_count 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_chat_sessions_count(clean_test_session: AsyncSession):
    """사용자의 채팅 세션 수 조회 테스트"""
    # Given: 테스트 사용자와 세션 3개 생성
    test_user = await create_test_user(clean_test_session, "cnt_basic")
    for i in range(3):
        await conversation_repo.create_chat_session(
            clean_test_session, user_id=test_user.id, title=f"세션 {i+1}"
        )

    # When: 세션 수 조회
    count = await conversation_repo.get_user_chat_sessions_count(
        clean_test_session, user_id=test_user.id
    )

    # Then: 3개
    assert count == 3


@pytest.mark.asyncio
async def test_get_user_chat_sessions_count_zero(clean_test_session: AsyncSession):
    """세션이 없는 사용자의 세션 수 조회"""
    # Given: 세션 없는 새 사용자
    test_user = await create_test_user(clean_test_session, "cnt_zero")

    # When: 세션 수 조회
    count = await conversation_repo.get_user_chat_sessions_count(
        clean_test_session, user_id=test_user.id
    )

    # Then: 0개
    assert count == 0


@pytest.mark.asyncio
async def test_get_user_chat_sessions_count_only_own(clean_test_session: AsyncSession):
    """다른 사용자의 세션은 카운트되지 않는지 테스트"""
    # Given: 두 사용자 생성, 각자 세션 생성
    test_user = await create_test_user(clean_test_session, "cnt_own1")
    another_user = await create_test_user(clean_test_session, "cnt_own2")

    await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="내 세션"
    )
    await conversation_repo.create_chat_session(
        clean_test_session, user_id=another_user.id, title="남의 세션 1"
    )
    await conversation_repo.create_chat_session(
        clean_test_session, user_id=another_user.id, title="남의 세션 2"
    )

    # When: test_user의 세션 수 조회
    count = await conversation_repo.get_user_chat_sessions_count(
        clean_test_session, user_id=test_user.id
    )

    # Then: 1개만 카운트
    assert count == 1


# =============================================================================
# get_total_conversations_count 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_total_conversations_count(clean_test_session: AsyncSession):
    """전체 채팅 세션 수 조회 테스트 (관리자용)"""
    # Given: 두 사용자 생성, 각자 세션 생성
    test_user = await create_test_user(clean_test_session, "total1")
    another_user = await create_test_user(clean_test_session, "total2")

    await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="유저1 세션"
    )
    await conversation_repo.create_chat_session(
        clean_test_session, user_id=another_user.id, title="유저2 세션"
    )

    # When: 전체 세션 수 조회
    count = await conversation_repo.get_total_conversations_count(clean_test_session)

    # Then: 모든 세션 카운트
    assert count >= 2


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_full_conversation_lifecycle(clean_test_session: AsyncSession):
    """전체 대화 생명주기 통합 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "lifecycle")

    # 1. 세션 생성
    session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="통합 테스트 대화"
    )
    assert session is not None

    # 2. 메시지 추가 (대화 진행)
    msg1 = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        content="안녕하세요",
        role="user"
    )
    assert msg1 is not None

    msg2 = await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        content="안녕하세요! 무엇을 도와드릴까요?",
        role="assistant"
    )
    assert msg2 is not None

    # 3. 히스토리 조회
    history = await conversation_repo.get_chat_history(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )
    assert history.total_messages == 2
    assert history.messages[0].role == "user"
    assert history.messages[1].role == "assistant"

    # 4. 제목 업데이트
    updated_session = await conversation_repo.update_chat_session_title(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        new_title="인사 대화"
    )
    assert updated_session.title == "인사 대화"

    # 5. 세션 목록에서 확인
    sessions = await conversation_repo.get_user_chat_sessions(
        clean_test_session, user_id=test_user.id
    )
    assert any(s.id == session.id for s in sessions)

    # 6. 세션 삭제
    deleted = await conversation_repo.delete_chat_session(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )
    assert deleted is True

    # 7. 삭제 확인
    deleted_session = await conversation_repo.get_chat_session_by_id(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )
    assert deleted_session is None


@pytest.mark.asyncio
async def test_cascade_delete_messages_on_session_delete(clean_test_session: AsyncSession):
    """세션 삭제 시 메시지도 함께 삭제되는지 테스트 (CASCADE)"""
    # Given: 테스트 사용자, 세션, 메시지 생성
    test_user = await create_test_user(clean_test_session, "cascade")
    session = await conversation_repo.create_chat_session(
        clean_test_session, user_id=test_user.id, title="삭제 테스트"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        content="삭제될 메시지 1",
        role="user"
    )
    await conversation_repo.add_message_to_session(
        clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        content="삭제될 메시지 2",
        role="assistant"
    )

    # 메시지 존재 확인
    history_before = await conversation_repo.get_chat_history(
        clean_test_session, conversation_id=session.id, user_id=test_user.id
    )
    assert history_before.total_messages == 2

    # When: 세션 삭제
    await conversation_repo.delete_chat_session(
        clean_test_session, conversation_id=session.id, user_id=test_user.id
    )

    # Then: 세션과 메시지 모두 삭제됨 (CASCADE)
    history_after = await conversation_repo.get_chat_history(
        clean_test_session, conversation_id=session.id, user_id=test_user.id
    )
    assert history_after is None  # 세션 자체가 없으므로 None


if __name__ == "__main__":
    print("Conversation Repository 통합 테스트")
    print("실제 테스트 DB를 사용한 채팅 세션 및 메시지 관리 검증")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/conversation/test_conversation_repositories.py -v")
