# Environment Guide

## Planned Prerequisites

- Git
- Docker with Docker Compose
- Python 3.12 (target; confirm during Phase 1)
- Node.js 22 LTS (target; confirm during frontend initialization)
- PostgreSQL 16 and Redis 7 when running outside containers

## Configuration Layers

Non-secret domain configuration lives in `configs/`. Runtime values and secrets come from environment variables modeled in `.env.example`. Local `.env` files are ignored by Git.

## Core Variables

`ENVIRONMENT`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`, `API_BASE_URL`, `CORS_ORIGINS`, and future admin/security values. Source credentials may be added only as placeholders after a source is approved.

## Local Commands

Executable setup commands will be added when backend/frontend packages exist. Do not infer that `docker compose up` is functional during Phase 0.
