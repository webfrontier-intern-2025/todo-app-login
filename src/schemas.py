# schemas.py
from pydantic import BaseModel
from typing import Optional, List


#　ここから
# ユーザー登録（新規登録）時にAPIが受け取るJSONの型
class UserCreate(BaseModel):
    username: str
    password: str

# ユーザー情報をAPIが返す時の型（パスワードは含めない）
class User(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True # SQLAlchemyモデルをPydanticモデルに自動変換する設定

# ログイン成功時に返すトークンの型
class Token(BaseModel):
    access_token: str
    token_type: str

# ここまで追記11061450


# --- まず、基本となるスキーマを定義します ---(元5行目)
class TodoBase(BaseModel):
    content: str
    due_date: Optional[str] = None

class TagBase(BaseModel):
    description: str

# --- 次に、作成用のスキーマを定義します ---
class TodoCreate(TodoBase):
    pass

class TagCreate(TagBase):
    pass

# src/schemas.py の Todo と Tag スキーマ
# ...
class Tag(TagBase):
    id: int # tag_id から変更

    class Config:
        from_attributes = True

class Todo(TodoBase):
    id: int # todo_id から変更
    is_completed: bool
    tags: List[Tag] = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str # APIで受け取る際は平文のパスワード

class User(UserBase):
    id: int
    is_active: bool
    # todos: List[Todo] = [] # 将来的にToDoと関連付ける場合

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None