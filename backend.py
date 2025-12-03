from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
import sqlite3
import os
import shutil

app = FastAPI(title="FastAPI Backend")

# Mount uploads directory to serve files statically
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "9f3c2e8d6a0b4f1c8b9a7d5e3f0c2b9a4e6d1f7c5b8a3d9e2c4f0a7b6d1e5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
    )
    # Add columns if not exist
    try:
        conn.execute("ALTER TABLE users ADD COLUMN name TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    conn.commit()
    conn.close()

init_db()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

class User(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    name: str
    filename: str
    file_type: str
    upload_date: str
    url: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(email: str, password: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.lower(), hash_password(password)),
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    conn.close()
    return user_id

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

@app.post("/api/signup", response_model=Token)
def signup(user: User):
    if not user.email or not user.password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    # Check if user already exists
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user with hashed password
    user_id = create_user(user.email, user.password)
    
    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id), "email": user.email}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(form_data, flush=True)
    # OAuth2PasswordRequestForm uses 'username' field, but we'll treat it as email
    db_user = get_user_by_email(form_data.username)
    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, db_user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user["id"]), "email": db_user["email"]},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me", response_model=UserResponse)
async def read_users_me(current_user: sqlite3.Row = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": current_user["id"], 
        "email": current_user["email"],
        "name": current_user["name"] if "name" in current_user.keys() else None,
        "avatar_url": current_user["avatar_url"] if "avatar_url" in current_user.keys() else None
    }

@app.put("/api/me", response_model=UserResponse)
async def update_profile(
    name: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    current_user: sqlite3.Row = Depends(get_current_user)
):
    conn = get_db_connection()
    cur = conn.cursor()
    
    avatar_url = current_user["avatar_url"] if "avatar_url" in current_user.keys() else None
    
    if avatar:
        # Save file to disk
        file_ext = os.path.splitext(avatar.filename)[1]
        unique_filename = f"avatar_{current_user['id']}_{datetime.now().timestamp()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
            
        avatar_url = f"http://127.0.0.1:8000/uploads/{unique_filename}"
    
    new_name = name if name is not None else (current_user["name"] if "name" in current_user.keys() else None)
    
    # Update DB
    cur.execute(
        "UPDATE users SET name = ?, avatar_url = ? WHERE id = ?",
        (new_name, avatar_url, current_user["id"])
    )
    conn.commit()
    
    # Fetch updated user
    cur.execute("SELECT * FROM users WHERE id = ?", (current_user["id"],))
    updated_user = cur.fetchone()
    conn.close()
    
    return {
        "id": updated_user["id"], 
        "email": updated_user["email"],
        "name": updated_user["name"],
        "avatar_url": updated_user["avatar_url"]
    }

@app.post("/api/documents", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: sqlite3.Row = Depends(get_current_user)
):
    # Save file to disk
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{datetime.now().timestamp()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Determine file type
    file_type = "text"
    if file_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        file_type = "image"
    elif file_ext.lower() == '.pdf':
        file_type = "pdf"
    elif file_ext.lower() in ['.xlsx', '.xls', '.csv']:
        file_type = "sheet"
        
    # Save file to DB
    conn = get_db_connection()
    cur = conn.cursor()
    upload_date = datetime.now().strftime("%Y-%m-%d")
    cur.execute(
        """
        INSERT INTO documents (user_id, name, filename, file_type, upload_date)
        VALUES (?, ?, ?, ?, ?)
        """,
        (current_user["id"], file.filename, unique_filename, file_type, upload_date)
    )
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()
    
    return {
        "id": doc_id,
        "name": file.filename,
        "filename": unique_filename,
        "file_type": file_type,
        "upload_date": upload_date,
        "url": f"http://127.0.0.1:8000/uploads/{unique_filename}"
    }

@app.get("/api/documents", response_model=List[DocumentResponse])
async def get_documents(current_user: sqlite3.Row = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY id DESC", (current_user["id"],))
    rows = cur.fetchall()
    conn.close()
    
    documents = []
    for row in rows:
        documents.append({
            "id": row["id"],
            "name": row["name"],
            "filename": row["filename"],
            "file_type": row["file_type"],
            "upload_date": row["upload_date"],
            "url": f"http://127.0.0.1:8000/uploads/{row['filename']}"
        })
    return documents

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: int, current_user: sqlite3.Row = Depends(get_current_user)):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check ownership
    cur.execute("SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, current_user["id"]))
    doc = cur.fetchone()
    
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete file from disk
    file_path = os.path.join(UPLOAD_DIR, doc["filename"])
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Delete file from DB
    cur.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    
    return {"message": "Document deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI Backend on http://localhost:8000", flush=True)
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)