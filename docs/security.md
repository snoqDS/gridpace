# Security

## Vulnerability Tracking

GridPace uses pip-audit in CI to scan dependencies for known CVEs on every push.
Critical vulnerabilities block merge. High and above are tracked here and must
be resolved before any release.

Severity levels:
    Critical — CI fails, fix immediately, never merge
    High     — fix within one sprint, tracked below
    Medium   — fix at next dependency update cycle
    Low      — fix opportunistically

## Current Status

Last audit: 2026-06-24
Status: Clean — no known vulnerabilities

## Resolved Issues

| Date       | Package           | Version | CVEs | Severity | Resolution                        |
|------------|-------------------|---------|------|----------|-----------------------------------|
| 2026-06-24 | mlflow            | 1.27.0  | 73   | Critical | Removed — not yet used, add back in Phase 3 with compatible pandas version |
| 2026-06-24 | langsmith         | 0.8.17  | 1    | Medium   | Updated to 0.9.2                  |
| 2026-06-24 | pydantic-settings | 2.14.1  | 1    | Low      | Updated to 2.14.2                 |

## CI Integration

pip-audit runs automatically on every push via GitHub Actions.
See .github/workflows/ci.yml — Security audit step.
Fails the build if any vulnerability is found.

## Dependency Update Policy

Run pip-audit before any release:

    uv run pip-audit

Update vulnerable packages:

    uv add package@latest

If a package cannot be updated due to conflicts, document the reason
and mitigation in the Resolved Issues table above.

## Notes on MLflow

MLflow 1.27.0 had 73 known CVEs and conflicts with pandas>=3.
Removed in Phase 1. Will be re-added in Phase 3 with a compatible
pandas version pinned. Track at: https://github.com/mlflow/mlflow
