from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.session import Base
import enum


class AgentStatusEnum(enum.Enum):
    PLANNING   = 'planning'
    RETRIEVING = 'retrieving'
    BUILDING   = 'building_context'
    GENERATING = 'generating_code'
    VALIDATING = 'validating'
    COMMITTING = 'committing'
    DONE       = 'done'
    FAILED     = 'failed'


# ── Table 1: Users ─────────────────────────────────────────
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

    repositories = relationship('Repository', back_populates='user')
    sessions     = relationship('Session',    back_populates='user')


# ── Table 2: Repositories ──────────────────────────────────
class Repository(Base):
    __tablename__ = 'repositories'

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    github_repo_id   = Column(Integer, unique=True, nullable=False)
    full_name        = Column(String(500), nullable=False)
    clone_url        = Column(String(500), nullable=False)
    default_branch   = Column(String(100), default='main')
    is_indexed       = Column(Boolean, default=False)
    last_indexed_at  = Column(DateTime, nullable=True)
    created_at       = Column(DateTime, server_default=func.now())

    user        = relationship('User',      back_populates='repositories')
    sessions    = relationship('Session',   back_populates='repository')
    code_chunks = relationship('CodeChunk', back_populates='repository')


# ── Table 3: Sessions ──────────────────────────────────────
class Session(Base):
    __tablename__ = 'sessions'

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(String(36), unique=True, nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey('users.id'), nullable=False)
    repository_id   = Column(Integer, ForeignKey('repositories.id'), nullable=True)
    raw_input       = Column(Text, nullable=False)
    cleaned_intent  = Column(Text, nullable=True)
    status          = Column(Enum(AgentStatusEnum), default=AgentStatusEnum.PLANNING)
    pr_url          = Column(String(500), nullable=True)
    error_message   = Column(Text, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, onupdate=func.now())

    user         = relationship('User',       back_populates='sessions')
    repository   = relationship('Repository', back_populates='sessions')
    agent_states = relationship('AgentState', back_populates='session')


# ── Table 4: Agent States ──────────────────────────────────
class AgentState(Base):
    __tablename__ = 'agent_states'

    id           = Column(Integer, primary_key=True, index=True)
    session_id   = Column(String(36), ForeignKey('sessions.session_id'), nullable=False)
    state_data   = Column(JSON, nullable=False)
    current_node = Column(String(100), nullable=True)
    retry_count  = Column(Integer, default=0)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, onupdate=func.now())

    session = relationship('Session', back_populates='agent_states')


# ── Table 5: Code Chunks (RAG) ─────────────────────────────
class CodeChunk(Base):
    __tablename__ = 'code_chunks'

    id            = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    file_path     = Column(String(1000), nullable=False)
    chunk_type    = Column(String(50), nullable=False)
    chunk_name    = Column(String(255), nullable=True)
    content       = Column(Text, nullable=False)
    start_line    = Column(Integer, nullable=True)
    end_line      = Column(Integer, nullable=True)
    embedding_id  = Column(String(255), nullable=True)
    created_at    = Column(DateTime, server_default=func.now())

    repository = relationship('Repository', back_populates='code_chunks')
