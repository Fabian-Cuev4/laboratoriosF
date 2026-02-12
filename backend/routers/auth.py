from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Importaciones con ruta absoluta del proyecto
from backend.database import SessionLocal 
from backend.models.users import User
from backend.schemas.users import UserCreate, UserLogin, UserOut

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Autenticación"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    new_user = User(
        username=user.username,
        email=user.email,
        password=get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Buscamos al usuario
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user:
        print(f"❌ Intento de login fallido: {user_credentials.username}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=403, detail="Contraseña incorrecta")
    
    return {"mensaje": "Login exitoso", "usuario": user.username}