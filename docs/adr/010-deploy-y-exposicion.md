# ADR-010: Deploy y exposición

- **Fecha:** 2026-07-09
- **Estado:** Aceptado

## Contexto

La app se despliega en un NAS on-premise. No debe exponer puertos directos
a internet por seguridad. El acceso externo se canaliza por Cloudflare.

## Decisión

| Componente       | Detalle                                      |
| ---------------- | -------------------------------------------- |
| Imagen           | Docker multi-arch (amd64 + arm64) via GHCR   |
| Orquestación     | `docker compose` en el NAS                   |
| Red              | Externa compartida (`ruki_shared`)            |
| Exposición       | Cloudflare Tunnel (ningún puerto en host)    |
| Autenticación    | Cloudflare Access (JWT validado en la app)   |

Nombrado de contenedores: `ruki-<proyecto>-<servicio>`.

## Consecuencias

- No hay `ports:` en docker-compose.
- La app debe validar el JWT de Cloudflare Access en cada request
  protegido (pendiente de implementar).
- El tunnel corre como contenedor separado en la misma red `ruki_shared`.
