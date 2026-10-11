from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime


class AnalyticsService:
    def __init__(self, connect, *, production: bool = False):
        self._connect = connect
        self._production = production

    def get_summary(self) -> dict[str, object]:
        with closing(self._connect()) as connection:
            total_profiles = connection.execute("SELECT COUNT(*) AS total FROM profiles").fetchone()["total"]
            total_cashiers = connection.execute("SELECT COUNT(*) AS total FROM cashier_users WHERE active = 1").fetchone()["total"]
            total_validations = connection.execute("SELECT COUNT(*) AS total FROM coupon_validations").fetchone()["total"]
            successful_validations = connection.execute("SELECT COUNT(*) AS total FROM coupon_validations WHERE status = 'success'").fetchone()["total"]
            failed_validations = connection.execute("SELECT COUNT(*) AS total FROM coupon_validations WHERE status = 'failed'").fetchone()["total"]
            redeemed_coupons = connection.execute("SELECT COUNT(*) AS total FROM coupons WHERE status = 'redeemed'").fetchone()["total"]
            active_coupons = connection.execute("SELECT COUNT(*) AS total FROM coupons WHERE status = 'active'").fetchone()["total"]
            validation_breakdown = connection.execute(
                "SELECT merchant_id, COUNT(*) AS total FROM coupon_validations WHERE merchant_id IS NOT NULL GROUP BY merchant_id ORDER BY total DESC LIMIT 8"
            ).fetchall()
            merchant_rows = connection.execute(
                "SELECT id, name, is_demo FROM merchants ORDER BY is_demo ASC, name ASC"
            ).fetchall()
            recent_validations = connection.execute(
                "SELECT code, status, validated_at, merchant_id, cashier_id FROM coupon_validations ORDER BY validated_at DESC LIMIT 10"
            ).fetchall()

        merchants = []
        for row in merchant_rows:
            merchants.append({
                "id": row["id"],
                "name": row["name"],
                "is_demo": bool(row["is_demo"]),
                "total_validations": next((item["total"] for item in validation_breakdown if item["merchant_id"] == row["id"]), 0),
            })

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_profiles": total_profiles,
                "total_cashiers": total_cashiers,
                "total_validations": total_validations,
                "successful_validations": successful_validations,
                "failed_validations": failed_validations,
                "redeemed_coupons": redeemed_coupons,
                "active_coupons": active_coupons,
                "production": self._production,
            },
            "merchants": merchants,
            "recent_validations": [
                {
                    "code": row["code"],
                    "status": row["status"],
                    "validated_at": row["validated_at"],
                    "merchant_id": row["merchant_id"],
                    "cashier_id": row["cashier_id"],
                }
                for row in recent_validations
            ],
        }
