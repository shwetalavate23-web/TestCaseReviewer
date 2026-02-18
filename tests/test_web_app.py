from main import STATE, _extract_coverage, render_page


def test_extract_coverage_from_report_line():
    report = "# title\n## Coverage Score: 76.50%\n"
    assert _extract_coverage(report) == "76.50%"


def test_render_page_disables_export_before_review():
    STATE.report = ""
    STATE.tree = ""
    STATE.coverage = ""
    STATE.error = ""

    page = render_page()

    assert "Export Review</button>" in page
    assert "disabled" in page


def test_render_page_shows_report_and_tree():
    STATE.report = "line1"
    STATE.tree = "tree"
    STATE.coverage = "100.00%"
    STATE.error = ""

    page = render_page()

    assert "Generated Review" in page
    assert "line1" in page
    assert "Coverage Tree (100.00%)" in page
    assert 'action="/export"' in page
