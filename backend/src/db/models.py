import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class DownloadStatus(enum.StrEnum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    READY = "ready"
    ERROR = "error"

class Plan(enum.StrEnum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"

class User(Base):
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(nullable=True)
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[Plan] = mapped_column(Enum(Plan, values_callable=lambda x: [e.value for e in x]), default=Plan.FREE, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(50), default=None, nullable=True)
    subscription_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    downloads = relationship("Download", back_populates="user", lazy="dynamic")

class Download(Base):
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    task_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    status: Mapped[DownloadStatus] = mapped_column(Enum(DownloadStatus, values_callable=lambda x: [e.value for e in x]), default=DownloadStatus.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)

    video_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    filename: Mapped[str | None] = mapped_column(String(500))
    height: Mapped[int | None] = mapped_column(Integer)
    platform: Mapped[str | None] = mapped_column(String(50))

    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="downloads")
