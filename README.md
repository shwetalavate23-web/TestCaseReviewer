# TestCaseReviewer

A lightweight reviewer for Zephyr-exported test cases, available as both CLI and web app.

## What it does

- Loads test cases from `.csv` or `.json` Zephyr exports.
- Reviews each case against documentation guidelines:
  - Title
  - Steps
  - Expected Results
  - Test Type
  - Preconditions
  - Labels
- Produces feedback in bullet points with constructive, humorous-professional language.
- Calculates overall coverage percentage based on guideline completeness.
- Prints a tree illustration where:
  - More leaves (`🍃`) = better coverage.
  - Fewer leaves (`·`) = lower coverage.
  - A fruit (`🍎`) appears at 100% coverage.
- Ends with two friendly roast lines.

## Run the web app

```bash
python main.py
```

Then open `http://localhost:8000`.

In the web app you can:
- Upload Zephyr export files (`.csv`, `.json`).
- Generate and view the review in a read-only text box.
- View the coverage tree on the same page.
- Click **Export Review** to download the generated review as markdown.

## CLI usage

```bash
python reviewer.py <zephyr_export.csv>
python reviewer.py <zephyr_export.json> -o report.md
```

## Run tests

```bash
pytest -q
```
