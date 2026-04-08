# yakuphanycl.github.io

[![CI](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/ci.yml)
[![CodeQL](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/yakuphanycl/yakuphanycl.github.io/actions/workflows/codeql.yml)

Personal website repository for [yakuphanycl.github.io](https://yakuphanycl.github.io).

## Contents

- `index.html`: main landing page
- `projects/`: project pages and assets
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

## Repository Baseline

- CI and CodeQL run on push + pull request
- Dependabot is enabled for weekly GitHub Actions updates
- `main` branch protection requires review and resolved conversations
