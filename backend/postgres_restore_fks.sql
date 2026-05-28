-- Restore key foreign keys (text UUID columns). Constraints are added NOT VALID to avoid failing on legacy rows; new data will be checked.

-- Helper to add FK if missing
DO $$
DECLARE
  tgt record;
  def text;
BEGIN
  FOR tgt IN
    SELECT *
    FROM (VALUES
      -- deals
      ('deals','fk_deals_customer','customer_id','companies','id'),
      ('deals','fk_deals_general_contractor','general_contractor_id','companies','id'),
      ('deals','fk_deals_our_company','our_company_id','companies','id'),
      -- contracts
      ('contracts','fk_contracts_customer','customer_id','companies','id'),
      ('contracts','fk_contracts_executor','executor_id','companies','id'),
      ('contracts','fk_contracts_deal','deal_id','deals','id'),
      ('contracts','fk_contracts_subcontractor_card','subcontractor_card_id','subcontractor_cards','id'),
      -- deal_products
      ('deal_products','fk_deal_products_deal','deal_id','deals','id'),
      ('deal_products','fk_deal_products_product','product_id','products','id'),
      -- stages
      ('stages','fk_stages_deal','deal_id','deals','id'),
      ('stages','fk_stages_parent','parent_id','stages','id'),
      ('stages','fk_stages_subcontractor','subcontractor_id','companies','id'),
      -- stage_product_links
      ('stage_product_links','fk_spl_deal','deal_id','deals','id'),
      ('stage_product_links','fk_spl_stage','stage_id','stages','id'),
      ('stage_product_links','fk_spl_deal_product','deal_product_id','deal_products','id'),
      -- stage_product_assignments
      ('stage_product_assignments','fk_spa_deal','deal_id','deals','id'),
      ('stage_product_assignments','fk_spa_stage','stage_id','stages','id'),
      ('stage_product_assignments','fk_spa_product','product_id','products','id'),
      ('stage_product_assignments','fk_spa_subcard','subcontractor_card_id','subcontractor_cards','id'),
      ('stage_product_assignments','fk_spa_subproduct','subcontractor_product_id','subcontractor_products','id'),
      ('stage_product_assignments','fk_spa_contract','contract_id','contracts','id'),
      -- subcontractor_cards
      ('subcontractor_cards','fk_subcards_company','company_id','companies','id'),
      ('subcontractor_cards','fk_subcards_customer','customer_id','companies','id'),
      ('subcontractor_cards','fk_subcards_gc','general_contractor_id','companies','id'),
      -- subcontractor_products
      ('subcontractor_products','fk_subprod_card','subcontractor_card_id','subcontractor_cards','id'),
      ('subcontractor_products','fk_subprod_contract','contract_id','contracts','id'),
      ('subcontractor_products','fk_subprod_product','product_id','products','id'),
      ('subcontractor_products','fk_subprod_stage','stage_id','subcontractor_stages','id'),
      -- subcontractor_stages
      ('subcontractor_stages','fk_substage_parent','parent_id','subcontractor_stages','id'),
      ('subcontractor_stages','fk_substage_card','subcontractor_card_id','subcontractor_cards','id'),
      ('subcontractor_stages','fk_substage_contract','contract_id','contracts','id'),
      ('subcontractor_stages','fk_substage_company','subcontractor_id','companies','id'),
      -- subcontractor_stage_dependencies
      ('subcontractor_stage_dependencies','fk_substage_dep_pred','predecessor_id','subcontractor_stages','id'),
      ('subcontractor_stage_dependencies','fk_substage_dep_succ','successor_id','subcontractor_stages','id'),
      -- stage_results
      ('stage_results','fk_stage_results_stage','stage_id','subcontractor_stages','id'),
      ('stage_results','fk_stage_results_card','subcontractor_card_id','subcontractor_cards','id'),
      ('stage_results','fk_stage_results_deal','deal_id','deals','id'),
      ('stage_results','fk_stage_results_reviewer','reviewer_id','users','id'),
      -- financial_plan
      ('financial_plans','fk_finplan_deal','deal_id','deals','id'),
      ('financial_plans','fk_finplan_contractor','contractor_id','companies','id'),
      ('financial_plans','fk_finplan_stage','stage_id','stages','id'),
      -- income_expense_entries
      ('income_expense_entries','fk_ie_payer','payer_id','companies','id'),
      ('income_expense_entries','fk_ie_payee','payee_id','companies','id'),
      ('income_expense_entries','fk_ie_deal','deal_id','deals','id'),
      ('income_expense_entries','fk_ie_contract','contract_id','contracts','id'),
      ('income_expense_entries','fk_ie_stage','stage_id','stages','id'),
      -- treasury_allocations
      ('treasury_allocations','fk_ta_tx','transaction_id','treasury_transactions','id'),
      ('treasury_allocations','fk_ta_ie','income_expense_id','income_expense_entries','id'),
      -- transaction_allocations
      ('transaction_allocations','fk_talloc_tx','transaction_id','treasury_transactions','id'),
      ('transaction_allocations','fk_talloc_fp','financial_plan_id','financial_plans','id'),
      -- tenders
      ('tenders','fk_tenders_deal','deal_id','deals','id'),
      ('tenders','fk_tenders_product','product_id','products','id'),
      ('tenders','fk_tenders_deal_product','deal_product_id','deal_products','id'),
      ('tenders','fk_tenders_winner','winner_company_id','companies','id'),
      -- tender_offers
      ('tender_offers','fk_to_tender','tender_id','tenders','id'),
      ('tender_offers','fk_to_company','company_id','companies','id'),
      -- deal_gips
      ('deal_gips','fk_gip_deal','deal_id','deals','id'),
      ('deal_gips','fk_gip_user','user_id','users','id'),
      -- company_user_links
      ('company_user_links','fk_cul_company','company_id','companies','id'),
      ('company_user_links','fk_cul_user','user_id','users','id'),
      -- leads
      ('leads','fk_leads_customer','customer_id','companies','id'),
      ('leads','fk_leads_our_company','our_company_id','companies','id'),
      ('leads','fk_leads_responsible','responsible_user_id','users','id'),
      ('leads','fk_leads_deal','deal_id','deals','id'),
      -- lead_products
      ('lead_products','fk_lp_lead','lead_id','leads','id'),
      ('lead_products','fk_lp_product','product_id','products','id'),
      -- tasks
      ('tasks','fk_tasks_deal','deal_id','deals','id'),
      ('tasks','fk_tasks_stage','stage_id','stages','id'),
      ('tasks','fk_tasks_assigned_company','assigned_to_id','companies','id'),
      ('tasks','fk_tasks_created_company','created_by_id','companies','id'),
      ('tasks','fk_tasks_assigned_user','assigned_to_user_id','users','id'),
      ('tasks','fk_tasks_created_user','created_by_user_id','users','id'),
      ('tasks','fk_tasks_payer','payer_id','companies','id'),
      ('tasks','fk_tasks_payee','payee_id','companies','id'),
      ('tasks','fk_tasks_ie','income_expense_id','income_expense_entries','id'),
      ('tasks','fk_tasks_source_auction','source_auction_id','task_auctions','id'),
      -- task_auctions
      ('task_auctions','fk_ta_deal','deal_id','deals','id'),
      ('task_auctions','fk_ta_block','block_id','task_auctions','id'),
      ('task_auctions','fk_ta_winner','winner_id','users','id'),
      ('task_auctions','fk_ta_created_task','created_task_id','tasks','id'),
      ('task_auctions','fk_ta_created_by','created_by_id','users','id'),
      -- task_auction_bids
      ('task_auction_bids','fk_tab_auction','auction_id','task_auctions','id'),
      ('task_auction_bids','fk_tab_user','user_id','users','id'),
      -- outgoing documents
      ('outgoing_documents','fk_od_recipient','recipient_company_id','companies','id'),
      ('outgoing_documents','fk_od_deal','deal_id','deals','id'),
      ('outgoing_document_versions','fk_odv_doc','document_id','outgoing_documents','id'),
      ('outgoing_document_files','fk_odf_doc','document_id','outgoing_documents','id'),
      ('outgoing_document_files','fk_odf_ver','version_id','outgoing_document_versions','id'),
      -- company_documents
      ('company_documents','fk_cd_company','company_id','companies','id'),
      ('company_documents','fk_cd_parent','parent_id','company_documents','id'),
      -- users
      ('users','fk_users_role','role_id','roles','id'),
      -- subcontractor_stage_dependencies already above
      -- work_results
      ('work_results','fk_wr_stage','stage_id','stages','id'),
      ('work_results','fk_wr_subcontractor','subcontractor_id','companies','id'),
      -- treasury_transactions
      ('treasury_transactions','fk_tt_ie','income_expense_id','income_expense_entries','id'),
      -- company_accreditations
      ('company_accreditations','fk_ca_company','company_id','companies','id')
      -- tender_product directions not linked (direction_id) – skip for now
    ) AS t(table_name, constraint_name, column_name, ref_table, ref_column)
  LOOP
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.table_constraints
      WHERE constraint_type='FOREIGN KEY'
        AND table_name=tgt.table_name
        AND constraint_name=tgt.constraint_name
    ) THEN
      def := format(
        'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES %I(%I) NOT VALID;',
        tgt.table_name, tgt.constraint_name, tgt.column_name, tgt.ref_table, tgt.ref_column
      );
      RAISE NOTICE 'Adding %', def;
      EXECUTE def;
    END IF;
  END LOOP;
END$$;

-- Validate selectively (optional; comment out if legacy rows are broken)
-- ALTER TABLE ONLY stage_product_links VALIDATE CONSTRAINT fk_spl_deal;
