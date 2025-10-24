# crud.py
from sqlalchemy.orm import Session
import models, schemas

# IDを指定して単一のTodoアイテムを取得する
def get_todo(db: Session, todo_id: int):
    return db.query(models.Todo).filter(models.Todo.todo_id == todo_id).first()

# Todoアイテムのリストを取得する
def get_todos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Todo).offset(skip).limit(limit).all()

# 新しいTodoアイテムを作成する
def create_todo(db: Session, todo: schemas.TodoCreate):
    db_todo = models.Todo(content=todo.content, due_date=todo.due_date)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

# IDを指定して単一のTagを取得する
def get_tag(db: Session, tag_id: int):
    return db.query(models.Tag).filter(models.Tag.tag_id == tag_id).first()

# description（内容）を指定してTagを取得する
def get_tag_by_description(db: Session, description: str):
    return db.query(models.Tag).filter(models.Tag.description == description).first()

# Tagのリストを取得する
def get_tags(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tag).offset(skip).limit(limit).all()

# 新しいTagを作成する
def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(description=tag.description)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

# TodoにTagを関連付ける
def add_tag_to_todo(db: Session, todo_id: int, tag_id: int):
    db_todo = get_todo(db, todo_id=todo_id)
    db_tag = get_tag(db, tag_id=tag_id)
    # TodoとTagの両方が存在する場合のみ処理
    if db_todo and db_tag:
        db_todo.tags.append(db_tag)
        db.commit()
        db.refresh(db_todo)
    return db_todo

# ToDoを更新する関数
def update_todo(db: Session, todo_id: int, content: str, due_date: str, is_completed: bool):
    db_todo = get_todo(db, todo_id=todo_id)
    if db_todo:
        db_todo.content = content
        db_todo.due_date = due_date
        db_todo.is_completed = is_completed
        db.commit()
        db.refresh(db_todo)
    return db_todo