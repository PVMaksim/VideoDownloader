"""Database models for VideoGrab"""
import enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum, Text, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Plan(str, enum.Enum):
    FREE = "free"
    PRO  = "pro"


class DownloadStatus(str, enum.Enum):
    QUEUED      = "queued"
    DOWNLOADING = "downloading"
    READY       = "ready"
    ERROR       = "error"


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan          = Column(Enum(Plan), default=Plan.FREE, nullable=False)

    # Email верификация
    is_verified       = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True, index=True)

    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    downloads = relationship("Download", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.email} verified={self.is_verified}>"


class Download(Base):
    __tablename__ = "downloads"

    id      = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    task_id  = Column(String(36), unique=True, index=True, nullable=False)
    status   = Column(Enum(DownloadStatus), default=DownloadStatus.QUEUED)
    progress = Column(Integer, default=0)

    video_url = Column(Text, nullable=False)
    title     = Column(String(500))
    filename  = Column(String(500))
    height    = Column(Integer)
    platform  = Column(String(50))

    error_message = Column(Text)
    created_at    = Column(DateTime, default=func.now())
    updated_at    = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="downloads")
