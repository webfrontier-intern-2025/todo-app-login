# models.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# データベースの接続設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 中間テーブルの定義 (TodoとTagの多対多関係)
todo_tag_association = Table('設定', Base.metadata, # 日本語テーブル名'設定' [cite: 132]
    Column('id', Integer, primary_key=True, index=True),
    Column('todo_id', Integer, ForeignKey('Todo.Todo番号')), # FK Todo番号 [cite: 134]
    Column('tag_id', Integer, ForeignKey('Tag.Tag番号')) # FK Tag番号 [cite: 135]
)

class Todo(Base):
    __tablename__ = 'Todo' # テーブル名 'Todo' [cite: 124]
    todo_id = Column('Todo番号', Integer, primary_key=True, index=True) # PK Todo番号 [cite: 125]
    content = Column('内容', String, index=True) # 内容 [cite: 126]
    due_date = Column('期限', String) # 期限 [cite: 127]
    is_completed = Column('完了/未完了', Boolean, default=False) # 完了/未完了 [cite: 128]
    
    tags = relationship("Tag", secondary=todo_tag_association, back_populates="todos")

class Tag(Base):
    __tablename__ = 'Tag' # テーブル名 'Tag' [cite: 131]
    tag_id = Column('Tag番号', Integer, primary_key=True, index=True) # PK Tag番号 [cite: 129]
    description = Column('説明', String, index=True) # 説明 [cite: 130]

    todos = relationship("Todo", secondary=todo_tag_association, back_populates="tags")