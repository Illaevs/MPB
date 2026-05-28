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

    cur.execute("SELECT 1 FROM stages WHERE name LIKE 'SEED Extra Stage %' LIMIT 1")
    if cur.fetchone():
        print("Extra stage seed already present. Skipping.")
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

    random.seed(84)

    stage_rows = []
    stage_product_rows = []
    deal_product_rows = []

    for d_index, deal_id in enumerate(deals, start=1):
        for s_index in range(2):
            stage_id = _uuid()
            stage_name = f"SEED Extra Stage {d_index}-{s_index + 1}"
            start_offset = 60 + s_index * 20 + d_index * 3
            duration = 25 + s_index * 5
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
                    420_000 + s_index * 90_000,
                    "planned",
                    0,
                ),
            )
            stage_rows.append((stage_id, deal_id))

            for prod_id in random.sample(products, 2):
                dp_id = _uuid()
                qty = 1
                unit_price = random.randint(90_000, 160_000)
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
                deal_product_rows.append((dp_id, deal_id, prod_id))
                cur.execute(
                    """
                    INSERT INTO stage_product_links (id, deal_id, stage_id, deal_product_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (_uuid(), deal_id, stage_id, dp_id),
                )
                stage_product_rows.append((stage_id, deal_id, prod_id))

    deal_cards = {}
    for deal_id in deals:
        deal_cards[deal_id] = []
        for company_id in random.sample(subcontractors, min(2, len(subcontractors))):
            cur.execute(
                "SELECT id FROM subcontractor_cards WHERE company_id = ? LIMIT 1",
                (company_id,),
            )
            row = cur.fetchone()
            if row:
                card_id = row[0]
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
                        f"SEED Extra Subcard {deal_id[:6]}",
                        f"SEED Subcontract Object {deal_id[:6]}",
                        "Seed subcontract address",
                        "office",
                        520,
                        "active",
                        our_company_id,
                        our_company_id,
                        company_id,
                    ),
                )
                for st_index in range(2):
                    cur.execute(
                        """
                        INSERT INTO subcontractor_stages (
                            id, subcontractor_card_id, name, date_start, duration, date_end, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            _uuid(),
                            card_id,
                            f"SEED Sub Stage {st_index + 1}",
                            _date(st_index * 15),
                            15 + st_index * 5,
                            _date(st_index * 15 + 15 + st_index * 5),
                            "planned",
                        ),
                    )
            deal_cards[deal_id].append((card_id, company_id))

    subcontractor_contracts = {}
    for deal_id, cards in deal_cards.items():
        for card_id, company_id in cards:
            cur.execute(
                "SELECT id FROM contracts WHERE subcontractor_card_id = ? LIMIT 1",
                (card_id,),
            )
            row = cur.fetchone()
            if row:
                subcontractor_contracts[card_id] = row[0]
                continue
            contract_id = _uuid()
            subcontractor_contracts[card_id] = contract_id
            cur.execute(
                """
                INSERT INTO contracts (
                    id, contract_number, contract_date, status, amount,
                    contract_type, customer_id, executor_id, deal_id, subcontractor_card_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contract_id,
                    f"SEED-SUB-{deal_id[:4]}-{card_id[:4]}",
                    _date(-20),
                    "in_progress",
                    650_000,
                    "subcontractor",
                    our_company_id,
                    company_id,
                    deal_id,
                    card_id,
                ),
            )
            for d_index, doc_type in enumerate(["contract", "addendum", "act"], start=1):
                cur.execute(
                    """
                    INSERT INTO contract_documents (
                        id, contract_id, doc_type, number_in_contract, status
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (_uuid(), contract_id, doc_type, d_index, "signed"),
                )

    for stage_id, deal_id, prod_id in stage_product_rows:
        cards = deal_cards.get(deal_id) or []
        if not cards:
            continue
        card_id, _company_id = random.choice(cards)
        contract_id = subcontractor_contracts.get(card_id)
        cur.execute(
            """
            SELECT id FROM subcontractor_products
            WHERE subcontractor_card_id = ? AND product_id = ?
            """,
            (card_id, prod_id),
        )
        row = cur.fetchone()
        if row:
            sp_id = row[0]
        else:
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
                    random.randint(70_000, 130_000),
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
                _date(90),
                "in_progress",
            ),
        )
        for t_index in range(2):
            cur.execute(
                """
                INSERT INTO stage_product_subtasks (
                    id, assignment_id, title, due_date, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    assignment_id,
                    f"SEED Exec Task {t_index + 1}",
                    _date(30 + t_index * 7),
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
                "SEED Exec Result",
                "v2",
                "Seed execution result",
                "/seed/execution/result.pdf",
            ),
        )

    conn.commit()
    conn.close()
    print("Extra stages, contracting, execution, and contracts inserted.")


if __name__ == "__main__":
    main()
