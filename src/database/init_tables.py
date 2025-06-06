import asyncio
from sqlalchemy import text

from user.models import UserModel
from conversation.models import ConversationModel
from database.connection.postgres_conn import async_engine

async def init_tables():
    try:
        async with async_engine.connect() as conn:
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