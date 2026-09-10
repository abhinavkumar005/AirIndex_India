# Deployment

## Status

PLANNED. Runtime images and services are not implemented.

## Initial Topology

Docker Compose is expected to run PostgreSQL (optionally TimescaleDB), Redis, FastAPI, Celery collection/processing workers, Celery Beat, frontend static assets, and optionally Nginx. The checked-in `docker-compose.yml` is a documentation-safe placeholder until service images exist.

## Environment Separation

Use separate development, test, staging, and production settings. Secrets come from a secure environment/secret manager, never Git. Production requires explicit CORS origins, strong admin authentication, TLS at ingress, backups, health checks, resource limits, monitoring, and migration controls.

## Release Process

Build immutable artifacts, run automated checks, review migrations, deploy to staging, run smoke tests, then promote with rollback instructions. Destructive migrations and data-retention changes require owner approval.

## Backup and Recovery

Before production use, define encrypted database backups, raw-evidence preservation, restore testing, recovery objectives, and incident ownership.
