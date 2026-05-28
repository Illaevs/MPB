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

    cur.execute("SELECT id FROM deals ORDER BY created_at")
    deals = [row[0] for row in cur.fetchall()]
    if not deals:
        print("No deals found.")
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

    random.seed(2024)

    for deal_id in deals:
        cur.execute("SELECT COUNT(*) FROM stages WHERE deal_id = ?", (deal_id,))
        stage_count = cur.fetchone()[0]
        stage_ids = []
        if stage_count == 0:
            for idx in range(3):
                stage_id = _uuid()
                stage_ids.append(stage_id)
                start_offset = 10 + idx * 25
                duration = 20 + idx * 5
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
                        f"Seed Stage {idx + 1}",
                        "stage",
                        "work_days",
                        _date(start_offset),
                        duration,
                        _date(start_offset + duration),
                        450_000 + idx * 120_000,
                        "planned",
                        0,
                    ),
                )
        else:
            cur.execute("SELECT id FROM stages WHERE deal_id = ?", (deal_id,))
            stage_ids = [row[0] for row in cur.fetchall()]

        cur.execute("SELECT COUNT(*) FROM deal_products WHERE deal_id = ?", (deal_id,))
        product_count = cur.fetchone()[0]
        deal_products = []
        if product_count == 0:
            for prod_id in random.sample(products, min(5, len(products))):
                dp_id = _uuid()
                qty = random.randint(1, 2)
                unit_price = random.randint(90_000, 170_000)
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
        else:
            cur.execute("SELECT id, product_id FROM deal_products WHERE deal_id = ?", (deal_id,))
            deal_products = [(row[0], row[1]) for row in cur.fetchall()]

        cur.execute("SELECT COUNT(*) FROM stage_product_links WHERE deal_id = ?", (deal_id,))
        if cur.fetchone()[0] == 0:
            for dp_id, _prod_id in deal_products:
                stage_id = random.choice(stage_ids)
                cur.execute(
                    """
                    INSERT INTO stage_product_links (id, deal_id, stage_id, deal_product_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (_uuid(), deal_id, stage_id, dp_id),
                )

        cur.execute(
            "SELECT id FROM contracts WHERE deal_id = ? AND contract_type = 'general_contractor' LIMIT 1",
            (deal_id,),
        )
        row = cur.fetchone()
        if row:
            general_contract_id = row[0]
        else:
            general_contract_id = _uuid()
            cur.execute(
                """
                INSERT INTO contracts (
                    id, contract_number, contract_date, status, amount,
                    contract_type, customer_id, executor_id, deal_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    general_contract_id,
                    f"SEED-GEN-{deal_id[:4]}",
                    _date(-30),
                    "in_progress",
                    2_200_000,
                    "general_contractor",
                    our_company_id,
                    our_company_id,
                    deal_id,
                ),
            )

        cur.execute(
            "SELECT COUNT(*) FROM contract_documents WHERE contract_id = ?",
            (general_contract_id,),
        )
        if cur.fetchone()[0] == 0:
            for idx, doc_type in enumerate(["contract", "addendum", "act", "waybill"], start=1):
                cur.execute(
                    """
                    INSERT INTO contract_documents (
                        id, contract_id, doc_type, number_in_contract, status
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (_uuid(), general_contract_id, doc_type, idx, "signed"),
                )

        cur.execute(
            "SELECT COUNT(*) FROM contracts WHERE deal_id = ? AND subcontractor_card_id IS NOT NULL",
            (deal_id,),
        )
        subcontractor_contracts = []
        if cur.fetchone()[0] == 0:
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
                            f"Seed Subcard {company_id[:6]}",
                            f"Seed Sub Object {deal_id[:6]}",
                            "Seed subcontract address",
                            "office",
                            520,
                            "active",
                            our_company_id,
                            our_company_id,
                            company_id,
                        ),
                    )

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
                        f"SEED-SUB-{deal_id[:4]}-{card_id[:4]}",
                        _date(-18),
                        "in_progress",
                        750_000,
                        "subcontractor",
                        our_company_id,
                        company_id,
                        deal_id,
                        card_id,
                    ),
                )
                subcontractor_contracts.append((contract_id, card_id, company_id))

                for idx, doc_type in enumerate(["contract", "addendum", "act"], start=1):
                    cur.execute(
                        """
                        INSERT INTO contract_documents (
                            id, contract_id, doc_type, number_in_contract, status
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (_uuid(), contract_id, doc_type, idx, "signed"),
                    )
        else:
            cur.execute(
                "SELECT id, subcontractor_card_id, executor_id FROM contracts WHERE deal_id = ? AND subcontractor_card_id IS NOT NULL",
                (deal_id,),
            )
            subcontractor_contracts = [(row[0], row[1], row[2]) for row in cur.fetchall()]

        for contract_id, card_id, _company_id in subcontractor_contracts:
            cur.execute(
                "SELECT COUNT(*) FROM subcontractor_stages WHERE contract_id = ?",
                (contract_id,),
            )
            if cur.fetchone()[0] == 0:
                for idx in range(2):
                    cur.execute(
                        """
                        INSERT INTO subcontractor_stages (
                            id, subcontractor_card_id, name, date_start, duration,
                            date_end, status, contract_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            _uuid(),
                            card_id,
                            f"Seed Sub Stage {idx + 1}",
                            _date(idx * 15),
                            15 + idx * 5,
                            _date(idx * 15 + 15 + idx * 5),
                            "planned",
                            contract_id,
                        ),
                    )

            cur.execute(
                "SELECT COUNT(*) FROM subcontractor_products WHERE contract_id = ?",
                (contract_id,),
            )
            if cur.fetchone()[0] == 0:
                for _dp_id, prod_id in deal_products[:2]:
                    cur.execute(
                        """
                        INSERT INTO subcontractor_products (
                            id, subcontractor_card_id, product_id, unit_price, status, contract_id
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            _uuid(),
                            card_id,
                            prod_id,
                            random.randint(85_000, 140_000),
                            "planned",
                            contract_id,
                        ),
                    )

        cur.execute(
            "SELECT COUNT(*) FROM stage_product_assignments WHERE deal_id = ?",
            (deal_id,),
        )
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT id, product_id FROM deal_products WHERE deal_id = ?", (deal_id,))
            deal_products_rows = cur.fetchall()
            cur.execute("SELECT id, stage_id, deal_product_id FROM stage_product_links WHERE deal_id = ?", (deal_id,))
            links = cur.fetchall()
            cur.execute(
                "SELECT id, subcontractor_card_id, contract_id, product_id FROM subcontractor_products WHERE subcontractor_card_id IS NOT NULL"
            )
            subprod_rows = cur.fetchall()
            subprod_by_product = {}
            for row in subprod_rows:
                subprod_by_product.setdefault(row["product_id"], []).append(row)

            for link in links:
                dp_id = link["deal_product_id"]
                stage_id = link["stage_id"]
                product_id = next((row["product_id"] for row in deal_products_rows if row["id"] == dp_id), None)
                if not product_id:
                    continue
                candidates = subprod_by_product.get(product_id) or subprod_rows
                if not candidates:
                    continue
                sub = random.choice(candidates)
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
                        product_id,
                        sub["subcontractor_card_id"],
                        sub["id"],
                        sub["contract_id"],
                        _date(90),
                        "in_progress",
                    ),
                )
                for s_idx in range(2):
                    cur.execute(
                        """
                        INSERT INTO stage_product_subtasks (
                            id, assignment_id, title, due_date, status
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            _uuid(),
                            assignment_id,
                            f"Seed Exec Task {s_idx + 1}",
                            _date(30 + s_idx * 7),
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
                        sub["subcontractor_card_id"],
                        deal_id,
                        "Seed Result",
                        "v1",
                        "Seed execution result",
                        "/seed/execution/result_auto.pdf",
                    ),
                )

    conn.commit()
    conn.close()
    print("Deals backfilled with stages, products, contracting, execution, and contracts.")


if __name__ == "__main__":
    main()
