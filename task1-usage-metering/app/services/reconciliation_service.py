from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.account import Account
from app.models.call import Call
from app.models.monthly_usage import MonthlyUsage
from app.schemas.usage import ReconciliationResponse
from app.core.logging import logger


class ReconciliationService:
    @staticmethod
    def reconcile_monthly_usage(db: Session, account_id: str, year_month: str) -> Optional[ReconciliationResponse]:
        """
        Recomputes actual monthly totals directly from individual Call records and
        reconciles them with the pre-aggregated MonthlyUsage table.
        Safe to run repeatedly (idempotent).
        """
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None

        # Determine datetime bounds for the target year_month (e.g. '2026-11')
        year, month = map(int, year_month.split("-"))
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        start_dt = datetime(year, month, 1, tzinfo=timezone.utc)
        end_dt = datetime(next_year, next_month, 1, tzinfo=timezone.utc)

        # 1. Aggregate from individual Call records
        raw_stats = (
            db.query(
                func.count(Call.id),
                func.coalesce(func.sum(Call.duration_seconds), 0),
                func.coalesce(func.sum(Call.cost_cents), 0)
            )
            .filter(
                Call.account_id == account_id,
                # A call belongs to this month if its start or end time falls within the month
                (
                    (Call.started_at >= start_dt) & (Call.started_at < end_dt) |
                    ((Call.started_at == None) & (Call.ended_at >= start_dt) & (Call.ended_at < end_dt))
                )
            )
            .first()
        )

        calls_raw = raw_stats[0]
        duration_raw = raw_stats[1]
        cost_raw = raw_stats[2]

        # 2. Query stored aggregate
        stored = (
            db.query(MonthlyUsage)
            .filter(MonthlyUsage.account_id == account_id, MonthlyUsage.year_month == year_month)
            .with_for_update()
            .first()
        )

        discrepancy = False
        discrepancy_details = None

        if not stored:
            discrepancy = True
            stored = MonthlyUsage(
                account_id=account_id,
                year_month=year_month,
                total_calls=calls_raw,
                total_duration_seconds=duration_raw,
                total_cost_cents=cost_raw
            )
            db.add(stored)
            discrepancy_details = {
                "reason": "Missing monthly aggregate row created",
                "calls_diff": calls_raw,
                "duration_diff": duration_raw,
                "cost_diff": cost_raw
            }
        else:
            if (
                stored.total_calls != calls_raw or
                stored.total_duration_seconds != duration_raw or
                stored.total_cost_cents != cost_raw
            ):
                discrepancy = True
                discrepancy_details = {
                    "stored_calls": stored.total_calls,
                    "actual_calls": calls_raw,
                    "stored_duration_seconds": stored.total_duration_seconds,
                    "actual_duration_seconds": duration_raw,
                    "stored_cost_cents": stored.total_cost_cents,
                    "actual_cost_cents": cost_raw,
                    "action": "Synchronized aggregate to match raw event totals"
                }

                # Auto-heal stored aggregate to match raw events
                stored.total_calls = calls_raw
                stored.total_duration_seconds = duration_raw
                stored.total_cost_cents = cost_raw

        db.commit()

        logger.info(
            f"Reconciliation completed for account {account_id} month {year_month}. Discrepancy: {discrepancy}",
            extra={"extra_data": {"account_id": account_id, "year_month": year_month, "details": discrepancy_details}}
        )

        return ReconciliationResponse(
            account_id=account_id,
            year_month=year_month,
            reconciled=True,
            calls_count_raw=calls_raw,
            calls_count_aggregated=stored.total_calls,
            duration_seconds_raw=duration_raw,
            duration_seconds_aggregated=stored.total_duration_seconds,
            cost_cents_raw=cost_raw,
            cost_cents_aggregated=stored.total_cost_cents,
            discrepancy_detected=discrepancy,
            discrepancy_details=discrepancy_details
        )
