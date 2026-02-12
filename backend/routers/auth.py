from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Importamos desde database.py para evitar el circulo
from backend.database import SessionLocal 
from backend.models.users import User
from backend.schemas.users import UserCreate, UserLogin, UserOut

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Dependency (Para obtener la DB)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNCIONES DE AYUDA ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# --- ENDPOINTS ---

@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    hashed_password = get_password_hash(user.password)
    
    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login")
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=403, detail="Contraseña incorrecta")
    
    return {"mensaje": "Login exitoso", "usuario": user.username}