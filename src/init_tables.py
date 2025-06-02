from sqlalchemy import text, inspect
from sqlalchemy.schema import MetaData

from models.user_model import UserModel
from models.conversation_model import ConversationModel
from database.connection.postgres_conn import engine

def init_tables():
    try:
        inspector = inspect(engine)
        tables_exist = all(
            inspector.has_table(table.__tablename__)
            for table in [UserModel, ConversationModel]
        )
        
        if tables_exist:
            print("Tables 'user' and 'conversation' already exist, skipping initialization")
            return

        # 테이블 생성
        UserModel.__table__.create(engine, checkfirst=True)
        ConversationModel.__table__.create(engine, checkfirst=True)
        print("Tables created successfully")

        # GIN 인덱스 추가
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS conversation_messages_gin 
                ON conversation USING GIN (messages);
            """))
            conn.commit()
        print("GIN index created successfully")

    except Exception as e:
        print(f"Error initializing tables: {e}")
        raise

if __name__ == "__main__":
    init_tables()