#!/usr/bin/env python3
"""Update live metrics in index.html from profile README values.

Reads APPS, TESTS, GOV from environment and a target HTML path as argv[1].
Detects stale values from the HTML itself, then applies substitutions across
all known display variants.

Handles nine variant classes (all reproduced in tests/fixtures/stale_index.html):

  (1) data-count attribute              data-count="N"
  (2) Inner text of <strong data-count> <strong data-count="N" ...>N</strong>
  (3) Natural-text EN/TR forms          "N apps", "N+ tests", "N uygulama", ...
  (4) Combined meta                     "N+ apps, M+ tests"
  (5) Governance attribute EN/TR        data-en="N/N governance", data-tr="N/N yönetişim"
  (6) Governance body text              "N/N governance", "N/N gates", "All N gates"
  (7) stat-number + sibling label       <div class="stat-number">N</div> ... data-en="Apps|Tests|..."
  (8) trust-kpi + localized small       <strong>N</strong><small data-en="apps shipped|tests in CI|...">
  (9) JS fallback literal               governance: gov || 'N/N'

Variants 2, 5, 7, 8, and 9 were the five patterns the original workflow missed
during the 59 -> 18 ratchet (see yakuphanycl/yakuphanycl.github.io#10).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def update_html(content: str, apps: str, tests: str, gov: str) -> tuple[str, dict]:
    """Apply all substitutions. Return (new_content, report)."""
    counts = re.findall(r'data-count="(\d+)"', content)
    if len(counts) < 2:
        return content, {"ok": False, "reason": "fewer than 2 data-count attributes"}
    old_tests, old_apps = counts[0], counts[1]

    gov_match = re.search(r"(\d+/\d+)(?=\s+governance)", content)
    old_gov = gov_match.group(1) if gov_match else ""

    # No early-return on "values match" — pattern (2) self-aligns inner text
    # to data-count and must run even on daily re-syncs so a previously buggy
    # sync doesn't leave permanent residue (the exact PR #10 scenario).
    # All substitutions are idempotent: old == new collapses each re.sub to
    # a no-op. We compute new, compare, write only when content changed.
    new = content

    # (1) data-count attribute — first two, tests then apps
    new = re.sub(rf'data-count="{old_tests}"', f'data-count="{tests}"', new, count=2)
    new = re.sub(rf'data-count="{old_apps}"', f'data-count="{apps}"', new, count=2)

    # (3) Natural-text variants (EN + TR) — run BEFORE inner-align so step (2)
    # always has the last word on <strong data-count> inner text. Previously
    # step (3) ran after step (2) and the f">{old}+<" variants could match
    # inner text that step (2) had just rewritten, flipping it back to the
    # stale value (reproduced by the PR#10-style buggy fixture).
    app_variants = [
        f"{old_apps}+ apps",
        f"{old_apps} apps",
        f"{old_apps}+ uygulama",
        f"{old_apps} uygulama",
        f">{old_apps}+<",
        f"{old_apps} apps registered",
    ]
    test_variants = [
        f"{old_tests}+ tests",
        f"{old_tests}+ test",
        f"{old_tests}+ CI tests",
        f"{old_tests}+ CI test",
        f">{old_tests}+<",
    ]
    for v in app_variants:
        new = new.replace(v, v.replace(old_apps, apps, 1))
    for v in test_variants:
        new = new.replace(v, v.replace(old_tests, tests, 1))

    # (2) Inner text of <strong data-count="N" data-suffix="S" ...>OLD</strong>
    # The pair (data-count, data-suffix) is authoritative — inner text must
    # equal their concatenation. Rebuild the inner from attrs so we preserve
    # "+" suffixes (e.g. 900+ tests) that live in data-suffix, not data-count.
    # INVARIANT: this block runs last among the strong-touching rewrites so
    # it always has the final say on inner text.
    def _align_strong_inner(m: re.Match[str]) -> str:
        attrs = m.group(1)
        count_m = re.search(r'\bdata-count="(\d+)"', attrs)
        if not count_m:
            return m.group(0)
        count = count_m.group(1)
        suffix_m = re.search(r'\bdata-suffix="([^"]*)"', attrs)
        suffix = suffix_m.group(1) if suffix_m else ""
        return f"<strong{attrs}>{count}{suffix}</strong>"

    new = re.sub(
        r'<strong([^>]*\bdata-count="\d+"[^>]*)>\d+\+?</strong>',
        _align_strong_inner,
        new,
    )

    # (4) Combined meta
    new = new.replace(
        f"{old_apps}+ apps, {old_tests}+ tests",
        f"{apps}+ apps, {tests}+ tests",
    )

    # (5, 6, 9) Governance patterns
    if gov:
        # (6) body text
        if old_gov:
            new = new.replace(f"{old_gov} governance", f"{gov} governance")
            new = new.replace(f"{old_gov} gates", f"{gov} gates")
            old_n, new_n = old_gov.split("/")[0], gov.split("/")[0]
            new = new.replace(f"All {old_n} gates", f"All {new_n} gates")

        # (5) EN attribute — data-en="N/N governance"
        new = re.sub(
            r'data-en="\d+/\d+(\s+governance")',
            lambda m: f'data-en="{gov}{m.group(1)}',
            new,
        )
        # (5) TR attribute — data-tr="N/N yönetişim"
        new = re.sub(
            r'data-tr="\d+/\d+(\s+yönetişim")',
            lambda m: f'data-tr="{gov}{m.group(1)}',
            new,
        )

        # (9) JS fallback literal — governance: gov || 'N/N'
        new = re.sub(
            r"(governance:\s*gov\s*\|\|\s*')\d+/\d+(')",
            lambda m: f"{m.group(1)}{gov}{m.group(2)}",
            new,
        )

    # (7) stat-number + sibling stat-label
    # Rewrite the raw number inside <div class="stat-number">N</div> when the
    # adjacent <div class="stat-label" data-en="..."> localizes to Apps/Tests.
    new = re.sub(
        rf'(<div class="stat-number">){old_apps}'
        rf'(</div>\s*<div class="stat-label"[^>]*data-en="[^"]*(?:[Aa]pps|[Uu]ygulama)[^"]*")',
        rf"\g<1>{apps}\g<2>",
        new,
    )
    new = re.sub(
        rf'(<div class="stat-number">){old_tests}'
        rf'(\+?</div>\s*<div class="stat-label"[^>]*data-en="[^"]*[Tt]est[^"]*")',
        rf"\g<1>{tests}\g<2>",
        new,
    )

    # (8) trust-kpi block — <strong>N</strong><small data-en="...apps/tests/...">
    def _update_trust_kpi(m: re.Match[str]) -> str:
        num = m.group(1)
        small_tag = m.group(2)  # full <small ...>...</small>
        label = m.group(3).lower()  # data-en value, for classification only
        if "apps" in label or "uygulama" in label:
            new_num = f"{apps}+" if num.endswith("+") else apps
        elif "test" in label:
            new_num = f"{tests}+" if num.endswith("+") else tests
        else:
            return m.group(0)
        return f"<strong>{new_num}</strong>{small_tag}"

    new = re.sub(
        r"<strong>(\d+\+?)</strong>"
        r'(<small[^>]*data-en="([^"]+)"[^>]*>[^<]*</small>)',
        _update_trust_kpi,
        new,
    )

    return new, {
        "ok": True,
        "changed": new != content,
        "apps": f"{old_apps}->{apps}",
        "tests": f"{old_tests}->{tests}",
        "gov": f"{old_gov}->{gov}" if gov else "",
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: sync_metrics.py <html_path>", file=sys.stderr)
        return 2

    html_path = Path(argv[1])
    apps = os.environ.get("APPS", "").strip()
    tests = os.environ.get("TESTS", "").strip()
    gov = os.environ.get("GOV", "").strip()

    if not apps or not tests:
        print("WARN: APPS or TESTS empty in env; skipping update")
        return 0

    content = html_path.read_text(encoding="utf-8")
    new_content, report = update_html(content, apps, tests, gov)

    if not report["ok"]:
        print(f"WARN: {report['reason']}; skipping update")
        return 0

    if report["changed"]:
        html_path.write_text(new_content, encoding="utf-8")
        print(
            f"Updated {html_path}: apps={report['apps']}, "
            f"tests={report['tests']}, gov={report['gov']}"
        )
    else:
        print(f"No changes needed: apps={apps}, tests={tests}, gov={gov}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
