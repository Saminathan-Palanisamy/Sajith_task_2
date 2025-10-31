from core.models import UserRole
import enum
from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Union


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
    model_config = {
        "from_attributes": True 
    }


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
    data: Optional[TemplateData]= None

    model_config = {
        "from_attributes": True
    }

class TemplateUpdate(BaseModel):
    Temp_name: Optional[str]
    Temp_desc: Optional[str]
    created_by: Optional[int]
    model_config = {
        "from_attributes": True
    }


#-------section schema models
class SectionCreate(BaseModel):
    section_name: str
    section_desc: str
    template_id: int
    order: int

class SectionData(BaseModel):
    section_id: int
    section_name: str
    section_desc: str
    template_id: int
    order: int

    model_config = {"from_attributes": True}

class SectionRead(BaseModel):
    status: str
    message: str
    data: Optional[SectionData]= None

    model_config = {
        "from_attributes": True
    }

class SectionUpdate(BaseModel):
    section_name: Optional[str]
    section_desc: Optional[str]
    template_id: Optional[int]
    order: Optional[int]

    model_config = {
        "from_attributes": True
    }

# --- Pydantic schema for update input
class UpdateDetails(BaseModel):
    name: str
    desc: str

#---------------------------------------

#-- rearranging orders in sections
class SectionReorderItem(BaseModel):
    section_id: int
    new_order: int

class SectionReorderRequest(BaseModel):
    sections: list[SectionReorderItem]
#----------------------------------------
