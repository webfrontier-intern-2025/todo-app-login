from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette.responses import RedirectResponse
from starlette import status
# 相対インポートを使用
from . import crud, models, schemas
from .models import SessionLocal, engine # ここで SessionLocal と engine をインポート
from fastapi.staticfiles import StaticFiles

# データベースのテーブルをすべて作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 静的ファイルのマウント (static ディレクトリは src の外にあるのでパスを調整)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2テンプレートを設定 (templates ディレクトリは src の外にあるのでパスを調整)
templates = Jinja2Templates(directory="templates")

# DBセッションを取得するための依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === フロントエンド用エンドポイント ===

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    todos = crud.get_todos(db)
    return templates.TemplateResponse("index.html", {"request": request, "todos": todos})

@app.get("/todo/new", response_class=HTMLResponse)
def new_todo_form(request: Request):
    return templates.TemplateResponse("todo_new.html", {"request": request})

@app.post("/todo/create")
def create_todo_from_form(db: Session = Depends(get_db), content: str = Form(...), due_date: str = Form(None)):
    todo_create = schemas.TodoCreate(content=content, due_date=due_date)
    crud.create_todo(db=db, todo=todo_create)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# todo_id を id に変更
@app.get("/todo/{id}", response_class=HTMLResponse)
def read_todo_detail(request: Request, id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return templates.TemplateResponse("todo_detail.html", {"request": request, "todo": todo})

# todo_id を id に変更
@app.get("/todo/{id}/edit", response_class=HTMLResponse)
def edit_todo_form(request: Request, id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return templates.TemplateResponse("todo_edit.html", {"request": request, "todo": todo})

# todo_id を id に変更
@app.post("/todo/{id}/update")
def update_todo_from_form(
    id: int,
    db: Session = Depends(get_db),
    content: str = Form(...),
    due_date: str = Form(None),
    is_completed: Optional[bool] = Form(False)
):
    completed_status = True if is_completed else False
    crud.update_todo(db=db, todo_id=id, content=content, due_date=due_date, is_completed=completed_status)
    return RedirectResponse(url=f"/todo/{id}", status_code=status.HTTP_303_SEE_OTHER)

# === WebAPI用エンドポイント ===

@app.post("/api/todo", response_model=schemas.Todo)
def create_todo_endpoint(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db=db, todo=todo)

@app.get("/api/todo", response_model=List[schemas.Todo])
def read_todos_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos

# todo_id を id に変更
@app.get("/api/todo/{id}", response_model=schemas.Todo)
def read_todo_endpoint(id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

# todo_id を id に変更
@app.put("/api/todo/{id}", response_model=schemas.Todo)
def update_todo_endpoint(id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db_todo.content = todo.content
    db_todo.due_date = todo.due_date
    db.commit()
    db.refresh(db_todo)
    return db_todo

# todo_id を id に変更
@app.delete("/api/todo/{id}", response_model=schemas.Todo)
def delete_todo_endpoint(id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(db_todo)
    db.commit()
    # 削除APIのレスポンスは削除されたオブジェクトを返すことが多いですが、IDだけ返す仕様もあります
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

# === 関連付け用のエンドポイント (ID名を修正) ===

@app.post("/api/todo/{todo_id}/tags/{tag_id}", response_model=schemas.Todo)
def add_tag_to_todo_endpoint(todo_id: int, tag_id: int, db: Session = Depends(get_db)):
    db_todo = crud.add_tag_to_todo(db, todo_id=todo_id, tag_id=tag_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo or Tag not found")
    return db_todo

# === カスタムエラーハンドラ ===

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # エラーページのテンプレートパスを修正
    return templates.TemplateResponse(
        "error.html", 
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )