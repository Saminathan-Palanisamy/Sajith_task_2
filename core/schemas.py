from core.models import UserRole
import enum
from pydantic import BaseModel, EmailStr
from typing import Optional, Any

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
    model_config = {
        "from_attributes": True 
    }

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    model_config = {
        "from_attributes": True 
    }    

class Token_Data(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(BaseModel):
    user: UserOut
    token: Token_Data
    status: str
    message: str

    model_config = {
        "from_attributes": True 
    }


#-------template schema models
class TemplateCreate(BaseModel):
    Temp_name: str
    Temp_desc: str
    created_by: int

class TemplateData(BaseModel):
    temp_id: int
    Temp_name: str
    Temp_desc: str
    created_by: int

    model_config = {"from_attributes": True}

class TemplateRead(BaseModel):
    status: str
    message: str
    data: TemplateData

    model_config = {
        "from_attributes": True
    }

#-------section schema models
class SectionCreate(BaseModel):
    section_name: str
    section_desc: str
    template_id: int

class SectionData(BaseModel):
    section_id: int
    section_name: str
    section_desc: str
    template_id: int

    model_config = {"from_attributes": True}

class SectionRead(BaseModel):
    status: str
    message: str
    data: SectionData

    model_config = {
        "from_attributes": True
    }
