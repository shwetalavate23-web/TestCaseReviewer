#!/usr/bin/env python3
"""Simple web app for reviewing Zephyr-exported test cases."""

from __future__ import annotations

import cgi
import html
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import NamedTemporaryFile

from reviewer import load_test_cases, render_tree, review_report


@dataclass
class AppState:
    report: str = ""
    tree: str = ""
    coverage: str = ""
    error: str = ""


STATE = AppState()


def _extract_coverage(report: str) -> str:
    marker = "## Coverage Score:"
    for line in report.splitlines():
        if line.startswith(marker):
            return line.replace(marker, "").strip()
    return "0.00%"


def render_page() -> str:
    safe_report = html.escape(STATE.report)
    safe_tree = html.escape(STATE.tree)
    safe_coverage = html.escape(STATE.coverage)
    safe_error = html.escape(STATE.error)
    download_button = (
        '<form method="POST" action="/export">'
        '<button type="submit">Export Review</button>'
        '</form>'
        if STATE.report
        else '<button type="button" disabled>Export Review</button>'
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Zephyr Test Case Reviewer</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; }}
    button {{ padding: .5rem .9rem; margin-top: .6rem; cursor: pointer; }}
    textarea {{ width: 100%; min-height: 320px; resize: vertical; font-family: Consolas, monospace; }}
    pre {{ background: #0b1220; color: #dbeafe; padding: .8rem; border-radius: 8px; overflow-x: auto; }}
    .row {{ display: flex; gap: .8rem; align-items: center; }}
    .error {{ color: #b91c1c; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Zephyr Test Case Reviewer</h1>

  <div class=\"card\">
    <form method=\"POST\" action=\"/review\" enctype=\"multipart/form-data\">
      <label for=\"upload\"><strong>Upload Zephyr export (.csv or .json):</strong></label><br>
      <input id=\"upload\" type=\"file\" name=\"zephyr_file\" accept=\".csv,.json\" required>
      <div class=\"row\">
        <button type=\"submit\">Generate Review</button>
      </div>
    </form>
    <div class=\"row\">{download_button}</div>
    {f'<p class="error">{safe_error}</p>' if safe_error else ''}
  </div>

  <div class=\"card\">
    <h2>Coverage Tree {f'({safe_coverage})' if safe_coverage else ''}</h2>
    <pre>{safe_tree or 'Upload a file and generate a review to see the tree.'}</pre>
  </div>

  <div class=\"card\">
    <h2>Generated Review</h2>
    <textarea readonly>{safe_report}</textarea>
  </div>
</body>
</html>
"""


class ReviewHandler(BaseHTTPRequestHandler):
    def _send_html(self, body: str, status: int = HTTPStatus.OK) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send_html(render_page())
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/review":
            self._handle_review()
            return
        if self.path == "/export":
            self._handle_export()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_review(self) -> None:
        STATE.error = ""
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
        )
        uploaded = form["zephyr_file"] if "zephyr_file" in form else None

        if not uploaded or not getattr(uploaded, "file", None):
            STATE.error = "Please upload a valid .csv or .json file."
            self._send_html(render_page(), HTTPStatus.BAD_REQUEST)
            return

        filename = Path(uploaded.filename or "uploaded_file").name
        suffix = Path(filename).suffix.lower()
        if suffix not in {".csv", ".json"}:
            STATE.error = "Unsupported file format. Please upload .csv or .json."
            self._send_html(render_page(), HTTPStatus.BAD_REQUEST)
            return

        try:
            file_bytes = uploaded.file.read()
            with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                test_cases = load_test_cases(Path(tmp.name))
            report = review_report(test_cases)
            STATE.report = report
            STATE.coverage = _extract_coverage(report)
            STATE.tree = render_tree(float(STATE.coverage.rstrip("%")))
        except Exception as exc:  # broad: user-provided file parsing errors should be shown in UI
            STATE.error = f"Could not process uploaded file: {exc}"

        self._send_html(render_page())

    def _handle_export(self) -> None:
        if not STATE.report:
            STATE.error = "Generate a review before exporting."
            self._send_html(render_page(), HTTPStatus.BAD_REQUEST)
            return

        payload = STATE.report.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/markdown; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="zephyr_review.md"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ReviewHandler)
    print(f"Serving Zephyr reviewer at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
