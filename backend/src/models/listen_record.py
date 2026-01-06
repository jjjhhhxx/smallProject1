from sqlalchemy import BigInteger, DateTime, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text
from db.base import Base

class ListenRecord(Base):
    __tablename__ = "listen_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    elder_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    context: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="PENDING")

    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[str] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )


    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    summary_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default="PENDING",
    )

    summary_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)


    __table_args__ = (
        Index("idx_elder_time", "elder_id", "created_at"),
        Index("idx_status", "status"),
        Index("idx_summary_status", "summary_status"),
    )
