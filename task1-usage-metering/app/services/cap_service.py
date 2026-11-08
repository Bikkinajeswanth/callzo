from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.usage_cap import UsageCap
from app.models.monthly_usage import MonthlyUsage
from app.schemas.cap import UsageCapUpdate, UsageCapResponse


class CapService:
    @staticmethod
    def get_account_cap(db: Session, account_id: str) -> Optional[UsageCapResponse]:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None

        cap = db.query(UsageCap).filter(UsageCap.account_id == account_id).first()
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        cur_usage = (
            db.query(MonthlyUsage)
            .filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == current_month)
            .first()
        )

        cur_sec = cur_usage.total_duration_seconds if cur_usage else 0
        cur_cost = cur_usage.total_cost_cents if cur_usage else 0
        cur_minutes = int(cur_sec / 60)

        min_cap = cap.monthly_minutes_cap if cap else None
        cost_cap = cap.monthly_cost_cents_cap if cap else None
        is_hard = cap.is_hard_cap if cap else True
        action = cap.cap_action if cap else "flag_exceeded"

        min_pct = round((cur_minutes / min_cap) * 100, 1) if min_cap and min_cap > 0 else None
        cost_pct = round((cur_cost / cost_cap) * 100, 1) if cost_cap and cost_cap > 0 else None

        breached = bool((min_cap and cur_minutes > min_cap) or (cost_cap and cur_cost > cost_cap))

        return UsageCapResponse(
            account_id=account_id,
            monthly_minutes_cap=min_cap,
            monthly_cost_cents_cap=cost_cap,
            is_hard_cap=is_hard,
            cap_action=action,
            current_month_minutes=cur_minutes,
            current_month_cost_cents=cur_cost,
            minutes_utilization_pct=min_pct,
            cost_utilization_pct=cost_pct,
            cap_breached=breached
        )

    @staticmethod
    def update_account_cap(db: Session, account_id: str, cap_in: UsageCapUpdate) -> UsageCapResponse:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            # Auto-provision account if updating cap
            account = Account(
                id=account_id,
                name=f"Account {account_id}",
                email=f"{account_id}@callzo-customer.io",
                country="US",
                plan="pro",
                status="active"
            )
            db.add(account)
            db.flush()

        cap = db.query(UsageCap).filter(UsageCap.account_id == account_id).first()
        if not cap:
            cap = UsageCap(
                account_id=account_id,
                monthly_minutes_cap=cap_in.monthly_minutes_cap,
                monthly_cost_cents_cap=cap_in.monthly_cost_cents_cap,
                is_hard_cap=cap_in.is_hard_cap,
                cap_action=cap_in.cap_action
            )
            db.add(cap)
        else:
            cap.monthly_minutes_cap = cap_in.monthly_minutes_cap
            cap.monthly_cost_cents_cap = cap_in.monthly_cost_cents_cap
            cap.is_hard_cap = cap_in.is_hard_cap
            cap.cap_action = cap_in.cap_action

        db.commit()
        db.refresh(cap)

        return CapService.get_account_cap(db, account_id)
