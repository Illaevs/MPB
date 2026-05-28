import random
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path


def _uuid() -> str:
    return str(uuid.uuid4())


def _date(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id FROM deals WHERE title LIKE 'SEED Deal %' ORDER BY title")
    deals = [row[0] for row in cur.fetchall()]
    if not deals:
        print("No SEED deals found. Run seed_test_data.py first.")
        return

    cur.execute("SELECT 1 FROM stages WHERE name LIKE 'SEED Added Stage B %' LIMIT 1")
    if cur.fetchone():
        print("Additional deal seed already present. Skipping.")
        return

    cur.execute("SELECT id FROM companies WHERE type = 'internal' ORDER BY name LIMIT 1")
    row = cur.fetchone()
    if not row:
        print("No internal company found.")
        return
    our_company_id = row[0]

    cur.execute("SELECT id FROM companies WHERE type = 'subcontractor' ORDER BY name")
    subcontractors = [row[0] for row in cur.fetchall()]
    cur.execute("SELECT id FROM products ORDER BY name")
    products = [row[0] for row in cur.fetchall()]

    if not subcontractors or not products:
        print("Missing subcontractors or products.")
        return

    random.seed(126)

    for deal_index, deal_id in enumerate(deals, start=1):
        stage_ids = []
        for stage_index in range(2):
            stage_id = _uuid()
            stage_ids.append(stage_id)
            stage_name = f"SEED Added Stage B {deal_index}-{stage_index + 1}"
            start_offset = 90 + stage_index * 25 + deal_index * 4
            duration = 25 + stage_index * 8
            cur.execute(
                """
                INSERT INTO stages (
                    id, deal_id, name, stage_type, term_type, date_start, duration,
                    date_end, planned_cost, status, is_closed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stage_id,
                    deal_id,
                    stage_name,
                    "stage",
                    "work_days",
                    _date(start_offset),
                    duration,
                    _date(start_offset + duration),
                    520_000 + stage_index * 110_000,
                    "planned",
                    0,
                ),
            )

        deal_products = []
        for prod_id in random.sample(products, 5):
            dp_id = _uuid()
            qty = random.randint(1, 2)
            unit_price = random.randint(95_000, 175_000)
            total = qty * unit_price
            cur.execute(
                """
                INSERT INTO deal_products (
                    id, deal_id, product_id, quantity, unit_price, total_price,
                    final_price, tax_rate, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dp_id,
                    deal_id,
                    prod_id,
                    qty,
                    unit_price,
                    total,
                    total,
                    20.0,
                    "planned",
                ),
            )
            deal_products.append((dp_id, prod_id))

        for dp_id, _prod_id in deal_products:
            stage_id = random.choice(stage_ids)
            cur.execute(
                """
                INSERT INTO stage_product_links (id, deal_id, stage_id, deal_product_id)
                VALUES (?, ?, ?, ?)
                """,
                (_uuid(), deal_id, stage_id, dp_id),
            )

        linked_cards = []
        for company_id in random.sample(subcontractors, min(2, len(subcontractors))):
            cur.execute(
                "SELECT id FROM subcontractor_cards WHERE company_id = ? ORDER BY created_at LIMIT 1",
                (company_id,),
            )
            card_row = cur.fetchone()
            if card_row:
                card_id = card_row[0]
            else:
                card_id = _uuid()
                cur.execute(
                    """
                    INSERT INTO subcontractor_cards (
                        id, title, obj_name, address, object_type, object_area, status,
                        customer_id, general_contractor_id, company_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        card_id,
                        f"SEED Card {company_id[:6]}",
                        f"SEED Contracting {deal_id[:6]}",
                        "Seed subcontract address",
                        "office",
                        640,
                        "active",
                        our_company_id,
                        our_company_id,
                        company_id,
                    ),
                )
            linked_cards.append((card_id, company_id))

        for card_id, company_id in linked_cards:
            cur.execute(
                "SELECT id FROM contracts WHERE subcontractor_card_id = ? LIMIT 1",
                (card_id,),
            )
            contract_row = cur.fetchone()
            if contract_row:
                contract_id = contract_row[0]
            else:
                contract_id = _uuid()
                cur.execute(
                    """
                    INSERT INTO contracts (
                        id, contract_number, contract_date, status, amount,
                        contract_type, customer_id, executor_id, deal_id, subcontractor_card_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        contract_id,
                        f"SEED-SUBX-{deal_id[:4]}-{card_id[:4]}",
                        _date(-12),
                    "in_progress",
                        780_000,
                        "subcontractor",
                        our_company_id,
                        company_id,
                        deal_id,
                        card_id,
                    ),
                )

            cur.execute(
                "SELECT COALESCE(MAX(number_in_contract), 0) FROM contract_documents WHERE contract_id = ?",
                (contract_id,),
            )
            start_num = (cur.fetchone()[0] or 0) + 1
            for doc_offset, doc_type in enumerate(["contract", "addendum", "act", "waybill"], start=start_num):
                cur.execute(
                    """
                    INSERT INTO contract_documents (
                        id, contract_id, doc_type, number_in_contract, status
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (_uuid(), contract_id, doc_type, doc_offset, "signed"),
                )

        cur.execute(
            "SELECT id FROM contracts WHERE deal_id = ? AND contract_type = 'general_contractor' LIMIT 1",
            (deal_id,),
        )
        gen_row = cur.fetchone()
        if gen_row:
            gen_contract_id = gen_row[0]
            cur.execute(
                "SELECT COALESCE(MAX(number_in_contract), 0) FROM contract_documents WHERE contract_id = ?",
                (gen_contract_id,),
            )
            start_num = (cur.fetchone()[0] or 0) + 1
            for doc_offset, doc_type in enumerate(["addendum", "act"], start=start_num):
                cur.execute(
                    """
                    INSERT INTO contract_documents (
                        id, contract_id, doc_type, number_in_contract, status
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (_uuid(), gen_contract_id, doc_type, doc_offset, "signed"),
                )

        for dp_id, prod_id in deal_products:
            stage_id = random.choice(stage_ids)
            card_id, _company_id = random.choice(linked_cards)
            cur.execute(
                """
                SELECT id FROM subcontractor_products
                WHERE subcontractor_card_id = ? AND product_id = ?
                """,
                (card_id, prod_id),
            )
            sp_row = cur.fetchone()
            if sp_row:
                sp_id = sp_row[0]
            else:
                cur.execute(
                    "SELECT id FROM contracts WHERE subcontractor_card_id = ? LIMIT 1",
                    (card_id,),
                )
                contract_row = cur.fetchone()
                contract_id = contract_row[0] if contract_row else None
                sp_id = _uuid()
                cur.execute(
                    """
                    INSERT INTO subcontractor_products (
                        id, subcontractor_card_id, product_id, unit_price, status, contract_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sp_id,
                        card_id,
                        prod_id,
                        random.randint(80_000, 140_000),
                        "planned",
                        contract_id,
                    ),
                )

            assignment_id = _uuid()
            cur.execute(
                """
                INSERT INTO stage_product_assignments (
                    id, deal_id, stage_id, product_id, subcontractor_card_id,
                    subcontractor_product_id, contract_id, due_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment_id,
                    deal_id,
                    stage_id,
                    prod_id,
                    card_id,
                    sp_id,
                    contract_id,
                    _date(120),
                    "in_progress",
                ),
            )

            for sub_index in range(2):
                cur.execute(
                    """
                    INSERT INTO stage_product_subtasks (
                        id, assignment_id, title, due_date, status
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        _uuid(),
                        assignment_id,
                        f"SEED Exec Subtask {sub_index + 1}",
                        _date(45 + sub_index * 10),
                        "not_started",
                    ),
                )

            cur.execute(
                """
                INSERT INTO stage_results (
                    id, stage_id, subcontractor_card_id, deal_id, product_name,
                    version_label, comment, yandex_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    stage_id,
                    card_id,
                    deal_id,
                    "SEED Exec Result B",
                    "v3",
                    "Seed execution result B",
                    "/seed/execution/result_b.pdf",
                ),
            )

    conn.commit()
    conn.close()
    print("Extra stages, products, contracting, execution, and contracts inserted.")


if __name__ == "__main__":
    main()
