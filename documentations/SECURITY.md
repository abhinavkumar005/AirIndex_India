# Security

## Baseline

- Store secrets only in environment variables or an approved secret manager.
- Commit `.env.example`, never `.env`, credentials, cookies, tokens, or certificates.
- Validate all input with bounded query parameters and canonical domain schemas.
- Use explicit CORS allowlists, secure headers, TLS in deployed environments, dependency scanning, and least-privilege database/service accounts.
- Protect administrative operations with authentication, role-based authorization, and audit logging.
- Return client-safe errors and correlation IDs; log restricted technical detail internally.

## Collection Security

Do not bypass source controls. Isolate connectors, restrict outbound destinations where practical, sanitize stored payloads, prevent secrets from entering logs, and implement per-source kill switches and bounded retries.

## Data Classification

Fare observations and public reference data are generally non-personal, but raw payloads may contain unexpected content. Minimize collection, avoid personal/session data, restrict raw access, and document any future sensitive fields before collection.

## Pending Threat Model

A formal threat model, admin identity provider, key rotation, dependency scanning workflow, and incident response runbook will be selected before deployment beyond local development.

Report suspected vulnerabilities privately to the project owner; do not publish secrets or exploit details in public issues.
