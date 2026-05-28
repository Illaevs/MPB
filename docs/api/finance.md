# Finance & Billing API

Сгенерировано из `docs/API.md` на 2026-02-15 03:22:39 (local time).

## Scope
- Домен: `finance`
- Описание: Финансы, казначейство, ДДС, экономика, штрафы и договоры.
- Routers: `5`
- Endpoints: `87`
- Список роутеров: `finance`, `income_expense`, `economy`, `penalty_rules`, `contracts`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `45`.

### Model `FinancialPlanCreate`

Source: `backend/app/schemas/financial_plan.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | str | yes | - | - |
| direction | str | yes | - | - |
| amount_plan | float | yes | - | - |
| date_plan_start | Optional[date] | no | None | - |
| date_plan_end | Optional[date] | no | None | - |
| description | Optional[str] | no | None | - |
| contractor_id | Optional[str] | no | None | - |
| subcontractor_contract_id | Optional[str] | no | None | - |
| payment_status | Optional[str] | no | 'unpaid' | - |
| stage_id | Optional[str] | no | None | - |


### Model `FinancialPlanResponse`

Source: `backend/app/schemas/financial_plan.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | str | yes | - | - |
| direction | str | yes | - | - |
| amount_plan | float | yes | - | - |
| date_plan_start | Optional[date] | no | None | - |
| date_plan_end | Optional[date] | no | None | - |
| description | Optional[str] | no | None | - |
| contractor_id | Optional[str] | no | None | - |
| subcontractor_contract_id | Optional[str] | no | None | - |
| payment_status | Optional[str] | no | 'unpaid' | - |
| stage_id | Optional[str] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `FinancialPlanUpdate`

Source: `backend/app/schemas/financial_plan.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | str | yes | - | - |
| direction | str | yes | - | - |
| amount_plan | float | yes | - | - |
| date_plan_start | Optional[date] | no | None | - |
| date_plan_end | Optional[date] | no | None | - |
| description | Optional[str] | no | None | - |
| contractor_id | Optional[str] | no | None | - |
| subcontractor_contract_id | Optional[str] | no | None | - |
| payment_status | Optional[str] | no | 'unpaid' | - |
| stage_id | Optional[str] | no | None | - |


### Model `LinkedPaymentInfo`

Source: `backend/app/schemas/treasury_transaction.py`

Description: Краткая информация о привязанном платеже.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | Union[str, UUID] | yes | - | - |
| doc_num | Optional[str] | no | None | - |
| transaction_date | Optional[date] | no | None | - |
| amount | Optional[float] | no | None | - |


### Model `TreasuryAllocationCreate`

Source: `backend/app/schemas/treasury_allocation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| income_expense_id | Optional[Union[str, UUID]] | no | None | - |
| amount | float | yes | - | - |
| category_code | Optional[str] | no | None | - |


### Model `TreasuryAllocationResponse`

Source: `backend/app/schemas/treasury_allocation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| transaction_id | Union[str, UUID] | yes | - | - |
| income_expense_id | Union[str, UUID] | yes | - | - |
| amount | float | yes | - | - |
| category_code | Optional[str] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |


### Model `TreasuryAllocationUpdate`

Source: `backend/app/schemas/treasury_allocation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| income_expense_id | Optional[Union[str, UUID]] | no | None | - |
| amount | Optional[float] | no | None | - |
| category_code | Optional[str] | no | None | - |


### Model `TreasuryAutoRuleCreate`

Source: `backend/app/schemas/treasury_auto_rule.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| match_text | str | yes | - | - |
| match_type | str | no | 'contains' | - |
| action_type | str | yes | - | - |
| category_code | Optional[str] | no | None | - |
| create_dds | bool | no | False | - |
| is_active | bool | no | True | - |
| priority | int | no | 100 | - |


### Model `TreasuryAutoRuleResponse`

Source: `backend/app/schemas/treasury_auto_rule.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| match_text | str | yes | - | - |
| match_type | str | no | 'contains' | - |
| action_type | str | yes | - | - |
| category_code | Optional[str] | no | None | - |
| create_dds | bool | no | False | - |
| is_active | bool | no | True | - |
| priority | int | no | 100 | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `TreasuryAutoRuleUpdate`

Source: `backend/app/schemas/treasury_auto_rule.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| match_text | Optional[str] | no | None | - |
| match_type | Optional[str] | no | None | - |
| action_type | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |
| create_dds | Optional[bool] | no | None | - |
| is_active | Optional[bool] | no | None | - |
| priority | Optional[int] | no | None | - |


### Model `TreasuryTransactionCreate`

Source: `backend/app/schemas/treasury_transaction.py`

Description: Schema for creating a treasury transaction manually.


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| doc_num | str | yes | - | - |
| transaction_date | date | yes | - | - |
| amount | float | yes | - | - |
| calc_type | Optional[str] | no | 'vtb' | - |
| payer_inn | Optional[str] | no | None | - |
| payee_inn | Optional[str] | no | None | - |
| payer_name | Optional[str] | no | None | - |
| payee_name | Optional[str] | no | None | - |
| purpose | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |
| income_expense_id | Optional[str] | no | None | - |
| ignore_flag | Optional[str] | no | 'Нет' | - |


### Model `TreasuryTransactionResponse`

Source: `backend/app/schemas/treasury_transaction.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| doc_num | str | yes | - | - |
| transaction_date | date | yes | - | - |
| amount | float | yes | - | - |
| calc_type | Optional[str] | no | 'vtb' | - |
| payer_inn | Optional[str] | no | None | - |
| payee_inn | Optional[str] | no | None | - |
| payer_name | Optional[str] | no | None | - |
| payee_name | Optional[str] | no | None | - |
| purpose | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |
| income_expense_id | Optional[str] | no | None | - |
| ignore_flag | Optional[str] | no | 'Нет' | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |
| allocations | List[TreasuryAllocationResponse] | no | [] | - |
| allocated_amount | Optional[float] | no | None | - |
| remainder | Optional[float] | no | None | - |
| auto_rule_id | Optional[str] | no | None | - |
| auto_filled | bool | no | False | - |
| linked_transaction_id | Optional[Union[str, UUID]] | no | None | - |
| linked_payments | List[LinkedPaymentInfo] | no | [] | - |


### Model `TreasuryTransactionUpdate`

Source: `backend/app/schemas/treasury_transaction.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| calc_type | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |
| ignore_flag | Optional[str] | no | None | - |
| income_expense_id | Optional[str] | no | None | - |
| linked_transaction_id | Optional[str] | no | None | - |


### Model `IncomeExpenseEntryCreate`

Source: `backend/app/schemas/income_expense.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| direction | str | yes | - | - |
| amount | float | yes | - | - |
| plan_date | date | yes | - | - |
| actual_date | Optional[date] | no | None | - |
| payer_id | Optional[str] | no | None | - |
| payee_id | Optional[str] | no | None | - |
| deal_id | Optional[str] | no | None | - |
| contract_id | Optional[str] | no | None | - |
| stage_id | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |


### Model `IncomeExpenseEntryResponse`

Source: `backend/app/schemas/income_expense.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| direction | str | yes | - | - |
| amount | float | yes | - | - |
| plan_date | date | yes | - | - |
| actual_date | Optional[date] | no | None | - |
| payer_id | Optional[str] | no | None | - |
| payee_id | Optional[str] | no | None | - |
| deal_id | Optional[str] | no | None | - |
| contract_id | Optional[str] | no | None | - |
| stage_id | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |
| id | str | yes | - | - |
| payer_name | Optional[str] | no | None | - |
| payee_name | Optional[str] | no | None | - |
| deal_title | Optional[str] | no | None | - |
| contract_number | Optional[str] | no | None | - |
| payment_status | str | yes | - | - |
| paid_amount | float | yes | - | - |
| payments_history | List[PaymentHistoryItem] | yes | - | - |
| warning | Optional[str] | no | None | - |


### Model `IncomeExpenseEntryUpdate`

Source: `backend/app/schemas/income_expense.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| direction | Optional[str] | no | None | - |
| amount | Optional[float] | no | None | - |
| plan_date | Optional[date] | no | None | - |
| actual_date | Optional[date] | no | None | - |
| payer_id | Optional[str] | no | None | - |
| payee_id | Optional[str] | no | None | - |
| deal_id | Optional[str] | no | None | - |
| contract_id | Optional[str] | no | None | - |
| category_code | Optional[str] | no | None | - |


### Model `AdvancePaymentCreate`

Source: `backend/app/schemas/advance_payment.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | Optional[UUID] | no | None | - |
| contract_id | Optional[UUID] | no | None | - |
| amount_total | float | no | 0.0 | - |
| vat_rate | float | no | 20.0 | - |
| remaining_total | float | no | 0.0 | - |


### Model `AdvancePaymentResponse`

Source: `backend/app/schemas/advance_payment.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | Optional[UUID] | no | None | - |
| contract_id | Optional[UUID] | no | None | - |
| amount_total | float | no | 0.0 | - |
| vat_rate | float | no | 20.0 | - |
| remaining_total | float | no | 0.0 | - |
| id | UUID | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `AdvancePaymentUpdate`

Source: `backend/app/schemas/advance_payment.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| amount_total | Optional[float] | no | None | - |
| remaining_total | Optional[float] | no | None | - |
| vat_rate | Optional[float] | no | None | - |


### Model `InflationIndexCreate`

Source: `backend/app/schemas/inflation_index.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| period | str | yes | - | - |
| value | float | no | 1.0 | - |
| note | Optional[str] | no | None | - |


### Model `InflationIndexResponse`

Source: `backend/app/schemas/inflation_index.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| period | str | yes | - | - |
| value | float | no | 1.0 | - |
| note | Optional[str] | no | None | - |
| id | UUID | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `InflationIndexUpdate`

Source: `backend/app/schemas/inflation_index.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| period | Optional[str] | no | None | - |
| value | Optional[float] | no | None | - |
| note | Optional[str] | no | None | - |


### Model `OverheadAllocationResponse`

Source: `backend/app/schemas/overhead_allocation.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | UUID | yes | - | - |
| deal_id | UUID | yes | - | - |
| period | str | yes | - | - |
| amount | float | yes | - | - |
| calc_version | int | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `OverheadCreate`

Source: `backend/app/schemas/overhead.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| period | str | yes | - | - |
| amount | float | no | 0.0 | - |
| category | Optional[str] | no | None | - |
| source | Optional[str] | no | 'manual' | - |


### Model `OverheadResponse`

Source: `backend/app/schemas/overhead.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| period | str | yes | - | - |
| amount | float | no | 0.0 | - |
| category | Optional[str] | no | None | - |
| source | Optional[str] | no | 'manual' | - |
| id | UUID | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `OverheadUpdate`

Source: `backend/app/schemas/overhead.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| period | Optional[str] | no | None | - |
| amount | Optional[float] | no | None | - |
| category | Optional[str] | no | None | - |
| source | Optional[str] | no | None | - |


### Model `PricingModelCreate`

Source: `backend/app/schemas/pricing_model.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| base_margin | float | no | 0.0 | - |
| risk_reserve | float | no | 0.0 | - |
| inflation_mode | str | no | 'auto' | - |


### Model `PricingModelResponse`

Source: `backend/app/schemas/pricing_model.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| base_margin | float | no | 0.0 | - |
| risk_reserve | float | no | 0.0 | - |
| inflation_mode | str | no | 'auto' | - |
| id | UUID | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `PricingModelUpdate`

Source: `backend/app/schemas/pricing_model.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| base_margin | Optional[float] | no | None | - |
| risk_reserve | Optional[float] | no | None | - |
| inflation_mode | Optional[str] | no | None | - |


### Model `PricingQuoteCreate`

Source: `backend/app/schemas/pricing_quote.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | UUID | yes | - | - |
| model_id | Optional[UUID] | no | None | - |
| calc_date | Optional[date] | no | None | - |
| margin | Optional[float] | no | None | - |
| risk | Optional[float] | no | None | - |


### Model `PricingQuoteResponse`

Source: `backend/app/schemas/pricing_quote.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | UUID | yes | - | - |
| deal_id | UUID | yes | - | - |
| model_id | Optional[UUID] | no | None | - |
| calc_date | date | yes | - | - |
| base_cost | float | yes | - | - |
| overheads | float | yes | - | - |
| indexed_cost | float | yes | - | - |
| risk | float | yes | - | - |
| margin | float | yes | - | - |
| final_price | float | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `QualityAlertCreate`

Source: `backend/app/schemas/quality_alert.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | UUID | yes | - | - |
| alert_type | str | yes | - | - |
| severity | str | no | 'info' | - |
| message | str | yes | - | - |


### Model `QualityAlertResponse`

Source: `backend/app/schemas/quality_alert.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | UUID | yes | - | - |
| alert_type | str | yes | - | - |
| severity | str | no | 'info' | - |
| message | str | yes | - | - |
| id | UUID | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `StageClosingCreate`

Source: `backend/app/schemas/stage_closing.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| stage_id | UUID | yes | - | - |
| deal_id | UUID | yes | - | - |
| contract_id | Optional[UUID] | no | None | - |
| closing_date | date | yes | - | - |
| base_amount | float | yes | - | - |


### Model `StageClosingResponse`

Source: `backend/app/schemas/stage_closing.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| stage_id | UUID | yes | - | - |
| deal_id | UUID | yes | - | - |
| contract_id | Optional[UUID] | no | None | - |
| closing_date | date | yes | - | - |
| base_amount | float | yes | - | - |
| id | UUID | yes | - | - |
| vat_rate | float | yes | - | - |
| vat_amount | float | yes | - | - |
| total_amount | float | yes | - | - |
| advance_covered_base | float | yes | - | - |
| advance_covered_vat | float | yes | - | - |
| remaining_base | float | yes | - | - |
| remaining_vat | float | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `WipMonthlyResponse`

Source: `backend/app/schemas/wip_monthly.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | UUID | yes | - | - |
| deal_id | UUID | yes | - | - |
| stage_id | UUID | yes | - | - |
| period | str | yes | - | - |
| base_amount | float | yes | - | - |
| vat_rate | float | yes | - | - |
| vat_amount | float | yes | - | - |
| total_amount | float | yes | - | - |
| is_forecast | bool | yes | - | - |
| calc_version | int | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `PenaltyRuleCreate`

Source: `backend/app/schemas/penalty_rule.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| rule_type | str | yes | - | - |
| condition_min | float | yes | - | - |
| condition_max | float | yes | - | - |
| coefficient | float | no | 1.0 | - |
| description | Optional[str] | no | None | - |
| is_active | bool | no | True | - |
| sort_order | int | no | 0 | - |


### Model `PenaltyRuleResponse`

Source: `backend/app/schemas/penalty_rule.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| rule_type | str | yes | - | - |
| condition_min | float | yes | - | - |
| condition_max | float | yes | - | - |
| coefficient | float | no | 1.0 | - |
| description | Optional[str] | no | None | - |
| is_active | bool | no | True | - |
| sort_order | int | no | 0 | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `PenaltyRuleUpdate`

Source: `backend/app/schemas/penalty_rule.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| rule_type | Optional[str] | no | None | - |
| condition_min | Optional[float] | no | None | - |
| condition_max | Optional[float] | no | None | - |
| coefficient | Optional[float] | no | None | - |
| description | Optional[str] | no | None | - |
| is_active | Optional[bool] | no | None | - |
| sort_order | Optional[int] | no | None | - |


### Model `ContractCardResponse`

Source: `backend/app/schemas/contract_card.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| contract | ContractResponse | yes | - | - |
| deal_title | Optional[str] | no | None | - |
| subcontractor_title | Optional[str] | no | None | - |
| documents | List[ContractDocumentResponse] | yes | - | - |
| payment_summary | ContractPaymentSummary | yes | - | - |
| payments | List[IncomeExpenseEntryResponse] | yes | - | - |
| stages | List[ContractStageSummary] | yes | - | - |


### Model `ContractCreate`

Source: `backend/app/schemas/contract.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| contract_number | str | yes | - | - |
| contract_date | date | yes | - | - |
| status | Optional[str] | no | 'approval' | - |
| amount | Optional[float] | no | 0.0 | - |
| contract_type | str | yes | - | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| executor_id | Optional[Union[str, UUID]] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| subcontractor_card_id | Optional[Union[str, UUID]] | no | None | - |


### Model `ContractDocumentResponse`

Source: `backend/app/schemas/contract_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| doc_type | str | yes | - | - |
| number_in_contract | int | yes | - | - |
| status | Optional[str] | no | 'draft' | - |
| pdf_file_name | Optional[str] | no | None | - |
| pdf_storage_path | Optional[str] | no | None | - |
| edit_file_name | Optional[str] | no | None | - |
| edit_storage_path | Optional[str] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `ContractDocumentUpdate`

Source: `backend/app/schemas/contract_document.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| status | Optional[str] | no | None | - |


### Model `ContractResponse`

Source: `backend/app/schemas/contract.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| contract_number | str | yes | - | - |
| contract_date | date | yes | - | - |
| status | Optional[str] | no | 'approval' | - |
| amount | Optional[float] | no | 0.0 | - |
| contract_type | str | yes | - | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| executor_id | Optional[Union[str, UUID]] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| subcontractor_card_id | Optional[Union[str, UUID]] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `ContractUpdate`

Source: `backend/app/schemas/contract.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| contract_number | Optional[str] | no | None | - |
| contract_date | Optional[date] | no | None | - |
| status | Optional[str] | no | None | - |
| amount | Optional[float] | no | None | - |
| contract_type | Optional[str] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| executor_id | Optional[Union[str, UUID]] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| subcontractor_card_id | Optional[Union[str, UUID]] | no | None | - |


## Routers / Controllers Reference

### Router `finance`

Source: `backend/app/routers/finance.py`

Prefix: `/api/v1/finance`

Endpoints: `30`

#### `GET /api/v1/finance/cashflow`

- Controller: `backend/app/routers/finance.py::get_cashflow`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `TreasuryAllocation.income_expense_id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/import-bank-statement/confirm`

- Controller: `backend/app/routers/finance.py::import_bank_statement_confirm`
- Data Contract:
  - Path params: none
  - Query params: `create_missing_companies`: bool (optional, default=False, constraints=-); `default_calc_type`: str (optional, default='vtb', constraints=-)
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `FinanceService.import_bank_statement`
    - `HTTPException`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Ошибка импорта выписки`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/import-bank-statement/preview`

- Controller: `backend/app/routers/finance.py::preview_bank_statement`
- Data Contract:
  - Path params: none
  - Query params: `default_calc_type`: str (optional, default='vtb', constraints=-)
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `HTTPException`
    - `Company.inn.in_`
    - `db.execute`
    - `and_`
    - `select`
  - Side effects: DB read, File/storage operation
- Error Handling:
  - `400`: `Ошибка предпросмотра выписки`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/overview`

- Controller: `backend/app/routers/finance.py::get_finance_overview`
- Data Contract:
  - Path params: none
  - Query params: `period`: str (optional, default='year', constraints=-); `start_date`: Optional[str] (optional, default=None, constraints=-); `end_date`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `and_`
    - `TreasuryAllocation.income_expense_id.in_`
    - `TreasuryAllocation.transaction_id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/penalties/{deal_id}`

- Controller: `backend/app/routers/finance.py::calculate_penalties`
- Summary: Р Р°СЃС‡РµС‚ РЅРµСѓСЃС‚РѕРµРє РґР»СЏ РїСЂРѕРµРєС‚Р°
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinanceService.calculate_penalties`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `РћС€РёР±РєР° СЂР°СЃС‡РµС‚Р° РЅРµСѓСЃС‚РѕРµРє`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/plans/`

- Controller: `backend/app/routers/finance.py::get_financial_plans`
- Summary: РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РІСЃРµС… С„РёРЅР°РЅСЃРѕРІС‹С… РїР»Р°РЅРѕРІ
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[FinancialPlanResponse]`
  - Response contracts: [`FinancialPlanResponse`](#model-financialplanresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinancialPlan.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/plans/`

- Controller: `backend/app/routers/finance.py::create_financial_plan`
- Summary: РЎРѕР·РґР°С‚СЊ РЅРѕРІС‹Р№ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`FinancialPlanCreate`](#model-financialplancreate)
  - Response model: `FinancialPlanResponse`
  - Response contracts: [`FinancialPlanResponse`](#model-financialplanresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinancialPlan.create`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `РћС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ С„РёРЅР°РЅСЃРѕРІРѕРіРѕ РїР»Р°РЅР°`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/plans/deal/{deal_id}`

- Controller: `backend/app/routers/finance.py::get_financial_plans_by_deal`
- Summary: РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ С„РёРЅР°РЅСЃРѕРІС‹Рµ РїР»Р°РЅС‹ РїСЂРѕРµРєС‚Р°
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[FinancialPlanResponse]`
  - Response contracts: [`FinancialPlanResponse`](#model-financialplanresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinancialPlan.get_by_deal_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/finance/plans/{plan_id}`

- Controller: `backend/app/routers/finance.py::delete_financial_plan`
- Summary: РЈРґР°Р»РёС‚СЊ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ
- Data Contract:
  - Path params: `plan_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinancialPlan.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/plans/{plan_id}`

- Controller: `backend/app/routers/finance.py::get_financial_plan`
- Summary: РџРѕР»СѓС‡РёС‚СЊ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РїРѕ ID
- Data Contract:
  - Path params: `plan_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `FinancialPlanResponse`
  - Response contracts: [`FinancialPlanResponse`](#model-financialplanresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinancialPlan.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/finance/plans/{plan_id}`

- Controller: `backend/app/routers/finance.py::update_financial_plan`
- Summary: РћР±РЅРѕРІРёС‚СЊ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ
- Data Contract:
  - Path params: `plan_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`FinancialPlanUpdate`](#model-financialplanupdate)
  - Response model: `FinancialPlanResponse`
  - Response contracts: [`FinancialPlanResponse`](#model-financialplanresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinancialPlan.update`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `РћС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ С„РёРЅР°РЅСЃРѕРІРѕРіРѕ РїР»Р°РЅР°`; body schema `{"detail": "..."}`
  - `404`: `Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/pv/{deal_id}`

- Controller: `backend/app/routers/finance.py::calculate_pv`
- Summary: Р Р°СЃС‡РµС‚ Present Value РґР»СЏ РїСЂРѕРµРєС‚Р°
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `FinanceService.calculate_pv`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `РћС€РёР±РєР° СЂР°СЃС‡РµС‚Р° PV`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/summary/{deal_id}`

- Controller: `backend/app/routers/finance.py::get_financial_summary`
- Summary: РџРѕР»СѓС‡РёС‚СЊ С„РёРЅР°РЅСЃРѕРІСѓСЋ СЃРІРѕРґРєСѓ РїРѕ РїСЂРѕРµРєС‚Сѓ
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Deal.__table__.select().where`
    - `FinanceService.calculate_pv`
    - `FinanceService.calculate_penalties`
    - `db.execute`
    - `HTTPException`
    - `Deal.__table__.select`
  - Side effects: DB read
- Error Handling:
  - `400`: `Ошибка получения финансовой сводки`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/finance/treasury/allocations/{alloc_id}`

- Controller: `backend/app/routers/finance.py::delete_treasury_allocation`
- Data Contract:
  - Path params: `alloc_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `db.commit`
    - `HTTPException`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Allocation not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/finance/treasury/allocations/{alloc_id}`

- Controller: `backend/app/routers/finance.py::update_treasury_allocation`
- Data Contract:
  - Path params: `alloc_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TreasuryAllocationUpdate`](#model-treasuryallocationupdate)
  - Response model: `TreasuryAllocationResponse`
  - Response contracts: [`TreasuryAllocationResponse`](#model-treasuryallocationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TreasuryAllocationResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Category is required unless transaction is ignored`; `Entry direction does not match transaction`; `Allocation amount must be greater than 0`; `Allocation exceeds remaining amount`; body schema `{"detail": "..."}`
  - `404`: `Allocation not found`; `Transaction not found`; `Entry not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/treasury/rules`

- Controller: `backend/app/routers/finance.py::list_treasury_rules`
- Summary: Get all auto-allocation rules.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[TreasuryAutoRuleResponse]`
  - Response contracts: [`TreasuryAutoRuleResponse`](#model-treasuryautoruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `TreasuryAutoRuleResponse.model_validate`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/treasury/rules`

- Controller: `backend/app/routers/finance.py::create_treasury_rule`
- Summary: Create a new auto-allocation rule.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TreasuryAutoRuleCreate`](#model-treasuryautorulecreate)
  - Response model: `TreasuryAutoRuleResponse`
  - Response contracts: [`TreasuryAutoRuleResponse`](#model-treasuryautoruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TreasuryAutoRule`
    - `db.add`
    - `TreasuryAutoRuleResponse.model_validate`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/finance/treasury/rules/{rule_id}`

- Controller: `backend/app/routers/finance.py::delete_treasury_rule`
- Summary: Delete an auto-allocation rule.
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Правило не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/finance/treasury/rules/{rule_id}`

- Controller: `backend/app/routers/finance.py::update_treasury_rule`
- Summary: Update an auto-allocation rule.
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TreasuryAutoRuleUpdate`](#model-treasuryautoruleupdate)
  - Response model: `TreasuryAutoRuleResponse`
  - Response contracts: [`TreasuryAutoRuleResponse`](#model-treasuryautoruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TreasuryAutoRuleResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Правило не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/treasury/rules/{rule_id}/apply-all`

- Controller: `backend/app/routers/finance.py::apply_rule_to_all`
- Summary: Apply a rule to all existing transactions that match.
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `or_`
    - `select`
    - `TreasuryTransaction.auto_rule_id.is_`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Правило не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/treasury/transactions`

- Controller: `backend/app/routers/finance.py::list_treasury_transactions`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `payer`: Optional[str] (optional, default=None, constraints=-); `payee`: Optional[str] (optional, default=None, constraints=-); `payer_name`: Optional[str] (optional, default=None, constraints=-); `payee_name`: Optional[str] (optional, default=None, constraints=-); `tx_type`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `category`: Optional[str] (optional, default=None, constraints=-); `calc_type`: Optional[str] (optional, default=None, constraints=-); `income_expense_id`: Optional[str] (optional, default=None, constraints=-); `unlinked_only`: bool (optional, default=False, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `or_`
    - `db.get_bind`
    - `and_`
    - `TreasuryAllocation.id.is_`
    - `TreasuryTransaction.doc_num.ilike`
    - `TreasuryTransaction.purpose.ilike`
    - `TreasuryTransaction.payer_name.ilike`
    - `TreasuryTransaction.payee_name.ilike`
    - `TreasuryTransaction.payer_inn.ilike`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/treasury/transactions`

- Controller: `backend/app/routers/finance.py::create_treasury_transaction`
- Summary: Create a new treasury transaction manually.
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TreasuryTransactionCreate`](#model-treasurytransactioncreate)
  - Response model: `TreasuryTransactionResponse`
  - Response contracts: [`TreasuryTransactionResponse`](#model-treasurytransactionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TreasuryTransaction`
    - `db.add`
    - `and_`
    - `db.execute`
    - `HTTPException`
    - `db.flush`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Транзакция с такими данными уже существует`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/treasury/transactions/bulk-action`

- Controller: `backend/app/routers/finance.py::bulk_action_treasury_transactions`
- Summary: Bulk action on multiple transactions.
- Data Contract:
  - Path params: none
  - Query params: `payload`: dict (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `TreasuryTransaction.id.in_`
    - `select`
    - `IncomeExpenseEntry`
    - `db.add`
    - `TreasuryAllocation`
    - `db.flush`
    - `Company.get_by_inn`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `transaction_ids and action required`; `category_code required`; `calc_type required`; `f'Unknown action: {action}`; body schema `{"detail": "..."}`
  - `404`: `Transactions not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/finance/treasury/transactions/{tx_id}`

- Controller: `backend/app/routers/finance.py::delete_treasury_transaction`
- Summary: Delete a treasury transaction and its allocations.
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `select`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Транзакция не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/finance/treasury/transactions/{tx_id}`

- Controller: `backend/app/routers/finance.py::update_treasury_transaction`
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TreasuryTransactionUpdate`](#model-treasurytransactionupdate)
  - Response model: `TreasuryTransactionResponse`
  - Response contracts: [`TreasuryTransactionResponse`](#model-treasurytransactionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `TreasuryAllocation`
    - `db.add`
    - `select`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Транзакция не найдена`; `Entry not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/treasury/transactions/{tx_id}/allocations`

- Controller: `backend/app/routers/finance.py::list_treasury_allocations`
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[TreasuryAllocationResponse]`
  - Response contracts: [`TreasuryAllocationResponse`](#model-treasuryallocationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `TreasuryAllocationResponse.model_validate`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/treasury/transactions/{tx_id}/allocations`

- Controller: `backend/app/routers/finance.py::create_treasury_allocation`
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TreasuryAllocationCreate`](#model-treasuryallocationcreate)
  - Response model: `TreasuryAllocationResponse`
  - Response contracts: [`TreasuryAllocationResponse`](#model-treasuryallocationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TreasuryAllocation`
    - `db.add`
    - `TreasuryAllocationResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `IncomeExpenseEntry`
    - `db.commit`
    - `db.refresh`
    - `db.flush`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Allocation amount must be greater than 0`; `Category is required unless transaction is ignored`; `Entry direction does not match transaction`; `Allocation exceeds remaining amount`; `No remaining amount to allocate`; body schema `{"detail": "..."}`
  - `404`: `Transaction not found`; `Entry not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/finance/treasury/transactions/{tx_id}/link`

- Controller: `backend/app/routers/finance.py::link_payment`
- Summary: Привязать платёж linked_transaction_id к платежу tx_id (возврат/зачёт).
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: dict (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `linked_transaction_id is required`; `Cannot link transaction to itself`; `This payment is already linked to another transaction`; body schema `{"detail": "..."}`
  - `404`: `Transaction not found`; `Linked transaction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/finance/treasury/transactions/{tx_id}/link/{linked_id}`

- Controller: `backend/app/routers/finance.py::unlink_payment`
- Summary: Отвязать платёж linked_id от платежа tx_id.
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-); `linked_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `This payment is not linked to the specified transaction`; body schema `{"detail": "..."}`
  - `404`: `Linked transaction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/finance/treasury/transactions/{tx_id}/linked`

- Controller: `backend/app/routers/finance.py::get_linked_payments`
- Summary: Получить платежи, привязанные к данной транзакции.
- Data Contract:
  - Path params: `tx_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[LinkedPaymentInfo]`
  - Response contracts: [`LinkedPaymentInfo`](#model-linkedpaymentinfo)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `LinkedPaymentInfo`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `income_expense`

Source: `backend/app/routers/income_expense.py`

Prefix: `/api/v1/income-expense`

Endpoints: `5`

#### `GET /api/v1/income-expense`

- Controller: `backend/app/routers/income_expense.py::list_income_expense_entries`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `direction`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `payer_id`: Optional[str] (optional, default=None, constraints=-); `payee_id`: Optional[str] (optional, default=None, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `contract_id`: Optional[str] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[IncomeExpenseEntryResponse]`
  - Response contracts: [`IncomeExpenseEntryResponse`](#model-incomeexpenseentryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/income-expense`

- Controller: `backend/app/routers/income_expense.py::create_income_expense_entry`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`IncomeExpenseEntryCreate`](#model-incomeexpenseentrycreate)
  - Response model: `IncomeExpenseEntryResponse`
  - Response contracts: [`IncomeExpenseEntryResponse`](#model-incomeexpenseentryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `IncomeExpenseEntry`
    - `db.add`
    - `db.refresh`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.rollback`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid contract_id`; `Invalid company or related reference`; body schema `{"detail": "..."}`
  - `404`: `Deal not found`; `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/income-expense/count`

- Controller: `backend/app/routers/income_expense.py::count_income_expense_entries`
- Summary: Get total count of income/expense entries with same filters as list.
- Data Contract:
  - Path params: none
  - Query params: `direction`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `payer_id`: Optional[str] (optional, default=None, constraints=-); `payee_id`: Optional[str] (optional, default=None, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `contract_id`: Optional[str] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/income-expense/{entry_id}`

- Controller: `backend/app/routers/income_expense.py::delete_income_expense_entry`
- Data Contract:
  - Path params: `entry_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `get_section_permissions`
    - `db.delete`
    - `db.commit`
    - `allowed_deal_ids`
    - `select`
    - `delete`
    - `update`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Entry not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/income-expense/{entry_id}`

- Controller: `backend/app/routers/income_expense.py::update_income_expense_entry`
- Data Contract:
  - Path params: `entry_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`IncomeExpenseEntryUpdate`](#model-incomeexpenseentryupdate)
  - Response model: `IncomeExpenseEntryResponse`
  - Response contracts: [`IncomeExpenseEntryResponse`](#model-incomeexpenseentryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `Contract.get_by_id`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid contract_id`; body schema `{"detail": "..."}`
  - `404`: `Entry not found`; `Payer company not found`; `Payee company not found`; `Deal not found`; `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `economy`

Source: `backend/app/routers/economy.py`

Prefix: `/api/v1/economy`

Endpoints: `26`

#### `GET /api/v1/economy/advances`

- Controller: `backend/app/routers/economy.py::list_advances`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `contract_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[AdvancePaymentResponse]`
  - Response contracts: [`AdvancePaymentResponse`](#model-advancepaymentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `AdvancePayment.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/advances`

- Controller: `backend/app/routers/economy.py::create_advance`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AdvancePaymentCreate`](#model-advancepaymentcreate)
  - Response model: `AdvancePaymentResponse`
  - Response contracts: [`AdvancePaymentResponse`](#model-advancepaymentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `AdvancePayment`
    - `db.add`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/economy/advances/{item_id}`

- Controller: `backend/app/routers/economy.py::update_advance`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`AdvancePaymentUpdate`](#model-advancepaymentupdate)
  - Response model: `AdvancePaymentResponse`
  - Response contracts: [`AdvancePaymentResponse`](#model-advancepaymentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Advance not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/alerts`

- Controller: `backend/app/routers/economy.py::list_quality_alerts`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[QualityAlertResponse]`
  - Response contracts: [`QualityAlertResponse`](#model-qualityalertresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `QualityAlert.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/alerts`

- Controller: `backend/app/routers/economy.py::create_quality_alert`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`QualityAlertCreate`](#model-qualityalertcreate)
  - Response model: `QualityAlertResponse`
  - Response contracts: [`QualityAlertResponse`](#model-qualityalertresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `QualityAlert`
    - `db.add`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/inflation`

- Controller: `backend/app/routers/economy.py::list_inflation`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[InflationIndexResponse]`
  - Response contracts: [`InflationIndexResponse`](#model-inflationindexresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `InflationIndex.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/inflation`

- Controller: `backend/app/routers/economy.py::create_inflation`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`InflationIndexCreate`](#model-inflationindexcreate)
  - Response model: `InflationIndexResponse`
  - Response contracts: [`InflationIndexResponse`](#model-inflationindexresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `InflationIndex.get_by_period`
    - `HTTPException`
    - `InflationIndex.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `Period already exists`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/economy/inflation/{item_id}`

- Controller: `backend/app/routers/economy.py::delete_inflation`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `InflationIndex.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Inflation index not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/economy/inflation/{item_id}`

- Controller: `backend/app/routers/economy.py::update_inflation`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`InflationIndexUpdate`](#model-inflationindexupdate)
  - Response model: `InflationIndexResponse`
  - Response contracts: [`InflationIndexResponse`](#model-inflationindexresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `InflationIndex.get_by_id`
    - `HTTPException`
    - `InflationIndex.update`
  - Side effects: DB write
- Error Handling:
  - `404`: `Inflation index not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/overheads`

- Controller: `backend/app/routers/economy.py::list_overheads`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[OverheadResponse]`
  - Response contracts: [`OverheadResponse`](#model-overheadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Overhead.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/overheads`

- Controller: `backend/app/routers/economy.py::create_overhead`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OverheadCreate`](#model-overheadcreate)
  - Response model: `OverheadResponse`
  - Response contracts: [`OverheadResponse`](#model-overheadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Overhead.create`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/overheads/allocate`

- Controller: `backend/app/routers/economy.py::allocate_overheads`
- Data Contract:
  - Path params: none
  - Query params: `period`: str (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[OverheadAllocationResponse]`
  - Response contracts: [`OverheadAllocationResponse`](#model-overheadallocationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `EconomyService.allocate_overheads`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/overheads/allocations`

- Controller: `backend/app/routers/economy.py::list_overhead_allocations`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `period`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[OverheadAllocationResponse]`
  - Response contracts: [`OverheadAllocationResponse`](#model-overheadallocationresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/overheads/import-dds`

- Controller: `backend/app/routers/economy.py::import_overheads_from_dds`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[OverheadResponse]`
  - Response contracts: [`OverheadResponse`](#model-overheadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `EconomyService.import_overheads_from_dds`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/economy/overheads/{item_id}`

- Controller: `backend/app/routers/economy.py::delete_overhead`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Overhead.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Overhead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/economy/overheads/{item_id}`

- Controller: `backend/app/routers/economy.py::update_overhead`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`OverheadUpdate`](#model-overheadupdate)
  - Response model: `OverheadResponse`
  - Response contracts: [`OverheadResponse`](#model-overheadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Overhead.get_by_id`
    - `HTTPException`
    - `Overhead.update`
  - Side effects: DB write
- Error Handling:
  - `404`: `Overhead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/pricing/models`

- Controller: `backend/app/routers/economy.py::list_pricing_models`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[PricingModelResponse]`
  - Response contracts: [`PricingModelResponse`](#model-pricingmodelresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `PricingModel.created_at.desc`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/pricing/models`

- Controller: `backend/app/routers/economy.py::create_pricing_model`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`PricingModelCreate`](#model-pricingmodelcreate)
  - Response model: `PricingModelResponse`
  - Response contracts: [`PricingModelResponse`](#model-pricingmodelresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PricingModel`
    - `db.add`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/economy/pricing/models/{item_id}`

- Controller: `backend/app/routers/economy.py::delete_pricing_model`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Pricing model not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/economy/pricing/models/{item_id}`

- Controller: `backend/app/routers/economy.py::update_pricing_model`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`PricingModelUpdate`](#model-pricingmodelupdate)
  - Response model: `PricingModelResponse`
  - Response contracts: [`PricingModelResponse`](#model-pricingmodelresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Pricing model not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/pricing/quote`

- Controller: `backend/app/routers/economy.py::create_pricing_quote`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`PricingQuoteCreate`](#model-pricingquotecreate)
  - Response model: `PricingQuoteResponse`
  - Response contracts: [`PricingQuoteResponse`](#model-pricingquoteresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `EconomyService.calculate_pricing_quote`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/pricing/quotes`

- Controller: `backend/app/routers/economy.py::list_pricing_quotes`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[PricingQuoteResponse]`
  - Response contracts: [`PricingQuoteResponse`](#model-pricingquoteresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
    - `PricingQuote.calc_date.desc`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/stage-closings`

- Controller: `backend/app/routers/economy.py::list_stage_closings`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `stage_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[StageClosingResponse]`
  - Response contracts: [`StageClosingResponse`](#model-stageclosingresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `db.execute`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/stage-closings`

- Controller: `backend/app/routers/economy.py::create_stage_closing`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageClosingCreate`](#model-stageclosingcreate)
  - Response model: `StageClosingResponse`
  - Response contracts: [`StageClosingResponse`](#model-stageclosingresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `EconomyService.vat_rate_for_date`
    - `StageClosing`
    - `db.add`
    - `db.execute`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/economy/wip`

- Controller: `backend/app/routers/economy.py::list_wip`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[WipMonthlyResponse]`
  - Response contracts: [`WipMonthlyResponse`](#model-wipmonthlyresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/economy/wip/rebuild`

- Controller: `backend/app/routers/economy.py::rebuild_wip`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: str (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[WipMonthlyResponse]`
  - Response contracts: [`WipMonthlyResponse`](#model-wipmonthlyresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `EconomyService.rebuild_wip_for_deal`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `penalty_rules`

Source: `backend/app/routers/penalty_rules.py`

Prefix: `/api/v1/penalty-rules`

Endpoints: `6`

#### `GET /api/v1/penalty-rules`

- Controller: `backend/app/routers/penalty_rules.py::get_penalty_rules`
- Summary: Получить все правила штрафов
- Data Contract:
  - Path params: none
  - Query params: `only_active`: bool (optional, default=False, constraints=-); `rule_type`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[PenaltyRuleResponse]`
  - Response contracts: [`PenaltyRuleResponse`](#model-penaltyruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PenaltyRule.get_by_type`
    - `PenaltyRule.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/penalty-rules`

- Controller: `backend/app/routers/penalty_rules.py::create_penalty_rule`
- Summary: Создать новое правило
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`PenaltyRuleCreate`](#model-penaltyrulecreate)
  - Response model: `PenaltyRuleResponse`
  - Response contracts: [`PenaltyRuleResponse`](#model-penaltyruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PenaltyRule.create`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/penalty-rules/seed-defaults`

- Controller: `backend/app/routers/penalty_rules.py::seed_default_rules`
- Summary: Создать правила по умолчанию
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PenaltyRule.get_all`
    - `PenaltyRule.create`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/penalty-rules/{rule_id}`

- Controller: `backend/app/routers/penalty_rules.py::delete_penalty_rule`
- Summary: Удалить правило
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PenaltyRule.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Правило не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/penalty-rules/{rule_id}`

- Controller: `backend/app/routers/penalty_rules.py::get_penalty_rule`
- Summary: Получить правило по ID
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `PenaltyRuleResponse`
  - Response contracts: [`PenaltyRuleResponse`](#model-penaltyruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PenaltyRule.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Правило не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/penalty-rules/{rule_id}`

- Controller: `backend/app/routers/penalty_rules.py::update_penalty_rule`
- Summary: Обновить правило
- Data Contract:
  - Path params: `rule_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`PenaltyRuleUpdate`](#model-penaltyruleupdate)
  - Response model: `PenaltyRuleResponse`
  - Response contracts: [`PenaltyRuleResponse`](#model-penaltyruleresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `PenaltyRule.get_by_id`
    - `HTTPException`
    - `PenaltyRule.update`
  - Side effects: DB write
- Error Handling:
  - `404`: `Правило не найдено`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `contracts`

Source: `backend/app/routers/contracts.py`

Prefix: `/api/v1/contracts`

Endpoints: `20`

#### `GET /api/v1/contracts`

- Controller: `backend/app/routers/contracts.py::get_contracts`
- Summary: List contracts with pagination, search and filters
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `contract_type`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `customer_id`: Optional[str] (optional, default=None, constraints=-); `executor_id`: Optional[str] (optional, default=None, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `subcontractor_card_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `get_section_permissions`
    - `Contract.search_all`
    - `Contract.count_by_status`
    - `allowed_deal_ids`
    - `Contract.get_by_deal_id`
    - `Contract.get_by_subcontractor_card_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/contracts`

- Controller: `backend/app/routers/contracts.py::create_contract`
- Summary: Create a contract
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ContractCreate`](#model-contractcreate)
  - Response model: `ContractResponse`
  - Response contracts: [`ContractResponse`](#model-contractresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `Contract.create`
    - `Deal.get_by_id`
    - `SubcontractorCard.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `400`: `Unsupported contract_type`; `Contract must be linked to deal or subcontractor, not both`; body schema `{"detail": "..."}`
  - `404`: `Deal not found`; `Subcontractor not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/deal/{deal_id}`

- Controller: `backend/app/routers/contracts.py::get_contracts_by_deal`
- Summary: List contracts linked to a deal
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ContractResponse]`
  - Response contracts: [`ContractResponse`](#model-contractresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `get_section_permissions`
    - `Contract.get_by_deal_id`
    - `allowed_deal_ids`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/contracts/documents/{document_id}`

- Controller: `backend/app/routers/contracts.py::delete_contract_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ContractDocument.get_by_id`
    - `HTTPException`
    - `ContractDocument.delete`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/contracts/documents/{document_id}`

- Controller: `backend/app/routers/contracts.py::update_contract_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ContractDocumentUpdate`](#model-contractdocumentupdate)
  - Response model: `ContractDocumentResponse`
  - Response contracts: [`ContractDocumentResponse`](#model-contractdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `ContractDocument.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Invalid status`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/documents/{document_id}/download`

- Controller: `backend/app/routers/contracts.py::download_contract_document`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: `file_kind`: str (optional, default='pdf', constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Query`
    - `Depends`
    - `is_local_storage`
    - `Response`
    - `HTTPException`
    - `ContractDocument.get_by_id`
    - `storage_available`
    - `get_download_href`
    - `httpx.AsyncClient`
    - `read_file_bytes`
    - `mimetypes.guess_type`
    - `quote`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Invalid file_kind`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; `File not found`; `File not found in storage`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `502`: `Failed to resolve storage download link`; `Failed to download file from storage`; `Failed to download file`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/contracts/documents/{document_id}/upload`

- Controller: `backend/app/routers/contracts.py::upload_contract_document_file`
- Data Contract:
  - Path params: `document_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `file_kind`: str (required, default=-, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `ContractDocumentResponse`
  - Response contracts: [`ContractDocumentResponse`](#model-contractdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `clean_name`
    - `HTTPException`
    - `ContractDocument.get_by_id`
    - `ensure_path`
    - `upload_bytes_with_safe_extension`
    - `ContractDocument.update`
    - `(settings.STORAGE_LOCAL_ROOT or '').rstrip`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Invalid file_kind`; body schema `{"detail": "..."}`
  - `404`: `Document not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/subcontractor/{subcontractor_id}`

- Controller: `backend/app/routers/contracts.py::get_contracts_by_subcontractor`
- Summary: List contracts linked to a subcontractor card
- Data Contract:
  - Path params: `subcontractor_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ContractResponse]`
  - Response contracts: [`ContractResponse`](#model-contractresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `get_section_permissions`
    - `Contract.get_by_subcontractor_card_id`
    - `allowed_deal_ids`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/contracts/{contract_id}`

- Controller: `backend/app/routers/contracts.py::delete_contract`
- Summary: Delete a contract
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Contract.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/{contract_id}`

- Controller: `backend/app/routers/contracts.py::get_contract`
- Summary: Get a contract by ID
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ContractResponse`
  - Response contracts: [`ContractResponse`](#model-contractresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Contract.get_by_id`
    - `HTTPException`
    - `get_section_permissions`
    - `allowed_deal_ids`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/contracts/{contract_id}`

- Controller: `backend/app/routers/contracts.py::update_contract`
- Summary: Update a contract
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ContractUpdate`](#model-contractupdate)
  - Response model: `ContractResponse`
  - Response contracts: [`ContractResponse`](#model-contractresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `Contract.get_by_id`
    - `Contract.update`
    - `Deal.get_by_id`
    - `SubcontractorCard.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `400`: `Unsupported contract_type`; `Contract must be linked to deal or subcontractor, not both`; body schema `{"detail": "..."}`
  - `404`: `Contract not found`; `Deal not found`; `Subcontractor not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/{contract_id}/card`

- Controller: `backend/app/routers/contracts.py::get_contract_card`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ContractCardResponse`
  - Response contracts: [`ContractCardResponse`](#model-contractcardresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ContractCardResponse`
    - `Contract.get_by_id`
    - `HTTPException`
    - `ContractDocument.get_by_contract`
    - `db.execute`
    - `Deal.get_by_id`
    - `SubcontractorCard.get_by_id`
    - `ContractPaymentSummary`
    - `IncomeExpenseEntry.plan_date.desc`
    - `ContractStageSummary`
    - `Stage.get_by_deal_id`
  - Side effects: DB read
- Error Handling:
  - `404`: `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/{contract_id}/documents`

- Controller: `backend/app/routers/contracts.py::list_contract_documents`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: `doc_type`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ContractDocumentResponse]`
  - Response contracts: [`ContractDocumentResponse`](#model-contractdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Contract.get_by_id`
    - `HTTPException`
    - `ContractDocument.get_by_contract`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Invalid doc_type`; body schema `{"detail": "..."}`
  - `404`: `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/contracts/{contract_id}/documents/upload`

- Controller: `backend/app/routers/contracts.py::upload_contract_document`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `doc_type`: str (required, default=-, constraints=-); `file_kind`: str (required, default=-, constraints=-); `status`: Optional[str] (optional, default='draft', constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `ContractDocumentResponse`
  - Response contracts: [`ContractDocumentResponse`](#model-contractdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `clean_name`
    - `HTTPException`
    - `Contract.get_by_id`
    - `ContractDocument.get_by_contract_and_type`
    - `ensure_path`
    - `upload_bytes_with_safe_extension`
    - `ContractDocument.create`
    - `(settings.STORAGE_LOCAL_ROOT or '').rstrip`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Invalid doc_type`; `Invalid file_kind`; `Invalid status`; body schema `{"detail": "..."}`
  - `404`: `Contract not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/contracts/{contract_id}/expenses`

- Controller: `backend/app/routers/contracts.py::get_contract_expenses`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ContractExpenseCardResponse`
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_get_service_contract_or_400`
    - `db.execute`
    - `ContractPaymentSummary`
    - `IncomeExpenseEntry.plan_date.desc`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/contracts/{contract_id}/expenses`

- Controller: `backend/app/routers/contracts.py::create_contract_expense`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: ContractExpenseCreate (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `IncomeExpenseEntryResponse`
  - Response contracts: [`IncomeExpenseEntryResponse`](#model-incomeexpenseentryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `IncomeExpenseEntry`
    - `db.add`
    - `_get_service_contract_or_400`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/contracts/{contract_id}/expenses/bulk`

- Controller: `backend/app/routers/contracts.py::create_contract_expenses_bulk`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: ContractExpenseBulkCreate (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[IncomeExpenseEntryResponse]`
  - Response contracts: [`IncomeExpenseEntryResponse`](#model-incomeexpenseentryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_get_service_contract_or_400`
    - `HTTPException`
    - `IncomeExpenseEntry`
    - `db.add`
    - `db.commit`
    - `monthrange`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `400`: `Invalid frequency`; `Periods must be positive`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/contracts/{contract_id}/expenses/{entry_id}`

- Controller: `backend/app/routers/contracts.py::delete_contract_expense`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-); `entry_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_get_service_contract_or_400`
    - `db.execute`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Entry does not belong to contract`; `Only expense entries allowed`; body schema `{"detail": "..."}`
  - `404`: `Entry not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/contracts/{contract_id}/expenses/{entry_id}`

- Controller: `backend/app/routers/contracts.py::update_contract_expense`
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-); `entry_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: ContractExpenseUpdate (required, default=-, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `IncomeExpenseEntryResponse`
  - Response contracts: [`IncomeExpenseEntryResponse`](#model-incomeexpenseentryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `_get_service_contract_or_400`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Entry does not belong to contract`; `Only expense entries allowed`; body schema `{"detail": "..."}`
  - `404`: `Entry not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/contracts/{contract_id}/link`

- Controller: `backend/app/routers/contracts.py::link_contract`
- Summary: Link/unlink contract to deal or subcontractor
- Data Contract:
  - Path params: `contract_id`: str (required, default=-, constraints=-)
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `subcontractor_card_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Contract.get_by_id`
    - `HTTPException`
    - `Contract.update`
    - `Deal.get_by_id`
    - `SubcontractorCard.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `400`: `Contract must be linked to deal or subcontractor, not both`; body schema `{"detail": "..."}`
  - `404`: `Contract not found`; `Deal not found`; `Subcontractor not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

### `GET /api/v1/finance/cashflow`

```bash
curl -X GET http://localhost:8000/api/v1/finance/cashflow -H "Authorization: Bearer $ACCESS_TOKEN" 
```

```json
{
  "status": "ok"
}
```


### `POST /api/v1/finance/treasury/transactions`

```bash
curl -X POST http://localhost:8000/api/v1/finance/treasury/transactions -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"amount": 0.0, "doc_num": "string", "transaction_date": "2026-01-01", "calc_type": "string", "category_code": "string", "ignore_flag": "string", "income_expense_id": "string", "payee_inn": "string"}'
```

```json
{
  "amount": 0.0,
  "created_at": "2026-01-01T00:00:00Z",
  "doc_num": "string",
  "id": "00000000-0000-0000-0000-000000000000",
  "transaction_date": "2026-01-01",
  "updated_at": "2026-01-01T00:00:00Z",
  "allocated_amount": 0.0,
  "allocations": []
}
```
