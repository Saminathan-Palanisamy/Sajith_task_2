import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, UniqueConstraint, Boolean, DateTime, text, JSON, func
from datetime import datetime
from core.database import Base
from sqlalchemy.orm import relationship


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

    sessions = relationship("Authenticator", back_populates="user")
    documents = relationship("Document", back_populates="user")



#---new template model
class Template(Base):
    __tablename__ = "templates"

    temp_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Temp_name = Column(String, unique=True, index=True, nullable=False)
    Temp_desc = Column(Text, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    documents = relationship("Document", back_populates="template")

#---new section model
class Section(Base):
    __tablename__ = "sections"

    section_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    section_name = Column(String, unique=True, index=True, nullable=False)
    section_desc = Column(Text, nullable=False)
    template_id = Column(Integer, ForeignKey("templates.temp_id"), nullable=False)
    order = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint('template_id', 'order', name='unique_template_order'),
    )

# Authenticator table for user's tracking
class Authenticator(Base):
    __tablename__ = "authentication"

    authenticator_id=Column(Integer,primary_key=True, index= True, autoincrement= True)
    User_id= Column(Integer,ForeignKey("users.id"),nullable=False)
    Token = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, server_default=text('true'))
    Login_time = Column(DateTime)
    Logout_time = Column(DateTime)
    Session_duration = Column(Integer)

    user=relationship("User", back_populates="sessions")
    

# creating table for documents
class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("templates.temp_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)            # original filename (not required unique)
    file_path = Column(String, nullable=False)            # stored relative path
    uploaded_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    parsed_content = Column(JSON, nullable=True)          # store parsed JSON
    markdown_content = Column(Text, nullable=True)        # store markdown text
    is_active = Column(Boolean, default=True, server_default=text('true'))

    user = relationship("User", back_populates="documents")
    template = relationship("Template", back_populates="documents")


#creating table for storing the records of hit results on words matcher
class WordsMatcher(Base):
    __tablename__ = "words_matcher"

    word_matcher_id = Column(Integer, primary_key=True, index=True)
    temp_id = Column(Integer, ForeignKey("templates.temp_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hit_time = Column(DateTime(timezone=True), server_default=func.now())

    list_to_search = Column(JSON, nullable=False)

    result = Column(JSON, nullable=False)

    count_within_list = Column(Integer, nullable=False, default=0)
    count_not_found = Column(Integer, nullable=False, default=0)
    status_of_matching = Column(String, nullable=False, default="Pending")

    template = relationship("Template", backref="word_matches")
    document = relationship("Document", backref="word_matches")
    user = relationship("User", backref="word_matches")