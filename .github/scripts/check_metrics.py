#!/usr/bin/env python3
"""Regression guard — verify no stale metric residue after sync_metrics.py.

Reads APPS, TESTS, GOV from environment and a target HTML path as argv[1].
Scans for post-conditions that must hold after a successful sync. Exits
non-zero with a specific violation list when stale numbers slip through.

Post-conditions checked:
  (2) inner text of <strong data-count="N"> equals N
  (5) data-en="N/N governance" and data-tr="N/N yönetişim" both equal GOV
  (7) stat-number near "Apps"/"Uygulama" label equals APPS;
      stat-number near "Test" label equals TESTS (strip trailing +)
  (8) trust-kpi <strong>N</strong><small data-en="apps shipped|..."> equals APPS;
      same block with "tests in CI|..." equals TESTS
  (9) governance: gov || 'N/N'  literal equals GOV

(1), (3), (4), (6) are covered transitively — any surviving "OLD apps" /
"OLD governance" string after the sync is a bug in the substitution logic
and shows up as a violation on (2) / (5) / (7) / (8).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def check_html(content: str, apps: str, tests: str, gov: str) -> list[str]:
    """Return a list of violations. Empty list = clean."""
    violations: list[str] = []
    tests_plain = tests.rstrip("+")

    # (2) <strong data-count="N" data-suffix="S" ...>INNER</strong>
    # INNER must equal N + S (suffix preserves "+" on 900+ tests).
    for m in re.finditer(
        r'<strong([^>]*\bdata-count="(\d+)"[^>]*)>(\d+\+?)</strong>',
        content,
    ):
        attrs, count, inner = m.group(1), m.group(2), m.group(3)
        suffix_m = re.search(r'\bdata-suffix="([^"]*)"', attrs)
        suffix = suffix_m.group(1) if suffix_m else ""
        expected = f"{count}{suffix}"
        if inner != expected:
            violations.append(
                f'(2) data-count="{count}" data-suffix="{suffix}" '
                f'but inner="{inner}" (expected "{expected}")'
            )

    # (5) Governance attribute in EN + TR must equal GOV
    if gov:
        for m in re.finditer(
            r'data-en="(\d+/\d+)\s+governance"',
            content,
        ):
            if m.group(1) != gov:
                violations.append(
                    f'(5) data-en="{m.group(1)} governance" expected {gov}'
                )
        for m in re.finditer(
            r'data-tr="(\d+/\d+)\s+yönetişim"',
            content,
        ):
            if m.group(1) != gov:
                violations.append(
                    f'(5) data-tr="{m.group(1)} yönetişim" expected {gov}'
                )

    # (7) stat-number near Apps/Uygulama | Test label
    for m in re.finditer(
        r'<div class="stat-number">(\d+)\+?</div>\s*'
        r'<div class="stat-label"[^>]*data-en="([^"]+)"',
        content,
    ):
        num, label = m.group(1), m.group(2).lower()
        if ("apps" in label or "uygulama" in label) and num != apps:
            violations.append(
                f'(7) stat-number near Apps label = "{num}", expected {apps}'
            )
        elif "test" in label and num != tests_plain:
            violations.append(
                f'(7) stat-number near Tests label = "{num}", expected {tests_plain}'
            )

    # (8) trust-kpi <strong>N</strong><small data-en="...">
    for m in re.finditer(
        r"<strong>(\d+)\+?</strong>"
        r'<small[^>]*data-en="([^"]+)"',
        content,
    ):
        num, label = m.group(1), m.group(2).lower()
        if ("apps" in label or "uygulama" in label) and num != apps:
            violations.append(
                f'(8) trust-kpi apps = "{num}", expected {apps}'
            )
        elif "test" in label and num != tests_plain:
            violations.append(
                f'(8) trust-kpi tests = "{num}", expected {tests_plain}'
            )

    # (9) JS fallback literal
    if gov:
        for m in re.finditer(
            r"governance:\s*gov\s*\|\|\s*'(\d+/\d+)'",
            content,
        ):
            if m.group(1) != gov:
                violations.append(
                    f"(9) JS fallback = '{m.group(1)}', expected {gov}"
                )

    return violations


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: check_metrics.py <html_path>", file=sys.stderr)
        return 2

    html_path = Path(argv[1])
    apps = os.environ.get("APPS", "").strip()
    tests = os.environ.get("TESTS", "").strip()
    gov = os.environ.get("GOV", "").strip()

    if not apps or not tests:
        print("WARN: APPS or TESTS empty in env; skipping regression guard")
        return 0

    content = html_path.read_text(encoding="utf-8")
    violations = check_html(content, apps, tests, gov)

    if violations:
        print(f"Regression guard FAILED — {len(violations)} stale pattern(s) in {html_path}:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print(f"Regression guard OK: {html_path} (apps={apps}, tests={tests}, gov={gov})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
