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

# --- 最後に、読み取り・返却用のスキーマを定義します ---
class Tag(TagBase):
    tag_id: int

    class Config:
        from_attributes = True

class Todo(TodoBase):
    todo_id: int
    is_completed: bool
    tags: List[Tag] = []

    class Config:
        from_attributes = True # 古いorm_modeから変更