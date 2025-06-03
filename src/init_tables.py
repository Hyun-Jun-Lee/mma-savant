import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.schema import MetaData

from models.user_model import UserModel
from models.conversation_model import ConversationModel
from database.connection.postgres_conn import async_engine

async def init_tables():
    try:
        # 비동기 검사기를 사용하여 테이블 존재 여부 확인
        async with async_engine.connect() as conn:
            # 메타데이터에서 테이블 정보 가져오기
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user'
                );
            """))
            user_exists = result.scalar()
            
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'conversation'
                );
            """))
            conversation_exists = result.scalar()
        
        if user_exists and conversation_exists:
            print("Tables 'user' and 'conversation' already exist, skipping initialization")
            return

        # 테이블 생성
        async with async_engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: UserModel.__table__.create(sync_conn, checkfirst=True))
            await conn.run_sync(lambda sync_conn: ConversationModel.__table__.create(sync_conn, checkfirst=True))
        print("Tables created successfully")

        # GIN 인덱스 추가
        async with async_engine.begin() as conn:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS conversation_messages_gin 
                ON conversation USING GIN (messages);
            """))
        print("GIN index created successfully")

    except Exception as e:
        print(f"Error initializing tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_tables())