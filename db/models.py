from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.session import Base


class User(Base):
    __tablename__ = 'users'

    id                     = Column(Integer, primary_key=True, index=True)
    github_id              = Column(Integer, unique=True, nullable=False, index=True)
    github_username        = Column(String(255), nullable=False)
    email                  = Column(String(255), nullable=True)
    avatar_url             = Column(String(500), nullable=True)
    encrypted_github_token = Column(Text, nullable=False)
    is_active              = Column(Boolean, default=True)
    created_at             = Column(DateTime, server_default=func.now())
    updated_at             = Column(DateTime, onupdate=func.now())
