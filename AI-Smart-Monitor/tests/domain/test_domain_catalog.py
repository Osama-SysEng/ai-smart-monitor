from app.domain import DOMAIN_CATALOG, supported_domains


def test_domain_catalog_exposes_the_supported_bounded_contexts():
    assert "reconciliation" in DOMAIN_CATALOG
    assert supported_domains() == tuple(DOMAIN_CATALOG)
