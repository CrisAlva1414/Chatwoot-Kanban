# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-31

### Added

- Initial public release as open source under MIT license.
- Kanban board with drag-and-drop pipeline stages using Chatwoot custom attributes.
- Task management system with automatic lifecycle transitions (active → due today → overdue → closed).
- Bidirectional sync with Chatwoot via `kanban_view_mensaje` and `kanban_view_fecha_termino` custom attributes.
- Webhook receiver for `contact_updated` and `conversation_updated` events with HMAC verification.
- Agent dashboard with performance stats and audit history.
- Dashboard App integration for embedding as Chatwoot iframe.
- Dark mode support via `prefers-color-scheme`.
- Docker multi-stage build with non-root user and read-only filesystem.
- CI/CD via GitHub Actions (lint, pytest, multi-arch Docker build to GHCR).
- Cloudflare Access authentication support (optional).

[0.1.0]: https://github.com/CrisAlva1414/Chatwoot-Kanban/releases/tag/v0.1.0
