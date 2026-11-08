from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class MonthlyUsage(Base):
    """
    Maintains pre-aggregated monthly billing and usage metrics per account.
    Target month is calculated from event.timestamp (format 'YYYY-MM').
    Late events update their appropriate historical month.
    """
    __tablename__ = "monthly_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    year_month = Column(String(7), index=True, nullable=False)  # e.g., '2026-11'
    total_calls = Column(Integer, default=0, nullable=False)
    total_duration_seconds = Column(Integer, default=0, nullable=False)
    total_cost_cents = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    account = relationship("Account", back_populates="monthly_usages")

    __table_args__ = (
        UniqueConstraint("account_id", "year_month", name="uq_account_year_month"),
        Index("ix_monthly_usage_account_month", "account_id", "year_month"),
    )
