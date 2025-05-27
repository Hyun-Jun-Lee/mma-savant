from typing import cast

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough

import chainlit as cl


@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI(streaming=True, api_key=os.getenv("LLM_API_KEY"))
# 프롬프트 템플릿 (대화 기록 포함)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're a very knowledgeable historian who provides accurate and eloquent answers to historical questions. 이전 대화를 참조하여 답변하세요."),
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

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cast(Runnable, cl.user_session.get("runnable"))
    memory = cast(ConversationBufferMemory, cl.user_session.get("memory"))
    
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