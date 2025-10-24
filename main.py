# main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates # Jinja2Templates を追加
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette.responses import RedirectResponse
from starlette import status
import crud, models, schemas
from models import SessionLocal, engine
from fastapi.staticfiles import StaticFiles

# データベースのテーブルをすべて作成する
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Jinja2テンプレートを設定する
templates = Jinja2Templates(directory="templates")

# 各リクエストでDBセッションを取得するための依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. トップページを表示するためのエンドポイントを追加する
@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    todos = crud.get_todos(db) # データベースからTodoのリストを取得
    return templates.TemplateResponse("index.html", {"request": request, "todos": todos})

# ToDo新規作成ページを表示するエンドポイント
@app.get("/todo/new", response_class=HTMLResponse)
def new_todo_form(request: Request):
    return templates.TemplateResponse("todo_new.html", {"request": request})

# 2. 詳細ページ表示用のエンドポイントを追加する
@app.get("/todo/{todo_id}", response_class=HTMLResponse)
def read_todo_detail(request: Request, todo_id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo(db, todo_id=todo_id)
    if todo is None:
        
        raise HTTPException(status_code=404, detail=f"ID {todo_id} のTodoは見つかりません")
    
    return templates.TemplateResponse("todo_detail.html", {"request": request, "todo": todo})

# ToDo編集ページを表示するエンドポイント
@app.get("/todo/{todo_id}/edit", response_class=HTMLResponse)
def edit_todo_form(request: Request, todo_id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo(db, todo_id=todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {todo_id} のTodoは見つかりません")
    
    return templates.TemplateResponse("todo_edit.html", {"request": request, "todo": todo})

# フォームデータでToDoを更新するエンドポイント
@app.post("/todo/{todo_id}/update")
def update_todo_from_form(
    todo_id: int, 
    db: Session = Depends(get_db), 
    content: str = Form(...), 
    due_date: str = Form(None),
    is_completed: Optional[bool] = Form(False) # チェックボックスは少し特殊
):
    # チェックボックスの値は 'on' または None で送信されることがあるため、boolに変換
    completed_status = True if is_completed else False
    
    crud.update_todo(db=db, todo_id=todo_id, content=content, due_date=due_date, is_completed=completed_status)
    # 更新が終わったら、詳細ページにリダイレクトして結果を反映させる
    return RedirectResponse(url=f"/todo/{todo_id}", status_code=status.HTTP_303_SEE_OTHER)

# 各APIリクエストでデータベースセッションを取得するための依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Todoのエンドポイント ===
@app.post("/todo/create")
def create_todo_from_form(db: Session = Depends(get_db), content: str = Form(...), due_date: str = Form(None)):
    # フォームから受け取ったデータをPydanticスキーマに変換
    todo_create = schemas.TodoCreate(content=content, due_date=due_date)
    # 既存のCRUD関数を使ってデータベースにTodoを作成
    crud.create_todo(db=db, todo=todo_create)
    # 作成が終わったら、トップページにリダイレクトして結果を反映させる
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# [cite_start]【作成】Todoを作成するAPIエンドポイント [cite: 69]
@app.post("/api/todo", response_model=schemas.Todo)
def create_todo_endpoint(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db=db, todo=todo)

# [cite_start]【取得(一覧)】Todoのリストを取得するAPIエンドポイント [cite: 69]
@app.get("/api/todo", response_model=list[schemas.Todo])
def read_todos_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos

# [cite_start]【取得(個別)】IDを指定して単一のTodoを取得するAPIエンドポイント [cite: 69]
@app.get("/api/todo/{todo_id}", response_model=schemas.Todo)
def read_todo_endpoint(todo_id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

# [cite_start]【更新】Todoを更新するAPIエンドポイント [cite: 69]
@app.put("/api/todo/{todo_id}", response_model=schemas.Todo)
def update_todo_endpoint(todo_id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db_todo.content = todo.content
    db_todo.due_date = todo.due_date
    # is_completedの更新ロジックは必要に応じて追加
    db.commit()
    db.refresh(db_todo)
    return db_todo

# [cite_start]【削除】Todoを削除するAPIエンドポイント [cite: 69]
@app.delete("/api/todo/{todo_id}", response_model=schemas.Todo)
def delete_todo_endpoint(todo_id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, todo_id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(db_todo)
    db.commit()
    return db_todo

# === Tagのエンドポイント ===

@app.post("/api/tag", response_model=schemas.Tag)
def create_tag_endpoint(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    db_tag = crud.get_tag_by_description(db, description=tag.description)
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    return crud.create_tag(db=db, tag=tag)

@app.get("/api/tag", response_model=List[schemas.Tag])
def read_tags_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tags = crud.get_tags(db, skip=skip, limit=limit)
    return tags

# === 関連付け用のエンドポイント ===

@app.post("/api/todo/{todo_id}/tags/{tag_id}", response_model=schemas.Todo)
def add_tag_to_todo_endpoint(todo_id: int, tag_id: int, db: Session = Depends(get_db)):
    db_todo = crud.add_tag_to_todo(db, todo_id=todo_id, tag_id=tag_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo or Tag not found")
    return db_todo

# === カスタムエラーハンドラ ===
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )