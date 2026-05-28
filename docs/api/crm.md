# CRM Core API

Сгенерировано из `docs/API.md` на 2026-05-19 01:30:03 (local time).

## Scope
- Домен: `crm`
- Описание: Сделки, лиды, этапы, задачи, продукты, тендеры и исполнение.
- Routers: `14`
- Endpoints: `139`
- Список роутеров: `deals`, `leads`, `stages`, `tasks`, `products`, `task_auctions`, `tenders`, `deal_execution`, `executor`, `subcontractors`, `subcontractor_stages`, `subcontractor_products`, `result_reviews`, `kp`

## Common Rules
- Общие правила API (base URL, auth headers, коды ошибок) вынесены в `docs/api/INDEX.md`.
- Ниже сохранена детальная структура endpoint'ов: Data Contract, Auth/AuthZ, Logic Flow, Error Handling.

## Data Contract Catalog (Domain)

Модели, используемые в домене: `52`.

### Model `DealCreate`

Source: `backend/app/schemas/deal.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| our_company_id | Optional[Union[str, UUID]] | no | None | - |
| general_contractor_id | Optional[Union[str, UUID]] | no | None | - |
| penalty_config | Optional[dict] | no | None | - |
| s3_prefix_tz | Optional[str] | no | None | - |
| s3_prefix_docs | Optional[str] | no | None | - |
| status | Optional[str] | no | 'active' | - |
| total_contract_value | Optional[float] | no | 0.0 | - |
| total_paid | Optional[float] | no | 0.0 | - |
| vat_rate | Optional[float] | no | 20.0 | - |
| vat_included | Optional[bool] | no | True | - |


### Model `DealGipsUpdate`

Source: `backend/app/schemas/deal.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| user_ids | list[str] | no | [] | - |


### Model `DealResponse`

Source: `backend/app/schemas/deal.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| our_company_id | Optional[Union[str, UUID]] | no | None | - |
| general_contractor_id | Optional[Union[str, UUID]] | no | None | - |
| penalty_config | Optional[dict] | no | None | - |
| s3_prefix_tz | Optional[str] | no | None | - |
| s3_prefix_docs | Optional[str] | no | None | - |
| status | Optional[str] | no | 'active' | - |
| total_contract_value | Optional[float] | no | 0.0 | - |
| total_paid | Optional[float] | no | 0.0 | - |
| vat_rate | Optional[float] | no | 20.0 | - |
| vat_included | Optional[bool] | no | True | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `DealUpdate`

Source: `backend/app/schemas/deal.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | Optional[str] | no | None | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| our_company_id | Optional[Union[str, UUID]] | no | None | - |
| general_contractor_id | Optional[Union[str, UUID]] | no | None | - |
| penalty_config | Optional[dict] | no | None | - |
| s3_prefix_tz | Optional[str] | no | None | - |
| s3_prefix_docs | Optional[str] | no | None | - |
| status | Optional[str] | no | None | - |
| total_contract_value | Optional[float] | no | None | - |
| total_paid | Optional[float] | no | None | - |
| vat_rate | Optional[float] | no | None | - |
| vat_included | Optional[bool] | no | None | - |


### Model `DealVatUpdate`

Source: `backend/app/schemas/deal.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| vat_rate | Optional[float] | no | None | - |
| vat_included | Optional[bool] | no | None | - |


### Model `LeadCreate`

Source: `backend/app/schemas/lead.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| our_company_id | Optional[Union[str, UUID]] | no | None | - |
| responsible_user_id | Optional[Union[str, UUID]] | no | None | - |
| advance_percent | Optional[float] | no | 0.0 | - |
| vat_rate | Optional[float] | no | 20.0 | - |
| status | Optional[str] | no | 'incoming' | - |
| total_value | Optional[float] | no | 0.0 | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |


### Model `LeadResponse`

Source: `backend/app/schemas/lead.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| our_company_id | Optional[Union[str, UUID]] | no | None | - |
| responsible_user_id | Optional[Union[str, UUID]] | no | None | - |
| advance_percent | Optional[float] | no | 0.0 | - |
| vat_rate | Optional[float] | no | 20.0 | - |
| status | Optional[str] | no | 'incoming' | - |
| total_value | Optional[float] | no | 0.0 | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `StageCreate`

Source: `backend/app/schemas/stage.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| stage_type | Optional[str] | no | 'stage' | - |
| term_type | Optional[str] | no | 'work_days' | - |
| date_start | date | yes | - | - |
| duration | int | yes | - | - |
| date_end | Optional[date] | no | None | - |
| close_date | Optional[date] | no | None | - |
| resources | Optional[List[dict]] | no | [] | - |
| planned_cost | Optional[float] | no | 0.0 | - |
| actual_cost | Optional[float] | no | 0.0 | - |
| status | Optional[str] | no | 'planned' | - |
| is_closed | Optional[bool] | no | False | - |
| parent_id | Optional[UUID] | no | None | - |
| deal_id | UUID | yes | - | - |
| subcontractor_id | Optional[UUID] | no | None | - |


### Model `StageResponse`

Source: `backend/app/schemas/stage.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| stage_type | Optional[str] | no | 'stage' | - |
| term_type | Optional[str] | no | 'work_days' | - |
| date_start | date | yes | - | - |
| duration | int | yes | - | - |
| date_end | Optional[date] | no | None | - |
| close_date | Optional[date] | no | None | - |
| resources | Optional[List[dict]] | no | [] | - |
| planned_cost | Optional[float] | no | 0.0 | - |
| actual_cost | Optional[float] | no | 0.0 | - |
| status | Optional[str] | no | 'planned' | - |
| is_closed | Optional[bool] | no | False | - |
| parent_id | Optional[UUID] | no | None | - |
| deal_id | UUID | yes | - | - |
| subcontractor_id | Optional[UUID] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `StageUpdate`

Source: `backend/app/schemas/stage.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| stage_type | Optional[str] | no | 'stage' | - |
| term_type | Optional[str] | no | 'work_days' | - |
| date_start | date | yes | - | - |
| duration | int | yes | - | - |
| date_end | Optional[date] | no | None | - |
| close_date | Optional[date] | no | None | - |
| resources | Optional[List[dict]] | no | [] | - |
| planned_cost | Optional[float] | no | 0.0 | - |
| actual_cost | Optional[float] | no | 0.0 | - |
| status | Optional[str] | no | 'planned' | - |
| is_closed | Optional[bool] | no | False | - |
| parent_id | Optional[UUID] | no | None | - |
| deal_id | UUID | yes | - | - |
| subcontractor_id | Optional[UUID] | no | None | - |


### Model `TaskCreate`

Source: `backend/app/schemas/task.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| description | Optional[str] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'new' | - |
| priority | Optional[str] | no | 'normal' | - |
| assigned_to_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_id | Optional[Union[str, UUID]] | no | None | - |
| assigned_to_user_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_user_id | Optional[Union[str, UUID]] | no | None | - |
| payer_id | Optional[Union[str, UUID]] | no | None | - |
| payee_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| due_time | Optional[str] | no | None | - |
| estimated_hours | Optional[float] | no | 0.0 | - |
| actual_hours | Optional[float] | no | 0.0 | - |
| budget | Optional[float] | no | None | - |
| category_code | Optional[str] | no | None | - |
| work_category | Optional[str] | no | None | - |
| tags | Optional[List[str]] | no | [] | - |
| attachments | Optional[List[Dict[str, Any]]] | no | [] | - |
| notify_assigned | Optional[bool] | no | True | - |
| notify_overdue | Optional[bool] | no | True | - |
| assignee_ids | Optional[List[Union[str, UUID]]] | no | None | - |
| watcher_ids | Optional[List[Union[str, UUID]]] | no | None | - |


### Model `TaskResponse`

Source: `backend/app/schemas/task.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| description | Optional[str] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'new' | - |
| priority | Optional[str] | no | 'normal' | - |
| assigned_to_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_id | Optional[Union[str, UUID]] | no | None | - |
| assigned_to_user_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_user_id | Optional[Union[str, UUID]] | no | None | - |
| payer_id | Optional[Union[str, UUID]] | no | None | - |
| payee_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| due_time | Optional[str] | no | None | - |
| estimated_hours | Optional[float] | no | 0.0 | - |
| actual_hours | Optional[float] | no | 0.0 | - |
| budget | Optional[float] | no | None | - |
| category_code | Optional[str] | no | None | - |
| work_category | Optional[str] | no | None | - |
| tags | Optional[List[str]] | no | [] | - |
| attachments | Optional[List[Dict[str, Any]]] | no | [] | - |
| notify_assigned | Optional[bool] | no | True | - |
| notify_overdue | Optional[bool] | no | True | - |
| assignee_ids | Optional[List[Union[str, UUID]]] | no | None | - |
| watcher_ids | Optional[List[Union[str, UUID]]] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| number | Optional[int] | no | None | - |
| completed_at | Optional[datetime] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `TaskUpdate`

Source: `backend/app/schemas/task.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | Optional[str] | no | None | - |
| description | Optional[str] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | None | - |
| priority | Optional[str] | no | None | - |
| assigned_to_id | Optional[Union[str, UUID]] | no | None | - |
| assigned_to_user_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_user_id | Optional[Union[str, UUID]] | no | None | - |
| payer_id | Optional[Union[str, UUID]] | no | None | - |
| payee_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| due_time | Optional[str] | no | None | - |
| estimated_hours | Optional[float] | no | None | - |
| actual_hours | Optional[float] | no | None | - |
| budget | Optional[float] | no | None | - |
| category_code | Optional[str] | no | None | - |
| work_category | Optional[str] | no | None | - |
| tags | Optional[List[str]] | no | None | - |
| attachments | Optional[List[Dict[str, Any]]] | no | None | - |
| notify_assigned | Optional[bool] | no | None | - |
| notify_overdue | Optional[bool] | no | None | - |
| executor_rating | Optional[int] | no | None | - |
| assignee_ids | Optional[List[Union[str, UUID]]] | no | None | - |
| watcher_ids | Optional[List[Union[str, UUID]]] | no | None | - |


### Model `TaskWithRelations`

Source: `backend/app/schemas/task.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| description | Optional[str] | no | None | - |
| deal_id | Optional[Union[str, UUID]] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'new' | - |
| priority | Optional[str] | no | 'normal' | - |
| assigned_to_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_id | Optional[Union[str, UUID]] | no | None | - |
| assigned_to_user_id | Optional[Union[str, UUID]] | no | None | - |
| created_by_user_id | Optional[Union[str, UUID]] | no | None | - |
| payer_id | Optional[Union[str, UUID]] | no | None | - |
| payee_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| due_time | Optional[str] | no | None | - |
| estimated_hours | Optional[float] | no | 0.0 | - |
| actual_hours | Optional[float] | no | 0.0 | - |
| budget | Optional[float] | no | None | - |
| category_code | Optional[str] | no | None | - |
| work_category | Optional[str] | no | None | - |
| tags | Optional[List[str]] | no | [] | - |
| attachments | Optional[List[Dict[str, Any]]] | no | [] | - |
| notify_assigned | Optional[bool] | no | True | - |
| notify_overdue | Optional[bool] | no | True | - |
| assignee_ids | Optional[List[str]] | no | None | - |
| watcher_ids | Optional[List[str]] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| number | Optional[int] | no | None | - |
| completed_at | Optional[datetime] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |
| deal_title | Optional[str] | no | None | - |
| stage_name | Optional[str] | no | None | - |
| assigned_to_name | Optional[str] | no | None | - |
| created_by_name | Optional[str] | no | None | - |
| assigned_to_user_name | Optional[str] | no | None | - |
| assigned_to_user_avatar_url | Optional[str] | no | None | - |
| created_by_user_name | Optional[str] | no | None | - |
| created_by_user_avatar_url | Optional[str] | no | None | - |
| payer_name | Optional[str] | no | None | - |
| payee_name | Optional[str] | no | None | - |
| source_auction_id | Optional[str] | no | None | - |
| executor_rating | Optional[int] | no | None | - |
| final_budget | Optional[float] | no | None | - |
| rating_coefficient | Optional[float] | no | None | - |
| deadline_coefficient | Optional[float] | no | None | - |
| penalty_amount | Optional[float] | no | None | - |
| matrix_quadrant | Optional[str] | no | None | - |
| matrix_sort_order | Optional[int] | no | None | - |
| matrix_manual | Optional[bool] | no | False | - |


### Model `DealProductCreate`

Source: `backend/app/schemas/deal_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | Union[str, UUID] | yes | - | - |
| product_id | Union[str, UUID] | yes | - | - |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | float | yes | - | - |
| unit | Optional[str] | no | None | - |
| unit_price | float | yes | - | - |
| discount_percent | Optional[float] | no | 0.0 | - |
| discount_amount | Optional[float] | no | 0.0 | - |
| tax_rate | Optional[float] | no | 0.0 | - |
| tax_included | Optional[bool] | no | False | - |
| currency | Optional[str] | no | 'RUB' | - |
| total_price | Optional[float] | no | None | - |
| discount_total | Optional[float] | no | 0.0 | - |
| tax_amount | Optional[float] | no | 0.0 | - |
| final_price | Optional[float] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'planned' | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | {} | - |


### Model `DealProductResponse`

Source: `backend/app/schemas/deal_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | Union[str, UUID] | yes | - | - |
| product_id | Union[str, UUID] | yes | - | - |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | float | yes | - | - |
| unit | Optional[str] | no | None | - |
| unit_price | float | yes | - | - |
| discount_percent | Optional[float] | no | 0.0 | - |
| discount_amount | Optional[float] | no | 0.0 | - |
| tax_rate | Optional[float] | no | 0.0 | - |
| tax_included | Optional[bool] | no | False | - |
| currency | Optional[str] | no | 'RUB' | - |
| total_price | Optional[float] | no | None | - |
| discount_total | Optional[float] | no | 0.0 | - |
| tax_amount | Optional[float] | no | 0.0 | - |
| final_price | Optional[float] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'planned' | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | {} | - |
| id | Union[str, UUID] | yes | - | - |
| product | Optional[ProductResponse] | no | None | - |
| invoice_links | List[DealProductInvoiceLinkResponse] | no | factory:list | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `DealProductUpdate`

Source: `backend/app/schemas/deal_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | Optional[float] | no | None | - |
| unit | Optional[str] | no | None | - |
| unit_price | Optional[float] | no | None | - |
| discount_percent | Optional[float] | no | None | - |
| discount_amount | Optional[float] | no | None | - |
| tax_rate | Optional[float] | no | None | - |
| tax_included | Optional[bool] | no | None | - |
| currency | Optional[str] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | None | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | None | - |


### Model `LeadProductCreate`

Source: `backend/app/schemas/lead_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| lead_id | Union[str, UUID] | yes | - | - |
| product_id | Union[str, UUID] | yes | - | - |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | float | yes | - | - |
| unit | Optional[str] | no | None | - |
| unit_price | float | yes | - | - |
| discount_percent | Optional[float] | no | 0.0 | - |
| discount_amount | Optional[float] | no | 0.0 | - |
| tax_rate | Optional[float] | no | 0.0 | - |
| currency | Optional[str] | no | 'RUB' | - |
| total_price | Optional[float] | no | None | - |
| discount_total | Optional[float] | no | 0.0 | - |
| tax_amount | Optional[float] | no | 0.0 | - |
| final_price | Optional[float] | no | None | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | {} | - |


### Model `LeadProductResponse`

Source: `backend/app/schemas/lead_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| lead_id | Union[str, UUID] | yes | - | - |
| product_id | Union[str, UUID] | yes | - | - |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | float | yes | - | - |
| unit | Optional[str] | no | None | - |
| unit_price | float | yes | - | - |
| discount_percent | Optional[float] | no | 0.0 | - |
| discount_amount | Optional[float] | no | 0.0 | - |
| tax_rate | Optional[float] | no | 0.0 | - |
| currency | Optional[str] | no | 'RUB' | - |
| total_price | Optional[float] | no | None | - |
| discount_total | Optional[float] | no | 0.0 | - |
| tax_amount | Optional[float] | no | 0.0 | - |
| final_price | Optional[float] | no | None | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | {} | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `LeadProductUpdate`

Source: `backend/app/schemas/lead_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | Optional[float] | no | None | - |
| unit | Optional[str] | no | None | - |
| unit_price | Optional[float] | no | None | - |
| discount_percent | Optional[float] | no | None | - |
| discount_amount | Optional[float] | no | None | - |
| tax_rate | Optional[float] | no | None | - |
| currency | Optional[str] | no | None | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | None | - |


### Model `ProductCategoryCreate`

Source: `backend/app/schemas/product_category.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| parent_id | Optional[Union[str, UUID]] | no | None | - |
| sort_order | Optional[int] | no | 0 | - |
| is_active | Optional[str] | no | 'Y' | - |


### Model `ProductCategoryResponse`

Source: `backend/app/schemas/product_category.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| parent_id | Optional[Union[str, UUID]] | no | None | - |
| sort_order | Optional[int] | no | 0 | - |
| is_active | Optional[str] | no | 'Y' | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `ProductCategoryUpdate`

Source: `backend/app/schemas/product_category.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| parent_id | Optional[Union[str, UUID]] | no | None | - |
| sort_order | Optional[int] | no | 0 | - |
| is_active | Optional[str] | no | 'Y' | - |


### Model `ProductCreate`

Source: `backend/app/schemas/product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| base_price | float | no | 0.0 | - |
| category_id | Optional[Union[str, UUID]] | no | None | - |


### Model `ProductResponse`

Source: `backend/app/schemas/product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| base_price | float | no | 0.0 | - |
| category_id | Optional[Union[str, UUID]] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `ProductUpdate`

Source: `backend/app/schemas/product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | Optional[str] | no | None | - |
| base_price | Optional[float] | no | None | - |
| category_id | Optional[Union[str, UUID]] | no | None | - |


### Model `TenderCreate`

Source: `backend/app/schemas/tender.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_product_id | str | yes | - | - |
| status | Optional[str] | no | None | - |
| winner_company_id | Optional[str] | no | None | - |
| submission_deadline | Optional[datetime] | no | None | - |


### Model `TenderOfferCreate`

Source: `backend/app/schemas/tender_offer.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| tender_id | str | yes | - | - |
| company_id | str | yes | - | - |
| status | Optional[str] | no | None | - |
| proposed_amount | Optional[float] | no | None | - |
| proposed_deadline | Optional[date] | no | None | - |
| comment | Optional[str] | no | None | - |


### Model `TenderOfferResponse`

Source: `backend/app/schemas/tender_offer.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| tender_id | str | yes | - | - |
| company_id | str | yes | - | - |
| status | str | yes | - | - |
| proposed_amount | Optional[float] | no | None | - |
| proposed_deadline | Optional[date] | no | None | - |
| comment | Optional[str] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `TenderOfferUpdate`

Source: `backend/app/schemas/tender_offer.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| status | Optional[str] | no | None | - |
| proposed_amount | Optional[float] | no | None | - |
| proposed_deadline | Optional[date] | no | None | - |
| comment | Optional[str] | no | None | - |


### Model `TenderResponse`

Source: `backend/app/schemas/tender.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| deal_product_id | str | yes | - | - |
| deal_id | str | yes | - | - |
| product_id | str | yes | - | - |
| direction_id | Optional[str] | no | None | - |
| status | str | yes | - | - |
| winner_company_id | Optional[str] | no | None | - |
| submission_deadline | Optional[datetime] | no | None | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `TenderUpdate`

Source: `backend/app/schemas/tender.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| status | Optional[str] | no | None | - |
| winner_company_id | Optional[str] | no | None | - |
| submission_deadline | Optional[datetime] | no | None | - |


### Model `StageProductAssignmentCreate`

Source: `backend/app/schemas/stage_product_assignment.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | Union[str, UUID] | yes | - | - |
| stage_id | Union[str, UUID] | yes | - | - |
| product_id | Union[str, UUID] | yes | - | - |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| subcontractor_product_id | Optional[Union[str, UUID]] | no | None | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| contract_due_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'not_started' | - |


### Model `StageProductAssignmentResponse`

Source: `backend/app/schemas/stage_product_assignment.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| deal_id | Union[str, UUID] | yes | - | - |
| stage_id | Union[str, UUID] | yes | - | - |
| product_id | Union[str, UUID] | yes | - | - |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| subcontractor_product_id | Optional[Union[str, UUID]] | no | None | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| contract_due_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'not_started' | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `StageProductAssignmentUpdate`

Source: `backend/app/schemas/stage_product_assignment.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| subcontractor_product_id | Optional[Union[str, UUID]] | no | None | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| start_date | Optional[date] | no | None | - |
| due_date | Optional[date] | no | None | - |
| contract_due_date | Optional[date] | no | None | - |
| status | Optional[str] | no | None | - |


### Model `StageProductSubtaskCreate`

Source: `backend/app/schemas/stage_product_subtask.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| assignment_id | Union[str, UUID] | yes | - | - |
| title | str | yes | - | - |
| due_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'not_started' | - |


### Model `StageProductSubtaskResponse`

Source: `backend/app/schemas/stage_product_subtask.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| assignment_id | Union[str, UUID] | yes | - | - |
| title | str | yes | - | - |
| due_date | Optional[date] | no | None | - |
| status | Optional[str] | no | 'not_started' | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `StageProductSubtaskUpdate`

Source: `backend/app/schemas/stage_product_subtask.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | Optional[str] | no | None | - |
| due_date | Optional[date] | no | None | - |
| status | Optional[str] | no | None | - |


### Model `SubcontractorCreate`

Source: `backend/app/schemas/subcontractor.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| company_id | Optional[Union[str, UUID]] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| general_contractor_id | Optional[Union[str, UUID]] | no | None | - |
| penalty_config | Optional[dict] | no | None | - |
| s3_prefix_tz | Optional[str] | no | None | - |
| s3_prefix_docs | Optional[str] | no | None | - |
| status | Optional[str] | no | 'active' | - |
| total_contract_value | Optional[float] | no | 0.0 | - |
| total_paid | Optional[float] | no | 0.0 | - |
| vat_rate | Optional[float] | no | 20.0 | - |
| vat_included | Optional[bool] | no | True | - |


### Model `SubcontractorResponse`

Source: `backend/app/schemas/subcontractor.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| title | str | yes | - | - |
| obj_name | Optional[str] | no | None | - |
| address | Optional[str] | no | None | - |
| object_type | Optional[str] | no | None | - |
| object_area | Optional[float] | no | None | - |
| company_id | Optional[Union[str, UUID]] | no | None | - |
| customer_id | Optional[Union[str, UUID]] | no | None | - |
| general_contractor_id | Optional[Union[str, UUID]] | no | None | - |
| penalty_config | Optional[dict] | no | None | - |
| s3_prefix_tz | Optional[str] | no | None | - |
| s3_prefix_docs | Optional[str] | no | None | - |
| status | Optional[str] | no | 'active' | - |
| total_contract_value | Optional[float] | no | 0.0 | - |
| total_paid | Optional[float] | no | 0.0 | - |
| vat_rate | Optional[float] | no | 20.0 | - |
| vat_included | Optional[bool] | no | True | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `SubcontractorStageCreate`

Source: `backend/app/schemas/subcontractor_stage.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| stage_type | Optional[str] | no | 'stage' | - |
| term_type | Optional[str] | no | 'work_days' | - |
| date_start | date | yes | - | - |
| duration | int | yes | - | - |
| date_end | Optional[date] | no | None | - |
| close_date | Optional[date] | no | None | - |
| resources | Optional[List[dict]] | no | [] | - |
| planned_cost | Optional[float] | no | 0.0 | - |
| actual_cost | Optional[float] | no | 0.0 | - |
| status | Optional[str] | no | 'planned' | - |
| parent_id | Optional[UUID] | no | None | - |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| subcontractor_id | Optional[UUID] | no | None | - |


### Model `SubcontractorStageResponse`

Source: `backend/app/schemas/subcontractor_stage.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| stage_type | Optional[str] | no | 'stage' | - |
| term_type | Optional[str] | no | 'work_days' | - |
| date_start | date | yes | - | - |
| duration | int | yes | - | - |
| date_end | Optional[date] | no | None | - |
| close_date | Optional[date] | no | None | - |
| resources | Optional[List[dict]] | no | [] | - |
| planned_cost | Optional[float] | no | 0.0 | - |
| actual_cost | Optional[float] | no | 0.0 | - |
| status | Optional[str] | no | 'planned' | - |
| parent_id | Optional[UUID] | no | None | - |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| subcontractor_id | Optional[UUID] | no | None | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `SubcontractorStageUpdate`

Source: `backend/app/schemas/subcontractor_stage.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| description | Optional[str] | no | None | - |
| stage_type | Optional[str] | no | 'stage' | - |
| term_type | Optional[str] | no | 'work_days' | - |
| date_start | date | yes | - | - |
| duration | int | yes | - | - |
| date_end | Optional[date] | no | None | - |
| close_date | Optional[date] | no | None | - |
| resources | Optional[List[dict]] | no | [] | - |
| planned_cost | Optional[float] | no | 0.0 | - |
| actual_cost | Optional[float] | no | 0.0 | - |
| status | Optional[str] | no | 'planned' | - |
| parent_id | Optional[UUID] | no | None | - |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| subcontractor_id | Optional[UUID] | no | None | - |


### Model `SubcontractorProductCreate`

Source: `backend/app/schemas/subcontractor_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| product_id | Union[str, UUID] | yes | - | - |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | float | yes | - | - |
| unit | Optional[str] | no | None | - |
| unit_price | float | yes | - | - |
| discount_percent | Optional[float] | no | 0.0 | - |
| discount_amount | Optional[float] | no | 0.0 | - |
| tax_rate | Optional[float] | no | 0.0 | - |
| currency | Optional[str] | no | 'RUB' | - |
| total_price | Optional[float] | no | None | - |
| discount_total | Optional[float] | no | 0.0 | - |
| tax_amount | Optional[float] | no | 0.0 | - |
| final_price | Optional[float] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'planned' | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | {} | - |


### Model `SubcontractorProductResponse`

Source: `backend/app/schemas/subcontractor_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| subcontractor_card_id | Union[str, UUID] | yes | - | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| product_id | Union[str, UUID] | yes | - | - |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | float | yes | - | - |
| unit | Optional[str] | no | None | - |
| unit_price | float | yes | - | - |
| discount_percent | Optional[float] | no | 0.0 | - |
| discount_amount | Optional[float] | no | 0.0 | - |
| tax_rate | Optional[float] | no | 0.0 | - |
| currency | Optional[str] | no | 'RUB' | - |
| total_price | Optional[float] | no | None | - |
| discount_total | Optional[float] | no | 0.0 | - |
| tax_amount | Optional[float] | no | 0.0 | - |
| final_price | Optional[float] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | 'planned' | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | {} | - |
| id | Union[str, UUID] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |


### Model `SubcontractorProductUpdate`

Source: `backend/app/schemas/subcontractor_product.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| custom_name | Optional[str] | no | None | - |
| custom_price | Optional[float] | no | None | - |
| quantity | Optional[float] | no | None | - |
| unit | Optional[str] | no | None | - |
| unit_price | Optional[float] | no | None | - |
| discount_percent | Optional[float] | no | None | - |
| discount_amount | Optional[float] | no | None | - |
| tax_rate | Optional[float] | no | None | - |
| currency | Optional[str] | no | None | - |
| contract_id | Optional[Union[str, UUID]] | no | None | - |
| stage_id | Optional[Union[str, UUID]] | no | None | - |
| status | Optional[str] | no | None | - |
| notes | Optional[str] | no | None | - |
| custom_properties | Optional[dict] | no | None | - |


### Model `KpDocumentCreate`

Source: `backend/app/schemas/kp.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| lead_id | str | yes | - | - |
| our_company_id | Optional[str] | no | None | - |
| template_id | Optional[str] | no | None | - |
| vat_rate | Optional[float] | no | 20.0 | - |


### Model `KpDocumentResponse`

Source: `backend/app/schemas/kp.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| lead_id | str | yes | - | - |
| number_seq | int | yes | - | - |
| number_display | str | yes | - | - |
| status | str | yes | - | - |
| current_version | int | yes | - | - |
| our_company_id | Optional[str] | yes | - | - |
| template_id | Optional[str] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |
| updated_at | Optional[datetime] | yes | - | - |
| versions | List[KpVersionResponse] | no | [] | - |


### Model `KpTemplateBindingCreate`

Source: `backend/app/schemas/kp.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| template_id | str | yes | - | - |
| our_company_id | str | yes | - | - |


### Model `KpTemplateBindingResponse`

Source: `backend/app/schemas/kp.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| template_id | str | yes | - | - |
| our_company_id | str | yes | - | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `KpTemplateResponse`

Source: `backend/app/schemas/kp.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| name | str | yes | - | - |
| docx_url | str | yes | - | - |
| pdf_url | Optional[str] | no | None | - |
| is_active | bool | no | True | - |
| id | str | yes | - | - |
| created_at | Optional[datetime] | no | None | - |
| updated_at | Optional[datetime] | no | None | - |


### Model `KpVersionResponse`

Source: `backend/app/schemas/kp.py`


| Field | Type | Required | Default | Constraints |
| --- | --- | --- | --- | --- |
| id | str | yes | - | - |
| kp_id | str | yes | - | - |
| version | int | yes | - | - |
| docx_url | Optional[str] | yes | - | - |
| pdf_url | Optional[str] | yes | - | - |
| total_amount | float | yes | - | - |
| vat_amount | float | yes | - | - |
| total_text | Optional[str] | yes | - | - |
| vat_text | Optional[str] | yes | - | - |
| template_id | Optional[str] | yes | - | - |
| created_at | Optional[datetime] | yes | - | - |


## Routers / Controllers Reference

### Router `deals`

Source: `backend/app/routers/deals.py`

Prefix: `/api/v1/deals`

Endpoints: `10`

#### `GET /api/v1/deals`

- Controller: `backend/app/routers/deals.py::get_deals`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `min_contract_value`: Optional[float] (optional, default=None, constraints=-); `max_contract_value`: Optional[float] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `customer_id`: Optional[str] (optional, default=None, constraints=-); `our_company_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DealResponse]`
  - Response contracts: [`DealResponse`](#model-dealresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `allowed_deal_ids`
    - `select`
    - `Deal.id.in_`
    - `db.execute`
    - `Deal.get_filtered`
    - `Deal.customer_id.in_`
    - `Deal.our_company_id.in_`
    - `or_`
    - `and_`
    - `Deal.title.ilike`
    - `Deal.obj_name.ilike`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/deals`

- Controller: `backend/app/routers/deals.py::create_deal`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DealCreate`](#model-dealcreate)
  - Response model: `DealResponse`
  - Response contracts: [`DealResponse`](#model-dealresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('projects'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `Deal.create`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/deals/{deal_id}`

- Controller: `backend/app/routers/deals.py::delete_deal`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
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
    - `_: Depends(require_section_write('projects'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `ensure_can_edit_record`
    - `Deal.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Проект не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/deals/{deal_id}`

- Controller: `backend/app/routers/deals.py::get_deal`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DealResponse`
  - Response contracts: [`DealResponse`](#model-dealresponse)
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

#### `PUT /api/v1/deals/{deal_id}`

- Controller: `backend/app/routers/deals.py::update_deal`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DealUpdate`](#model-dealupdate)
  - Response model: `DealResponse`
  - Response contracts: [`DealResponse`](#model-dealresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('projects'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `ensure_can_edit_record`
    - `HTTPException`
    - `Deal.update`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - `400`: `Нет данных для обновления`; body schema `{"detail": "..."}`
  - `404`: `Проект не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/deals/{deal_id}/activity`

- Controller: `backend/app/routers/deals.py::get_deal_activity`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: `category`: Optional[str] (optional, default=None, constraints=-); `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=50, constraints=-)
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
    - `select(EventLog).where(or_(and_(EventLog.entity_type == 'deal', EventLog.entity_id == deal_id_str), EventLog.details.like(details_pattern))).order_by(desc(EventLog.created_at)).limit`
    - `select(EventLog).where(or_(and_(EventLog.entity_type == 'deal', EventLog.entity_id == deal_id_str), EventLog.details.like(details_pattern))).order_by`
    - `User.id.in_`
    - `desc`
    - `select`
    - `select(EventLog).where`
    - `or_`
    - `and_`
    - `EventLog.details.like`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/deals/{deal_id}/folders`

- Controller: `backend/app/routers/deals.py::get_deal_folders`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
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
    - `storage_available`
    - `ensure_path`
  - Side effects: File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/deals/{deal_id}/gips`

- Controller: `backend/app/routers/deals.py::get_deal_gips`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
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
    - `select`
    - `User.id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/deals/{deal_id}/gips`

- Controller: `backend/app/routers/deals.py::set_deal_gips`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DealGipsUpdate`](#model-dealgipsupdate)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('projects'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `ensure_can_edit_record`
    - `db.execute`
    - `db.add`
    - `db.commit`
    - `HTTPException`
    - `DealGip`
    - `User.id.in_`
    - `delete`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `В payload передан неверный user_id`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/deals/{deal_id}/vat`

- Controller: `backend/app/routers/deals.py::update_deal_vat`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DealVatUpdate`](#model-dealvatupdate)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
    - `_: Depends(require_section_write('projects'))`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `require_section_write`
    - `ensure_can_edit_record`
    - `HTTPException`
    - `Deal.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Нет данных для обновления НДС`; body schema `{"detail": "..."}`
  - `404`: `Проект не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `leads`

Source: `backend/app/routers/leads.py`

Prefix: `/api/v1/leads`

Endpoints: `11`

#### `GET /api/v1/leads`

- Controller: `backend/app/routers/leads.py::get_leads`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `responsible_user_id`: Optional[str] (optional, default=None, constraints=-); `customer_id`: Optional[str] (optional, default=None, constraints=-); `our_company_id`: Optional[str] (optional, default=None, constraints=-); `sort_by`: Optional[str] (optional, default='created_at', constraints=-); `sort_dir`: Optional[str] (optional, default='desc', constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[LeadResponse]`
  - Response contracts: [`LeadResponse`](#model-leadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `get_section_permissions`
    - `and_`
    - `func.count`
    - `asc`
    - `desc`
    - `or_`
    - `Lead.customer_id.in_`
    - `Lead.our_company_id.in_`
    - `Lead.title.ilike`
    - `Lead.obj_name.ilike`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/leads`

- Controller: `backend/app/routers/leads.py::create_lead`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LeadCreate`](#model-leadcreate)
  - Response model: `LeadResponse`
  - Response contracts: [`LeadResponse`](#model-leadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Lead.create`
    - `LeadActivity.create`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/leads/activities/{activity_id}`

- Controller: `backend/app/routers/leads.py::delete_lead_activity`
- Data Contract:
  - Path params: `activity_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context; route may enforce role/section checks
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `LeadActivity.delete`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `400`: `System activities cannot be deleted`; body schema `{"detail": "..."}`
  - `403`: `Not author`; body schema `{"detail": "..."}`
  - `404`: `Activity not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/leads/{lead_id}`

- Controller: `backend/app/routers/leads.py::delete_lead`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
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
    - `Lead.get_by_id`
    - `HTTPException`
    - `ensure_can_edit_record`
    - `Lead.delete`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/leads/{lead_id}`

- Controller: `backend/app/routers/leads.py::get_lead`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `LeadResponse`
  - Response contracts: [`LeadResponse`](#model-leadresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Lead.get_by_id`
    - `HTTPException`
    - `get_section_permissions`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/leads/{lead_id}`

- Controller: `backend/app/routers/leads.py::update_lead`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `lead_update`: dict
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Depends`
    - `HTTPException`
    - `Lead.get_by_id`
    - `ensure_can_edit_record`
    - `Lead.update`
    - `LeadActivity.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `No fields to update`; body schema `{"detail": "..."}`
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/leads/{lead_id}/comments`

- Controller: `backend/app/routers/leads.py::add_lead_comment`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `body`: dict
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Depends`
    - `Lead.get_by_id`
    - `HTTPException`
    - `LeadActivity.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `Empty comment`; body schema `{"detail": "..."}`
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/leads/{lead_id}/convert`

- Controller: `backend/app/routers/leads.py::convert_lead`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
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
    - `Lead.get_by_id`
    - `HTTPException`
    - `Deal.create`
    - `LeadProduct.get_by_lead`
    - `Deal.calculate_total_value`
    - `Lead.update`
    - `Product.get_by_id`
    - `DealProduct.create`
    - `LeadActivity.create`
  - Side effects: DB write
- Error Handling:
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/leads/{lead_id}/files`

- Controller: `backend/app/routers/leads.py::upload_lead_file`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: `caption`: Optional[str] (optional, default=None, constraints=-)
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Form`
    - `Depends`
    - `clean_name`
    - `Lead.get_by_id`
    - `HTTPException`
    - `storage_available`
    - `ensure_path`
    - `write_upload_to_tmp`
    - `LeadActivity.create`
    - `upload_file_with_safe_extension`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `500`: `Storage not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/leads/{lead_id}/tasks`

- Controller: `backend/app/routers/leads.py::create_lead_task`
- Summary: Create a task linked to this lead and add a timeline entry.
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `body`: dict
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Depends`
    - `Lead.get_by_id`
    - `HTTPException`
    - `Task.create`
    - `LeadActivity.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `Title is required`; body schema `{"detail": "..."}`
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/leads/{lead_id}/timeline`

- Controller: `backend/app/routers/leads.py::get_lead_timeline`
- Summary: Return timeline activities for a lead. `types` is a comma-separated filter.
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: `limit`: int (optional, default=200, constraints=-); `offset`: int (optional, default=0, constraints=-); `types`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Lead.get_by_id`
    - `HTTPException`
    - `LeadActivity.created_at.desc`
    - `LeadActivity.activity_type.in_`
    - `select`
    - `db.execute`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `stages`

Source: `backend/app/routers/stages.py`

Prefix: `/api/v1/stages`

Endpoints: `13`

#### `GET /api/v1/stages`

- Controller: `backend/app/routers/stages.py::get_stages`
- Summary: Получить список всех этапов
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[StageResponse]`
  - Response contracts: [`StageResponse`](#model-stageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Stage.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/stages`

- Controller: `backend/app/routers/stages.py::create_stage`
- Summary: Создать новый этап
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageCreate`](#model-stagecreate)
  - Response model: `StageResponse`
  - Response contracts: [`StageResponse`](#model-stageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Stage.create`
    - `safe_refresh_deal_health_issues`
    - `HTTPException`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - `400`: `f'Ошибка создания этапа: {str(e)}`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/stages/deal/{deal_id}`

- Controller: `backend/app/routers/stages.py::get_stages_by_deal`
- Summary: Получить все этапы проекта
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[StageResponse]`
  - Response contracts: [`StageResponse`](#model-stageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Stage.get_by_deal_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/stages/deal/{deal_id}/dependencies`

- Controller: `backend/app/routers/stages.py::get_stage_dependencies_by_deal`
- Summary: Get stage dependencies for deal.
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
    - `Stage.get_by_deal_id`
    - `db.execute`
    - `normalize_dependency_type`
    - `StageDependency.successor_id.in_`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/stages/deal/{deal_id}/products`

- Controller: `backend/app/routers/stages.py::get_stage_products_by_deal`
- Summary: Get stage-product links for deal.
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
    - `db.get_bind`
    - `StageProductLink.get_by_deal`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/stages/gantt/{deal_id}`

- Controller: `backend/app/routers/stages.py::get_gantt_tree`
- Summary: Получить дерево этапов для Gantt диаграммы
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
    - `GanttService.get_gantt_tree`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Ошибка получения дерева Gantt`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/stages/{stage_id}`

- Controller: `backend/app/routers/stages.py::delete_stage`
- Summary: Удалить этап
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
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
    - `Stage.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `Stage.delete`
    - `safe_refresh_deal_health_issues`
    - `log_event`
    - `delete`
    - `or_`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `404`: `Этап не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/stages/{stage_id}`

- Controller: `backend/app/routers/stages.py::get_stage`
- Summary: Получить этап по ID
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `StageResponse`
  - Response contracts: [`StageResponse`](#model-stageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Stage.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Этап не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/stages/{stage_id}`

- Controller: `backend/app/routers/stages.py::update_stage`
- Summary: Обновить этап
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageUpdate`](#model-stageupdate)
  - Response model: `StageResponse`
  - Response contracts: [`StageResponse`](#model-stageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Stage.get_by_id`
    - `HTTPException`
    - `Stage.update`
    - `safe_refresh_deal_health_issues`
    - `GanttService.propagate_dates`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - `400`: `Ошибка обновления этапа`; body schema `{"detail": "..."}`
  - `404`: `Этап не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/stages/{stage_id}/copy`

- Controller: `backend/app/routers/stages.py::copy_stage`
- Summary: Create a new editable stage copy in the same deal.
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: Optional[StageCopyPayload] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `StageResponse`
  - Response contracts: [`StageResponse`](#model-stageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Stage`
    - `db.add`
    - `Stage.get_by_id`
    - `HTTPException`
    - `db.flush`
    - `db.commit`
    - `db.refresh`
    - `safe_refresh_deal_health_issues`
    - `db.execute`
    - `log_event`
    - `StageProductLink`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `404`: `Stage not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/stages/{stage_id}/dependency`

- Controller: `backend/app/routers/stages.py::set_stage_dependency`
- Summary: Replace stage predecessor dependencies.
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: dict (required, default=-, constraints=-)
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
    - `Stage.get_by_id`
    - `HTTPException`
    - `normalize_dependency_type`
    - `db.execute`
    - `StageDependency`
    - `db.add`
    - `db.flush`
    - `GanttService._resolve_successor_schedule`
    - `safe_refresh_deal_health_issues`
    - `db.commit`
    - `GanttService.propagate_dates`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `400`: `Stage cannot depend on itself`; `Predecessor stage must belong to the same deal`; `Dependency cycle is not allowed`; body schema `{"detail": "..."}`
  - `404`: `Stage not found`; `Predecessor stage not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/stages/{stage_id}/products`

- Controller: `backend/app/routers/stages.py::set_stage_products`
- Summary: Replace products assigned to stage.
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: dict (required, default=-, constraints=-)
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
    - `Stage.get_by_id`
    - `HTTPException`
    - `Deal.get_by_id`
    - `DealProduct.get_by_deal`
    - `StageProductLink.delete_by_stage`
    - `safe_refresh_deal_health_issues`
    - `StageProductLink.create`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - `400`: `Invalid deal products for stage`; body schema `{"detail": "..."}`
  - `404`: `Stage not found`; `Deal not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/stages/{stage_id}/propagate`

- Controller: `backend/app/routers/stages.py::propagate_dates`
- Summary: Пересчитать даты этапов при изменении параметров
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: `new_start_date`: Optional[str] (optional, default=None, constraints=-); `new_duration`: Optional[int] (optional, default=None, constraints=-)
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
    - `GanttService.propagate_dates`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Ошибка пересчета дат`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `tasks`

Source: `backend/app/routers/tasks.py`

Prefix: `/api/v1/tasks`

Endpoints: `11`

#### `GET /api/v1/tasks`

- Controller: `backend/app/routers/tasks.py::get_tasks`
- Summary: Получить список всех задач с фильтрами. Возвращает заголовок X-Total-Count.
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `assigned_to_id`: Optional[str] (optional, default=None, constraints=-); `assigned_to_user_id`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `priority`: Optional[str] (optional, default=None, constraints=-); `category_code`: Optional[str] (optional, default=None, constraints=-); `work_category`: Optional[str] (optional, default=None, constraints=-); `source`: Optional[str] (optional, default=None, constraints=-); `has_budget`: Optional[bool] (optional, default=None, constraints=-); `overdue`: Optional[bool] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-); `due_date_from`: Optional[str] (optional, default=None, constraints=-); `due_date_to`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[TaskWithRelations]`
  - Response contracts: [`TaskWithRelations`](#model-taskwithrelations)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `select`
    - `get_section_permissions`
    - `Task.created_at.desc`
    - `db.execute`
    - `Task.source_auction_id.isnot`
    - `Task.status.notin_`
    - `or_`
    - `func.count`
    - `Task.source_auction_id.is_`
    - `Task.title.ilike`
    - `Task.description.ilike`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tasks`

- Controller: `backend/app/routers/tasks.py::create_task`
- Summary: Создать новую задачу
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TaskCreate`](#model-taskcreate)
  - Response model: `TaskResponse`
  - Response contracts: [`TaskResponse`](#model-taskresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Deal.get_by_id`
    - `HTTPException`
    - `Stage.get_by_id`
    - `Company.get_by_id`
    - `User.get_by_id`
    - `db.execute`
    - `IncomeExpenseEntry`
    - `db.add`
    - `Task.create`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `400`: `Не удалось сохранить задачу: проверьте поля.`; body schema `{"detail": "..."}`
  - `404`: `Проект не найден`; `Этап не найден`; `Ответственный не найден`; `Assigned user not found`; `Created user not found`; body schema `{"detail": "..."}`
  - `503`: `Не удалось присвоить номер задаче, повторите попытку.`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/tasks/deals/{deal_id}/tasks`

- Controller: `backend/app/routers/tasks.py::get_deal_tasks`
- Summary: Получить все задачи проекта
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[TaskWithRelations]`
  - Response contracts: [`TaskWithRelations`](#model-taskwithrelations)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Deal.get_by_id`
    - `HTTPException`
    - `Task.created_at.desc`
    - `db.execute`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Проект не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/tasks/matrix/reorder`

- Controller: `backend/app/routers/tasks.py::reorder_task_matrix`
- Summary: Сохранить персональный порядок задач внутри квадранта матрицы.
- Data Contract:
  - Path params: none
  - Query params: `payload`: TaskMatrixReorder (required, default=-, constraints=-)
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
    - `HTTPException`
    - `db.execute`
    - `get_section_permissions`
    - `db.commit`
    - `db.add`
    - `Task.id.in_`
    - `TaskUserMatrix.task_id.in_`
    - `TaskUserMatrix`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid matrix quadrant`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/tasks/{task_id}`

- Controller: `backend/app/routers/tasks.py::delete_task`
- Summary: Удалить задачу
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
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
    - `Task.get_by_id`
    - `HTTPException`
    - `ensure_can_edit_record`
    - `db.execute`
    - `db.commit`
    - `Task.delete`
    - `delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Задача не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/tasks/{task_id}`

- Controller: `backend/app/routers/tasks.py::get_task`
- Summary: Получить задачу по ID
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `TaskWithRelations`
  - Response contracts: [`TaskWithRelations`](#model-taskwithrelations)
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
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `Задача не найдена`; `Р—Р°РґР°С‡Р° РЅРµ РЅР°Р№РґРµРЅР°`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/tasks/{task_id}`

- Controller: `backend/app/routers/tasks.py::update_task`
- Summary: Обновить задачу
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TaskUpdate`](#model-taskupdate)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `HTTPException`
    - `Task.get_by_id`
    - `ensure_can_edit_record`
    - `Deal.get_by_id`
    - `Stage.get_by_id`
    - `Company.get_by_id`
    - `User.get_by_id`
    - `ensure_entity_action_allowed`
    - `Task.update`
    - `IncomeExpenseEntry`
    - `db.add`
  - Side effects: DB write, DB read, Audit/Event logging
- Error Handling:
  - `400`: `Нет данных для обновления`; body schema `{"detail": "..."}`
  - `404`: `Task not found`; `Проект не найден`; `Этап не найден`; `Ответственный не найден`; `Payer company not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/tasks/{task_id}/attachments`

- Controller: `backend/app/routers/tasks.py::delete_task_attachment`
- Summary: Delete a specific task attachment.
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: `path`: str (required, default=-, constraints=-)
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
    - `Task.get_by_id`
    - `HTTPException`
    - `Task.update`
    - `delete_path`
  - Side effects: DB write
- Error Handling:
  - `404`: `Task not found`; `Attachment not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tasks/{task_id}/attachments`

- Controller: `backend/app/routers/tasks.py::upload_task_attachments`
- Summary: Upload attachments for a task.
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
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
    - `Task.get_by_id`
    - `HTTPException`
    - `storage_available`
    - `ensure_path`
    - `Task.update`
    - `clean_name`
    - `write_upload_to_tmp`
    - `upload_file_with_safe_extension`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `No files uploaded`; body schema `{"detail": "..."}`
  - `404`: `Task not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/tasks/{task_id}/matrix`

- Controller: `backend/app/routers/tasks.py::update_task_matrix_position`
- Summary: Обновить персональный квадрант задачи для текущего пользователя.
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: TaskMatrixUpdate (required, default=-, constraints=-)
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
    - `HTTPException`
    - `Task.get_by_id`
    - `db.execute`
    - `TaskUserMatrix`
    - `db.add`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Invalid matrix quadrant`; body schema `{"detail": "..."}`
  - `404`: `Task not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tasks/{task_id}/recalculate-penalty`

- Controller: `backend/app/routers/tasks.py::recalculate_task_penalty`
- Summary: Принудительно пересчитать штраф/бонус по задаче
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
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
    - `Task.get_by_id`
    - `HTTPException`
    - `Task.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `У задачи нет бюджета`; `Для пересчета нужна завершенная задача с оценкой`; `Нет данных для пересчета`; body schema `{"detail": "..."}`
  - `404`: `Задача не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `products`

Source: `backend/app/routers/products.py`

Prefix: `/api/v1/products`

Endpoints: `21`

#### `GET /api/v1/products`

- Controller: `backend/app/routers/products.py::get_products`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `category_id`: Optional[str] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ProductResponse]`
  - Response contracts: [`ProductResponse`](#model-productresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Product.get_all`
    - `Product.search`
    - `Product.get_by_category`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/products`

- Controller: `backend/app/routers/products.py::create_product`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ProductCreate`](#model-productcreate)
  - Response model: `ProductResponse`
  - Response contracts: [`ProductResponse`](#model-productresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Product.create`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to create product`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/categories/`

- Controller: `backend/app/routers/products.py::get_product_categories`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[ProductCategoryResponse]`
  - Response contracts: [`ProductCategoryResponse`](#model-productcategoryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ProductCategory.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/products/categories/`

- Controller: `backend/app/routers/products.py::create_product_category`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ProductCategoryCreate`](#model-productcategorycreate)
  - Response model: `ProductCategoryResponse`
  - Response contracts: [`ProductCategoryResponse`](#model-productcategoryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ProductCategory.create`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to create category`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/products/categories/{category_id}`

- Controller: `backend/app/routers/products.py::delete_product_category`
- Data Contract:
  - Path params: `category_id`: str (required, default=-, constraints=-)
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
    - `ProductCategory.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Category not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/categories/{category_id}`

- Controller: `backend/app/routers/products.py::get_product_category`
- Data Contract:
  - Path params: `category_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ProductCategoryResponse`
  - Response contracts: [`ProductCategoryResponse`](#model-productcategoryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ProductCategory.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Category not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/products/categories/{category_id}`

- Controller: `backend/app/routers/products.py::update_product_category`
- Data Contract:
  - Path params: `category_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ProductCategoryUpdate`](#model-productcategoryupdate)
  - Response model: `ProductCategoryResponse`
  - Response contracts: [`ProductCategoryResponse`](#model-productcategoryresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `ProductCategory.update`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to update category`; body schema `{"detail": "..."}`
  - `404`: `Category not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/products/deal/`

- Controller: `backend/app/routers/products.py::add_product_to_deal`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DealProductCreate`](#model-dealproductcreate)
  - Response model: `DealProductResponse`
  - Response contracts: [`DealProductResponse`](#model-dealproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Deal.get_by_id`
    - `HTTPException`
    - `Product.get_by_id`
    - `DealProductCreate`
    - `DealProduct.create`
    - `Deal.calculate_total_value`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to add product to deal`; body schema `{"detail": "..."}`
  - `404`: `Deal not found`; `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/deal/item/{deal_product_id}`

- Controller: `backend/app/routers/products.py::get_deal_product`
- Data Contract:
  - Path params: `deal_product_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `DealProductResponse`
  - Response contracts: [`DealProductResponse`](#model-dealproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DealProduct.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Deal product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/deal/{deal_id}`

- Controller: `backend/app/routers/products.py::get_deal_products`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[DealProductResponse]`
  - Response contracts: [`DealProductResponse`](#model-dealproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DealProduct.get_by_deal`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/products/deal/{deal_id}/quick-add/{product_id}`

- Controller: `backend/app/routers/products.py::quick_add_product_to_deal`
- Data Contract:
  - Path params: `deal_id`: str (required, default=-, constraints=-); `product_id`: str (required, default=-, constraints=-)
  - Query params: `quantity`: float (optional, default=1.0, constraints=-); `discount_percent`: float (optional, default=0.0, constraints=-)
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
    - `Deal.get_by_id`
    - `HTTPException`
    - `Product.get_by_id`
    - `DealProduct.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to add product to deal`; body schema `{"detail": "..."}`
  - `404`: `Deal not found`; `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/products/deal/{deal_product_id}`

- Controller: `backend/app/routers/products.py::remove_product_from_deal`
- Data Contract:
  - Path params: `deal_product_id`: str (required, default=-, constraints=-)
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
    - `DealProduct.get_by_id`
    - `HTTPException`
    - `DealProduct.delete`
    - `Deal.calculate_total_value`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Deal product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/products/deal/{deal_product_id}`

- Controller: `backend/app/routers/products.py::update_deal_product`
- Data Contract:
  - Path params: `deal_product_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`DealProductUpdate`](#model-dealproductupdate)
  - Response model: `DealProductResponse`
  - Response contracts: [`DealProductResponse`](#model-dealproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `DealProduct.update`
    - `HTTPException`
    - `Deal.calculate_total_value`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to update deal product`; body schema `{"detail": "..."}`
  - `404`: `Deal product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/products/lead/`

- Controller: `backend/app/routers/products.py::add_product_to_lead`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LeadProductCreate`](#model-leadproductcreate)
  - Response model: `LeadProductResponse`
  - Response contracts: [`LeadProductResponse`](#model-leadproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Lead.get_by_id`
    - `HTTPException`
    - `Product.get_by_id`
    - `LeadProductCreate`
    - `LeadProduct.create`
    - `Lead.calculate_total_value`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to add product to lead`; body schema `{"detail": "..."}`
  - `404`: `Lead not found`; `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/lead/item/{lead_product_id}`

- Controller: `backend/app/routers/products.py::get_lead_product`
- Data Contract:
  - Path params: `lead_product_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `LeadProductResponse`
  - Response contracts: [`LeadProductResponse`](#model-leadproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LeadProduct.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Lead product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/lead/{lead_id}`

- Controller: `backend/app/routers/products.py::get_lead_products`
- Data Contract:
  - Path params: `lead_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[LeadProductResponse]`
  - Response contracts: [`LeadProductResponse`](#model-leadproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LeadProduct.get_by_lead`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/products/lead/{lead_product_id}`

- Controller: `backend/app/routers/products.py::remove_product_from_lead`
- Data Contract:
  - Path params: `lead_product_id`: str (required, default=-, constraints=-)
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
    - `LeadProduct.get_by_id`
    - `HTTPException`
    - `LeadProduct.delete`
    - `Lead.calculate_total_value`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Lead product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/products/lead/{lead_product_id}`

- Controller: `backend/app/routers/products.py::update_lead_product`
- Data Contract:
  - Path params: `lead_product_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`LeadProductUpdate`](#model-leadproductupdate)
  - Response model: `LeadProductResponse`
  - Response contracts: [`LeadProductResponse`](#model-leadproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `LeadProduct.update`
    - `HTTPException`
    - `Lead.calculate_total_value`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to update lead product`; body schema `{"detail": "..."}`
  - `404`: `Lead product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/products/{product_id}`

- Controller: `backend/app/routers/products.py::delete_product`
- Data Contract:
  - Path params: `product_id`: str (required, default=-, constraints=-)
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
    - `Product.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/products/{product_id}`

- Controller: `backend/app/routers/products.py::get_product`
- Data Contract:
  - Path params: `product_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `ProductResponse`
  - Response contracts: [`ProductResponse`](#model-productresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Product.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/products/{product_id}`

- Controller: `backend/app/routers/products.py::update_product`
- Data Contract:
  - Path params: `product_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`ProductUpdate`](#model-productupdate)
  - Response model: `ProductResponse`
  - Response contracts: [`ProductResponse`](#model-productresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Product.update`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to update product`; body schema `{"detail": "..."}`
  - `404`: `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `task_auctions`

Source: `backend/app/routers/task_auctions.py`

Prefix: `/api/v1`

Endpoints: `12`

#### `GET /api/v1`

- Controller: `backend/app/routers/task_auctions.py::list_auctions`
- Summary: List all auctions with optional filters.
- Data Contract:
  - Path params: none
  - Query params: `status`: Optional[str] (optional, default=None, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=50, constraints=-)
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
    - `TaskAuction.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1`

- Controller: `backend/app/routers/task_auctions.py::create_auction`
- Summary: Create a new task auction.
- Data Contract:
  - Path params: none
  - Query params: `data`: TaskAuctionCreate (required, default=-, constraints=-); `created_by_id`: Optional[str] (optional, default=None, constraints=-)
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
    - `TaskAuction.create`
  - Side effects: DB write
- Error Handling:
  - `400`: `budget is required`; `items required for auction block`; `Block must have at least one item`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tasks/{task_id}/rate`

- Controller: `backend/app/routers/task_auctions.py::rate_executor`
- Summary: Rate the executor of a completed task (1-5 stars).
- Data Contract:
  - Path params: `task_id`: str (required, default=-, constraints=-)
  - Query params: `data`: RateExecutorRequest (required, default=-, constraints=-)
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
    - `Task.get_by_id`
    - `Task.update`
    - `User.get_by_id`
    - `User.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Rating must be 1-5`; `Task must be completed to rate`; `Task already rated`; `Task has no assigned user`; body schema `{"detail": "..."}`
  - `404`: `Task not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/{auction_id}`

- Controller: `backend/app/routers/task_auctions.py::cancel_auction`
- Summary: Cancel an auction (set status to cancelled).
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuction.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Cannot cancel awarded auction`; `Cannot cancel block with awarded tasks`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/{auction_id}`

- Controller: `backend/app/routers/task_auctions.py::get_auction`
- Summary: Get auction details with all bids.
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuctionBid.get_by_auction`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Auction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/{auction_id}`

- Controller: `backend/app/routers/task_auctions.py::update_auction`
- Summary: Update auction (only if status is 'new').
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
  - Query params: `data`: TaskAuctionUpdate (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuctionBid.get_by_auction`
    - `TaskAuction.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Cannot edit non-new auction`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/{auction_id}/bids`

- Controller: `backend/app/routers/task_auctions.py::list_bids`
- Summary: List all bids for an auction.
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuctionBid.get_by_auction`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Auction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/{auction_id}/bids`

- Controller: `backend/app/routers/task_auctions.py::create_bid`
- Summary: Submit a bid for an auction.
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
  - Query params: `data`: TaskAuctionBidCreate (required, default=-, constraints=-); `user_id`: Optional[str] (optional, default=None, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `TaskAuctionBid.get_by_user_and_auction`
    - `TaskAuctionBid.create`
    - `TaskAuctionBid.get_by_auction`
  - Side effects: DB write
- Error Handling:
  - `400`: `user_id is required`; `Auction is not open`; `You already have a bid. Use PATCH to update.`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/{auction_id}/bids/{bid_id}`

- Controller: `backend/app/routers/task_auctions.py::delete_bid`
- Summary: Withdraw a bid.
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-); `bid_id`: str (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuctionBid.get_by_id`
    - `TaskAuctionBid.delete`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Auction is not open`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; `Bid not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/{auction_id}/bids/{bid_id}`

- Controller: `backend/app/routers/task_auctions.py::update_bid`
- Summary: Update a bid.
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-); `bid_id`: str (required, default=-, constraints=-)
  - Query params: `data`: TaskAuctionBidUpdate (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuctionBid.get_by_id`
    - `TaskAuctionBid.get_by_auction`
    - `TaskAuctionBid.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Auction is not open`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; `Bid not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/{auction_id}/hard`

- Controller: `backend/app/routers/task_auctions.py::delete_auction`
- Summary: Hard delete an auction (admin use).
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `db.delete`
    - `db.commit`
    - `Task.get_by_id`
    - `db.execute`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Delete the created task before deleting this auction`; `Delete tasks created from block before deleting it`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/{auction_id}/select-winner`

- Controller: `backend/app/routers/task_auctions.py::select_winner`
- Summary: Select winner from bids and create a task.
- Data Contract:
  - Path params: `auction_id`: str (required, default=-, constraints=-)
  - Query params: `data`: SelectWinnerRequest (required, default=-, constraints=-)
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
    - `TaskAuction.get_by_id`
    - `HTTPException`
    - `TaskAuctionBid.get_by_id`
    - `Task.create`
    - `IncomeExpenseEntry`
    - `db.add`
    - `TaskAuction.update`
    - `Company.get_by_id`
    - `db.commit`
    - `db.refresh`
    - `Task.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Auction is not open`; `Block has no items`; `category_code, payer_id, payee_id and due_date required for task with budget`; `Invalid due_date`; body schema `{"detail": "..."}`
  - `404`: `Auction not found`; `Bid not found`; `Payer company not found`; `Payee company not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `tenders`

Source: `backend/app/routers/tenders.py`

Prefix: `/api/v1/tenders`

Endpoints: `8`

#### `POST /api/v1/tenders`

- Controller: `backend/app/routers/tenders.py::create_tender`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TenderCreate`](#model-tendercreate)
  - Response model: `TenderResponse`
  - Response contracts: [`TenderResponse`](#model-tenderresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Tender`
    - `db.add`
    - `TenderResponse.model_validate`
    - `DealProduct.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `Deal.get_by_id`
    - `Product.get_by_id`
    - `db.commit`
    - `db.refresh`
    - `TenderOffer`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Deal product not found`; `Deal or product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/tenders/company/{company_id}`

- Controller: `backend/app/routers/tenders.py::list_company_tenders`
- Data Contract:
  - Path params: `company_id`: str (required, default=-, constraints=-)
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
    - `Deal.id.in_`
    - `DealProduct.id.in_`
    - `select`
    - `Product.id.in_`
  - Side effects: DB read
- Error Handling:
  - `500`: `str(exc)`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/tenders/items`

- Controller: `backend/app/routers/tenders.py::list_tender_items`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-)
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
    - `db.get_bind`
    - `select`
    - `db.execute`
    - `DealProduct.deal_id.in_`
    - `Deal.id.in_`
    - `Tender.deal_product_id.in_`
    - `TenderOffer.tender_id.in_`
    - `Company.id.in_`
    - `Product.id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/tenders/offers/{offer_id}`

- Controller: `backend/app/routers/tenders.py::update_tender_offer`
- Data Contract:
  - Path params: `offer_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TenderOfferUpdate`](#model-tenderofferupdate)
  - Response model: `TenderOfferResponse`
  - Response contracts: [`TenderOfferResponse`](#model-tenderofferresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TenderOfferResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Amount is required to respond`; body schema `{"detail": "..."}`
  - `404`: `Offer not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/tenders/{tender_id}`

- Controller: `backend/app/routers/tenders.py::get_tender`
- Data Contract:
  - Path params: `tender_id`: str (required, default=-, constraints=-)
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
    - `TenderResponse.model_validate`
    - `select`
    - `Company.id.in_`
  - Side effects: DB read
- Error Handling:
  - `404`: `Tender not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/tenders/{tender_id}`

- Controller: `backend/app/routers/tenders.py::update_tender`
- Summary: Set tender fields — used for the admin "установка даты"
- Data Contract:
  - Path params: `tender_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TenderUpdate`](#model-tenderupdate)
  - Response model: `TenderResponse`
  - Response contracts: [`TenderResponse`](#model-tenderresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TenderResponse.model_validate`
    - `db.execute`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Tender not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tenders/{tender_id}/offers`

- Controller: `backend/app/routers/tenders.py::create_tender_offer`
- Data Contract:
  - Path params: `tender_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`TenderOfferCreate`](#model-tenderoffercreate)
  - Response model: `TenderOfferResponse`
  - Response contracts: [`TenderOfferResponse`](#model-tenderofferresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `TenderOffer`
    - `db.add`
    - `TenderOfferResponse.model_validate`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `db.refresh`
    - `and_`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Tender mismatch`; body schema `{"detail": "..."}`
  - `404`: `Tender not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/tenders/{tender_id}/select-winner`

- Controller: `backend/app/routers/tenders.py::select_winner`
- Data Contract:
  - Path params: `tender_id`: str (required, default=-, constraints=-)
  - Query params: `offer_id`: str (required, default=-, constraints=-)
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
  - `404`: `Tender not found`; `Offer not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `deal_execution`

Source: `backend/app/routers/deal_execution.py`

Prefix: `/api/v1`

Endpoints: `10`

#### `GET /api/v1/deals/{deal_id}/defacto`

- Controller: `backend/app/routers/deal_execution.py::get_defacto_view`
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
    - `Deal.get_by_id`
    - `HTTPException`
    - `DealProduct.get_by_deal`
    - `StageProductLink.get_by_deal`
    - `Stage.get_by_deal_id`
    - `Contract.get_by_deal_id`
    - `db.execute`
    - `db.commit`
    - `select`
    - `delete`
    - `StageProductAssignment.create`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Deal not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/deals/{deal_id}/dejure`

- Controller: `backend/app/routers/deal_execution.py::get_dejure_view`
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
    - `Deal.get_by_id`
    - `HTTPException`
    - `Contract.get_by_deal_id`
    - `db.execute`
    - `SubcontractorCard.get_by_id`
    - `select`
    - `selectinload`
  - Side effects: DB read
- Error Handling:
  - `404`: `Deal not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/defacto/assignments`

- Controller: `backend/app/routers/deal_execution.py::create_assignment`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageProductAssignmentCreate`](#model-stageproductassignmentcreate)
  - Response model: `StageProductAssignmentResponse`
  - Response contracts: [`StageProductAssignmentResponse`](#model-stageproductassignmentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `Deal.get_by_id`
    - `HTTPException`
    - `Stage.get_by_id`
    - `Product.get_by_id`
    - `SubcontractorCard.get_by_id`
    - `StageProductAssignment.create`
    - `safe_refresh_deal_health_issues`
    - `SubcontractorProduct.get_by_id`
  - Side effects: DB write
- Error Handling:
  - `400`: `Stage does not belong to deal`; body schema `{"detail": "..."}`
  - `404`: `Deal not found`; `Product not found`; `Subcontractor card not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/defacto/assignments/{assignment_id}`

- Controller: `backend/app/routers/deal_execution.py::delete_assignment`
- Data Contract:
  - Path params: `assignment_id`: str (required, default=-, constraints=-)
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
    - `StageProductAssignment.get_by_id`
    - `StageProductAssignment.delete`
    - `HTTPException`
    - `safe_refresh_deal_health_issues`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Assignment not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/defacto/assignments/{assignment_id}`

- Controller: `backend/app/routers/deal_execution.py::update_assignment`
- Data Contract:
  - Path params: `assignment_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageProductAssignmentUpdate`](#model-stageproductassignmentupdate)
  - Response model: `StageProductAssignmentResponse`
  - Response contracts: [`StageProductAssignmentResponse`](#model-stageproductassignmentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `StageProductAssignment.update`
    - `HTTPException`
    - `safe_refresh_deal_health_issues`
  - Side effects: DB write
- Error Handling:
  - `404`: `Assignment not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/defacto/assignments/{assignment_id}/subtasks`

- Controller: `backend/app/routers/deal_execution.py::list_subtasks`
- Data Contract:
  - Path params: `assignment_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[StageProductSubtaskResponse]`
  - Response contracts: [`StageProductSubtaskResponse`](#model-stageproductsubtaskresponse)
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

#### `POST /api/v1/defacto/assignments/{assignment_id}/subtasks/auto`

- Controller: `backend/app/routers/deal_execution.py::auto_create_subtasks`
- Data Contract:
  - Path params: `assignment_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[StageProductSubtaskResponse]`
  - Response contracts: [`StageProductSubtaskResponse`](#model-stageproductsubtaskresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `StageProductAssignment.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `safe_refresh_deal_health_issues`
    - `StageProductSubtask.create`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Assignment not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/defacto/subtasks`

- Controller: `backend/app/routers/deal_execution.py::create_subtask`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageProductSubtaskCreate`](#model-stageproductsubtaskcreate)
  - Response model: `StageProductSubtaskResponse`
  - Response contracts: [`StageProductSubtaskResponse`](#model-stageproductsubtaskresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `StageProductSubtask.create`
    - `StageProductAssignment.get_by_id`
    - `safe_refresh_deal_health_issues`
  - Side effects: DB write
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/defacto/subtasks/{subtask_id}`

- Controller: `backend/app/routers/deal_execution.py::delete_subtask`
- Data Contract:
  - Path params: `subtask_id`: str (required, default=-, constraints=-)
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
    - `StageProductSubtask.get_by_id`
    - `StageProductSubtask.delete`
    - `HTTPException`
    - `safe_refresh_deal_health_issues`
    - `StageProductAssignment.get_by_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Subtask not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/defacto/subtasks/{subtask_id}`

- Controller: `backend/app/routers/deal_execution.py::update_subtask`
- Data Contract:
  - Path params: `subtask_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`StageProductSubtaskUpdate`](#model-stageproductsubtaskupdate)
  - Response model: `StageProductSubtaskResponse`
  - Response contracts: [`StageProductSubtaskResponse`](#model-stageproductsubtaskresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `StageProductSubtask.update`
    - `HTTPException`
    - `StageProductAssignment.get_by_id`
    - `safe_refresh_deal_health_issues`
  - Side effects: DB write
- Error Handling:
  - `404`: `Subtask not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `executor`

Source: `backend/app/routers/executor.py`

Prefix: `/api/v1`

Endpoints: `11`

#### `GET /api/v1/executor/cards`

- Controller: `backend/app/routers/executor.py::get_executor_cards`
- Data Contract:
  - Path params: none
  - Query params: `company_id`: Optional[str] (optional, default=None, constraints=-)
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
    - `db.execute`
    - `select`
    - `CompanyUserLink.link_type.in_`
    - `or_`
    - `Stage.id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/executor/results`

- Controller: `backend/app/routers/executor.py::get_stage_results`
- Data Contract:
  - Path params: none
  - Query params: `stage_id`: str (required, default=-, constraints=-)
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
    - `StageResult.get_by_stage`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/executor/results/upload`

- Controller: `backend/app/routers/executor.py::upload_stage_results`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `stage_id`: str (required, default=-, constraints=-); `product_name`: str (required, default=-, constraints=-); `subcontractor_card_id`: str (required, default=-, constraints=-); `deal_id`: Optional[str] (optional, default=None, constraints=-); `comment`: Optional[str] (optional, default=None, constraints=-); `created_by`: Optional[str] (optional, default=None, constraints=-)
  - File params: `files`: List[UploadFile] (required, default=-, constraints=-)
  - Body: none
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
    - `storage_available`
    - `HTTPException`
    - `SubcontractorCard.get_by_id`
    - `upload_slot`
    - `Deal.get_by_id`
    - `clean_name`
    - `ensure_path`
    - `list_items`
    - `publish`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `400`: `Files are required`; body schema `{"detail": "..."}`
  - `404`: `Subcontractor card not found`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/executor/results/{result_id}`

- Controller: `backend/app/routers/executor.py::withdraw_stage_result`
- Data Contract:
  - Path params: `result_id`: str (required, default=-, constraints=-)
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
    - `StageResult.get_by_id`
    - `HTTPException`
    - `StageResult.delete`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Можно отозвать только результат на рассмотрении`; body schema `{"detail": "..."}`
  - `404`: `Result not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/executor/stages/{stage_id}`

- Controller: `backend/app/routers/executor.py::get_executor_stage`
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: `subcontractor_card_id`: str (required, default=-, constraints=-)
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
    - `Stage.get_by_id`
    - `HTTPException`
    - `SubcontractorCard.get_by_id`
    - `Deal.get_by_id`
    - `DealProduct.get_by_deal`
    - `StageProductLink.get_by_deal`
    - `db.execute`
    - `select`
    - `or_`
    - `selectinload`
  - Side effects: DB read
- Error Handling:
  - `404`: `Stage not found`; `Subcontractor card not found`; `Deal not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/executor/storage/create-folder`

- Controller: `backend/app/routers/executor.py::create_storage_folder`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `path`: str (required, default=-, constraints=-); `name`: str (required, default=-, constraints=-)
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
    - `Form`
    - `Depends`
    - `authorize_storage_path`
    - `ensure_path`
    - `clean_name`
  - Side effects: File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/executor/storage/delete`

- Controller: `backend/app/routers/executor.py::delete_storage_item`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-)
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
    - `storage_available`
    - `HTTPException`
    - `authorize_storage_path`
    - `delete_path`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Path is required`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/executor/storage/download`

- Controller: `backend/app/routers/executor.py::download_storage_item`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-)
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
    - `HTTPException`
    - `authorize_storage_path`
    - `get_download_href`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Path is required`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/executor/storage/list`

- Controller: `backend/app/routers/executor.py::list_storage_items`
- Data Contract:
  - Path params: none
  - Query params: `path`: str (required, default=-, constraints=-)
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
    - `authorize_storage_path`
    - `list_items`
  - Side effects: File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/executor/storage/publish`

- Controller: `backend/app/routers/executor.py::publish_storage_path`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `path`: str (required, default=-, constraints=-)
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
    - `Form`
    - `Depends`
    - `HTTPException`
    - `authorize_storage_path`
    - `publish`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Path is required`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/executor/storage/upload`

- Controller: `backend/app/routers/executor.py::upload_storage_files`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `path`: str (required, default=-, constraints=-)
  - File params: `files`: List[UploadFile] (required, default=-, constraints=-)
  - Body: none
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `user: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `storage_available`
    - `HTTPException`
    - `upload_slot`
    - `authorize_storage_path`
    - `ensure_path`
    - `upload.read`
    - `upload_bytes_with_safe_extension`
    - `clean_name`
  - Side effects: File/storage operation
- Error Handling:
  - `400`: `Files are required`; body schema `{"detail": "..."}`
  - `500`: `Storage is not configured`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `subcontractors`

Source: `backend/app/routers/subcontractors.py`

Prefix: `/api/v1/subcontractors`

Endpoints: `6`

#### `GET /api/v1/subcontractors`

- Controller: `backend/app/routers/subcontractors.py::get_subcontractors`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `min_contract_value`: Optional[float] (optional, default=None, constraints=-); `max_contract_value`: Optional[float] (optional, default=None, constraints=-); `search`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[SubcontractorResponse]`
  - Response contracts: [`SubcontractorResponse`](#model-subcontractorresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorCard.get_filtered`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/subcontractors`

- Controller: `backend/app/routers/subcontractors.py::create_subcontractor`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`SubcontractorCreate`](#model-subcontractorcreate)
  - Response model: `SubcontractorResponse`
  - Response contracts: [`SubcontractorResponse`](#model-subcontractorresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorCard.create`
    - `HTTPException`
    - `db.rollback`
  - Side effects: DB write
- Error Handling:
  - `500`: `str(exc)`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/subcontractors/{card_id}`

- Controller: `backend/app/routers/subcontractors.py::delete_subcontractor`
- Data Contract:
  - Path params: `card_id`: str (required, default=-, constraints=-)
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
    - `SubcontractorCard.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Карточка субподрядчика не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractors/{card_id}`

- Controller: `backend/app/routers/subcontractors.py::get_subcontractor`
- Data Contract:
  - Path params: `card_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `SubcontractorResponse`
  - Response contracts: [`SubcontractorResponse`](#model-subcontractorresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorCard.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Карточка субподрядчика не найдена`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/subcontractors/{card_id}`

- Controller: `backend/app/routers/subcontractors.py::update_subcontractor`
- Data Contract:
  - Path params: `card_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: `card_update`: dict
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Body`
    - `Depends`
    - `HTTPException`
    - `SubcontractorCard.update`
    - `db.rollback`
  - Side effects: DB write
- Error Handling:
  - `400`: `??? ?????? ??? ??????????`; body schema `{"detail": "..."}`
  - `404`: `???????? ????????????? ?? ???????`; body schema `{"detail": "..."}`
  - `500`: `str(exc)`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/subcontractors/{card_id}/vat`

- Controller: `backend/app/routers/subcontractors.py::update_subcontractor_vat`
- Data Contract:
  - Path params: `card_id`: str (required, default=-, constraints=-)
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
    - `HTTPException`
    - `SubcontractorCard.update`
  - Side effects: DB write
- Error Handling:
  - `400`: `Нет данных для обновления НДС`; `Ошибка чтения данных`; body schema `{"detail": "..."}`
  - `404`: `Субподрядчик не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `subcontractor_stages`

Source: `backend/app/routers/subcontractor_stages.py`

Prefix: `/api/v1/subcontractor-stages`

Endpoints: `10`

#### `GET /api/v1/subcontractor-stages`

- Controller: `backend/app/routers/subcontractor_stages.py::get_stages`
- Data Contract:
  - Path params: none
  - Query params: `skip`: int (optional, default=0, constraints=-); `limit`: int (optional, default=100, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[SubcontractorStageResponse]`
  - Response contracts: [`SubcontractorStageResponse`](#model-subcontractorstageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorStage.get_all`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/subcontractor-stages`

- Controller: `backend/app/routers/subcontractor_stages.py::create_stage`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`SubcontractorStageCreate`](#model-subcontractorstagecreate)
  - Response model: `SubcontractorStageResponse`
  - Response contracts: [`SubcontractorStageResponse`](#model-subcontractorstageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorStage.create`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `f'???????????? ???????????????? ??????????: {str(e)}`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractor-stages/gantt/{subcontractor_id}`

- Controller: `backend/app/routers/subcontractor_stages.py::get_gantt_tree`
- Data Contract:
  - Path params: `subcontractor_id`: str (required, default=-, constraints=-)
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
    - `SubcontractorGanttService.get_gantt_tree`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Ошибка загрузки дерева Gantt`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractor-stages/subcontractor/{subcontractor_id}`

- Controller: `backend/app/routers/subcontractor_stages.py::get_stages_by_subcontractor`
- Data Contract:
  - Path params: `subcontractor_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[SubcontractorStageResponse]`
  - Response contracts: [`SubcontractorStageResponse`](#model-subcontractorstageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorStage.get_by_subcontractor_card_id`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractor-stages/subcontractor/{subcontractor_id}/dependencies`

- Controller: `backend/app/routers/subcontractor_stages.py::get_stage_dependencies_by_subcontractor`
- Summary: Get subcontractor stage dependencies for subcontractor card.
- Data Contract:
  - Path params: `subcontractor_id`: str (required, default=-, constraints=-)
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
    - `SubcontractorStage.get_by_subcontractor_card_id`
    - `db.execute`
    - `normalize_dependency_type`
    - `SubcontractorStageDependency.successor_id.in_`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/subcontractor-stages/{stage_id}`

- Controller: `backend/app/routers/subcontractor_stages.py::delete_stage`
- Summary: Delete subcontractor stage
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
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
    - `SubcontractorStage.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `SubcontractorStage.delete`
  - Side effects: DB write, DB read
- Error Handling:
  - `404`: `Stage not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractor-stages/{stage_id}`

- Controller: `backend/app/routers/subcontractor_stages.py::get_stage`
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `SubcontractorStageResponse`
  - Response contracts: [`SubcontractorStageResponse`](#model-subcontractorstageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorStage.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Этап не найден`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/subcontractor-stages/{stage_id}`

- Controller: `backend/app/routers/subcontractor_stages.py::update_stage`
- Summary: Update subcontractor stage
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`SubcontractorStageUpdate`](#model-subcontractorstageupdate)
  - Response model: `SubcontractorStageResponse`
  - Response contracts: [`SubcontractorStageResponse`](#model-subcontractorstageresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorStage.get_by_id`
    - `HTTPException`
    - `SubcontractorStage.update`
    - `SubcontractorGanttService.propagate_dates`
  - Side effects: DB write
- Error Handling:
  - `400`: `Error updating stage`; body schema `{"detail": "..."}`
  - `404`: `Stage not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/subcontractor-stages/{stage_id}/dependency`

- Controller: `backend/app/routers/subcontractor_stages.py::set_stage_dependency`
- Summary: Set a single predecessor dependency for subcontractor stage.
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
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
    - `normalize_dependency_type`
    - `SubcontractorStageDependency`
    - `db.add`
    - `SubcontractorStage.get_by_id`
    - `HTTPException`
    - `db.execute`
    - `db.commit`
    - `SubcontractorGanttService.propagate_dates`
  - Side effects: DB write, DB read
- Error Handling:
  - `400`: `Stage cannot depend on itself`; `Predecessor stage must belong to the same subcontractor`; `Predecessor stage must belong to the same contract`; `Dependency cycle is not allowed`; body schema `{"detail": "..."}`
  - `404`: `Stage not found`; `Predecessor stage not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/subcontractor-stages/{stage_id}/propagate`

- Controller: `backend/app/routers/subcontractor_stages.py::propagate_dates`
- Data Contract:
  - Path params: `stage_id`: str (required, default=-, constraints=-)
  - Query params: `new_start_date`: Optional[str] (optional, default=None, constraints=-); `new_duration`: Optional[int] (optional, default=None, constraints=-)
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
    - `SubcontractorGanttService.propagate_dates`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `400`: `Ошибка перерасчета дат`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `subcontractor_products`

Source: `backend/app/routers/subcontractor_products.py`

Prefix: `/api/v1/subcontractor-products`

Endpoints: `5`

#### `POST /api/v1/subcontractor-products`

- Controller: `backend/app/routers/subcontractor_products.py::add_product_to_subcontractor`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`SubcontractorProductCreate`](#model-subcontractorproductcreate)
  - Response model: `SubcontractorProductResponse`
  - Response contracts: [`SubcontractorProductResponse`](#model-subcontractorproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorCard.get_by_id`
    - `HTTPException`
    - `Product.get_by_id`
    - `SubcontractorProduct.create`
  - Side effects: DB write
- Error Handling:
  - `404`: `Subcontractor card not found`; `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractor-products/subcontractor/{subcontractor_id}`

- Controller: `backend/app/routers/subcontractor_products.py::get_subcontractor_products`
- Data Contract:
  - Path params: `subcontractor_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[SubcontractorProductResponse]`
  - Response contracts: [`SubcontractorProductResponse`](#model-subcontractorproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorProduct.get_by_subcontractor_card`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `DELETE /api/v1/subcontractor-products/{item_id}`

- Controller: `backend/app/routers/subcontractor_products.py::delete_subcontractor_product`
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
    - `SubcontractorProduct.delete`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/subcontractor-products/{item_id}`

- Controller: `backend/app/routers/subcontractor_products.py::get_subcontractor_product`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `SubcontractorProductResponse`
  - Response contracts: [`SubcontractorProductResponse`](#model-subcontractorproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorProduct.get_by_id`
    - `HTTPException`
  - Side effects: No explicit side effects (read/transform path)
- Error Handling:
  - `404`: `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PUT /api/v1/subcontractor-products/{item_id}`

- Controller: `backend/app/routers/subcontractor_products.py::update_subcontractor_product`
- Data Contract:
  - Path params: `item_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`SubcontractorProductUpdate`](#model-subcontractorproductupdate)
  - Response model: `SubcontractorProductResponse`
  - Response contracts: [`SubcontractorProductResponse`](#model-subcontractorproductresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware)
  - Depends/Security:
    - `db: Depends(get_db)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `SubcontractorProduct.update`
    - `HTTPException`
  - Side effects: DB write
- Error Handling:
  - `400`: `Failed to update product`; body schema `{"detail": "..."}`
  - `404`: `Product not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `result_reviews`

Source: `backend/app/routers/result_reviews.py`

Prefix: `/api/v1`

Endpoints: `3`

#### `GET /api/v1/result-reviews`

- Controller: `backend/app/routers/result_reviews.py::list_result_reviews`
- Data Contract:
  - Path params: none
  - Query params: `deal_id`: Optional[str] (optional, default=None, constraints=-); `product_name`: Optional[str] (optional, default=None, constraints=-); `status`: Optional[str] (optional, default=None, constraints=-); `only_assigned`: bool (optional, default=False, constraints=-); `gip_user_id`: Optional[str] (optional, default=None, constraints=-); `limit`: Optional[int] (optional, default=None, constraints=ge=1, le=1000); `offset`: int (optional, default=0, constraints=ge=0)
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
    - `select`
    - `db.execute`
    - `or_`
    - `StageResult.created_at.desc`
    - `StageResult.status.is_`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/result-reviews/versions`

- Controller: `backend/app/routers/result_reviews.py::list_result_versions`
- Data Contract:
  - Path params: none
  - Query params: `stage_id`: str (required, default=-, constraints=-); `product_name`: str (required, default=-, constraints=-)
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
    - `StageResult.created_at.desc`
    - `db.execute`
    - `or_`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `PATCH /api/v1/result-reviews/{result_id}`

- Controller: `backend/app/routers/result_reviews.py::update_result_review`
- Data Contract:
  - Path params: `result_id`: str (required, default=-, constraints=-)
  - Query params: `payload`: ResultReviewUpdate (required, default=-, constraints=-)
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
    - `StageResult.get_by_id`
    - `HTTPException`
    - `StageResult.update`
    - `log_event`
  - Side effects: DB write, Audit/Event logging
- Error Handling:
  - `400`: `Invalid status`; `Комментарий обязателен при отклонении`; body schema `{"detail": "..."}`
  - `404`: `Result not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


### Router `kp`

Source: `backend/app/routers/kp.py`

Prefix: `/api/v1`

Endpoints: `8`

#### `GET /api/v1/kp/`

- Controller: `backend/app/routers/kp.py::list_kp`
- Data Contract:
  - Path params: none
  - Query params: `lead_id`: Optional[str] (optional, default=None, constraints=-)
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[KpDocumentResponse]`
  - Response contracts: [`KpDocumentResponse`](#model-kpdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `selectinload`
    - `db.execute`
    - `select`
    - `KpDocument.created_at.desc`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/kp/`

- Controller: `backend/app/routers/kp.py::create_kp`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`KpDocumentCreate`](#model-kpdocumentcreate)
  - Response model: `KpDocumentResponse`
  - Response contracts: [`KpDocumentResponse`](#model-kpdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.get`
    - `HTTPException`
    - `sequence_lock`
    - `KpDocument`
    - `db.add`
    - `db.refresh`
    - `db.commit`
  - Side effects: DB write
- Error Handling:
  - `404`: `Lead not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/kp/template-bindings`

- Controller: `backend/app/routers/kp.py::list_bindings`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[KpTemplateBindingResponse]`
  - Response contracts: [`KpTemplateBindingResponse`](#model-kptemplatebindingresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `select`
  - Side effects: DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/kp/template-bindings`

- Controller: `backend/app/routers/kp.py::bind_template`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body models: [`KpTemplateBindingCreate`](#model-kptemplatebindingcreate)
  - Response model: `KpTemplateBindingResponse`
  - Response contracts: [`KpTemplateBindingResponse`](#model-kptemplatebindingresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `KpTemplateBinding`
    - `db.add`
    - `db.get`
    - `HTTPException`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write
- Error Handling:
  - `404`: `Template not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/kp/templates`

- Controller: `backend/app/routers/kp.py::list_templates`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `List[KpTemplateResponse]`
  - Response contracts: [`KpTemplateResponse`](#model-kptemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `KpTemplate.created_at.desc`
    - `select`
  - Side effects: DB write, DB read
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/kp/templates`

- Controller: `backend/app/routers/kp.py::create_template`
- Data Contract:
  - Path params: none
  - Query params: none
  - Header params: none
  - Form params: `name`: str (required, default=-, constraints=-)
  - File params: `docx`: UploadFile (required, default=-, constraints=-); `pdf`: Optional[UploadFile] (optional, default=None, constraints=-)
  - Body: none
  - Response model: `KpTemplateResponse`
  - Response contracts: [`KpTemplateResponse`](#model-kptemplateresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Form`
    - `File`
    - `Depends`
    - `(settings.STORAGE_LOCAL_ROOT or '').rstrip`
    - `KpTemplate`
    - `db.add`
    - `ensure_path`
    - `upload_bytes_with_safe_extension`
    - `db.commit`
    - `db.refresh`
    - `clean_name`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - Explicit `HTTPException` not found in handler body
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `GET /api/v1/kp/{kp_id}`

- Controller: `backend/app/routers/kp.py::get_kp`
- Data Contract:
  - Path params: `kp_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: none
  - Body: none
  - Response model: `KpDocumentResponse`
  - Response contracts: [`KpDocumentResponse`](#model-kpdocumentresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `Depends`
    - `db.execute`
    - `HTTPException`
    - `selectinload`
    - `select`
  - Side effects: DB read
- Error Handling:
  - `404`: `KP not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`

#### `POST /api/v1/kp/{kp_id}/upload`

- Controller: `backend/app/routers/kp.py::upload_kp_version`
- Data Contract:
  - Path params: `kp_id`: str (required, default=-, constraints=-)
  - Query params: none
  - Header params: none
  - Form params: none
  - File params: `file`: UploadFile (required, default=-, constraints=-)
  - Body: none
  - Response model: `KpVersionResponse`
  - Response contracts: [`KpVersionResponse`](#model-kpversionresponse)
  - Success status: `200`
- Authentication & Authorization:
  - Access mode: JWT (AuthMiddleware) + current user context
  - Depends/Security:
    - `db: Depends(get_db)`
    - `_: Depends(CurrentUser)`
- Logic Flow:
  - Internal calls:
    - `File`
    - `Depends`
    - `(settings.STORAGE_LOCAL_ROOT or '').rstrip`
    - `KpVersion`
    - `db.add`
    - `db.get`
    - `HTTPException`
    - `ensure_path`
    - `upload_bytes_with_safe_extension`
    - `LeadProduct.get_by_lead`
    - `db.commit`
    - `db.refresh`
  - Side effects: DB write, File/storage operation
- Error Handling:
  - `404`: `KP not found`; body schema `{"detail": "..."}`
  - `422`: validation error by FastAPI/Pydantic, body schema `{'detail': [{'loc': [...], 'msg': '...', 'type': '...'}]}`


## Usage Examples (Domain)

### `GET /api/v1/deals`

```bash
curl -X GET http://localhost:8000/api/v1/deals -H "Authorization: Bearer $ACCESS_TOKEN" 
```

```json
{
  "created_at": "2026-01-01T00:00:00Z",
  "id": "00000000-0000-0000-0000-000000000000",
  "title": "string",
  "updated_at": "2026-01-01T00:00:00Z",
  "address": "string",
  "customer_id": "00000000-0000-0000-0000-000000000000",
  "general_contractor_id": "00000000-0000-0000-0000-000000000000",
  "obj_name": "string"
}
```


### `GET /api/v1/tasks`

```bash
curl -X GET http://localhost:8000/api/v1/tasks -H "Authorization: Bearer $ACCESS_TOKEN" 
```

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "title": "string",
  "actual_hours": 0.0,
  "assigned_to_id": "00000000-0000-0000-0000-000000000000",
  "assigned_to_name": "string",
  "assigned_to_user_avatar_url": "string",
  "assigned_to_user_id": "00000000-0000-0000-0000-000000000000",
  "assigned_to_user_name": "string"
}
```


### `POST /api/v1/deals`

```bash
curl -X POST http://localhost:8000/api/v1/deals -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"title": "string", "address": "string", "customer_id": "00000000-0000-0000-0000-000000000000", "general_contractor_id": "00000000-0000-0000-0000-000000000000", "obj_name": "string", "object_area": 0.0, "object_type": "string", "our_company_id": "00000000-0000-0000-0000-000000000000"}'
```

```json
{
  "created_at": "2026-01-01T00:00:00Z",
  "id": "00000000-0000-0000-0000-000000000000",
  "title": "string",
  "updated_at": "2026-01-01T00:00:00Z",
  "address": "string",
  "customer_id": "00000000-0000-0000-0000-000000000000",
  "general_contractor_id": "00000000-0000-0000-0000-000000000000",
  "obj_name": "string"
}
```


### `POST /api/v1/tasks`

```bash
curl -X POST http://localhost:8000/api/v1/tasks -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" -d '{"title": "string", "actual_hours": 0.0, "assigned_to_id": "00000000-0000-0000-0000-000000000000", "assigned_to_user_id": "00000000-0000-0000-0000-000000000000", "assignee_ids": "00000000-0000-0000-0000-000000000000", "attachments": {}, "budget": 0.0, "category_code": "string"}'
```

```json
{
  "id": "00000000-0000-0000-0000-000000000000",
  "title": "string",
  "actual_hours": 0.0,
  "assigned_to_id": "00000000-0000-0000-0000-000000000000",
  "assigned_to_user_id": "00000000-0000-0000-0000-000000000000",
  "assignee_ids": "00000000-0000-0000-0000-000000000000",
  "attachments": {},
  "budget": 0.0
}
```
