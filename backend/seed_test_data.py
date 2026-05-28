import random
import sqlite3
import uuid
from datetime import date, timedelta
from pathlib import Path


def _uuid() -> str:
    return str(uuid.uuid4())


def _date(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def _month_str(days_from_today: int) -> str:
    return (date.today() + timedelta(days=days_from_today)).strftime("%Y-%m")


def main() -> None:
    db_path = Path.cwd() / "crm.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM deals WHERE title LIKE 'SEED %' LIMIT 1")
    if cur.fetchone():
        print("Seed data already present. Skipping.")
        return

    def fetch_ids(sql: str, params=()):
        cur.execute(sql, params)
        return [row[0] for row in cur.fetchall()]

    customers = fetch_ids("SELECT id FROM companies WHERE type = 'customer'")
    subcontractors = fetch_ids("SELECT id FROM companies WHERE type = 'subcontractor'")
    internals = fetch_ids("SELECT id FROM companies WHERE type = 'internal'")
    users = fetch_ids("SELECT id FROM users")
    products = fetch_ids("SELECT id FROM products")
    categories = fetch_ids("SELECT id FROM product_categories")

    if not (customers and subcontractors and internals and users and products and categories):
        print("Missing base data (companies/users/products/categories). Seed aborted.")
        return

    random.seed(42)
    our_company_id = internals[0]

    deals = []
    for idx in range(3):
        deal_id = _uuid()
        deals.append(deal_id)
        cur.execute(
            """
            INSERT INTO deals (
                id, title, obj_name, address, customer_id, general_contractor_id,
                status, total_contract_value, total_paid, object_type, object_area,
                vat_rate, vat_included, our_company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                deal_id,
                f"SEED Deal {idx + 1}",
                f"SEED Object {idx + 1}",
                f"Seed address {idx + 1}",
                random.choice(customers),
                our_company_id,
                "active",
                2_500_000 + idx * 500_000,
                250_000 + idx * 50_000,
                "office",
                1200 + idx * 150,
                20.0,
                1,
                our_company_id,
            ),
        )

    stages = []
    for deal_id in deals:
        for i, name in enumerate(["Stage 1 Design", "Stage 2 Review", "Stage 3 Delivery"]):
            stage_id = _uuid()
            stages.append((stage_id, deal_id))
            start = _date(i * 30)
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
                    name,
                    "stage",
                    "work_days",
                    start,
                    30 + i * 10,
                    _date(i * 30 + 30 + i * 10),
                    600_000 + i * 150_000,
                    "planned",
                    0,
                ),
            )

    deal_products = []
    for deal_id in deals:
        for prod_id in random.sample(products, 4):
            dp_id = _uuid()
            qty = random.randint(1, 3)
            unit_price = random.randint(80_000, 180_000)
            total = qty * unit_price
            deal_products.append((dp_id, deal_id, prod_id))
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

    for dp_id, deal_id, _prod_id in deal_products:
        stage_id = random.choice([s for s, d in stages if d == deal_id])
        cur.execute(
            """
            INSERT INTO stage_product_links (id, deal_id, stage_id, deal_product_id)
            VALUES (?, ?, ?, ?)
            """,
            (_uuid(), deal_id, stage_id, dp_id),
        )

    contracts = []
    for idx, deal_id in enumerate(deals):
        contract_id = _uuid()
        contracts.append(contract_id)
        cur.execute(
            """
            INSERT INTO contracts (
                id, contract_number, contract_date, status, amount,
                contract_type, customer_id, executor_id, deal_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contract_id,
                f"SEED-{100 + idx}",
                _date(-30 + idx * 2),
                "in_progress",
                2_000_000 + idx * 250_000,
                "general_contractor",
                random.choice(customers),
                our_company_id,
                deal_id,
            ),
        )

        for doc_idx, doc_type in enumerate(["contract", "addendum", "act", "waybill"], start=1):
            cur.execute(
                """
                INSERT INTO contract_documents (
                    id, contract_id, doc_type, number_in_contract, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (_uuid(), contract_id, doc_type, doc_idx, "signed"),
            )

    subcontractor_cards = []
    for idx, company_id in enumerate(subcontractors[:2]):
        card_id = _uuid()
        subcontractor_cards.append(card_id)
        cur.execute(
            """
            INSERT INTO subcontractor_cards (
                id, title, obj_name, address, object_type, object_area, status,
                customer_id, general_contractor_id, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card_id,
                f"SEED Subcontractor Card {idx + 1}",
                f"Seed Sub Object {idx + 1}",
                f"Seed Sub Address {idx + 1}",
                "office",
                450 + idx * 50,
                "active",
                random.choice(customers),
                our_company_id,
                company_id,
            ),
        )

    subcontractor_product_map = {}
    for card_id in subcontractor_cards:
        for prod_id in random.sample(products, 2):
            sp_id = _uuid()
            subcontractor_product_map[(card_id, prod_id)] = sp_id
            cur.execute(
                """
                INSERT INTO subcontractor_products (
                    id, subcontractor_card_id, product_id, unit_price, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (sp_id, card_id, prod_id, random.randint(50_000, 120_000), "planned"),
            )

        for i, name in enumerate(["Sub Stage A", "Sub Stage B"]):
            cur.execute(
                """
                INSERT INTO subcontractor_stages (
                    id, subcontractor_card_id, name, date_start, duration, date_end, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    card_id,
                    name,
                    _date(i * 20),
                    20 + i * 5,
                    _date(i * 20 + 20 + i * 5),
                    "planned",
                ),
            )

    assignments = []
    for stage_id, deal_id in stages:
        for prod_id in random.sample(products, 2):
            card_id = random.choice(subcontractor_cards)
            assignment_id = _uuid()
            assignments.append(assignment_id)
            sp_id = subcontractor_product_map.get((card_id, prod_id))
            cur.execute(
                """
                INSERT INTO stage_product_assignments (
                    id, deal_id, stage_id, product_id, subcontractor_card_id,
                    subcontractor_product_id, due_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assignment_id,
                    deal_id,
                    stage_id,
                    prod_id,
                    card_id,
                    sp_id,
                    _date(45),
                    "in_progress",
                ),
            )

    for assignment_id in assignments:
        for i in range(2):
            cur.execute(
                """
                INSERT INTO stage_product_subtasks (
                    id, assignment_id, title, due_date, status
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    assignment_id,
                    f"Subtask {i + 1}",
                    _date(10 + i * 5),
                    "not_started",
                ),
            )

    for stage_id, deal_id in stages[:3]:
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
                random.choice(subcontractor_cards),
                deal_id,
                "Seed Result Product",
                "v1",
                "Seed result file",
                "/seed/results/file.pdf",
            ),
        )

    income_expenses = []
    for deal_id in deals:
        for direction in ["income", "expense", "expense"]:
            entry_id = _uuid()
            income_expenses.append(entry_id)
            payer_id = random.choice(customers) if direction == "income" else our_company_id
            payee_id = our_company_id if direction == "income" else random.choice(subcontractors)
            category_code = "01.01" if direction == "income" else "2.3.1"
            amount = 450_000 if direction == "income" else 180_000
            cur.execute(
                """
                INSERT INTO income_expense_entries (
                    id, direction, amount, plan_date, payer_id, payee_id,
                    deal_id, category_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry_id,
                    direction,
                    amount,
                    _date(10),
                    payer_id,
                    payee_id,
                    deal_id,
                    category_code,
                ),
            )

    treasury_transactions = []
    for idx, entry_id in enumerate(income_expenses[:4]):
        tx_id = str(uuid.uuid4())
        treasury_transactions.append(tx_id)
        amount = 200_000 + idx * 25_000
        cur.execute(
            """
            INSERT INTO treasury_transactions (
                id, doc_num, transaction_date, amount, payer_name, payee_name,
                purpose, remainder, processed, category_code, income_expense_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tx_id,
                f"TX-{1000 + idx}",
                _date(-5 + idx),
                amount,
                "Seed Payer",
                "Seed Payee",
                "Seed payment",
                amount,
                "yes",
                "2.3.1",
                entry_id,
            ),
        )
        cur.execute(
            """
            INSERT INTO treasury_allocations (
                id, transaction_id, income_expense_id, amount, category_code
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (_uuid(), tx_id, entry_id, amount, "2.3.1"),
        )

    tenders = []
    for dp_id, deal_id, prod_id in deal_products[:3]:
        tender_id = _uuid()
        tenders.append(tender_id)
        cur.execute(
            """
            INSERT INTO tenders (
                id, deal_product_id, deal_id, product_id, direction_id, status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                tender_id,
                dp_id,
                deal_id,
                prod_id,
                random.choice(categories),
                "pending",
            ),
        )

        for company_id in random.sample(subcontractors, 2):
            cur.execute(
                """
                INSERT INTO tender_offers (
                    id, tender_id, company_id, status, proposed_amount, proposed_deadline, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    tender_id,
                    company_id,
                    "submitted",
                    random.randint(250_000, 420_000),
                    _date(60),
                    "Seed offer",
                ),
            )

    for company_id in subcontractors[:3]:
        cur.execute(
            """
            INSERT INTO company_accreditations (
                id, company_id, direction_id, status, comment
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (_uuid(), company_id, random.choice(categories), "approved", "Seed approval"),
        )
        cur.execute(
            """
            INSERT INTO company_documents (
                id, company_id, doc_type, doc_value, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (_uuid(), company_id, "portfolio", "Seed portfolio", "approved"),
        )

    cur.execute("SELECT COALESCE(MAX(outgoing_number_seq), 0) FROM outgoing_documents")
    start_seq = (cur.fetchone()[0] or 0) + 1
    outgoing_ids = []
    for i in range(2):
        out_id = _uuid()
        outgoing_ids.append(out_id)
        seq = start_seq + i
        cur.execute(
            """
            INSERT INTO outgoing_documents (
                id, outgoing_number_seq, outgoing_number, recipient_company_id,
                deal_id, letter_date, subject, body, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                out_id,
                seq,
                f"{seq}/{date.today().strftime('%Y-%m')}",
                random.choice(customers),
                random.choice(deals),
                _date(-2),
                f"Seed letter {i + 1}",
                "Seed letter body",
                "draft",
            ),
        )
        version_id = _uuid()
        cur.execute(
            """
            INSERT INTO outgoing_document_versions (
                id, document_id, version_number, status, created_by, comment, pdf_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (version_id, out_id, 1, "draft", "seed", "Seed version", "/seed/outgoing.pdf"),
        )
        cur.execute(
            """
            INSERT INTO outgoing_document_files (
                id, document_id, version_id, file_type, file_path, file_name
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_uuid(), out_id, version_id, "pdf", "/seed/outgoing.pdf", "seed.pdf"),
        )

    documents = []
    doc_types = ["outgoing_letter", "contract", "addendum", "act", "waybill", "result"]
    statuses = ["draft", "sent", "received", "archived"]
    for i, doc_type in enumerate(doc_types):
        doc_id = _uuid()
        documents.append(doc_id)
        cur.execute(
            """
            INSERT INTO documents (
                id, doc_type, title, number, document_date, status, project_id,
                counterparty_id, source_type, source_id, our_company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                doc_type,
                f"Seed Doc {i + 1}",
                f"SEED-DOC-{i + 1}",
                _date(-1 * (i + 1)),
                statuses[i % len(statuses)],
                random.choice(deals),
                random.choice(customers),
                "seed",
                "seed",
                our_company_id,
            ),
        )

    cur.execute(
        """
        INSERT INTO document_relations (
            id, document_id, related_document_id, relation_type
        ) VALUES (?, ?, ?, ?)
        """,
        (_uuid(), documents[0], documents[1], "related"),
    )

    package_ids = []
    for i in range(2):
        pkg_id = _uuid()
        package_ids.append(pkg_id)
        cur.execute(
            """
            INSERT INTO document_packages (
                id, title, package_date, status, project_id, counterparty_id, our_company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pkg_id,
                f"Seed Package {i + 1}",
                _date(-3),
                "draft",
                random.choice(deals),
                random.choice(customers),
                our_company_id,
            ),
        )

    for pkg_id, doc_id in zip(package_ids, documents[:2]):
        cur.execute(
            """
            INSERT INTO document_package_items (id, package_id, document_id)
            VALUES (?, ?, ?)
            """,
            (_uuid(), pkg_id, doc_id),
        )

    dispatch_ids = []
    for doc_id in documents[:2]:
        dispatch_id = _uuid()
        dispatch_ids.append(dispatch_id)
        cur.execute(
            """
            INSERT INTO document_dispatches (id, document_id, status, note)
            VALUES (?, ?, ?, ?)
            """,
            (dispatch_id, doc_id, "sent", "Seed dispatch"),
        )

    channels = ["post", "courier", "email", "edo"]
    for dispatch_id in dispatch_ids:
        for ch in channels[:2]:
            cur.execute(
                """
                INSERT INTO document_dispatch_channels (
                    id, dispatch_id, channel, channel_date, confirmation_file, track_number
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    _uuid(),
                    dispatch_id,
                    ch,
                    _date(-1),
                    "/seed/confirm.pdf",
                    "TRACK-12345" if ch == "post" else None,
                ),
            )

    tasks = []
    for deal_id in deals:
        for i in range(3):
            task_id = _uuid()
            tasks.append(task_id)
            has_budget = i % 2 == 0
            due_date = _date(7 + i * 5)
            category_code = "2.3.1" if has_budget else None
            payer_id = our_company_id if has_budget else None
            payee_id = random.choice(subcontractors) if has_budget else None
            income_expense_id = None
            if has_budget:
                ie_id = _uuid()
                income_expense_id = ie_id
                cur.execute(
                    """
                    INSERT INTO income_expense_entries (
                        id, direction, amount, plan_date, payer_id, payee_id,
                        deal_id, category_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ie_id,
                        "expense",
                        120_000 + i * 20_000,
                        (date.today() + timedelta(days=7 + i * 5 + 14)).isoformat(),
                        payer_id,
                        payee_id,
                        deal_id,
                        category_code,
                    ),
                )
            cur.execute(
                """
                INSERT INTO tasks (
                    id, title, description, deal_id, status, priority,
                    assigned_to_user_id, created_by_user_id, due_date, budget,
                    category_code, payer_id, payee_id, income_expense_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    f"Seed Task {i + 1}",
                    "Seed task description",
                    deal_id,
                    "in_progress",
                    "normal",
                    random.choice(users),
                    users[0],
                    due_date,
                    120_000 + i * 20_000 if has_budget else None,
                    category_code,
                    payer_id,
                    payee_id,
                    income_expense_id,
                ),
            )

    auctions = []
    for i in range(2):
        auction_id = _uuid()
        auctions.append(auction_id)
        cur.execute(
            """
            INSERT INTO task_auctions (
                id, title, description, budget, deal_id, category_code, status, created_by_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                auction_id,
                f"Seed Auction {i + 1}",
                "Seed auction description",
                200_000 + i * 50_000,
                random.choice(deals),
                "2.3.1",
                "archived" if i == 1 else "pending",
                users[0],
            ),
        )

        bid_ids = []
        for u in users[-2:]:
            bid_id = _uuid()
            bid_ids.append(bid_id)
            cur.execute(
                """
                INSERT INTO task_auction_bids (
                    id, auction_id, user_id, bid_price, comment
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    bid_id,
                    auction_id,
                    u,
                    180_000 + i * 20_000,
                    "Seed bid",
                ),
            )
        cur.execute(
            "UPDATE task_auctions SET winner_id = ?, winner_bid_id = ? WHERE id = ?",
            (users[-1], bid_ids[-1], auction_id),
        )

    conn.commit()
    conn.close()
    print("Seed data inserted successfully.")


if __name__ == "__main__":
    main()
