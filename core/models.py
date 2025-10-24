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
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, index=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    contact_number = Column(String, unique=True, index=True, nullable=False)