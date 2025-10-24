from core.models import UserRole
import enum
from pydantic import BaseModel, EmailStr
from typing import Optional

#-------user schema roles enum
class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"

#------user schema roles models
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = None
class UserRead(BaseModel):
    id: int
    username: str
    role: UserRole
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    class Config:
        orm_mode = True