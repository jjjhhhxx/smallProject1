from sqlalchemy import BigInteger, DateTime, String, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text
from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ELDER / CHILD
    role: Mapped[str] = mapped_column(String(16), nullable=False)

    # 微信小程序用户标识（openid）
    wx_openid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[str] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        Index("idx_users_role", "role"),
    )
