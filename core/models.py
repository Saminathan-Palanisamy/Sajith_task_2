import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from core.database import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


#-------user model roles enum
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, index=True, nullable=False)
    password = Column(String, index=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    contact_number = Column(String, unique=True, index=True, nullable=False)


#---new template model
class Template(Base):
    __tablename__ = "templates"

    temp_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Temp_name = Column(String, unique=True, index=True, nullable=False)
    Temp_desc = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

#---new section model
class Section(Base):
    __tablename__ = "sections"


    section_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_name = Column(String, unique=True, index=True, nullable=False)
    section_desc = Column(Text, nullable=False)
    template_id = Column(Integer, ForeignKey("templates.temp_id"), nullable=False)

