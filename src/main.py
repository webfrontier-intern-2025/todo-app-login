from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette.responses import RedirectResponse
from starlette import status
from fastapi.staticfiles import StaticFiles

# srcパッケージ内のモジュールには相対インポートを使用
from . import crud, models, schemas
from .models import SessionLocal, engine

# データベースのテーブルが存在しない場合は作成する
# 注意: 本番環境ではAlembicがマイグレーションを管理すべき
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 静的ファイル（CSS, JS, 画像など）をマウント
# 'static'ディレクトリがプロジェクトルート（'src'の外）にあると想定
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2テンプレートを設定
# 'templates'ディレクトリがプロジェクトルート（'src'の外）にあると想定
templates = Jinja2Templates(directory="templates")

# 各リクエストでDBセッションを取得するための依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === フロントエンド用エンドポイント (HTMLページ) ===

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    """全てのToDo項目の一覧を表示します。"""
    todos = crud.get_todos(db)
    return templates.TemplateResponse("index.html", {"request": request, "todos": todos})

@app.get("/todo/new", response_class=HTMLResponse)
def new_todo_form(request: Request):
    """新しいToDoを作成するためのフォームを表示します。"""
    return templates.TemplateResponse("todo_new.html", {"request": request})

@app.post("/todo/create", status_code=status.HTTP_303_SEE_OTHER)
def create_todo_from_form(db: Session = Depends(get_db), content: str = Form(...), due_date: Optional[str] = Form(None)):
    """新しいToDoを作成するためのフォーム送信を処理します。"""
    # 空文字列で送信されたdue_dateをNoneに変換
    due_date_val = due_date if due_date else None
    todo_create = schemas.TodoCreate(content=content, due_date=due_date_val)
    crud.create_todo(db=db, todo=todo_create)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/todo/{id}", response_class=HTMLResponse)
def read_todo_detail(request: Request, id: int, db: Session = Depends(get_db)):
    """単一のToDo項目の詳細を表示します。"""
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return templates.TemplateResponse("todo_detail.html", {"request": request, "todo": todo})

@app.get("/todo/{id}/edit", response_class=HTMLResponse)
def edit_todo_form(request: Request, id: int, db: Session = Depends(get_db)):
    """既存のToDoを編集するためのフォームを表示します。"""
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return templates.TemplateResponse("todo_edit.html", {"request": request, "todo": todo})

@app.post("/todo/{id}/update", status_code=status.HTTP_303_SEE_OTHER)
def update_todo_from_form(
    id: int,
    db: Session = Depends(get_db),
    content: str = Form(...),
    due_date: Optional[str] = Form(None), # フォームから空文字列を許可
    is_completed: Optional[bool] = Form(False) # チェックボックスの値
):
    """ToDoを更新するためのフォーム送信を処理します。"""
    completed_status = True if is_completed else False
    # 空文字列で送信されたdue_dateをNoneに変換
    due_date_val = due_date if due_date else None

    updated_todo = crud.update_todo(db=db, todo_id=id, content=content, due_date=due_date_val, is_completed=completed_status)
    if updated_todo is None:
         raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return RedirectResponse(url=f"/todo/{id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/todo/{id}/manage-tags", response_class=HTMLResponse)
def manage_todo_tags_form(request: Request, id: int, db: Session = Depends(get_db)):
    """特定のToDoに関連付けられたタグを管理するページを表示します。"""
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")

    # タグを追加するフォーム用に、利用可能な全てのタグリストも渡す
    all_tags = crud.get_tags(db)

    return templates.TemplateResponse("manage_tags.html", {
        "request": request,
        "todo": todo,
        "all_tags": all_tags
    })

# ↓↓↓ ここにタグ追加処理のエンドポイントを追加 ↓↓↓
@app.post("/todo/{id}/tags/add", status_code=status.HTTP_303_SEE_OTHER)
def add_tag_to_todo_from_form(id: int, tag_id: int = Form(...), db: Session = Depends(get_db)):
    """フォームから送信されたタグIDを特定のToDoに関連付けます。"""

    # 存在確認 (add_tag_to_todo の中でも確認するが、ここで先にチェックしても良い)
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    tag = crud.get_tag(db, id=tag_id)
    if tag is None:
         raise HTTPException(status_code=404, detail=f"ID {tag_id} のTagは見つかりません")

    crud.add_tag_to_todo(db=db, todo_id=id, tag_id=tag_id)

    # 処理が終わったら、タグ管理ページにリダイレクトして結果を反映させる
    return RedirectResponse(url=f"/todo/{id}/manage-tags", status_code=status.HTTP_303_SEE_OTHER)
# ↑↑↑ 追加ここまで ↑↑↑

# === WebAPI用エンドポイント (JSON) ===

# --- ToDo API ---
@app.post("/api/todo", response_model=schemas.Todo, status_code=status.HTTP_201_CREATED)
def create_todo_endpoint(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    """ToDoを新規作成します。"""
    return crud.create_todo(db=db, todo=todo)

@app.get("/api/todo", response_model=List[schemas.Todo])
def read_todos_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """ToDoのリストを取得します。"""
    # 将来的に必要であれば、ここで完了ステータスによるフィルタリングを追加
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos

@app.get("/api/todo/{id}", response_model=schemas.Todo)
def read_todo_endpoint(id: int, db: Session = Depends(get_db)):
    """IDを指定して単一のToDoを取得します。"""
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.put("/api/todo/{id}", response_model=schemas.Todo)
def update_todo_endpoint(id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)): # TodoUpdateの代わりにTodoCreateを使用
    """IDを指定してToDoを更新します。"""
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # シンプルな更新ロジック。必要に応じてTodoUpdateスキーマを使い、より堅牢なロジックに置き換える。
    updated_todo = crud.update_todo(
        db=db,
        todo_id=id,
        content=todo.content,
        due_date=todo.due_date,
        is_completed=db_todo.is_completed # PUTでは完了ステータスは変更しない例（必要なら修正）
    )
    return updated_todo

@app.delete("/api/todo/{id}", response_model=schemas.Todo) # 削除された項目を返す
def delete_todo_endpoint(id: int, db: Session = Depends(get_db)):
    """IDを指定してToDoを削除します。"""
    db_todo = crud.get_todo(db, id=id) # 最初に存在確認
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    deleted_todo = crud.delete_todo(db, todo_id=id)
    return deleted_todo

# --- Tag API ---
@app.post("/api/tag", response_model=schemas.Tag, status_code=status.HTTP_201_CREATED)
def create_tag_endpoint(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    """Tagを新規作成します。"""
    db_tag = crud.get_tag_by_description(db, description=tag.description)
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag description already exists")
    return crud.create_tag(db=db, tag=tag)

@app.get("/api/tag", response_model=List[schemas.Tag])
def read_tags_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Tagのリストを取得します。"""
    tags = crud.get_tags(db, skip=skip, limit=limit)
    return tags

@app.get("/api/tag/{id}", response_model=schemas.Tag)
def read_tag_endpoint(id: int, db: Session = Depends(get_db)):
    """IDを指定して単一のTagを取得します。"""
    db_tag = crud.get_tag(db, id=id)
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db_tag

@app.put("/api/tag/{id}", response_model=schemas.Tag)
def update_tag_endpoint(id: int, tag: schemas.TagCreate, db: Session = Depends(get_db)):
    """IDを指定してTagを更新します。"""
    db_tag_to_update = crud.get_tag(db, id=id)
    if db_tag_to_update is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    # 新しいdescriptionが他の既存タグと競合しないかチェック
    existing_tag = crud.get_tag_by_description(db, description=tag.description)
    if existing_tag and existing_tag.id != id:
         raise HTTPException(status_code=400, detail="Another tag with this description already exists")

    updated_tag = crud.update_tag(db, tag_id=id, tag=tag)
    return updated_tag

@app.delete("/api/tag/{id}", response_model=schemas.Tag) # 削除された項目を返す
def delete_tag_endpoint(id: int, db: Session = Depends(get_db)):
    """IDを指定してTagを削除します。"""
    db_tag = crud.get_tag(db, id=id) # 最初に存在確認
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    deleted_tag = crud.delete_tag(db, tag_id=id)
    return deleted_tag

# --- 関連付けAPI ---
@app.post("/api/todo/{todo_id}/tags/{tag_id}", response_model=schemas.Todo)
def add_tag_to_todo_endpoint(todo_id: int, tag_id: int, db: Session = Depends(get_db)):
    """TodoにTagを関連付けます。"""
    db_todo = crud.get_todo(db, id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    db_tag = crud.get_tag(db, id=tag_id)
    if db_tag is None:
        raise HTTPException(status_code=404, detail=f"Tag with id {tag_id} not found")

    # crud関数を呼び出す前に存在確認したので、crud側でのNoneチェックは不要
    updated_todo = crud.add_tag_to_todo(db, todo_id=todo_id, tag_id=tag_id)
    return updated_todo


# === カスタムエラーハンドラ ===
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTMLエラーページをレンダリングするためのカスタムハンドラ。"""
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )