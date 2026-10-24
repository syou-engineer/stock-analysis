import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DBファイルの保存先を作成
os.makedirs("backend/data", exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/data/stock.db"

# SQLite接続エンジン
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()