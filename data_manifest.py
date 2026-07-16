"""
The catalog of business tables the assistant can query.

One entry per table. Each entry says where the data was vendored from (a sibling
portfolio repo), the domain it belongs to, and a plain-English description. The
description is what the language model reads to decide which tables and columns
answer a question, so it is written for that purpose: what the grain is, what the
money columns mean, and which codes are non-obvious.

Every dataset here is synthetic (Faker, fixed seeds) — no PHI, no real customers,
no real employees. See the source repos for how each was generated.

`table` is the base name; the loaded DuckDB table is `<domain>_<table>` so that
the several `dim_customer` / `fact_orders` tables across domains never collide.
"""

DOMAINS = {
    "healthcare": "Hospital revenue cycle — claims from submission through paid / denied / open AR.",
    "hr": "Workforce & people analytics — employees, attrition, hiring funnel, flight risk.",
    "finance": "GL reconciliation — ERP general ledger vs. subledger, and the exceptions between them.",
    "supplychain": "Cold-chain distribution — orders, inventory lots, warehouses, demand forecast.",
    "retail": "Specialty-meats wholesale — customers, sales lines, RFM analytics, cross-sell recs.",
    "migration": "A legacy-to-Fabric migration program — the moved data plus parallel-run validation.",
}

# domain, table, source path (relative to the portfolio-projects root), description
MANIFEST = [
    # ---- healthcare (revenue cycle)
    ("healthcare", "dim_payer", "healthcare-claims-analytics/data/dim_payer.csv",
     "Insurance payers. payer_type groups them (Medicare, Medicaid, Commercial, Medicare Advantage, Self-Pay)."),
    ("healthcare", "dim_provider", "healthcare-claims-analytics/data/dim_provider.csv",
     "Rendering providers with their specialty and facility."),
    ("healthcare", "dim_service_line", "healthcare-claims-analytics/data/dim_service_line.csv",
     "Clinical service lines (Cardiology, Oncology, Emergency Department, ...)."),
    ("healthcare", "fact_claims", "healthcare-claims-analytics/data/fact_claims.csv",
     "One row per claim. status is Paid / Denied / Pending. submitted_amount is billed charges, "
     "allowed_amount is the contracted amount, paid_amount is cash collected (all blank while Pending). "
     "denial_reason is a CARC code. ar_age_days / ar_bucket age the open (Pending) AR. Joins dim_payer, "
     "dim_provider, dim_service_line by their id columns."),
    ("healthcare", "ar_yield_predictions", "healthcare-claims-analytics/output/ar_yield_predictions.csv",
     "Predictive worklist for open AR: expected_nrv is forecast collectable cash, denial_propensity and "
     "expected_yield_rate are probabilities, priority_score ranks which claims to work first (priority_rank = 1 is highest)."),

    # ---- hr (workforce)
    ("hr", "dim_department", "hr-attrition-analytics/data/dim_department.csv", "Departments."),
    ("hr", "dim_job", "hr-attrition-analytics/data/dim_job.csv", "Job roles and their level."),
    ("hr", "dim_location", "hr-attrition-analytics/data/dim_location.csv", "Office locations / regions."),
    ("hr", "comp_benchmark", "hr-attrition-analytics/data/comp_benchmark.csv",
     "Market pay benchmark by job level — the reference for pay-equity and compa-ratio analysis."),
    ("hr", "fact_employees", "hr-attrition-analytics/data/fact_employees.csv",
     "One row per employee. is_active flags current staff; termination_date / term_type describe leavers "
     "(Voluntary vs Involuntary). compa_ratio is pay vs market (1.0 = at market). engagement_score, "
     "performance_rating, overtime_hours, months_since_promotion are attrition drivers. Joins dim_department, "
     "dim_job, dim_location by id."),
    ("hr", "fact_applications", "hr-attrition-analytics/data/fact_applications.csv",
     "Recruiting funnel — one row per application, with boolean stage flags (reached_screen ... hired) and days_to_fill."),
    ("hr", "fact_interventions", "hr-attrition-analytics/data/fact_hr_interventions.csv",
     "Retention interventions applied to employees and whether they stayed — for measuring intervention effect."),
    ("hr", "flight_risk_scores", "hr-attrition-analytics/output/flight_risk_scores.csv",
     "Model output: per-employee attrition risk_score (0-1), risk_band, and top_reason. Active employees only."),

    # ---- finance (GL reconciliation)
    ("finance", "dim_account", "gl-reconciliation-dashboard/data/dim_account.csv",
     "Chart of accounts. account_type and statement (Balance Sheet / Income Statement) classify each account."),
    ("finance", "dim_cost_center", "gl-reconciliation-dashboard/data/dim_cost_center.csv", "Cost centers."),
    ("finance", "erp_gl", "gl-reconciliation-dashboard/data/source_erp_gl.csv",
     "General-ledger transactions from the ERP (the system of record). amount, period, posted_date, account_id."),
    ("finance", "subledger_gl", "gl-reconciliation-dashboard/data/source_subledger_gl.csv",
     "The same transactions as recorded in the subledger. Reconciliation compares this against erp_gl."),
    ("finance", "reconciliation_exceptions", "gl-reconciliation-dashboard/output/gl_reconciliation_exceptions.csv",
     "Where ERP and subledger disagree. exception_type is Missing / Timing / Amount / Duplicate; variance_amount is the gap."),

    # ---- supplychain (cold-chain distribution)
    ("supplychain", "dim_customer", "supply-chain-control-tower/data/bronze/dim_customer.csv", "Customers being shipped to."),
    ("supplychain", "dim_product", "supply-chain-control-tower/data/bronze/dim_product.csv",
     "Products with category, shelf_life_days, unit_cost and unit_price."),
    ("supplychain", "dim_supplier", "supply-chain-control-tower/data/bronze/dim_supplier.csv", "Suppliers."),
    ("supplychain", "dim_warehouse", "supply-chain-control-tower/data/bronze/dim_warehouse.csv", "Distribution warehouses."),
    ("supplychain", "dim_lot", "supply-chain-control-tower/data/bronze/dim_lot.csv",
     "Inventory lots with production and expiry dates — drives FEFO (first-expiry-first-out) and spoilage risk."),
    ("supplychain", "fact_orders", "supply-chain-control-tower/data/bronze/fact_orders.csv",
     "One row per order line. qty_ordered vs qty_shipped measures fill rate; promised_date vs shipped_date "
     "measures on-time delivery (OTIF). Joins dim_customer, dim_product, dim_lot, dim_warehouse by id."),
    ("supplychain", "fact_inventory", "supply-chain-control-tower/data/bronze/fact_inventory_snapshot.csv",
     "Inventory on hand by product / lot / warehouse over time."),
    ("supplychain", "demand_forecast", "supply-chain-control-tower/analytics/output/forecast_next_28d.csv",
     "Model output: forecast_units by product category for the next 28 days."),

    # ---- retail (specialty-meats wholesale)
    ("retail", "dim_product", "Customer-Recommendation-Engine/data/catalog.csv",
     "Product catalog (sku, protein, description, unit_cost, unit_price)."),
    ("retail", "dim_customer", "Customer-Recommendation-Engine/data/customers.csv",
     "Wholesale customers with persona, region and assigned sales rep."),
    ("retail", "fact_sales", "Customer-Recommendation-Engine/data/sales_lines.csv",
     "One row per sales line. revenue and cost are dollars; quantity_lb is pounds sold. Denormalized with "
     "customer_name, region, rep, protein already joined in."),
    ("retail", "customer_analytics", "Customer-Recommendation-Engine/output/customer_analytics.csv",
     "Per-customer analytics: total_revenue, total_margin, rfm_segment, churn_risk, clv_12m_runrate, recency_days, "
     "expected_next_order — the customer-health table."),
    ("retail", "cross_sell_recommendations", "Customer-Recommendation-Engine/output/cross_sell_recommendations.csv",
     "Model output: recommended next SKUs per customer with a score and dollar opportunity."),

    # ---- migration (legacy -> Fabric program)
    ("migration", "dim_customer", "legacy-to-fabric-migration/data/customers.csv", "Customers in the migrated dataset."),
    ("migration", "dim_product", "legacy-to-fabric-migration/data/products.csv", "Products in the migrated dataset."),
    ("migration", "fact_orders", "legacy-to-fabric-migration/data/orders.csv", "Orders in the migrated dataset."),
    ("migration", "migration_plan", "legacy-to-fabric-migration/data/migration/migration_plan.csv",
     "The migration program plan — artifacts to move, their wave, complexity and status."),
    ("migration", "parallel_run_results", "legacy-to-fabric-migration/data/migration/parallel_run_results.csv",
     "Parallel-run validation: for each artifact, whether row counts / control totals / checksums matched between "
     "legacy and Fabric, and the GO/NO-GO verdict."),
]


def table_name(domain, table):
    return f"{domain}_{table}"
