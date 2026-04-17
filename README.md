# yakuphanycl.github.io

[![CI](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/ci.yml)
[![CodeQL](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/codeql.yml)
[![Pulse](https://winstonredguard-production.up.railway.app/badge/yakuphanycl/yakuphanycl.github.io.svg)](https://winstonredguard-production.up.railway.app/p/yakuphanycl/yakuphanycl.github.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Personal website and project portfolio for [yakuphanycl.github.io](https://yakuphanycl.github.io).

The site hosts the public-facing surface for WinstonRedGuard monorepo
work — project pages for PulseBoard, instinct, wrg-devguard, and the
broader apps catalogue — plus the landing page that aggregates
shipping metrics straight from the repo's own automation.

## Contents

- `index.html`: main landing page with live project metrics
- `projects/`: per-project deep-dive pages (PulseBoard, instinct,
  wrg-devguard, etc.)
- `assets/`: shared CSS, JS, and images
- `sitemap.xml` and `robots.txt`: indexing metadata
- social preview assets (`og-image.*`, `favicon.*`)

## Local Preview

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Deployment

- GitHub Pages publishes from default branch (`main`)
- Site updates are delivered by GitHub Actions
- `sync-metrics.yml` periodically refreshes the apps/tests counters
  displayed on the landing page

## Repository Baseline

- CI and CodeQL run on push + pull request
- Dependabot is enabled for weekly GitHub Actions updates
- `main` branch protection requires review and resolved conversations
- Licensed under [MIT](LICENSE)

## Health

The [Pulse badge](https://winstonredguard-production.up.railway.app/p/yakuphanycl/yakuphanycl.github.io)
above is produced by PulseBoard (one of the projects hosted on this
site). It scores the repo from seven public signals — CI, coverage,
PR age, commit activity, dependency health, license, release cadence —
and links through to the full breakdown. The badge is intentionally
applied to this repo: if the site's own health score is not defensible
in public, neither is the pitch for PulseBoard.
