"""The warehouse and its catalog must match the manifest exactly — the model can
only be as correct as the schema description it is handed."""

from data_manifest import MANIFEST, table_name
from engine.query import run_query
from engine.warehouse import schema_catalog, table_names


def test_every_manifest_table_loads_with_rows(con):
    loaded = set(table_names(con))
    for domain, table, _source, _desc in MANIFEST:
        name = table_name(domain, table)
        assert name in loaded, f"{name} not loaded"
        n = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        assert n > 0, f"{name} loaded empty"


def test_catalog_lists_every_table_and_description(con):
    catalog = schema_catalog(con)
    for domain, table, _source, desc in MANIFEST:
        assert table_name(domain, table) in catalog
        assert desc.split(".")[0][:20] in catalog, f"description for {table} missing"


def test_table_names_are_domain_prefixed(con):
    # the disambiguation guarantee: dim_customer exists in three domains
    names = table_names(con)
    assert "supplychain_dim_customer" in names
    assert "retail_dim_customer" in names
    assert "migration_dim_customer" in names


def test_known_control_total(con):
    # a fact the healthcare repo independently verifies: 12,000 claims
    res = run_query(con, "SELECT COUNT(*) AS n FROM healthcare_fact_claims")
    assert res.ok and res.rows[0][0] == 12000
