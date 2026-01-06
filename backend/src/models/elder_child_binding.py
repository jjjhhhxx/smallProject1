from sqlalchemy import BigInteger, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text
from db.base import Base


class ElderChildBinding(Base):
    __tablename__ = "elder_child_bindings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    elder_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    child_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    created_at: Mapped[str] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        UniqueConstraint("elder_id", "child_id", name="uq_elder_child"),
        Index("idx_binding_elder", "elder_id"),
        Index("idx_binding_child", "child_id"),
    )
