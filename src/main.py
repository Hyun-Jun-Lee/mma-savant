from typing import cast
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일 로드
load_dotenv(dotenv_path="../.env")

# 환경변수 확인
print("=== 환경변수 확인 ===")
print(f"OAUTH_GOOGLE_CLIENT_ID: {os.getenv('OAUTH_GOOGLE_CLIENT_ID')}")
print(f"OAUTH_GOOGLE_CLIENT_SECRET: {os.getenv('OAUTH_GOOGLE_CLIENT_SECRET')}")
print(f"CHAINLIT_AUTH_SECRET: {os.getenv('CHAINLIT_AUTH_SECRET')}")
print("====================")

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough

import chainlit as cl

print("=== Chainlit 모듈 로드 완료 ===")

# Google OAuth 인증 설정 (선택적 로그인)
@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict,
    default_app_user: cl.User,
) -> cl.User | None:
    """
    Google OAuth 콜백 함수
    사용자가 Google로 로그인하면 자동으로 호출됩니다.
    """
    print(f"=== OAuth 콜백 호출됨 ===")
    print(f"provider_id: {provider_id}")
    print(f"raw_user_data: {raw_user_data}")
    
    if provider_id == "google":
        print("Google OAuth 처리 중...")
        
        # Google 사용자 정보 추출
        email = raw_user_data.get("email", "")
        name = raw_user_data.get("name", "")
        picture = raw_user_data.get("picture", "")
        
        # 사용자 객체 생성 (추가 메타데이터 포함)
        user = cl.User(
            identifier=email,  # 이메일을 고유 식별자로 사용
            metadata={
                "email": email,
                "name": name,
                "picture": picture,
                "provider": "google",
                "role": "user",
                "registration_date": datetime.now().isoformat()
            }
        )
        print(f"생성된 사용자: {user}")
        return user
    
    print("Google이 아닌 제공자, None 반환")
    return None

@cl.on_chat_start
async def on_chat_start():
    print("=== on_chat_start 호출됨 ===")
    # 세션 ID 및 사용자 컨텍스트 초기화
    session_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()
    
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("start_time", start_time)
    cl.user_session.set("message_count", 0)
    
    # 사용자 정보 가져오기
    user = cl.user_session.get("user")
    print(f"사용자 정보: {user}")
    
    welcome_msg = f"MMA Savant 챗봇에 오신 것을 환영합니다! 🥊"
    
    if user and hasattr(user, 'metadata'):
        # Google OAuth 사용자의 경우 이름 표시
        display_name = user.metadata.get("name", user.identifier) if user.metadata else user.identifier
        welcome_msg += f"\n안녕하세요, {display_name}님!"
        if user.metadata and user.metadata.get('email'):
            welcome_msg += f"\n로그인: Google 계정 ({user.metadata.get('email')})"
    elif user:
        welcome_msg += f"\n안녕하세요, {user.identifier}님!"
    else:
        welcome_msg += "\n게스트 모드로 접속하셨습니다."
    
    welcome_msg += f"\n세션 ID: {session_id[:8]}..."
    await cl.Message(welcome_msg).send()
    
    model = ChatOpenAI(streaming=True, api_key=os.getenv("LLM_API_KEY"))
    # 프롬프트 템플릿 (대화 기록 포함)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're a very knowledgeable MMA (Mixed Martial Arts) expert who provides accurate and detailed answers about fighters, techniques, events, and MMA history. 이전 대화를 참조하여 답변하세요. Always respond in Korean unless specifically asked otherwise."),
        ("human", "{chat_history}\n\n현재 질문: {question}"),
    ])
    
    # 메모리 초기화
    memory = ConversationBufferMemory(return_messages=True)
    cl.user_session.set("memory", memory)
    
    # Runnable 체인: 메모리 + 프롬프트 + 모델 + 파서
    runnable = (
        RunnablePassthrough.assign(
            chat_history=lambda x: memory.load_memory_variables({})["history"]
        )
        | prompt
        | model
        | StrOutputParser()
    )
    cl.user_session.set("runnable", runnable)

@cl.on_chat_resume
async def on_chat_resume():
    memory = cl.user_session.get("memory")
    runnable = cl.user_session.get("runnable")
    
    if memory is None or runnable is None:
        await cl.Message("세션을 복원하는 중입니다...").send()
        await on_chat_start()
    else:
        await cl.Message("이전 대화를 이어서 진행합니다.").send()

@cl.on_message
async def on_message(message: cl.Message):
    try:
        # 메시지 카운트 증가
        message_count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", message_count)
        
        runnable = cast(Runnable, cl.user_session.get("runnable"))
        memory = cast(ConversationBufferMemory, cl.user_session.get("memory"))
        
        if runnable is None or memory is None:
            await cl.Message("세션이 초기화되지 않았습니다. 잠시 후 다시 시도해주세요.").send()
            await on_chat_start()
            return
        
        # 메시지 처리
        msg = cl.Message(content="")
        
        async for chunk in runnable.astream(
            {"question": message.content},
            config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
        ):
            await msg.stream_token(chunk)
        
        # 메모리 업데이트
        memory.save_context(
            {"input": message.content},
            {"output": msg.content}
        )
        
        await msg.send()
        
    except Exception as e:
        await cl.Message(f"죄송합니다. 오류가 발생했습니다: {str(e)}").send()