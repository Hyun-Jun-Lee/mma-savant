"""
Conversation Service 통합 테스트
conversation/services.py의 서비스 레이어 함수들에 대한 통합 테스트
실제 테스트 DB를 사용하여 채팅 세션 및 메시지 관리 비즈니스 로직 검증
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from conversation import services as conv_svc
from conversation.models import (
    ChatSessionCreate, ChatSessionResponse, ChatSessionListResponse,
    ChatMessageCreate, ChatMessageResponse, ChatHistoryResponse
)
from user.models import UserSchema
from user import repositories as user_repo


# =============================================================================
# 헬퍼 함수: 테스트용 사용자 생성
# =============================================================================

async def create_test_user(session: AsyncSession, suffix: str = "") -> object:
    """테스트용 고유 사용자 생성"""
    timestamp = datetime.now().strftime("%H%M%S%f")
    username = f"svc_test_{suffix}_{timestamp}"
    return await user_repo.create_user(
        session,
        UserSchema(
            username=username,
            password_hash="test_hash",
            is_active=True
        )
    )


# =============================================================================
# create_new_session 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_create_new_session_with_title(clean_test_session: AsyncSession):
    """제목이 있는 세션 생성 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "create_title")
    session_data = ChatSessionCreate(title="UFC 분석 대화")

    # When: 제목과 함께 세션 생성
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # Then: 세션 생성 성공
    assert session is not None
    assert isinstance(session, ChatSessionResponse)
    assert session.user_id == test_user.id
    assert session.title == "UFC 분석 대화"
    assert session.id is not None


@pytest.mark.asyncio
async def test_create_new_session_without_title(clean_test_session: AsyncSession):
    """제목 없이 세션 생성 시 기본 제목 생성 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "create_notitle")
    session_data = ChatSessionCreate(title=None)

    # When: 제목 없이 세션 생성
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # Then: 기본 제목이 생성됨
    assert session is not None
    assert session.title is not None
    assert "채팅" in session.title


@pytest.mark.asyncio
async def test_create_new_session_returns_correct_structure(clean_test_session: AsyncSession):
    """세션 생성 시 ChatSessionResponse 구조 검증"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "create_struct")
    session_data = ChatSessionCreate(title="구조 테스트")

    # When: 세션 생성
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # Then: ChatSessionResponse 구조 검증
    assert hasattr(session, 'id')
    assert hasattr(session, 'user_id')
    assert hasattr(session, 'title')
    assert hasattr(session, 'last_message_at')
    assert hasattr(session, 'created_at')
    assert hasattr(session, 'updated_at')


# =============================================================================
# get_user_sessions 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_user_sessions_with_multiple_sessions(clean_test_session: AsyncSession):
    """여러 세션을 가진 사용자의 세션 목록 조회 테스트"""
    # Given: 테스트 사용자와 3개 세션 생성
    test_user = await create_test_user(clean_test_session, "get_multi")
    for i in range(3):
        session_data = ChatSessionCreate(title=f"세션 {i+1}")
        await conv_svc.create_new_session(
            db=clean_test_session,
            user_id=test_user.id,
            session_data=session_data
        )

    # When: 세션 목록 조회
    result = await conv_svc.get_user_sessions(
        db=clean_test_session,
        user_id=test_user.id
    )

    # Then: 3개 세션 반환 및 total_sessions 확인
    assert isinstance(result, ChatSessionListResponse)
    assert len(result.sessions) == 3
    assert result.total_sessions == 3
    assert all(isinstance(s, ChatSessionResponse) for s in result.sessions)


@pytest.mark.asyncio
async def test_get_user_sessions_pagination(clean_test_session: AsyncSession):
    """세션 목록 페이지네이션 테스트"""
    # Given: 테스트 사용자와 5개 세션 생성
    test_user = await create_test_user(clean_test_session, "get_page")
    for i in range(5):
        session_data = ChatSessionCreate(title=f"세션 {i+1}")
        await conv_svc.create_new_session(
            db=clean_test_session,
            user_id=test_user.id,
            session_data=session_data
        )

    # When: 2개씩 페이지네이션 조회
    page1 = await conv_svc.get_user_sessions(
        db=clean_test_session,
        user_id=test_user.id,
        limit=2,
        offset=0
    )
    page2 = await conv_svc.get_user_sessions(
        db=clean_test_session,
        user_id=test_user.id,
        limit=2,
        offset=2
    )

    # Then: 각 페이지에 2개씩, total은 5
    assert len(page1.sessions) == 2
    assert page1.total_sessions == 5
    assert len(page2.sessions) == 2
    assert page2.total_sessions == 5

    # 중복 확인
    page1_ids = {s.id for s in page1.sessions}
    page2_ids = {s.id for s in page2.sessions}
    assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
async def test_get_user_sessions_returns_list_response_structure(clean_test_session: AsyncSession):
    """get_user_sessions가 ChatSessionListResponse 구조로 반환하는지 검증"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "get_struct")
    session_data = ChatSessionCreate(title="구조 테스트")
    await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 세션 목록 조회
    result = await conv_svc.get_user_sessions(
        db=clean_test_session,
        user_id=test_user.id
    )

    # Then: ChatSessionListResponse 구조 검증
    assert isinstance(result, ChatSessionListResponse)
    assert hasattr(result, 'sessions')
    assert hasattr(result, 'total_sessions')
    assert isinstance(result.sessions, list)
    assert isinstance(result.total_sessions, int)


@pytest.mark.asyncio
async def test_get_user_sessions_empty_list(clean_test_session: AsyncSession):
    """세션이 없는 사용자 조회 시 빈 목록 반환 테스트"""
    # Given: 세션 없는 새 사용자
    test_user = await create_test_user(clean_test_session, "get_empty")

    # When: 세션 목록 조회
    result = await conv_svc.get_user_sessions(
        db=clean_test_session,
        user_id=test_user.id
    )

    # Then: 빈 리스트 및 total_sessions = 0
    assert isinstance(result, ChatSessionListResponse)
    assert result.sessions == []
    assert result.total_sessions == 0


# =============================================================================
# get_session_by_id 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_session_by_id_success(clean_test_session: AsyncSession):
    """ID로 세션 조회 성공 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "byid_success")
    session_data = ChatSessionCreate(title="조회할 세션")
    created_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: ID로 조회
    found_session = await conv_svc.get_session_by_id(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )

    # Then: 동일한 세션 반환
    assert found_session is not None
    assert found_session.id == created_session.id
    assert found_session.title == "조회할 세션"


@pytest.mark.asyncio
async def test_get_session_by_id_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션 ID로 조회 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "byid_notfound")

    # When: 존재하지 않는 ID로 조회
    result = await conv_svc.get_session_by_id(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_get_session_by_id_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 조회 시 None 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "byid_wrong1")
    another_user = await create_test_user(clean_test_session, "byid_wrong2")
    session_data = ChatSessionCreate(title="비공개 세션")
    created_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: another_user가 조회 시도
    result = await conv_svc.get_session_by_id(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=another_user.id
    )

    # Then: None 반환 (권한 없음)
    assert result is None


# =============================================================================
# delete_session 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_delete_session_success(clean_test_session: AsyncSession):
    """세션 삭제 성공 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "del_success")
    session_data = ChatSessionCreate(title="삭제할 세션")
    created_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 세션 삭제
    result = await conv_svc.delete_session(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )

    # Then: 삭제 성공 (True 반환)
    assert result is True

    # 삭제 확인
    deleted_session = await conv_svc.get_session_by_id(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )
    assert deleted_session is None


@pytest.mark.asyncio
async def test_delete_session_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션 삭제 시 False 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "del_notfound")

    # When: 존재하지 않는 세션 삭제 시도
    result = await conv_svc.delete_session(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: False 반환
    assert result is False


@pytest.mark.asyncio
async def test_delete_session_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 삭제 시도 시 False 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "del_wrong1")
    another_user = await create_test_user(clean_test_session, "del_wrong2")
    session_data = ChatSessionCreate(title="남의 세션")
    created_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: another_user가 삭제 시도
    result = await conv_svc.delete_session(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=another_user.id
    )

    # Then: 삭제 실패 (False 반환)
    assert result is False

    # 세션이 여전히 존재하는지 확인
    still_exists = await conv_svc.get_session_by_id(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id
    )
    assert still_exists is not None


# =============================================================================
# update_session_title 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_update_session_title_success(clean_test_session: AsyncSession):
    """세션 제목 업데이트 성공 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "upd_success")
    session_data = ChatSessionCreate(title="원래 제목")
    created_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 제목 업데이트
    updated_session = await conv_svc.update_session_title(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=test_user.id,
        new_title="새로운 제목"
    )

    # Then: 제목이 변경됨
    assert updated_session is not None
    assert updated_session.title == "새로운 제목"
    assert updated_session.id == created_session.id


@pytest.mark.asyncio
async def test_update_session_title_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션 제목 업데이트 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "upd_notfound")

    # When: 존재하지 않는 세션 업데이트 시도
    result = await conv_svc.update_session_title(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id,
        new_title="새 제목"
    )

    # Then: None 반환
    assert result is None


@pytest.mark.asyncio
async def test_update_session_title_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 제목 업데이트 시 None 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "upd_wrong1")
    another_user = await create_test_user(clean_test_session, "upd_wrong2")
    session_data = ChatSessionCreate(title="원래 제목")
    created_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: another_user가 업데이트 시도
    result = await conv_svc.update_session_title(
        db=clean_test_session,
        conversation_id=created_session.id,
        user_id=another_user.id,
        new_title="해킹 시도"
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# get_session_history 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_session_history_with_messages(clean_test_session: AsyncSession):
    """메시지가 있는 세션의 히스토리 조회 테스트"""
    # Given: 테스트 사용자, 세션, 메시지 생성
    test_user = await create_test_user(clean_test_session, "hist_with")
    session_data = ChatSessionCreate(title="히스토리 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # 메시지 추가
    msg_data1 = ChatMessageCreate(
        content="첫 번째 메시지",
        role="user",
        conversation_id=session.id
    )
    msg_data2 = ChatMessageCreate(
        content="두 번째 메시지",
        role="assistant",
        conversation_id=session.id
    )
    await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        message_data=msg_data1
    )
    await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        message_data=msg_data2
    )

    # When: 히스토리 조회
    history = await conv_svc.get_session_history(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )

    # Then: 히스토리 반환
    assert history is not None
    assert isinstance(history, ChatHistoryResponse)
    assert history.conversation_id == session.id
    assert len(history.messages) == 2
    assert history.total_messages == 2


@pytest.mark.asyncio
async def test_get_session_history_pagination(clean_test_session: AsyncSession):
    """히스토리 페이지네이션 테스트"""
    # Given: 테스트 사용자, 세션, 5개 메시지 생성
    test_user = await create_test_user(clean_test_session, "hist_page")
    session_data = ChatSessionCreate(title="페이지네이션 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    for i in range(5):
        msg_data = ChatMessageCreate(
            content=f"메시지 {i+1}",
            role="user" if i % 2 == 0 else "assistant",
            conversation_id=session.id
        )
        await conv_svc.add_message(
            db=clean_test_session,
            conversation_id=session.id,
            user_id=test_user.id,
            message_data=msg_data
        )

    # When: 2개씩 조회
    page1 = await conv_svc.get_session_history(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        limit=2,
        offset=0
    )

    # Then: 첫 페이지 확인
    assert len(page1.messages) == 2
    assert page1.total_messages == 5
    assert page1.has_more is True


@pytest.mark.asyncio
async def test_get_session_history_empty(clean_test_session: AsyncSession):
    """메시지가 없는 세션의 히스토리 조회"""
    # Given: 메시지 없는 세션 생성
    test_user = await create_test_user(clean_test_session, "hist_empty")
    session_data = ChatSessionCreate(title="빈 세션")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 히스토리 조회
    history = await conv_svc.get_session_history(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )

    # Then: 빈 메시지 리스트
    assert history is not None
    assert history.messages == []
    assert history.total_messages == 0
    assert history.has_more is False


@pytest.mark.asyncio
async def test_get_session_history_not_found(clean_test_session: AsyncSession):
    """존재하지 않는 세션의 히스토리 조회 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "hist_notfound")

    # When: 존재하지 않는 세션 히스토리 조회
    result = await conv_svc.get_session_history(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# add_message 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_add_message_user_message(clean_test_session: AsyncSession):
    """사용자 메시지 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "msg_user")
    session_data = ChatSessionCreate(title="메시지 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 사용자 메시지 추가
    msg_data = ChatMessageCreate(
        content="UFC 챔피언에 대해 알려줘",
        role="user",
        conversation_id=session.id
    )
    message = await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        message_data=msg_data
    )

    # Then: 메시지 생성 성공
    assert message is not None
    assert isinstance(message, ChatMessageResponse)
    assert message.content == "UFC 챔피언에 대해 알려줘"
    assert message.role == "user"
    assert message.conversation_id == session.id


@pytest.mark.asyncio
async def test_add_message_assistant_message(clean_test_session: AsyncSession):
    """어시스턴트 메시지 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "msg_asst")
    session_data = ChatSessionCreate(title="메시지 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 어시스턴트 메시지 추가
    msg_data = ChatMessageCreate(
        content="현재 UFC 챔피언은...",
        role="assistant",
        conversation_id=session.id
    )
    message = await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        message_data=msg_data
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
    session_data = ChatSessionCreate(title="tool 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )
    tool_results = [{"tool": "search", "result": "found 5 champions"}]

    # When: tool_results 포함 메시지 추가
    msg_data = ChatMessageCreate(
        content="검색 결과입니다",
        role="assistant",
        conversation_id=session.id,
        tool_results=tool_results
    )
    message = await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        message_data=msg_data
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
    msg_data = ChatMessageCreate(
        content="테스트 메시지",
        role="user",
        conversation_id=99999
    )
    result = await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id,
        message_data=msg_data
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# validate_session_access 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_validate_session_access_success(clean_test_session: AsyncSession):
    """사용자가 자신의 세션에 접근 권한이 있는지 검증"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "val_success")
    session_data = ChatSessionCreate(title="접근 권한 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 접근 권한 검증
    has_access = await conv_svc.validate_session_access(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )

    # Then: True 반환 (접근 권한 있음)
    assert has_access is True


@pytest.mark.asyncio
async def test_validate_session_access_wrong_user(clean_test_session: AsyncSession):
    """다른 사용자의 세션 접근 권한 검증 시 False 반환"""
    # Given: 두 사용자 생성, test_user의 세션
    test_user = await create_test_user(clean_test_session, "val_wrong1")
    another_user = await create_test_user(clean_test_session, "val_wrong2")
    session_data = ChatSessionCreate(title="비공개 세션")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: another_user가 접근 권한 검증
    has_access = await conv_svc.validate_session_access(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=another_user.id
    )

    # Then: False 반환 (접근 권한 없음)
    assert has_access is False


@pytest.mark.asyncio
async def test_validate_session_access_nonexistent_session(clean_test_session: AsyncSession):
    """존재하지 않는 세션 접근 권한 검증 시 False 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "val_noexist")

    # When: 존재하지 않는 세션 접근 권한 검증
    has_access = await conv_svc.validate_session_access(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id
    )

    # Then: False 반환
    assert has_access is False


# =============================================================================
# get_or_create_session 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_get_or_create_session_existing(clean_test_session: AsyncSession):
    """conversation_id가 제공되고 세션이 존재하면 기존 세션 반환"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "getorcreate_exist")
    session_data = ChatSessionCreate(title="기존 세션")
    existing_session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: conversation_id로 조회
    session = await conv_svc.get_or_create_session(
        db=clean_test_session,
        user_id=test_user.id,
        conversation_id=existing_session.id
    )

    # Then: 기존 세션 반환
    assert session is not None
    assert session.id == existing_session.id
    assert session.title == "기존 세션"


@pytest.mark.asyncio
async def test_get_or_create_session_create_when_none(clean_test_session: AsyncSession):
    """conversation_id가 None이면 새 세션 생성"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "getorcreate_none")

    # When: conversation_id=None으로 호출
    session = await conv_svc.get_or_create_session(
        db=clean_test_session,
        user_id=test_user.id,
        conversation_id=None,
        content="새 대화 시작"
    )

    # Then: 새 세션 생성
    assert session is not None
    assert session.id is not None
    assert session.title == "새 대화 시작"


@pytest.mark.asyncio
async def test_get_or_create_session_create_when_not_exists(clean_test_session: AsyncSession):
    """conversation_id가 제공되었지만 세션이 존재하지 않으면 새 세션 생성"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "getorcreate_notexist")

    # When: 존재하지 않는 conversation_id로 호출
    session = await conv_svc.get_or_create_session(
        db=clean_test_session,
        user_id=test_user.id,
        conversation_id=99999,
        content="존재하지 않아서 새로 생성"
    )

    # Then: 새 세션 생성
    assert session is not None
    assert session.id != 99999
    assert session.title == "존재하지 않아서 새로 생성"


@pytest.mark.asyncio
async def test_get_or_create_session_title_from_content(clean_test_session: AsyncSession):
    """content 파라미터가 제목으로 설정되는지 검증"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "getorcreate_title")

    # When: content와 함께 새 세션 생성
    session = await conv_svc.get_or_create_session(
        db=clean_test_session,
        user_id=test_user.id,
        conversation_id=None,
        content="UFC 파이터 분석"
    )

    # Then: content가 title로 설정됨
    assert session.title == "UFC 파이터 분석"


# =============================================================================
# add_assistant_response 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_add_assistant_response_without_tool_results(clean_test_session: AsyncSession):
    """tool_results 없이 어시스턴트 응답 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "asst_notool")
    session_data = ChatSessionCreate(title="어시스턴트 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )

    # When: 어시스턴트 응답 추가
    message = await conv_svc.add_assistant_response(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        response_content="어시스턴트 응답입니다"
    )

    # Then: 어시스턴트 메시지 생성 성공
    assert message is not None
    assert message.role == "assistant"
    assert message.content == "어시스턴트 응답입니다"
    assert message.tool_results is None


@pytest.mark.asyncio
async def test_add_assistant_response_with_tool_results(clean_test_session: AsyncSession):
    """tool_results와 함께 어시스턴트 응답 추가 테스트"""
    # Given: 테스트 사용자와 세션 생성
    test_user = await create_test_user(clean_test_session, "asst_tool")
    session_data = ChatSessionCreate(title="tool 테스트")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )
    tool_results = [
        {"tool": "database_query", "result": "3 fighters found"},
        {"tool": "analytics", "result": "win rate: 75%"}
    ]

    # When: tool_results와 함께 어시스턴트 응답 추가
    message = await conv_svc.add_assistant_response(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        response_content="분석 결과입니다",
        tool_results=tool_results
    )

    # Then: tool_results 포함된 메시지 생성
    assert message is not None
    assert message.role == "assistant"
    assert message.tool_results == tool_results


@pytest.mark.asyncio
async def test_add_assistant_response_to_nonexistent_session(clean_test_session: AsyncSession):
    """존재하지 않는 세션에 어시스턴트 응답 추가 시 None 반환"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "asst_noexist")

    # When: 존재하지 않는 세션에 응답 추가
    result = await conv_svc.add_assistant_response(
        db=clean_test_session,
        conversation_id=99999,
        user_id=test_user.id,
        response_content="테스트 응답"
    )

    # Then: None 반환
    assert result is None


# =============================================================================
# 통합 시나리오 테스트
# =============================================================================

@pytest.mark.asyncio
async def test_full_conversation_workflow(clean_test_session: AsyncSession):
    """전체 대화 워크플로우 통합 테스트"""
    # Given: 테스트 사용자 생성
    test_user = await create_test_user(clean_test_session, "workflow")

    # 1. 세션 생성
    session_data = ChatSessionCreate(title="통합 테스트 대화")
    session = await conv_svc.create_new_session(
        db=clean_test_session,
        user_id=test_user.id,
        session_data=session_data
    )
    assert session is not None

    # 2. 사용자 메시지 추가
    user_msg_data = ChatMessageCreate(
        content="안녕하세요",
        role="user",
        conversation_id=session.id
    )
    user_msg = await conv_svc.add_message(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        message_data=user_msg_data
    )
    assert user_msg is not None

    # 3. 어시스턴트 응답 추가
    asst_msg = await conv_svc.add_assistant_response(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id,
        response_content="안녕하세요! 무엇을 도와드릴까요?"
    )
    assert asst_msg is not None

    # 4. 히스토리 조회
    history = await conv_svc.get_session_history(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )
    assert history.total_messages == 2
    assert history.messages[0].role == "user"
    assert history.messages[1].role == "assistant"

    # 5. 세션 삭제
    deleted = await conv_svc.delete_session(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )
    assert deleted is True

    # 6. 삭제 확인
    deleted_session = await conv_svc.get_session_by_id(
        db=clean_test_session,
        conversation_id=session.id,
        user_id=test_user.id
    )
    assert deleted_session is None


if __name__ == "__main__":
    print("Conversation Service 통합 테스트")
    print("실제 테스트 DB를 사용한 채팅 세션 및 메시지 관리 서비스 로직 검증")
    print("\n테스트 실행:")
    print("uv run pytest src/tests/conversation/test_conversation_services.py -v")
