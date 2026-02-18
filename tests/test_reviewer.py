from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reviewer import TestCase as ReviewCase, render_tree, review_report, review_test_case


def test_review_test_case_full_score():
    case = ReviewCase(
        title="Verify login succeeds",
        steps="Open login page, enter credentials, click sign in",
        expected_results="Dashboard is displayed",
        test_type="functional",
        preconditions="User account exists",
        labels="auth,smoke",
    )

    feedback, score = review_test_case(case, 1)

    assert score == 6
    assert any("Gorgeous work" in line for line in feedback)


def test_review_report_shows_fruit_on_full_coverage():
    case = ReviewCase(
        title="Verify profile update",
        steps="Navigate to profile and click save",
        expected_results="Success toast appears",
        test_type="regression",
        preconditions="User is logged in",
        labels="profile",
    )

    report = review_report([case])

    assert "Coverage Score: 100.00%" in report
    assert "🍎" in report


def test_render_tree_low_coverage_has_fewer_leaves():
    low = render_tree(20)
    high = render_tree(80)

    assert low.count("🍃") < high.count("🍃")
