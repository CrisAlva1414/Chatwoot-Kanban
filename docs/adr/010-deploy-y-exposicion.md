# ADR-010: Deploy y exposición

- **Fecha:** 2026-07-09
- **Actualizado:** 2026-07-13
- **Estado:** Aceptado

## Contexto

La app se despliega en un NAS on-premise. No debe exponer puertos directos
a internet por seguridad. El acceso externo se canaliza por Cloudflare.

## Decisión

| Componente       | Detalle                                                 |
| ---------------- | ------------------------------------------------------- |
| Imagen           | Docker multi-arch (amd64 + arm64) via GHCR              |
| CI/CD            | GitHub Actions: build + push a GHCR en cada push a main |
| Orquestación     | `docker compose` en el NAS                              |
| Deploy UI        | Arcane: gestiona contenedores, logs y actualizaciones   |
| Red              | Externa compartida (`ruki_cloudflared`)                 |
| Exposición       | Cloudflare Tunnel (ningún puerto en host)               |
| Autenticación    | Cloudflare Access (JWT validado en la app)              |

Nombrado de contenedores: `ruki-<proyecto>-<servicio>`.

## Flujo de deploy

1. Push a `main` → GitHub Actions construye imagen multi-arch y la publica en GHCR.
2. Arcane detecta la nueva imagen y ejecuta `docker compose pull && docker compose up -d`.
3. La app se conecta a PostgreSQL (contenedor `ruki-kanban-postgres`).
4. Cloudflare Tunnel expone la app sin puertos en el host.

## Consecuencias

- No hay `ports:` en docker-compose.
- La app debe validar el JWT de Cloudflare Access en cada request
  protegido (pendiente de implementar).
- El tunnel corre como contenedor separado en la misma red `ruki_cloudflared`.
- La imagen se ejecuta como usuario no-root (`appuser`).
- El Dockerfile usa multi-stage build para reducir tamaño.
