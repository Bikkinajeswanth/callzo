from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.account import Account
from app.models.call import Call
from app.models.monthly_usage import MonthlyUsage
from app.models.usage_cap import UsageCap
from app.schemas.usage import UsageOverviewResponse, MonthlyUsageRecord, CallRecord
from app.schemas.cap import UsageCapResponse


def format_currency(cents: int) -> str:
    dollars = cents / 100.0
    return f"${dollars:,.2f}"


class UsageService:
    @staticmethod
    def get_account_overview(db: Session, account_id: str) -> Optional[UsageOverviewResponse]:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None

        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        cur_usage = (
            db.query(MonthlyUsage)
            .filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == current_month)
            .first()
        )

        cur_calls = cur_usage.total_calls if cur_usage else 0
        cur_duration_sec = cur_usage.total_duration_seconds if cur_usage else 0
        cur_cost = cur_usage.total_cost_cents if cur_usage else 0

        # Lifetime aggregates
        lifetime = (
            db.query(
                func.coalesce(func.sum(MonthlyUsage.total_calls), 0),
                func.coalesce(func.sum(MonthlyUsage.total_duration_seconds), 0),
                func.coalesce(func.sum(MonthlyUsage.total_cost_cents), 0)
            )
            .filter(MonthlyUsage.account_id == account_id)
            .first()
        )

        life_calls = lifetime[0]
        life_duration_sec = lifetime[1]
        life_cost = lifetime[2]

        # Cap info
        cap = db.query(UsageCap).filter(UsageCap.account_id == account_id).first()
        cap_status = "ok"
        cap_details = None

        if cap:
            cur_minutes = cur_duration_sec / 60.0
            min_breached = bool(cap.monthly_minutes_cap and cur_minutes > cap.monthly_minutes_cap)
            cost_breached = bool(cap.monthly_cost_cents_cap and cur_cost > cap.monthly_cost_cents_cap)

            if min_breached or cost_breached:
                cap_status = "hard_limit_exceeded" if cap.is_hard_cap else "soft_limit_exceeded"

            cap_details = {
                "monthly_minutes_cap": cap.monthly_minutes_cap,
                "monthly_cost_cents_cap": cap.monthly_cost_cents_cap,
                "is_hard_cap": cap.is_hard_cap,
                "minutes_utilization_pct": round((cur_minutes / cap.monthly_minutes_cap) * 100, 1) if cap.monthly_minutes_cap else None,
                "cost_utilization_pct": round((cur_cost / cap.monthly_cost_cents_cap) * 100, 1) if cap.monthly_cost_cents_cap else None
            }

        return UsageOverviewResponse(
            account_id=account.id,
            account_name=account.name,
            account_status=account.status,
            current_month=current_month,
            current_month_calls=cur_calls,
            current_month_minutes=round(cur_duration_sec / 60.0, 2),
            current_month_cost_cents=cur_cost,
            current_month_cost_formatted=format_currency(cur_cost),
            lifetime_calls=life_calls,
            lifetime_minutes=round(life_duration_sec / 60.0, 2),
            lifetime_cost_cents=life_cost,
            lifetime_cost_formatted=format_currency(life_cost),
            cap_status=cap_status,
            cap_details=cap_details
        )

    @staticmethod
    def get_monthly_usage(db: Session, account_id: str, year_month: Optional[str] = None) -> List[MonthlyUsageRecord]:
        query = db.query(MonthlyUsage).filter(MonthlyUsage.account_id == account_id)
        if year_month:
            query = query.filter(MonthlyUsage.year_month == year_month)

        records = query.order_by(MonthlyUsage.year_month.desc()).all()

        return [
            MonthlyUsageRecord(
                account_id=r.account_id,
                year_month=r.year_month,
                total_calls=r.total_calls,
                total_duration_seconds=r.total_duration_seconds,
                total_duration_minutes=round(r.total_duration_seconds / 60.0, 2),
                total_cost_cents=r.total_cost_cents,
                total_cost_formatted=format_currency(r.total_cost_cents),
                updated_at=r.updated_at
            )
            for r in records
        ]

    @staticmethod
    def get_calls_history(
        db: Session,
        account_id: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        destination_country: Optional[str] = None
    ) -> Tuple[List[CallRecord], int]:
        query = db.query(Call).filter(Call.account_id == account_id)

        if status:
            query = query.filter(Call.status == status)
        if destination_country:
            query = query.filter(Call.destination_country == destination_country.upper())

        total_count = query.count()
        calls = (
            query.order_by(Call.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        records = [
            CallRecord(
                call_id=c.call_id,
                account_id=c.account_id,
                status=c.status,
                started_at=c.started_at,
                ended_at=c.ended_at,
                duration_seconds=c.duration_seconds,
                cost_cents=c.cost_cents,
                destination_country=c.destination_country,
                created_at=c.created_at
            )
            for c in calls
        ]

        return records, total_count
