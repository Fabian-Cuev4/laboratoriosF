from pydantic import BaseModel, EmailStr

# Lo que el usuario envía para REGISTRARSE
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Lo que el usuario envía para LOGUEARSE
class UserLogin(BaseModel):
    username: str
    password: str

# Lo que le devolvemos al usuario (sin la contraseña)
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True