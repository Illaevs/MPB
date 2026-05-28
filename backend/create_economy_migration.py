#!/usr/bin/env python3
"""
Migration script to add economy-related tables.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from sqlalchemy import text
from app.database.session import async_session


TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS inflation_index (
        id UUID PRIMARY KEY,
        period VARCHAR(7) NOT NULL,
        value FLOAT DEFAULT 1.0,
        note VARCHAR(255),
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS overheads (
        id UUID PRIMARY KEY,
        period VARCHAR(7) NOT NULL,
        amount FLOAT DEFAULT 0.0,
        category VARCHAR(100),
        source VARCHAR(50),
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS overhead_allocations (
        id UUID PRIMARY KEY,
        deal_id UUID NOT NULL,
        period VARCHAR(7) NOT NULL,
        amount FLOAT DEFAULT 0.0,
        calc_version INTEGER DEFAULT 1,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wip_monthly (
        id UUID PRIMARY KEY,
        deal_id UUID NOT NULL,
        stage_id UUID NOT NULL,
        period VARCHAR(7) NOT NULL,
        base_amount FLOAT DEFAULT 0.0,
        vat_rate FLOAT DEFAULT 20.0,
        vat_amount FLOAT DEFAULT 0.0,
        total_amount FLOAT DEFAULT 0.0,
        is_forecast BOOLEAN DEFAULT 1,
        calc_version INTEGER DEFAULT 1,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS advance_payments (
        id UUID PRIMARY KEY,
        deal_id UUID,
        contract_id UUID,
        amount_total FLOAT DEFAULT 0.0,
        vat_rate FLOAT DEFAULT 20.0,
        remaining_total FLOAT DEFAULT 0.0,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stage_closings (
        id UUID PRIMARY KEY,
        stage_id UUID NOT NULL,
        deal_id UUID NOT NULL,
        contract_id UUID,
        closing_date DATE NOT NULL,
        base_amount FLOAT DEFAULT 0.0,
        vat_rate FLOAT DEFAULT 20.0,
        vat_amount FLOAT DEFAULT 0.0,
        total_amount FLOAT DEFAULT 0.0,
        advance_covered_base FLOAT DEFAULT 0.0,
        advance_covered_vat FLOAT DEFAULT 0.0,
        remaining_base FLOAT DEFAULT 0.0,
        remaining_vat FLOAT DEFAULT 0.0,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pricing_models (
        id UUID PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        base_margin FLOAT DEFAULT 0.0,
        risk_reserve FLOAT DEFAULT 0.0,
        inflation_mode VARCHAR(20) DEFAULT 'auto',
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pricing_quotes (
        id UUID PRIMARY KEY,
        deal_id UUID NOT NULL,
        model_id UUID,
        calc_date DATE NOT NULL,
        base_cost FLOAT DEFAULT 0.0,
        overheads FLOAT DEFAULT 0.0,
        indexed_cost FLOAT DEFAULT 0.0,
        risk FLOAT DEFAULT 0.0,
        margin FLOAT DEFAULT 0.0,
        final_price FLOAT DEFAULT 0.0,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quality_alerts (
        id UUID PRIMARY KEY,
        deal_id UUID NOT NULL,
        alert_type VARCHAR(50) NOT NULL,
        severity VARCHAR(20) DEFAULT 'info',
        message TEXT NOT NULL,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
]


async def main():
    async with async_session() as session:
        try:
            for stmt in TABLES_SQL:
                await session.execute(text(stmt))
            await session.commit()
            print("Economy migration completed successfully!")
        except Exception as exc:
            print(f"Economy migration failed: {exc}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
