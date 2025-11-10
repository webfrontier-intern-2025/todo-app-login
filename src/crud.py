from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas # 相対インポートを使用
from .security import get_password_hash


# ここから
from .security import password_hash

# ユーザー名でユーザーを検索する（ログイン時と登録時の重複チェックで使う）
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# ユーザーを作成する
def create_user(db: Session, user: schemas.UserCreate):

    hashed_password = hash_password(user.password) #ハッシュ化処理

    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ここまで追記1106


# === Todo CRUD 関数 ===(元5行目)

def get_todo(db: Session, id: int):
    """IDを指定して単一のTodo項目を取得します。"""
    return db.query(models.Todo).filter(models.Todo.id == id).first()

def get_todos(db: Session, skip: int = 0, limit: int = 100):
    """Todo項目のリストを取得します。"""
    return db.query(models.Todo).offset(skip).limit(limit).all()

def create_todo(db: Session, todo: schemas.TodoCreate):
    """新しいTodo項目を作成します。"""
    db_todo = models.Todo(content=todo.content, due_date=todo.due_date)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def update_todo(db: Session, todo_id: int, content: str, due_date: Optional[str], is_completed: bool):
    """既存のTodo項目を更新します。"""
    db_todo = get_todo(db, id=todo_id)
    if db_todo:
        db_todo.content = content
        db_todo.due_date = due_date
        db_todo.is_completed = is_completed
        db.commit()
        db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int):
    """IDを指定してTodo項目を削除します。"""
    db_todo = get_todo(db, id=todo_id)
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo # 削除されたオブジェクトまたはNoneを返す

# === Tag CRUD 関数 ===

def get_tag(db: Session, id: int):
    """IDを指定して単一のTag項目を取得します。"""
    return db.query(models.Tag).filter(models.Tag.id == id).first()

def get_tag_by_description(db: Session, description: str):
    """description（説明）を指定してTag項目を取得します。"""
    return db.query(models.Tag).filter(models.Tag.description == description).first()

def get_tags(db: Session, skip: int = 0, limit: int = 100):
    """Tag項目のリストを取得します。"""
    return db.query(models.Tag).offset(skip).limit(limit).all()

def create_tag(db: Session, tag: schemas.TagCreate):
    """新しいTag項目を作成します。"""
    db_tag = models.Tag(description=tag.description)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def update_tag(db: Session, tag_id: int, tag: schemas.TagCreate):
    """既存のTag項目を更新します。"""
    db_tag = get_tag(db, id=tag_id)
    if db_tag:
        db_tag.description = tag.description
        db.commit()
        db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int):
    """IDを指定してTag項目を削除します。"""
    db_tag = get_tag(db, id=tag_id)
    if db_tag:
        db.delete(db_tag)
        db.commit()
    return db_tag # 削除されたオブジェクトまたはNoneを返す

# === 関連付け用関数 ===

def add_tag_to_todo(db: Session, todo_id: int, tag_id: int):
    """TodoにTagを関連付けます。"""
    db_todo = get_todo(db, id=todo_id)
    db_tag = get_tag(db, id=tag_id)
    if db_todo and db_tag:
        # 同じタグを複数回追加しないようにチェック（任意）
        if db_tag not in db_todo.tags:
            db_todo.tags.append(db_tag)
            db.commit()
            db.refresh(db_todo)
    return db_todo

def get_user(db: Session, user_id: int):
    """
    IDでユーザーを1件取得
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    """
    ユーザー名でユーザーを1件取得 (ログイン認証時に使用)
    """
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    """
    新しいユーザーを作成
    """
    # パスワードをハッシュ化
    hashed_password = get_password_hash(user.password)
    
    # データベースモデルを作成
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
