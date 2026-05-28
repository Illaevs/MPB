"""
TreasuryTransaction model - Банковские транзакции (выписки)
"""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, String, DateTime, Date, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class TreasuryTransaction(Base):
    __tablename__ = "treasury_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Идентификация платежа
    doc_num = Column(String(100), nullable=False)  # Номер ПП
    transaction_date = Column(Date, nullable=False, index=True)

    # Сумма
    amount = Column(Float, nullable=False)

    calc_type = Column(String(50), default="vtb")

    # Контрагенты
    payer_inn = Column(String(12), index=True)     # ИНН плательщика
    payee_inn = Column(String(12), index=True)     # ИНН получателя
    payer_name = Column(String(255))              # Наименование плательщика
    payee_name = Column(String(255))              # Наименование получателя

    # Назначение платежа
    purpose = Column(Text)

    # Категория (код/название в одном поле)
    category_code = Column(String(255))

    # Связь с доходами/расходами
    income_expense_id = Column(String(36), ForeignKey("income_expense_entries.id"))

    # Флаг "не учитывать"
    ignore_flag = Column(String(10), default="Нет")

    # ID применённого правила автораспределения (для индикации автозаполнения)
    auto_rule_id = Column(String(36), nullable=True)

    # Не распределенный остаток (для сплитования платежей)
    remainder = Column(Float, default=0.0)

    # Привязка к другому платежу (возвраты/зачёты)
    linked_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_transactions.id"), nullable=True)

    # Статус обработки
    processed = Column(String(50), default="pending")  # pending, processed, error

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TreasuryTransaction(id={self.id}, doc_num='{self.doc_num}', amount={self.amount})>"

