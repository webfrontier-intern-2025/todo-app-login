from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone # <-- 'timedelta' も 'datetime' から必要です
from typing import Optional # <--- この行を追加してください
from jose import JWTError, jwt

# Bcryptアルゴリズムを使用してパスワードをハッシュ化する設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文のパスワードとハッシュ化されたパスワードを比較します。
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    平文のパスワードを受け取り、ハッシュ化された文字列を返します。
    """
    return pwd_context.hash(password)

# JWT (JSON Web Token) の設定
# このSECRET_KEYは非常に重要です。実際には環境変数などから読み込むべきです。
# (ターミナルで `openssl rand -hex 32` を実行して生成したランダムな文字列に置き換えてください)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # トークンの有効期限 (例: 30分)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    JWTアクセストークンを作成します。
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # デフォルトの有効期限を設定
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[str]:
    """
    JWTアクセストークンをデコードし、ユーザー名 (sub) を返します。
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None
    