# schemas.py
from pydantic import BaseModel
from typing import Optional, List

# --- まず、基本となるスキーマを定義します ---
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