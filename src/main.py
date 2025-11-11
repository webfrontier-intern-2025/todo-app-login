from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
from starlette.responses import RedirectResponse
from starlette import status
from fastapi.staticfiles import StaticFiles

# --- ↓↓↓ ログイン機能のために追加 ↓↓↓ ---
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from . import security # security.py を import
# --- ↑↑↑ ログイン機能のために追加 ↑↑↑ ---

from . import crud, models, schemas
from .models import SessionLocal, engine

# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 静的ファイルとテンプレートの設定 (プロジェクトルート基準)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# DBセッション取得用の依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ↓↓↓ ログイン機能 (OAuth2/JWT) の設定 ↓↓↓ ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    トークンをデコードし、現在のユーザーを取得する依存関係
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = security.decode_access_token(token)
    if username is None:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user
# --- ↑↑↑ ログイン機能 (OAuth2/JWT) の設定 ↑↑↑ ---


# === フロントエンド用エンドポイント (HTMLページ) ===

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    ToDoアプリのメインページ
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """
    ログインページのHTMLを返します。
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    """
    ユーザー登録ページのHTMLを返します。
    """
    return templates.TemplateResponse("register.html", {"request": request})

### --- ↓↓↓ これが /todo/1 などのアクセスを処理するエンドポイントです ↓↓↓ ---
@app.get("/todo/{id}", response_class=HTMLResponse)
def read_todo_detail(request: Request, id: int, db: Session = Depends(get_db)):
    """
    単一のToDo項目の詳細を表示します。
    """
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    
    # templates/todo_detail.html を表示
    return templates.TemplateResponse("todo_detail.html", {"request": request, "todo": todo})

@app.get("/todo/{id}/edit", response_class=HTMLResponse)
def edit_todo_form(request: Request, id: int, db: Session = Depends(get_db)):
    """
    既存のToDoを編集するためのフォームを表示します。
    """
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return templates.TemplateResponse("todo_edit.html", {"request": request, "todo": todo})

@app.post("/todo/{id}/update", status_code=status.HTTP_303_SEE_OTHER)
def update_todo_from_form(
    id: int,
    db: Session = Depends(get_db),
    content: str = Form(...),
    due_date: Optional[str] = Form(None), 
    is_completed: Optional[bool] = Form(False)
):
    """
    ToDoを更新するためのフォーム送信を処理します。
    """
    completed_status = True if is_completed else False
    due_date_val = due_date if due_date else None

    updated_todo = crud.update_todo(db=db, todo_id=id, content=content, due_date=due_date_val, is_completed=completed_status)
    if updated_todo is None:
         raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    return RedirectResponse(url=f"/todo/{id}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/todo/{id}/manage-tags", response_class=HTMLResponse)
def manage_todo_tags_form(request: Request, id: int, db: Session = Depends(get_db)):
    """
    特定のToDoに関連付けられたタグを管理するページを表示します。
    """
    todo = crud.get_todo(db, id=id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")

    all_tags = crud.get_tags(db)
    return templates.TemplateResponse("manage_tags.html", {
        "request": request,
        "todo": todo,
        "all_tags": all_tags
    })

@app.post("/todo/{id}/tags/add", status_code=status.HTTP_303_SEE_OTHER)
def add_tag_to_todo_from_form(id: int, tag_id: int = Form(...), db: Session = Depends(get_db)):
    """
    フォームから送信されたタグIDを特定のToDoに関連付けます。
    """
    if crud.get_todo(db, id=id) is None:
        raise HTTPException(status_code=404, detail=f"ID {id} のTodoは見つかりません")
    if crud.get_tag(db, id=tag_id) is None:
         raise HTTPException(status_code=404, detail=f"ID {tag_id} のTagは見つかりません")
        
    crud.add_tag_to_todo(db=db, todo_id=id, tag_id=tag_id)
    return RedirectResponse(url=f"/todo/{id}/manage-tags", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/tag/create/from-page", status_code=status.HTTP_303_SEE_OTHER)
def create_tag_from_form(
    db: Session = Depends(get_db), 
    description: str = Form(...), 
    todo_id: int = Form(...) # 戻るためにToDoのIDを受け取る
):
    """
    フォームから送信されたデータで新しいタグを作成します。
    """
    db_tag = crud.get_tag_by_description(db, description=description)
    if not db_tag:
        tag_create = schemas.TagCreate(description=description)
        crud.create_tag(db=db, tag=tag_create)
    return RedirectResponse(url=f"/todo/{todo_id}/manage-tags", status_code=status.HTTP_303_SEE_OTHER)
### --- ↑↑↑ HTMLページ用エンドポイントここまで ↑↑↑ ---


# === WebAPI用エンドポイント (JSON) ===

# --- 認証API (ログイン・登録) ---

@app.post("/api/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    ユーザー名とパスワードで認証し、アクセストークンを返します。
    """
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    新しいユーザーを登録します。
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    return crud.create_user(db=db, user=user)

@app.get("/api/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    現在のログインユーザーの情報を返します (トークン検証用)
    """
    return current_user


# --- ToDo API (ログイン必須) ---

#11/11/1057変更
@app.post("/api/todo", response_model=schemas.Todo, status_code=status.HTTP_201_CREATED)
def create_todo_endpoint(
    todo: schemas.TodoCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # current_user.id を渡す
    return crud.create_todo(db=db, todo=todo, user_id=current_user.id)

#11/11/1057変更
@app.get("/api/todo", response_model=List[schemas.Todo])
def read_todos_endpoint(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # current_user.id を渡して絞り込む
    todos = crud.get_todos(db, user_id=current_user.id) 
    return todos

@app.get("/api/todo/{id}", response_model=schemas.Todo)
def read_todo_endpoint(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.put("/api/todo/{id}", response_model=schemas.Todo)
def update_todo_endpoint(
    id: int, 
    todo: schemas.TodoCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    updated_todo = crud.update_todo(
        db=db, todo_id=id,
        content=todo.content,
        due_date=todo.due_date,
        is_completed=db_todo.is_completed 
    )
    return updated_todo

@app.delete("/api/todo/{id}", response_model=schemas.Todo) 
def delete_todo_endpoint(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_todo = crud.get_todo(db, id=id) 
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    deleted_todo = crud.delete_todo(db, todo_id=id)
    return deleted_todo

@app.put("/api/todo/{id}/toggle", response_model=schemas.Todo)
def toggle_todo_completed(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_todo = crud.get_todo(db, id=id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    new_status = not db_todo.is_completed
    updated_todo = crud.update_todo(
        db=db, todo_id=id,
        content=db_todo.content, due_date=db_todo.due_date, is_completed=new_status
    )
    if updated_todo is None:
         raise HTTPException(status_code=500, detail="Todoの更新に失敗しました")
    return updated_todo


# --- Tag API (ログイン必須) ---

@app.post("/api/tag", response_model=schemas.Tag, status_code=status.HTTP_201_CREATED)
def create_tag_endpoint(
    tag: schemas.TagCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_tag = crud.get_tag_by_description(db, description=tag.description)
    if db_tag:
        raise HTTPException(status_code=400, detail="Tag description already exists")
    return crud.create_tag(db=db, tag=tag)

@app.get("/api/tag", response_model=List[schemas.Tag])
def read_tags_endpoint(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    tags = crud.get_tags(db)
    return tags

@app.get("/api/tag/{id}", response_model=schemas.Tag)
def read_tag_endpoint(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_tag = crud.get_tag(db, id=id)
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db_tag

@app.put("/api/tag/{id}", response_model=schemas.Tag)
def update_tag_endpoint(
    id: int, 
    tag: schemas.TagCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_tag_to_update = crud.get_tag(db, id=id)
    if db_tag_to_update is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    existing_tag = crud.get_tag_by_description(db, description=tag.description)
    if existing_tag and existing_tag.id != id:
         raise HTTPException(status_code=400, detail="Another tag with this description already exists")

    updated_tag = crud.update_tag(db, tag_id=id, tag=tag)
    return updated_tag

@app.delete("/api/tag/{id}", response_model=schemas.Tag)
def delete_tag_endpoint(
    id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_tag = crud.get_tag(db, id=id)
    if db_tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    deleted_tag = crud.delete_tag(db, tag_id=id)
    return deleted_tag

# --- 関連付けAPI (ログイン必須) ---
@app.post("/api/todo/{todo_id}/tags/{tag_id}", response_model=schemas.Todo)
def add_tag_to_todo_endpoint(
    todo_id: int, 
    tag_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # <--- 保護
):
    db_todo = crud.get_todo(db, id=todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    db_tag = crud.get_tag(db, id=tag_id)
    if db_tag is None:
        raise HTTPException(status_code=404, detail=f"Tag with id {tag_id} not found")

    updated_todo = crud.add_tag_to_todo(db, todo_id=todo_id, tag_id=tag_id)
    return updated_todo


# === カスタムエラーハンドラ (JSONではなくHTMLを返す) ===
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTMLエラーページをレンダリングするためのカスタムハンドラ。
    """
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=exc.status_code,
    )
