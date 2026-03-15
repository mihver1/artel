from pathlib import Path


def test_product_scope_doc_exists_with_required_sections():
    content = Path("PRODUCT_SCOPE.md").read_text(encoding="utf-8")

    assert "# Product scope" in content
    assert "## Supported now" in content
    assert "## Experimental / partial" in content
    assert "## Out of current scope" in content
