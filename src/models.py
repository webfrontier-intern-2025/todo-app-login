# src/models.py
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Table,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker # sessionmakerを追加

# データベースの接続設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# ↓↓↓ SessionLocalの定義を追加 ↓↓↓
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 中間テーブルの定義
todo_tag_association = Table(
    "設定",
    Base.metadata,
    Column("todo_id", Integer, ForeignKey("Todo.id")),
    Column("tag_id", Integer, ForeignKey("Tag.id")),
)

class Todo(Base):
    __tablename__ = "Todo"
    id = Column("id", Integer, primary_key=True, index=True)
    content = Column("内容", String, index=True)
    due_date = Column("期限", String)
    is_completed = Column("完了/未完了", Boolean, default=False)
    created_at = Column("作成日時", DateTime, server_default=func.now())
    
    tags = relationship("Tag", secondary=todo_tag_association, back_populates="todos")

class Tag(Base):
    __tablename__ = "Tag"
    id = Column("id", Integer, primary_key=True, index=True)
    description = Column("説明", String, index=True)

    todos = relationship("Todo", secondary=todo_tag_association, back_populates="tags")

class User(Base):
    """
    ユーザーモデル
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)