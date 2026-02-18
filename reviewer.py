#!/usr/bin/env python3
"""Zephyr test case reviewer with guideline checks and coverage tree output."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


GUIDELINE_FIELDS = [
    "title",
    "steps",
    "expected_results",
    "test_type",
    "preconditions",
    "labels",
]

FIELD_ALIASES = {
    "title": ["title", "summary", "name", "test case", "testcase"],
    "steps": ["steps", "step", "test steps", "test script", "action"],
    "expected_results": ["expected results", "expected", "expected result", "result"],
    "test_type": ["test type", "type"],
    "preconditions": ["preconditions", "precondition", "setup"],
    "labels": ["labels", "label", "tags"],
}


@dataclass
class TestCase:
    title: str = ""
    steps: str = ""
    expected_results: str = ""
    test_type: str = ""
    preconditions: str = ""
    labels: str = ""


def _normalize_key(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()


def _extract_field(row: dict[str, Any], field: str) -> str:
    alias_lookup = {_normalize_key(key): key for key in row.keys()}
    for alias in FIELD_ALIASES[field]:
        key = alias_lookup.get(_normalize_key(alias))
        if key is not None:
            value = row.get(key, "")
            return "" if value is None else str(value).strip()
    return ""


def _to_test_case(row: dict[str, Any]) -> TestCase:
    return TestCase(**{field: _extract_field(row, field) for field in GUIDELINE_FIELDS})


def load_test_cases(path: Path) -> list[TestCase]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [_to_test_case(row) for row in csv.DictReader(handle)]

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            if "testcases" in payload and isinstance(payload["testcases"], list):
                payload = payload["testcases"]
            else:
                payload = [payload]
        if not isinstance(payload, list):
            raise ValueError("JSON input must be a list or object containing test case data.")
        rows: list[dict[str, Any]] = [item for item in payload if isinstance(item, dict)]
        return [_to_test_case(row) for row in rows]

    raise ValueError("Unsupported input format. Please provide a .csv or .json file.")


def _is_present(value: str) -> bool:
    return bool(value and value.strip())


def _contains_action_verb(text: str) -> bool:
    verbs = ["verify", "click", "select", "enter", "open", "check", "navigate", "submit"]
    lower = text.lower()
    return any(verb in lower for verb in verbs)


def review_test_case(test_case: TestCase, index: int) -> tuple[list[str], int]:
    feedback: list[str] = [f"- **Test Case {index}: {test_case.title or 'Untitled Test'}**"]
    score = 0

    if _is_present(test_case.title) and len(test_case.title) >= 8:
        score += 1
    else:
        feedback.append("  - Title needs a touch-up: make it specific enough that future-you won't need a detective hat.")

    if _is_present(test_case.steps) and _contains_action_verb(test_case.steps):
        score += 1
    else:
        feedback.append("  - Steps are shy right now. Add clear actions so execution is less "
                        "'guessing game' and more 'smooth speedrun'.")

    if _is_present(test_case.expected_results):
        score += 1
    else:
        feedback.append("  - Expected result is missing. Let's tell QA what success looks like before chaos does.")

    allowed_types = {"functional", "integration", "regression", "smoke", "performance", "security", "ui", "api"}
    if _is_present(test_case.test_type) and test_case.test_type.lower() in allowed_types:
        score += 1
    else:
        feedback.append("  - Test type is unclear. Pick a type (Functional/Regression/etc.) so reporting doesn't look like mystery genre.")

    if _is_present(test_case.preconditions):
        score += 1
    else:
        feedback.append("  - Preconditions are MIA. Add setup details so testers don't summon random environments.")

    if _is_present(test_case.labels):
        score += 1
    else:
        feedback.append("  - Labels are empty. A few tags now save a thousand filter-clicks later.")

    if score == len(GUIDELINE_FIELDS):
        feedback.append("  - Gorgeous work: this test case is cleaner than a freshly linted codebase.")

    return feedback, score


def render_tree(coverage: float) -> str:
    max_leaves = 10
    leaves = round((coverage / 100) * max_leaves)
    canopy = "🍃" * leaves + "·" * (max_leaves - leaves)
    fruit = " 🍎" if round(coverage, 2) >= 100 else ""
    return "\n".join(
        [
            f"      [{canopy}]{fruit}",
            "           ||",
            "           ||",
            "          /  \\",
            "         /____\\",
        ]
    )


def roast_lines(coverage: float) -> list[str]:
    if coverage >= 90:
        return [
            "You gave these test cases such good structure that even flaky tests are feeling stable.",
            "If this quality gets any higher, the bug backlog might file a complaint for neglect.",
        ]
    if coverage >= 60:
        return [
            "Solid effort—your test suite is jogging confidently, but it still wheezes on hill climbs.",
            "A few more details and this pack will graduate from 'pretty good' to 'release-day hero'.",
        ]
    return [
        "Right now these test cases are on a minimalist diet—great for aesthetics, rough for execution.",
        "Your bugs are currently playing hide-and-seek on easy mode. Let's add detail and ruin their fun.",
    ]


def review_report(test_cases: Iterable[TestCase]) -> str:
    cases = list(test_cases)
    if not cases:
        return "No test cases found in the input file."

    all_feedback: list[str] = ["# Zephyr Test Case Review", ""]
    total_possible = len(cases) * len(GUIDELINE_FIELDS)
    total_score = 0

    for index, case in enumerate(cases, start=1):
        feedback, score = review_test_case(case, index)
        total_score += score
        all_feedback.extend(feedback)
        all_feedback.append("")

    coverage = (total_score / total_possible) * 100 if total_possible else 0
    all_feedback.append(f"## Coverage Score: {coverage:.2f}%")
    all_feedback.append("")
    all_feedback.append("### Coverage Tree")
    all_feedback.append("```")
    all_feedback.append(render_tree(coverage))
    all_feedback.append("```")
    all_feedback.append("")
    all_feedback.append("### Friendly Roast")
    for line in roast_lines(coverage):
        all_feedback.append(f"- {line}")

    return "\n".join(all_feedback)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review Zephyr-exported test cases.")
    parser.add_argument("input_file", type=Path, help="Path to Zephyr export (.csv or .json)")
    parser.add_argument("-o", "--output", type=Path, help="Optional output file path")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    test_cases = load_test_cases(args.input_file)
    report = review_report(test_cases)

    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
