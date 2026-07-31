# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Instead, send an email to the project maintainer describing the issue. Include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

You will receive a response within 72 hours. Once the issue is confirmed and resolved, a public disclosure will be coordinated.

## Supported Versions

| Version | Supported          |
|---------|------------------- |
| latest  | :white_check_mark: |

## Security Considerations

- The application handles Chatwoot API tokens — these are loaded from environment variables only and never exposed to the frontend.
- Webhook endpoints support optional HMAC-SHA256 signature verification via `CHATWOOT_WEBHOOK_SECRET`.
- Cloudflare Access authentication is supported via `Cf-Access-Authenticated-User-Email` and JWT assertion headers.
- Docker containers run as non-root, read-only filesystem, with all capabilities dropped.
