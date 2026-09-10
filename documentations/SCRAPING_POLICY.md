# Data Collection and Scraping Policy

## Principle

Automated access is not presumed permitted. A source connector may be enabled only after its authorization, robots.txt position where applicable, Terms of Service, technical restrictions, rate limits, and data-use conditions are reviewed and recorded.

## Permitted Approaches

- Authorized APIs and government/partner feeds
- Explicitly permitted public data and approved integrations
- Source-provided sandbox/test systems
- Mock/synthetic sources for development

## Prohibited Techniques

- CAPTCHA or bot-protection bypass
- Authentication, paywall, or access-control circumvention
- Credential/session theft or reuse without authorization
- Fingerprint evasion, stealth intended to defeat restrictions, or rate-limit evasion
- Collection contrary to law, contract, policy, or recorded owner approval

## Connector Controls

Each connector will have a compliance state, owner/contact, evidence/reference date, allowed method, schedule, rate/concurrency limits, session policy, version, and kill switch. `UNKNOWN`, `RESTRICTED`, or `DISALLOWED` sources fail closed. Health status must distinguish technical failure from compliance disablement.

## Collection Conduct

Minimize requests and collected fields, identify the integration where appropriate, cache stable reference data, use bounded retries with backoff, honor retry/rate signals, and record collection events. Never collect personal data unless explicitly necessary, lawful, approved, and documented.

## Current Status

No real airline or OTA source is authorized or enabled. The initial pipeline will use clearly labeled synthetic/mock data. Each future source requires separate review and owner approval.
